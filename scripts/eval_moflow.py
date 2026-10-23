#!/usr/bin/env python
"""MoFlow eval wrapper — honest metrics, reference math untouched (G7/G11).

Runs the REFERENCE generate.py in random-generation mode around a checkpoint and
captures its own metrics output verbatim. We add nothing to the math; we only
enforce the M-MOFLOW-4 honesty rule: every eval logs validity WITH and WITHOUT
correction (two invocations --correct_validity true / false).

Outputs: artifacts/<run>/eval/eval_corrected.log · eval_uncorrected.log · eval_summary.json
Usage: python scripts/eval_moflow.py --config configs/molgen-zinc250k.yaml \
         --snapshot artifacts/<run>/snapshots/model_snapshot_epoch_200 \
         [--n_samples 10000] [--temperature 0.85] [--experiments 5]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from train_moflow import sha256_file  # noqa: E402  (same helpers)


def parse_metrics(log_text: str) -> dict:
    out = {}
    for key in ("validity", "novelty", "uniqueness", "abs_novelty", "abs_uniqueness"):
        m = re.search(rf"{key}: mean=([\d.]+)%", log_text)
        if m:
            out[key] = float(m.group(1))
    return out


def run_generate(model_dir: Path, snapshot: str, n: int, temp: float, exps: int, correct: bool, log_path: Path) -> dict:
    cmd = [
        sys.executable, "generate.py",
        "--model_dir", str(model_dir),
        "-snapshot", snapshot,
        "--gpu", "0",
        "--data_name", "zinc250k",
        "--hyperparams-path", "moflow-params.json",
        "--batch-size", str(n),
        "--temperature", str(temp),
        "--n_experiments", str(exps),
        "--save_fig", "false",
        "--correct_validity", "true" if correct else "false",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=ROOT / "third_party" / "moflow" / "mflow")
    log_path.write_text(proc.stdout + ("\nSTDERR:\n" + proc.stderr if proc.stderr else ""), encoding="utf-8")
    metrics = parse_metrics(proc.stdout)
    print(f"[eval] correct_validity={correct} -> {'ok ' + json.dumps(metrics) if metrics else 'NO METRICS PARSED (see ' + str(log_path) + ')'}")
    return metrics


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--run_dir", required=True, help="e.g. artifacts/20261023-184040-moflow30m-zinc250k-r1")
    ap.add_argument("--snapshot", required=True, help="snapshot filename inside <run_dir>/snapshots")
    ap.add_argument("--n_samples", type=int, default=10000)   # [REF] README protocol
    ap.add_argument("--temperature", type=float, default=0.85)  # [REF]
    ap.add_argument("--experiments", type=int, default=5)    # [REF]
    args = ap.parse_args()

    run_dir = ROOT / args.run_dir
    snap_dir = run_dir / "snapshots"
    # generate.py joins model_dir with BOTH the snapshot and the hyperparams filename
    # (generate.py:445-446), so model_dir must be the dir that holds the snapshot AND
    # moflow-params.json — i.e. snap_dir itself.
    model_dir = snap_dir
    eval_dir = run_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    summary = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "snapshot": args.snapshot,
               "snapshot_sha256": sha256_file(snap_dir / args.snapshot),
               "n_samples": args.n_samples, "temperature": args.temperature,
               "experiments": args.experiments}
    for label, correct in (("corrected", True), ("uncorrected", False)):
        m = run_generate(model_dir, args.snapshot, args.n_samples, args.temperature,
                         args.experiments, correct, eval_dir / f"eval_{label}.log")
        summary[label] = m

    (eval_dir / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[g7] summary -> {eval_dir / 'eval_summary.json'}")
    print("NOTE: reference reports corrected numbers; uncorrected block is the honest one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
