#!/usr/bin/env python
"""Molek-30M distributional metrics via the MOSES library (rung 2, sota-roadmap).

HONESTY (G7/G14): Molek was trained on zinc250k (MoFlow's set), NOT the MOSES training
set. So this is NOT a MOSES-leaderboard entry. We use the MOSES *metrics library* to
compute the richer distributional metrics — FCD, SNN, Frag, Scaf, IntDiv, Novelty — on
Molek's generations vs the **zinc250k test split** (apples-to-apples with how Molek was
trained). FCD especially is the gold-standard distribution-quality signal.

Reference code untouched (G11): generation uses the pinned generate_mols + check_validity;
metrics use the pinned moses library. Run with cwd = third_party/moflow/mflow.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "..")  # for `from data import ...` (like generate.py)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True, help="dir with snapshot + moflow-params.json")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--n_gen", type=int, default=30000)   # MOSES standard sample size
    ap.add_argument("--batch", type=int, default=10000)
    ap.add_argument("--temp", type=float, default=0.85)   # [REF]
    ap.add_argument("--csv", default="../data/zinc250k.csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import torch
    import pandas as pd
    from mflow.models.hyperparams import Hyperparameters
    from mflow.models.utils import check_validity
    from mflow.utils.model_utils import load_model
    from mflow.generate import generate_mols
    from data import transform_zinc250k

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    atomic_num_list = transform_zinc250k.zinc250_atomic_num_list

    # --- load Molek ---
    mp = Hyperparameters(path=str(Path(args.model_dir) / "moflow-params.json"))
    model = load_model(str(Path(args.model_dir) / args.snapshot), mp, debug=True)
    model.to(device).eval()

    # --- generate n_gen valid (corrected) SMILES ---
    gen = []
    t0 = time.time()
    while len(gen) < args.n_gen:
        with torch.no_grad():
            adj, x = generate_mols(model, batch_size=args.batch, temp=args.temp, device=device)
        val = check_validity(adj, x, atomic_num_list, correct_validity=True, debug=False)
        gen.extend(val["valid_smiles"])
        print(f"[gen] {len(gen)}/{args.n_gen}  ({time.time()-t0:.0f}s)")
    gen = gen[: args.n_gen]

    # --- zinc250k train/test SMILES split (reference valid_idx = held-out test) ---
    df = pd.read_csv(args.csv)
    smiles_col = "smiles" if "smiles" in df.columns else [c for c in df.columns if c.lower() == "smiles"][0]
    all_smiles = [s.strip() for s in df[smiles_col].tolist()]
    test_idx = set(transform_zinc250k.get_val_ids())
    test_smiles = [all_smiles[i] for i in sorted(test_idx) if i < len(all_smiles)]
    train_smiles = [s for i, s in enumerate(all_smiles) if i not in test_idx]
    print(f"[data] gen={len(gen)} train={len(train_smiles)} test={len(test_smiles)}")

    # --- MOSES library metrics (pinned moses) ---
    import moses
    metrics = moses.get_all_metrics(
        gen=gen, test=test_smiles, train=train_smiles,
        device=str(device), n_jobs=2,
    )
    metrics = {k: (float(v) if hasattr(v, "__float__") else v) for k, v in metrics.items()}

    out = {
        "model": "molek-30m", "snapshot": args.snapshot,
        "n_gen": len(gen), "temperature": args.temp,
        "reference_set": "zinc250k test split (NOT the MOSES benchmark train/test)",
        "note": "MOSES metrics LIBRARY vs zinc250k test — informative distributional "
                "quality (FCD etc.), NOT a MOSES-leaderboard entry (Molek trained on "
                "zinc250k, not MOSES-train). G7.",
        "metrics": metrics,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("[moses] metrics:", json.dumps(metrics, indent=2))
    print(f"[moses] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
