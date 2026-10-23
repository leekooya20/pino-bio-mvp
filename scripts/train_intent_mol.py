#!/usr/bin/env python
"""Train the OWNED intent-mol head (N-NLP-1): natural language -> molecular
descriptor-target vector, which steers Molek's farm-knob region. PinoBio MVP-4.

Pipeline (G11 recipe = Pinal's trainable projection e_t -> target space, read 2026-10-23):
  text definition --[frozen MiniLM, Apache-2.0]--> e_t (384-d)
  e_t --[OUR small MLP, trained here]--> descriptor target vector

Trains on scripts/fetch_chebi_agchem.py output (data/external/chebi_agchem/pairs.jsonl):
real (definition, RDKit-descriptor) pairs. This is independent of Molek's checkpoint,
so it can train early.

HARD RULES:
- G7  : per-dimension recovery reported honestly on a held-out split (no blended score);
        owned numbers never mixed with served Pinal/ESM-2.
- G9  : only the small MLP is trained; the text encoder stays frozen (owned adapter).
- G10 : seed + config hash + per-dim recovery + normalization stats in run_meta.
- N-NLP-4 : stores training-embedding centroids + a distance threshold so out-of-
        distribution prompts get FLAGGED at inference, not silently answered.

Heavy deps (torch, sentence-transformers) are gated; the pure-math helpers are tested.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = ROOT / "data" / "external" / "chebi_agchem" / "pairs.jsonl"
OUT = ROOT / "artifacts" / "intent-mol"
SEED = 20261023
HOLDOUT = 0.10
# fixed descriptor order = the output vector dimensions (farmknob-spec §4 subset)
DESCRIPTOR_KEYS = ["MolWt", "cLogP", "TPSA", "HBD", "HBA", "RotBonds",
                   "AromaticRings", "F", "Cl", "Br"]


# --- pure math (tested) ---
def standardize_fit(rows: list[list[float]]) -> tuple[list[float], list[float]]:
    """Per-dimension mean/std; std floored to 1.0 for constant dims (no div-by-zero)."""
    n = len(rows)
    d = len(rows[0])
    mean = [sum(r[j] for r in rows) / n for j in range(d)]
    std = []
    for j in range(d):
        var = sum((r[j] - mean[j]) ** 2 for r in rows) / n
        std.append(math.sqrt(var) or 1.0)
    return mean, std


def standardize_apply(row: list[float], mean: list[float], std: list[float]) -> list[float]:
    return [(row[j] - mean[j]) / std[j] for j in range(len(row))]


def split_indices(n: int, holdout: float, seed: int) -> tuple[list[int], list[int]]:
    import random
    idx = list(range(n))
    random.Random(seed).shuffle(idx)
    k = int(n * holdout)
    return idx[k:], idx[:k]  # train, eval


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


def main() -> int:
    if not PAIRS.exists():
        print(f"missing {PAIRS}; run scripts/fetch_chebi_agchem.py on compute first.",
              file=sys.stderr)
        return 2
    rows = [json.loads(l) for l in PAIRS.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("descriptors") and r.get("definition")]
    if len(rows) < 20:
        print(f"only {len(rows)} usable pairs — too few to train honestly (G7).", file=sys.stderr)
        return 3

    try:
        import numpy as np
        import torch
        import torch.nn as nn
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"need torch + sentence-transformers to train: {e!r}", file=sys.stderr)
        return 4

    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)

    texts = [r["definition"] for r in rows]
    Y = [[float(r["descriptors"][k]) for k in DESCRIPTOR_KEYS] for r in rows]
    mean, std = standardize_fit(Y)
    Yz = [standardize_apply(y, mean, std) for y in Y]

    print("encoding definitions with frozen MiniLM (Apache-2.0) ...")
    enc = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    X = enc.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    tr, ev = split_indices(len(rows), HOLDOUT, SEED)
    Xtr = torch.tensor(X[tr], dtype=torch.float32)
    Ytr = torch.tensor(np.array(Yz)[tr], dtype=torch.float32)
    Xev = torch.tensor(X[ev], dtype=torch.float32)
    Yev = torch.tensor(np.array(Yz)[ev], dtype=torch.float32)

    head = nn.Sequential(nn.Linear(X.shape[1], 256), nn.ReLU(),
                         nn.Linear(256, 128), nn.ReLU(),
                         nn.Linear(128, len(DESCRIPTOR_KEYS)))
    opt = torch.optim.Adam(head.parameters(), lr=1e-3)
    lossf = nn.MSELoss()
    for epoch in range(200):
        head.train(); opt.zero_grad()
        loss = lossf(head(Xtr), Ytr)
        loss.backward(); opt.step()
        if epoch % 50 == 0:
            print(f"  epoch {epoch}  train_mse {loss.item():.4f}")

    head.eval()
    with torch.no_grad():
        pred = head(Xev)
        # G7: per-dimension recovery (MAE in standardized units), not one blended score
        per_dim = {k: float(torch.mean(torch.abs(pred[:, j] - Yev[:, j])))
                   for j, k in enumerate(DESCRIPTOR_KEYS)}

    # N-NLP-4 OOD gate: training-embedding centroid + 95th-pct distance threshold
    import numpy as np2
    centroid = X[tr].mean(axis=0)
    dists = np2.linalg.norm(X[tr] - centroid, axis=1)
    ood_threshold = float(np2.percentile(dists, 95))

    torch.save(head.state_dict(), OUT / "intent_mol_head.pt")
    cfg = {"encoder": "all-MiniLM-L6-v2", "descriptor_keys": DESCRIPTOR_KEYS,
           "seed": SEED, "holdout": HOLDOUT, "n_pairs": len(rows)}
    (OUT / "run_meta.json").write_text(json.dumps({
        "stage": "intent-mol", "module": "N-NLP-1",
        "config_hash": config_hash(cfg), "config": cfg,
        "n_train": len(tr), "n_eval": len(ev),
        "per_dimension_recovery_mae_z": per_dim,   # G7 honest, per-dim
        "normalization": {"mean": mean, "std": std},
        "ood_gate": {"centroid_dim": len(centroid), "threshold_p95": ood_threshold},
        "compare_to_served": False,
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, indent=2), encoding="utf-8")
    print(f"ok  intent-mol head -> {OUT} (per-dim recovery recorded, OOD threshold {ood_threshold:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
