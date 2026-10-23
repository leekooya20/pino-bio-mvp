#!/usr/bin/env python
"""Background checkpoint pusher (M-MOFLOW-12, crash-safety).

Kaggle persists /kaggle/working ONLY on a successful commit — a session killed at the
~12h ceiling mid-training would otherwise lose every done epoch. This pusher ships the
latest snapshot(s) to a Kaggle **Dataset** every few minutes, so progress survives any
kernel fate and the next run can `--resume` from it.

Usage (inside the Kaggle runner, as a background thread):
    python scripts/kaggle_ckpt_push.py --snap-dir /kaggle/working/molek-snapshots \
        --dataset leexze/molek-checkpoints --every 900

Gated on Kaggle API creds (KAGGLE_USERNAME/KAGGLE_KEY or ~/.kaggle/kaggle.json). If
creds are absent it exits cleanly — snapshots still land in /kaggle/working and are saved
on a successful commit (best-effort). G8: no creds are hardcoded or logged.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def have_creds() -> bool:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    return (Path.home() / ".kaggle" / "kaggle.json").exists()


def ensure_dataset(snap_dir: Path, dataset: str) -> None:
    """Create the dataset once if it doesn't exist (idempotent-ish)."""
    meta = snap_dir / "dataset-metadata.json"
    owner, slug = dataset.split("/", 1)
    meta.write_text(json.dumps({
        "title": slug, "id": dataset,
        "licenses": [{"name": "other"}],
    }), encoding="utf-8")
    # try create; if it already exists this fails harmlessly and we version instead.
    subprocess.run(["kaggle", "datasets", "create", "-p", str(snap_dir), "-r", "zip", "-u"],
                   capture_output=True)


def push_once(snap_dir: Path, dataset: str) -> bool:
    if not any(snap_dir.glob("model_snapshot_epoch_*")):
        return False
    r = subprocess.run(
        ["kaggle", "datasets", "version", "-p", str(snap_dir),
         "-m", f"auto checkpoint {time.strftime('%Y-%m-%dT%H:%M:%S')}", "-r", "zip", "-d"],
        capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"[ckpt-push] {'ok' if ok else 'retry-next-cycle'}: {r.stdout.strip() or r.stderr.strip()[:200]}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap-dir", required=True)
    ap.add_argument("--dataset", required=True, help="owner/slug")
    ap.add_argument("--every", type=int, default=900, help="seconds between pushes")
    args = ap.parse_args()

    snap = Path(args.snap_dir)
    snap.mkdir(parents=True, exist_ok=True)
    if not have_creds():
        print("[ckpt-push] no Kaggle API creds — skipping dataset push; snapshots still in "
              "/kaggle/working (saved on successful commit).", file=sys.stderr)
        return 0

    ensure_dataset(snap, args.dataset)
    print(f"[ckpt-push] pushing {snap} -> {args.dataset} every {args.every}s")
    while True:
        time.sleep(args.every)
        try:
            push_once(snap, args.dataset)
        except Exception as e:  # noqa: BLE001 — never let the pusher kill training
            print(f"[ckpt-push] error (continuing): {e!r}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
