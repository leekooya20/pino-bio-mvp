#!/usr/bin/env python
"""UniRef50 subsample builder + live-license verifier + manifest writer
(PinoBio MVP-4 — Seqgen-small / ProtGPT2 replica, G1/G7/G10/G11).

Reference recipe (G11, docs/reading-list.md): Ferruz et al. 2022 trained on
UniRef50 **v2021_04** (49,874,565 seqs), 10% random holdout -> 44.88M train /
4.99M eval, dedup = UniRef50's inherent 50%-identity clustering (no extra step),
block 512, BPE. We replicate the DATA SEMANTICS faithfully at a documented
smaller scale (P-PTGPT2-2: an 8M stratified subsample curriculum stage), never a
blind copy.

HARD RULES enforced here:
- G1  : UniProt license is verified **LIVE at download** before any sequence is
        accepted (configs/licenses.yaml basis: "re-verify snapshot license at
        download time"). On a license-field change the build STOPS.
- G7  : exact counts, never rounded; the manifest records what was actually read.
- G10 : seed (20261023) + release pin + per-shard sha256 go into the manifest and
        run_meta; the holdout split is deterministic from the seed.
- G11 : faithful corpus version (2021_04) + inherent-cluster dedup; our ONLY
        deviation is the documented subsample (P-PTGPT2-2), labelled as such.

This script does not fabricate data. Point it at a UniRef50 v2021_04 FASTA
(UNIREF50_FASTA env or argv[1]); on compute it streams, verifies, subsamples and
writes data/manifests/uniref50-subsample.jsonl + the train/eval shards.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external" / "uniref50_2021_04"
MANIFEST = ROOT / "data" / "manifests" / "uniref50-subsample.jsonl"
RUN_META = ROOT / "artifacts" / "seqgen-data" / "run_meta.json"

SEED = 20261023                      # G10 (matches the program seed)
RELEASE = "2021_04"                  # [REF] exact reference corpus version
TARGET_SEQUENCES = int(os.environ.get("UR50_TARGET", 8_000_000))  # [P-PTGPT2-2]
HOLDOUT_FRACTION = 0.10              # [REF] 10% random eval holdout
# UniProt previous-releases FTP path for the pinned release (used only if no local
# file is supplied; large — on compute attach the dataset instead).
SOURCE_URL = (
    "https://ftp.uniprot.org/pub/databases/uniprot/"
    "previous_releases/release-2021_04/uniref/uniref50/uniref50.fasta.gz"
)
# G1: UniProt license pages we re-read live before accepting data. We assert the
# page still states the open/CC BY 4.0 basis our licenses.yaml entry relies on.
LICENSE_URLS = [
    "https://www.uniprot.org/help/license",
    "https://rest.uniprot.org/uniref/search?query=*&size=0",  # presence/terms header probe
]
LICENSE_EXPECT = re.compile(r"(CC[\s-]*BY[\s-]*4\.0|Creative Commons Attribution)", re.I)

# UniRef50 FASTA headers end with "n=<cluster_size> Tax=... RepID=..." — the cluster
# size (member count) drives our stratification so rare clusters are not washed out.
N_MEMBERS = re.compile(r"\bn=(\d+)\b")


def sha256_bytes_stream(fh) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    for chunk in iter(lambda: fh.read(1 << 20), b""):
        h.update(chunk)
        n += len(chunk)
    return h.hexdigest(), n


def verify_license_live() -> dict:
    """G1 gate: the UniProt license basis must still be live before we accept data."""
    results = {}
    ok = False
    for url in LICENSE_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pino-bio-mvp/g1-licence-check"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read(200_000).decode("utf-8", "replace")
                hit = bool(LICENSE_EXPECT.search(body))
                results[url] = {"status": r.status, "license_phrase_found": hit}
                ok = ok or hit
        except Exception as e:  # noqa: BLE001 — record, do not crash the gate silently
            results[url] = {"error": repr(e)}
    results["verdict"] = "pass" if ok else "FAIL-license-not-confirmed-live"
    return results


def stratum_of(cluster_size: int) -> str:
    if cluster_size <= 1:
        return "singleton"
    if cluster_size <= 10:
        return "small_2_10"
    if cluster_size <= 100:
        return "mid_11_100"
    return "large_100plus"


def iter_fasta(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    header = None
    buf: list[str] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(buf)
                header = line[1:].strip()
                buf = []
            else:
                buf.append(line.strip())
        if header is not None:
            yield header, "".join(buf)


def main() -> int:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    RUN_META.parent.mkdir(parents=True, exist_ok=True)

    # --- G1: live license gate FIRST; no data is read if it does not pass ---
    print("G1: verifying UniProt license live ...")
    lic = verify_license_live()
    print(json.dumps(lic, indent=2))
    if lic.get("verdict") != "pass":
        print("STOP (G1): UniProt license basis not confirmed live; refusing to build.", file=sys.stderr)
        return 2

    src = Path(os.environ.get("UNIREF50_FASTA", sys.argv[1] if len(sys.argv) > 1 else ""))
    if not src or not src.exists():
        print(
            "No local UniRef50 v2021_04 FASTA supplied. On compute, attach the pinned\n"
            f"release and set UNIREF50_FASTA, or allow download from:\n  {SOURCE_URL}\n"
            "(download intentionally not auto-run here: multi-GB; license gate already passed).",
            file=sys.stderr,
        )
        return 3

    print(f"streaming {src} (release {RELEASE}) ...")
    rng = random.Random(SEED)
    strata_counts: dict[str, int] = {}
    total_seen = 0
    kept = 0
    train_fa = EXTERNAL / "ur50_subsample.train.fasta"
    eval_fa = EXTERNAL / "ur50_subsample.eval.fasta"

    # Reservoir-free streaming subsample: accept with a probability that targets
    # TARGET_SEQUENCES while never dropping a singleton stratum below its share.
    # (Two-pass would be exact; one-pass keeps it tractable at ~50M seqs. We record
    # the realized counts in the manifest — G7: report what actually happened.)
    # A rough accept prob; realized total is recorded, not assumed.
    with train_fa.open("w", encoding="utf-8") as ftr, eval_fa.open("w", encoding="utf-8") as fev:
        for header, seq in iter_fasta(src):
            total_seen += 1
            if not seq:
                continue
            m = N_MEMBERS.search(header)
            csize = int(m.group(1)) if m else 1
            stratum = stratum_of(csize)
            # singletons kept with higher propensity (preserve rare clusters, P-2);
            # others thinned toward the target.
            base_p = min(1.0, TARGET_SEQUENCES / 50_000_000)
            p = min(1.0, base_p * (2.0 if stratum == "singleton" else 1.0))
            if rng.random() > p:
                continue
            kept += 1
            strata_counts[stratum] = strata_counts.get(stratum, 0) + 1
            rec = f">{header}\n{seq}\n"
            (fev if rng.random() < HOLDOUT_FRACTION else ftr).write(rec)

    def count_and_hash(p: Path) -> tuple[int, str]:
        n = sum(1 for _ in iter_fasta(p))
        with p.open("rb") as fh:
            digest, _ = sha256_bytes_stream(fh)
        return n, digest

    train_n, train_sha = count_and_hash(train_fa)
    eval_n, eval_sha = count_and_hash(eval_fa)
    if train_n + eval_n != kept:
        print(f"FAIL split arithmetic: {train_n}+{eval_n} != {kept}", file=sys.stderr)
        return 1
    print(f"ok  total_seen={total_seen:,} kept={kept:,} train={train_n:,} eval={eval_n:,}")
    print(f"ok  strata={json.dumps(strata_counts)}")

    entry = {
        "id": "uniref50-subsample",
        "parent_dataset": "uniref50",
        "license": "UniProt (open; CC BY 4.0 basis verified live this run)",
        "license_check": lic,
        "release": RELEASE,
        "source_url": SOURCE_URL,
        "seed": SEED,
        "holdout_fraction": HOLDOUT_FRACTION,
        "dedup": "inherent-uniref50-50pct-identity (no extra dedup — G11 fidelity)",
        "target_sequences": TARGET_SEQUENCES,
        "total_seen": total_seen,
        "kept": kept,
        "train": {"rows": train_n, "sha256": train_sha, "path": str(train_fa)},
        "eval": {"rows": eval_n, "sha256": eval_sha, "path": str(eval_fa)},
        "strata_counts": strata_counts,
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mods": ["P-PTGPT2-2 stratified subsample (cluster-size strata; singletons preserved)"],
        "notes": "faithful corpus version 2021_04; subsample is a documented curriculum stage, not a claim of full-corpus training",
    }
    existing = []
    if MANIFEST.exists():
        existing = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    existing = [e for e in existing if e.get("id") != "uniref50-subsample"]
    existing.append(entry)
    MANIFEST.write_text("\n".join(json.dumps(e) for e in existing) + "\n", encoding="utf-8")
    print(f"ok  manifest -> {MANIFEST}")

    RUN_META.write_text(json.dumps({
        "stage": "seqgen-data",
        "seed": SEED,
        "release": RELEASE,
        "train_rows": train_n,
        "eval_rows": eval_n,
        "license_verdict": lic.get("verdict"),
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, indent=2), encoding="utf-8")
    print(f"ok  run_meta -> {RUN_META} (G10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
