#!/usr/bin/env python
"""Fetch the trained Molek-30M checkpoint so the /v1 `mol.generate` tool goes live.

Pulls the epoch-197 snapshot from the Kaggle dataset `leexze/molek-30m-ckpt` and places
it at artifacts/molek-30m/model.pt (the path serving/tools.py:mol_generate probes, or
point MOLEK_CKPT at it). Verifies the known sha256 before accepting it (G10), so a corrupt
or swapped file is rejected rather than silently served.

Run on the inference host (GPU/container with torch + rdkit + third_party/moflow). The dev
box has no torch, so generation runs where the stack is present — this only stages weights.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST_DIR = ROOT / "artifacts" / "molek-30m"
DEST = DEST_DIR / "model.pt"
DATASET = "leexze/molek-30m-ckpt"
SNAPSHOT = "model_snapshot_epoch_197"
EXPECT_SHA = "7f8374df3cb86e31182d4a42ff1bfd2d97df7edd5b788c9cd1090e6dbf722228"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if DEST.exists() and sha256_file(DEST) == EXPECT_SHA:
        print(f"ok  checkpoint already present + verified -> {DEST}")
        return 0
    print(f"downloading {DATASET} ...")
    subprocess.run(["kaggle", "datasets", "download", "-d", DATASET,
                    "-p", str(DEST_DIR), "--unzip"], check=True)
    src = DEST_DIR / SNAPSHOT
    if not src.exists():
        print(f"expected {SNAPSHOT} in the dataset but it is missing.", file=sys.stderr)
        return 2
    shutil.move(str(src), str(DEST))
    got = sha256_file(DEST)
    if got != EXPECT_SHA:
        print(f"STOP (G10): sha256 mismatch\n  expected {EXPECT_SHA}\n  got      {got}",
              file=sys.stderr)
        DEST.unlink(missing_ok=True)
        return 3
    print(f"ok  Molek-30M checkpoint verified ({got[:12]}...) -> {DEST}")
    print("    serving/tools.py:mol_generate will now return real molecules (G7).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
