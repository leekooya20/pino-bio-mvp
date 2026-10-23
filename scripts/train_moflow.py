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


DATASET_CONSTANTS = {
    # Verbatim from reference train_model.py lines 132-135 (zinc250k branch) —
    # dataset-bound in the reference, therefore dataset-bound here (G11 provenance).
    "zinc250k": {"b_n_type": 4, "b_n_squeeze": 19, "a_n_node": 38, "a_n_type": 10},
}


def count_reference_params(cfg: dict) -> int:
    """Build the reference MoFlow model (unchanged math) and count params.

    Imports live in third_party/moflow/mflow/models (verified train_model.py:12-13).
    We never modify that code — we instantiate with OUR config values (M-MOFLOW-1)
    and enforce the budget BEFORE spending GPU time.
    """
    import torch  # noqa: F401  (heavy dep; only needed for real training runs)
    tp = ROOT / "third_party" / "moflow"
    sys.path.insert(0, str(tp))
    from mflow.models.hyperparams import Hyperparameters  # type: ignore
    from mflow.models.model import MoFlow  # type: ignore

    m = cfg["model"]
    d = cfg["data"]["name"]
    if d not in DATASET_CONSTANTS:
        raise SystemExit(f"no dataset constants for {d} — add to DATASET_CONSTANTS w/ reference line refs")
    c = DATASET_CONSTANTS[d]
    listify = lambda v: v if isinstance(v, list) else [v]  # noqa: E731
    hp = Hyperparameters(
        b_n_type=c["b_n_type"], b_n_flow=m["b_n_flow"], b_n_block=1,
        b_n_squeeze=c["b_n_squeeze"], b_hidden_ch=listify(m["b_hidden_ch"]),
        b_affine=True, b_conv_lu=m["b_conv_lu"],
        a_n_node=c["a_n_node"], a_n_type=c["a_n_type"],
        a_hidden_gnn=listify(m["a_hidden_gnn"]), a_hidden_lin=listify(m["a_hidden_lin"]),
        a_n_flow=m["a_n_flow"], a_n_block=1,
        mask_row_size_list=listify(m["mask_row_size_list"]),
        mask_row_stride_list=listify(m["mask_row_stride_list"]),
        a_affine=True, learn_dist=True, seed=0, noise_scale=m["noise_scale"],
    )
    model = MoFlow(hp)
    n = sum(p.numel() for p in model.parameters())
    budget = int(m["param_budget_m"]) * 1_000_000
    if n > budget:
        print(f"FAIL param budget: {n:,} > {budget:,} (M-MOFLOW-1) — shrink flows/width", file=sys.stderr)
        raise SystemExit(1)
    print(f"[M-MOFLOW-1] counted params: {n:,} <= budget {budget:,} OK")
    return n


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
    snap_dir = run_dir / "snapshots"
    ref_args += [
        "--save_dir", str(snap_dir),                       # centralize snapshots in our run dir
        "--seed", str(cfg["run"]["seed"]),                 # reference --seed exists (train_model.py:76) — G10
        "--learning_rate", str(cfg["train"].get("learning_rate", 0.001)),
        "--save_interval", str(cfg["train"].get("save_interval", 20)),
    ]
    latest_snapshot = None
    if args.resume:
        snaps = sorted(snap_dir.glob("model_snapshot_epoch_*"))
        if snaps:
            latest_snapshot = snaps[-1]
            ref_args += ["--load_snapshot", str(latest_snapshot)]  # reference arg name (line 36)
            ref_args += ["--load_params", "1"]
        else:
            print("[resume] no snapshot found — starting fresh", file=sys.stderr)

    # M-MOFLOW-1 pre-flight: enforce the 30M budget before any GPU spend
    # (skipped in dry_run so config review works without torch on the host)
    n_params = None if args.dry_run else count_reference_params(cfg)

    cmd = [sys.executable, "train_model.py"] + ref_args
    print("[g11] reference CLI (verbatim names, our values):")
    print("  " + " ".join(cmd))
    if n_params is not None:
        print(f"[g10] model params: {n_params:,}")

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
