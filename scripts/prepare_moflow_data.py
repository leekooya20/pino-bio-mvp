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

    gz = EXTERNAL / "250k_rndm_zinc_drugs_clean_3.csv.gz"
    csv_path = EXTERNAL / "zinc250k.csv"

    if not csv_path.exists():
        if not gz.exists():
            print(f"downloading {SOURCE_URL} ... (~35 MB)")
            urllib.request.urlretrieve(SOURCE_URL, gz)
            print(f"sha256(gz) = {sha256_file(gz)}")
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
        "notes": "canonical file consumed by calvin-zcx/moflow data_preprocess.py; mirrors configs/licenses.yaml entry moses-zinc250k",
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
