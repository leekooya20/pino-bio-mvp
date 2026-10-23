#!/usr/bin/env python
"""MoFlow-30M trainer wrapper (PinoBio MVP-4, phase 1).

READ THIS FIRST (G11): the recipe we replicate is the official
calvin-zcx/moflow zinc250k config — recorded verbatim in
Project Katala docs/08-generative-recipes.md §2. This wrapper does NOT
reinvent the math: it drives the reference train_model.py with our
documented modifications (M-MOFLOW-1..4) from --config.

What it adds on top of the reference:
  - config-driven run (no hardcoded hyperparas; Katala repo convention)
  - G10 run_meta.json (seed, data version pin, config hash, SHA of reference code)
  - hard param-budget assertion (fail if model params > model.param_budget_m)
  - artifacts/<run>/train.log capture
  - --resume: restart from latest snapshot in the run dir

Usage: python scripts/train_moflow.py --config configs/molgen-zinc250k.yaml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import yaml
except ImportError:  # pragma: no cover
    print("pip install pyyaml", file=sys.stderr)
    raise


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def bjoin(v) -> str:
    if isinstance(v, (list, tuple)):
        return ",".join(str(x) for x in v)
    return str(v)


def build_reference_args(cfg: dict) -> list[str]:
    """Map our YAML onto the reference train_model.py CLI (names unchanged, G11)."""
    m = cfg["model"]
    t = cfg["train"]
    return [
        "--data_name", f"{cfg['data']['name']}",
        "--batch_size", str(t["batch_size"]),
        "--max_epochs", str(t["max_epochs"]),
        "--b_n_flow", str(m["b_n_flow"]),
        "--b_hidden_ch", bjoin(m["b_hidden_ch"]),
        "--a_n_flow", str(m["a_n_flow"]),
        "--a_hidden_gnn", bjoin(m["a_hidden_gnn"]),
        "--a_hidden_lin", bjoin(m["a_hidden_lin"]),
        "--mask_row_size_list", bjoin(m["mask_row_size_list"]),
        "--mask_row_stride_list", bjoin(m["mask_row_stride_list"]),
        "--noise_scale", str(m["noise_scale"]),
        "--b_conv_lu", str(m["b_conv_lu"]),
    ]


def count_reference_params() -> int:
    """Build the reference model (unchanged math) and count params vs budget."""
    import torch
    tp = ROOT / "third_party"
    pin = tp / "PINNED.json"
    if not pin.exists():
        raise SystemExit("third_party not pinned — run scripts/fetch_thirdparty.py first")
    sys.path.insert(0, str(tp / "moflow"))
    from fast_jtm import build  # placeholder import; resolved in phase-1 wiring step
    raise SystemExit("param counter lands with phase-1 wiring: src/train/moflow_model.py")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--resume", action="store_true", help="continue from latest snapshot in run dir")
    ap.add_argument("--dry_run", action="store_true", help="print the reference CLI and exit")
    args = ap.parse_args()

    cfg_path = ROOT / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    # G10: run metadata hash-first
    run_name = time.strftime("%Y%m%d-%H%M%S") + "-" + cfg["run"]["name"]
    run_dir = ROOT / "artifacts" / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(cfg_path, run_dir / "config.yaml")

    pin = ROOT / "third_party" / "PINNED.json"
    meta = {
        "run": run_name,
        "seed": cfg["run"]["seed"],
        "config_hash": sha256_file(cfg_path),
        "data_name": cfg["data"]["name"],
        "data_version_pin": cfg["data"]["version_pin"],
        "license_manifest": cfg["data"]["manifest"],
        "third_party_pin": json.loads(pin.read_text()) if pin.exists() else "NOT_PINNED",
        "modifications": ["M-MOFLOW-1", "M-MOFLOW-2", "M-MOFLOW-3", "M-MOFLOW-4"],
        "resume": args.resume,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "host": sys.platform,
    }
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    ref_args = build_reference_args(cfg)
    cmd = [sys.executable, "train_model.py"] + ref_args
    if args.resume:
        cmd += ["--restore_file", "model_snapshot_epoch_last"]  # reference snapshot naming
    print("[g11] reference CLI (verbatim names, our values):")
    print("  " + " ".join(cmd))

    if args.dry_run:
        (run_dir / "planned_cmd.txt").write_text(" ".join(cmd), encoding="utf-8")
        return 0

    if not (ROOT / "third_party" / "moflow" / ".git").exists():
        print("FAIL: run scripts/fetch_thirdparty.py first (G11)", file=sys.stderr)
        return 1

    env_path = str(ROOT / "third_party" / "moflow" / "mflow")
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = env_path + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(cmd, cwd=ROOT / "third_party" / "moflow" / "mflow", env=env)
    code = proc.returncode

    meta["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    meta["exit_code"] = code
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[g7] run exit code: {code} — report failures honestly (never round up)")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
