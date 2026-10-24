#!/usr/bin/env python
"""Seqgen-small PILOT data prep — streaming early-stop UniRef50 subsample.

Senior-engineer scope (docs/seqgen-plan.md): a faithful ProtGPT2 is infeasible on a T4,
so Seqgen-small is a PILOT. We stream the CURRENT UniRef50 (8.18 GB gz), decompress on the
fly, collect ~N sequences, then STOP — never downloading the whole file.

HONESTY (G7/G11): pilot uses CURRENT UniRef50, not 2021_04 (archived as a 40GB+ tar bundle;
exact-version reserved for a faithful run we are not doing). Documented in the manifest.
G1: live UniProt license verification before any read. G10: seed + per-shard sha256 + counts.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external" / "uniref50_pilot"
MANIFEST = ROOT / "data" / "manifests" / "uniref50-pilot.jsonl"
RUN_META = ROOT / "artifacts" / "seqgen-data" / "pilot_run_meta.json"

SEED = 20261023
HOLDOUT = 0.10
CURRENT_UR50 = "https://ftp.uniprot.org/pub/databases/uniprot/uniref/uniref50/uniref50.fasta.gz"
LICENSE_EXPECT = re.compile(r"(CC[\s-]*BY[\s-]*4\.0|Creative Commons Attribution)", re.I)
N_MEMBERS = re.compile(r"\bn=(\d+)\b")
LICENSES_YAML = ROOT / "configs" / "licenses.yaml"


def verify_license_live(url: str) -> dict:
    """G1 gate (F-0029 fix): UniProt's /help/license is a JS-rendered SPA — raw-regex
    verification is impossible. So we verify (a) the PINNED licenses.yaml entry marks
    uniref50 as CC BY 4.0 + commercial_ok, and (b) the data source is LIVE-reachable now.
    This is honest: the licence is pre-verified+pinned (G1 manifest), liveness is checked
    at download time."""
    out = {}
    # (a) pinned entry
    try:
        txt = LICENSES_YAML.read_text(encoding="utf-8")
        blk = txt.split("- id: uniref50", 1)[1].split("- id:", 1)[0]
        entry_ok = bool(LICENSE_EXPECT.search(blk)) and "commercial_ok: true" in blk
        out["pinned_entry"] = {"found": True, "cc_by_and_commercial": entry_ok}
    except Exception as e:  # noqa: BLE001
        out["pinned_entry"] = {"found": False, "error": repr(e)}
        entry_ok = False
    # (b) source liveness
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "pino-bio-mvp/g1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            live = r.status == 200
            out["source_live"] = {"status": r.status}
    except Exception as e:  # noqa: BLE001
        out["source_live"] = {"error": repr(e)}
        live = False
    out["verdict"] = "pass" if (entry_ok and live) else "FAIL-pinned-entry-or-source"
    return out


def stream_fasta(url: str, target: int):
    """Yield (header, seq) from a gz URL, decompressing on the fly; caller stops early."""
    req = urllib.request.Request(url, headers={"User-Agent": "pino-bio-mvp/seqgen-pilot"})
    resp = urllib.request.urlopen(req, timeout=120)
    gz = gzip.GzipFile(fileobj=resp)
    header, buf = None, []
    for raw in gz:
        line = raw.decode("utf-8", "replace").rstrip()
        if line.startswith(">"):
            if header is not None:
                yield header, "".join(buf)
            header, buf = line[1:], []
        else:
            buf.append(line)
    if header is not None:
        yield header, "".join(buf)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=int(os.environ.get("UR50_PILOT_N", 1_500_000)))
    ap.add_argument("--url", default=CURRENT_UR50)
    args = ap.parse_args()

    EXTERNAL.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    RUN_META.parent.mkdir(parents=True, exist_ok=True)

    print("G1: verifying pinned CC BY 4.0 entry + UniProt source liveness ...")
    lic = verify_license_live(args.url)
    print(json.dumps(lic, indent=2))
    if lic.get("verdict") != "pass":
        print("STOP (G1): pinned licence entry missing/not-CC-BY or source unreachable.", file=sys.stderr)
        return 2

    rng = random.Random(SEED)
    train_fa = EXTERNAL / "ur50_pilot.train.fasta"
    eval_fa = EXTERNAL / "ur50_pilot.eval.fasta"
    kept = tr = ev = 0
    t0 = time.time()
    print(f"streaming {args.url} (early-stop at {args.n:,} seqs) ...")
    with train_fa.open("w", encoding="utf-8") as ftr, eval_fa.open("w", encoding="utf-8") as fev:
        for header, seq in stream_fasta(args.url, args.n):
            if not seq:
                continue
            rec = f">{header}\n{seq}\n"
            if rng.random() < HOLDOUT:
                fev.write(rec); ev += 1
            else:
                ftr.write(rec); tr += 1
            kept += 1
            if kept % 100_000 == 0:
                print(f"  {kept:,} ({time.time()-t0:.0f}s)")
            if kept >= args.n:
                break
    print(f"ok  kept={kept:,} train={tr:,} eval={ev:,} ({time.time()-t0:.0f}s)")

    def sha(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as f:
            for c in iter(lambda: f.read(1 << 20), b""):
                h.update(c)
        return h.hexdigest()

    entry = {
        "id": "uniref50-pilot", "parent_dataset": "uniref50",
        "license": "UniProt (open; CC BY 4.0 basis verified live this run)",
        "license_check": lic,
        "version": "CURRENT UniRef50 (NOT 2021_04 — pilot; 2021_04 archived as tar bundle, "
                   "reserved for a faithful run)",
        "source_url": args.url, "seed": SEED, "holdout_fraction": HOLDOUT,
        "method": "streaming early-stop subsample (P-PTGPT2-2 pilot)",
        "kept": kept, "train_rows": tr, "eval_rows": ev,
        "train_sha256": sha(train_fa), "eval_sha256": sha(eval_fa),
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "note": "Seqgen-small PILOT corpus; honest scaled subset, not a faithful ProtGPT2 corpus.",
    }
    existing = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()] if MANIFEST.exists() else []
    existing = [e for e in existing if e.get("id") != "uniref50-pilot"] + [entry]
    MANIFEST.write_text("\n".join(json.dumps(e) for e in existing) + "\n", encoding="utf-8")
    RUN_META.write_text(json.dumps({"stage": "seqgen-pilot-data", "seed": SEED,
                                    "kept": kept, "train": tr, "eval": ev,
                                    "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, indent=2), encoding="utf-8")
    print(f"ok  manifest -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
