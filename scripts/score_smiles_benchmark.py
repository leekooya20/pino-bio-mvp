#!/usr/bin/env python
"""Model-AGNOSTIC molecular-generation scorer — the fairness core of the in-house
ZINC250k competitor benchmark (BENCH-MOL-001). PinoBio MVP-4, G7/G11.

Every model (Molek-30M + the frozen competitor checkpoints GDSS/CDGS) emits a plain list
of generated SMILES; this one script scores them all IDENTICALLY, so the comparison has
zero metric-implementation drift. Metrics match the Molek distribution report
(scripts/eval_moses_metrics.py): validity / uniqueness / novelty + FCD (fcd_torch, the same
ChemNet distance MOSES uses) + IntDiv/SNN (RDKit), against the SAME zinc250k test split and
the SAME train set used for Molek's novelty.

Honest (G7): numbers are measured on raw generations; competitors run under their OWN frozen
code (G11, run-only — their source is NOT vendored into this repo). Lower FCD = closer to the
reference distribution.

Usage:
  python scripts/score_smiles_benchmark.py --gen gen.smi --train train.smi --test test.smi \
      --model gdss --out results/bench-gdss.json
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

SEED = 20261023


# --- pure logic (unit-tested; no RDKit needed) -------------------------------------------
def dedup_novelty(valid_canon: list[str], train_canon: set[str]) -> dict:
    """Uniqueness + novelty from canonical SMILES lists (pure set math, testable)."""
    n_valid = len(valid_canon)
    unique = set(valid_canon)
    novel = [s for s in unique if s not in train_canon]
    return {
        "n_valid": n_valid,
        "n_unique": len(unique),
        "uniqueness": (len(unique) / n_valid) if n_valid else 0.0,
        "novelty": (len(novel) / len(unique)) if unique else 0.0,
    }


# --- RDKit-backed helpers (shared with eval_moses_metrics) -------------------------------
def canonicalize(smiles: list[str]) -> list[str]:
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    out = []
    for s in smiles:
        if not s:
            continue
        m = Chem.MolFromSmiles(s)
        if m is not None:
            out.append(Chem.MolToSmiles(m))
    return out


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
    from rdkit import DataStructs
    n = len(fps)
    if n < 2:
        return None
    total, count = 0.0, 0
    for i in range(n):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[i + 1:])
        if sims:
            total += sum(s ** p for s in sims)
            count += len(sims)
    mean_sim = (total / count) ** (1.0 / p) if count else 0.0
    return 1.0 - mean_sim


def snn(gen_fps, ref_fps):
    from rdkit import DataStructs
    if not gen_fps or not ref_fps:
        return None
    tot = 0.0
    for fp in gen_fps:
        tot += max(DataStructs.BulkTanimotoSimilarity(fp, ref_fps))
    return tot / len(gen_fps)


def read_smiles(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    # tolerate "SMILES\tid" or "SMILES,prop" — take the first whitespace/comma field
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.lower().startswith("smiles"):
            continue
        out.append(ln.replace(",", " ").split()[0])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True, help="generated SMILES (one per line)")
    ap.add_argument("--train", required=True, help="zinc250k TRAIN smiles (novelty reference)")
    ap.add_argument("--test", required=True, help="zinc250k TEST smiles (FCD/SNN reference)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    rng = random.Random(SEED)
    raw = read_smiles(args.gen)
    n_total = len(raw)
    valid_canon = canonicalize(raw)              # validity on RAW generations
    train_canon = set(canonicalize(read_smiles(args.train)))
    test_smiles = read_smiles(args.test)

    uv = dedup_novelty(valid_canon, train_canon)
    validity = (uv["n_valid"] / n_total) if n_total else 0.0

    # distribution: FCD vs test (gold standard), IntDiv + SNN (sampled for tractability)
    from fcd_torch import FCD
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    fcd_score = float(FCD(device=dev, n_jobs=2)(gen=valid_canon, ref=test_smiles)) \
        if valid_canon else None

    gen_fps = morgan_fps(rng.sample(valid_canon, min(5000, len(valid_canon)))) if valid_canon else []
    ref_fps = morgan_fps(rng.sample(test_smiles, min(5000, len(test_smiles)))) if test_smiles else []
    snn_fps = morgan_fps(rng.sample(valid_canon, min(2000, len(valid_canon)))) if valid_canon else []

    metrics = {
        "validity": round(validity * 100, 2),            # % of raw generations that are valid
        "uniqueness": round(uv["uniqueness"] * 100, 2),  # % of valid that are distinct
        "novelty": round(uv["novelty"] * 100, 2),        # % of unique absent from train
        "FCD/Test": round(fcd_score, 4) if fcd_score is not None else None,
        "IntDiv": round(int_div(gen_fps, 1), 4) if gen_fps else None,
        "IntDiv2": round(int_div(gen_fps, 2), 4) if gen_fps else None,
        "SNN/Test": round(snn(snn_fps, ref_fps), 4) if snn_fps and ref_fps else None,
    }
    out = {
        "benchmark": "BENCH-MOL-001", "model": args.model,
        "n_generated_raw": n_total, "n_valid": uv["n_valid"], "n_unique": uv["n_unique"],
        "reference_set": "zinc250k (train=novelty ref, test=FCD/SNN ref) — same splits as Molek",
        "scorer": "score_smiles_benchmark.py (identical for every model; G7 no metric drift)",
        "metrics": metrics,
        "note": args.note or "Measured in-house on our hardware; competitor runs under their "
                "own frozen code (G11 run-only, source not vendored).",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
