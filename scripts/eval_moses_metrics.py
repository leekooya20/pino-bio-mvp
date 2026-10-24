#!/usr/bin/env python
"""Molek-30M distributional metrics — FCD + diversity (rung 2, sota-roadmap).

HONESTY (G7): Molek trained on zinc250k (not MOSES-train), so this is NOT a MOSES
leaderboard entry. We compute the gold-standard distribution metric **FCD** (via
fcd_torch — the same ChemNet distance MOSES uses) plus **IntDiv/SNN** (RDKit), on Molek's
generations vs the **zinc250k test split**.

Why not the `moses` package: moses (2020) is incompatible with py3.13 + pandas2/numpy2
(rdkit.six removed, DataFrame.append removed, ...). fcd_torch gives the identical FCD
metric without that dependency hell; Frag/Scaf (moses-specific) are deferred to a pinned
moses container. Reference generation untouched (G11).

Run with cwd = third_party/moflow/mflow.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "..")  # for `from data import ...`


def morgan_fps(smiles):
    from rdkit import Chem
    from rdkit.Chem import AllChem
    fps = []
    for s in smiles:
        m = Chem.MolFromSmiles(s)
        if m is not None:
            fps.append(AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048))
    return fps


def int_div(fps, p=1):
    """MOSES internal diversity: 1 - mean pairwise Tanimoto (power p)."""
    from rdkit import DataStructs
    n = len(fps)
    if n < 2:
        return None
    total = 0.0
    count = 0
    for i in range(n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:])
        if sims:
            total += sum(s ** p for s in sims)
            count += len(sims)
    mean_sim = (total / count) ** (1.0 / p) if count else 0.0
    return 1.0 - mean_sim


def snn(gen_fps, ref_fps):
    """Mean over gen of max Tanimoto to any ref (similarity to nearest neighbour)."""
    from rdkit import DataStructs
    if not gen_fps or not ref_fps:
        return None
    tot = 0.0
    for fp in gen_fps:
        tot += max(DataStructs.BulkTanimotoSimilarity(fp, ref_fps))
    return tot / len(gen_fps)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--n_gen", type=int, default=30000)
    ap.add_argument("--batch", type=int, default=10000)
    ap.add_argument("--temp", type=float, default=0.85)
    ap.add_argument("--csv", default="../data/zinc250k.csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import pandas as pd
    import torch
    from mflow.models.hyperparams import Hyperparameters
    from mflow.models.utils import check_validity
    from mflow.utils.model_utils import load_model
    from mflow.generate import generate_mols
    from data import transform_zinc250k

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    atomic_num_list = transform_zinc250k.zinc250_atomic_num_list
    rng = random.Random(20261023)

    mp = Hyperparameters(path=str(Path(args.model_dir) / "moflow-params.json"))
    model = load_model(str(Path(args.model_dir) / args.snapshot), mp, debug=True)
    model.to(device).eval()

    gen = []
    t0 = time.time()
    while len(gen) < args.n_gen:
        with torch.no_grad():
            adj, x = generate_mols(model, batch_size=args.batch, temp=args.temp, device=device)
        val = check_validity(adj, x, atomic_num_list, correct_validity=True, debug=False)
        gen.extend(val["valid_smiles"])
        print(f"[gen] {len(gen)}/{args.n_gen} ({time.time()-t0:.0f}s)")
    gen = gen[: args.n_gen]

    df = pd.read_csv(args.csv)
    scol = "smiles" if "smiles" in df.columns else [c for c in df.columns if c.lower() == "smiles"][0]
    all_smiles = [s.strip() for s in df[scol].tolist()]
    test_idx = set(transform_zinc250k.get_val_ids())
    test_smiles = [all_smiles[i] for i in sorted(test_idx) if i < len(all_smiles)]
    print(f"[data] gen={len(gen)} test={len(test_smiles)}")

    # --- FCD (gold standard; fcd_torch == MOSES's FCD) ---
    from fcd_torch import FCD
    fcd_score = float(FCD(device=str(device), n_jobs=2)(gen=gen, ref=test_smiles))

    # --- diversity + nearest-neighbour similarity (RDKit, sampled for tractability) ---
    gen_fps = morgan_fps(rng.sample(gen, min(5000, len(gen))))
    ref_fps = morgan_fps(rng.sample(test_smiles, min(5000, len(test_smiles))))
    snn_fps = morgan_fps(rng.sample(gen, min(2000, len(gen))))
    metrics = {
        "FCD/Test": fcd_score,
        "IntDiv": int_div(gen_fps, p=1),
        "IntDiv2": int_div(gen_fps, p=2),
        "SNN/Test": snn(snn_fps, ref_fps),
    }
    out = {
        "model": "molek-30m", "snapshot": args.snapshot, "n_gen": len(gen),
        "temperature": args.temp,
        "reference_set": "zinc250k test split (NOT the MOSES benchmark)",
        "note": "FCD via fcd_torch (= MOSES FCD metric); IntDiv/SNN via RDKit. NOT a MOSES "
                "leaderboard entry (Molek trained on zinc250k). Frag/Scaf deferred (moses "
                "pkg py3.13-incompatible). G7.",
        "metrics": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("[dist] metrics:", json.dumps(out["metrics"], indent=2))
    print(f"[dist] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
