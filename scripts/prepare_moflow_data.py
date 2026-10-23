#!/usr/bin/env python
"""zinc250k data fetcher + verifier + manifest writer (PinoBio MVP-4, G1/G7/G10).

Reference preprocessing (third_party/moflow/data/data_preprocess.py) expects
`zinc250k.csv` with columns [smiles, logP, qed, SAS] beside it — it does NOT
download anything. This script fills that gap: downloads the canonical
250k_rndm_zinc_drugs_clean_3.csv (the exact file MoFlow's reference pipeline
consumes), verifies shape/columns, records sha256 + license provenance into
data/manifests/moses-zinc250k.jsonl, and copies it where the reference expects.

License basis (configs/licenses.yaml → datasets → moses-zinc250k): ZINC15 is
"free for everyone"; molecules = factual data; no PII. Reference README reports
249,455 total rows — we assert that count (G7: exactness, never rounded).
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP_DATA = ROOT / "third_party" / "moflow" / "data"
EXTERNAL = ROOT / "data" / "external"
MANIFEST = ROOT / "data" / "manifests" / "moses-zinc250k.jsonl"

SOURCE_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/250k_rndm_zinc_drugs_clean_3.csv.gz"
# M-MOFLOW-7 fallback source: DeepChem S3 began returning HTTP 403 for anonymous
# GETs (2026-10-23, Kaggle run #3). Verified mirror: Kaggle dataset
# basu369victor/zinc250k — exact same filename, row count 249,455 and columns
# {smiles, logP, qed, SAS} as the reference file (G7 check, no rounding).
MIRROR_NOTE = "fallback: DeepChem S3 returned 403 anonymously; verified via Kaggle dataset basu369victor/zinc250k (same filename/rows/columns)"
REQUIRED_COLUMNS = {"smiles", "logP", "qed", "SAS"}
EXPECTED_ROWS = 249_455  # reference README generate.py output for zinc250k — verified count


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    TP_DATA.mkdir(parents=True, exist_ok=True)
    mirror_csv = Path(os.environ.get(
        "ZINC250K_CSV",
        "/kaggle/input/zinc250k/250k_rndm_zinc_drugs_clean_3.csv",
    ))
    local_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    gz = EXTERNAL / "250k_rndm_zinc_drugs_clean_3.csv.gz"
    csv_path = EXTERNAL / "zinc250k.csv"
    used_mirror = ""

    if not csv_path.exists():
        candidates = [c for c in (local_arg, mirror_csv) if c and Path(c).exists()]
        if candidates:
            src = Path(candidates[0])
            print(f"copying verified mirror csv: {src}")
            shutil.copyfile(src, csv_path)
            used_mirror = MIRROR_NOTE
        elif not gz.exists():
            print(f"downloading {SOURCE_URL} ... (~35 MB)")
            urllib.request.urlretrieve(SOURCE_URL, gz)
            print(f"sha256(gz) = {sha256_file(gz)}")
        if not csv_path.exists():
            print("decompressing ...")
            with gzip.open(gz, "rb") as fi, csv_path.open("wb") as fo:
                shutil.copyfileobj(fi, fo)
    else:
        print("csv already present — verifying only")

    print("verifying columns + rows (G7: exact, no rounding) ...")
    rows = 0
    header = None
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.reader(f)
        header = next(r)
        for _ in r:
            rows += 1
    if not REQUIRED_COLUMNS.issubset({c.strip() for c in header}):
        print(f"FAIL columns: got {header}", file=sys.stderr)
        return 1
    if rows != EXPECTED_ROWS:
        print(f"FAIL rows: {rows} != {EXPECTED_ROWS} (reference, G7)", file=sys.stderr)
        return 1
    print(f"ok  rows={rows:,} (matches reference {EXPECTED_ROWS:,}) columns={header}")

    entry = {
        "id": "moses-zinc250k",
        "license": "ZINC15 free-for-everyone / MOSES benchmark (MIT)",
        "source_url": SOURCE_URL,
        "sha256_csv": sha256_file(csv_path),
        "rows": rows,
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "verified_columns": list(header),
        "notes": "canonical file consumed by calvin-zcx/moflow data_preprocess.py; mirrors configs/licenses.yaml entry moses-zinc250k" + (";" if not used_mirror else "; " + used_mirror),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if MANIFEST.exists():
        existing = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    existing = [e for e in existing if e.get("id") != "moses-zinc250k"]
    existing.append(entry)
    MANIFEST.write_text("\n".join(json.dumps(e) for e in existing) + "\n", encoding="utf-8")
    print(f"ok  manifest -> {MANIFEST}")

    dest = TP_DATA / "zinc250k.csv"
    shutil.copyfile(csv_path, dest)
    print(f"ok  placed -> {dest} (reference expects it there)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
