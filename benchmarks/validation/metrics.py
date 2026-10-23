"""AF3-grade validation metrics (§8) — exact, tested, honest.

DockQ (Basu & Wallner, PLoS ONE 2016) and Kabsch-superposed RMSD are the load-bearing
numbers; both are computed exactly here so they are auditable. CAPRI/RMSD classifiers
match the published thresholds. Bootstrap + Wilcoxon reuse the PPI harness style.
"""
from __future__ import annotations

import math
import random

# DockQ scaling constants (Basu & Wallner 2016)
_D1_LRMS = 8.5
_D2_IRMS = 1.5
DOCKQ_ACCEPTABLE = 0.23   # CAPRI acceptable threshold
RMSD_WELLFOLDED = 2.0     # sub-2Å Cα = well-folded (Fig-1 family)


def dockq(fnat: float, irms: float, lrms: float) -> float:
    """DockQ composite in [0,1]. fnat in [0,1]; irms/lrms in Å."""
    scaled_irms = 1.0 / (1.0 + (irms / _D2_IRMS) ** 2)
    scaled_lrms = 1.0 / (1.0 + (lrms / _D1_LRMS) ** 2)
    return (fnat + scaled_irms + scaled_lrms) / 3.0


def capri_class(dq: float) -> str:
    if dq < 0.23:
        return "incorrect"
    if dq < 0.49:
        return "acceptable"
    if dq < 0.80:
        return "medium"
    return "high"


def is_wellfolded(rmsd_ca: float) -> bool:
    return rmsd_ca < RMSD_WELLFOLDED


def kabsch_rmsd(p: list[list[float]], q: list[list[float]]) -> float:
    """Minimal-RMSD after optimal superposition (Kabsch). Needs numpy; raises if absent."""
    import numpy as np
    P = np.asarray(p, dtype=float)
    Q = np.asarray(q, dtype=float)
    if P.shape != Q.shape or P.shape[0] == 0:
        raise ValueError("coordinate sets must be same non-empty shape")
    Pc = P - P.mean(axis=0)
    Qc = Q - Q.mean(axis=0)
    H = Pc.T @ Qc
    V, _, Wt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Wt.T @ V.T))
    D = np.diag([1.0, 1.0, d])
    R = Wt.T @ D @ V.T
    Pr = Pc @ R.T
    return float(np.sqrt(((Pr - Qc) ** 2).sum() / P.shape[0]))


def bootstrap_ci(successes: int, attempts: int, iters: int = 10_000,
                 alpha: float = 0.05, seed: int = 20261023) -> dict:
    if attempts == 0:
        return {"point": 0.0, "low": 0.0, "high": 0.0, "n": 0, "note": "no attempts"}
    rng = random.Random(seed)
    sample = [1] * successes + [0] * (attempts - successes)
    rates = []
    for _ in range(iters):
        rates.append(sum(rng.choice(sample) for _ in range(attempts)) / attempts)
    rates.sort()
    return {"point": successes / attempts,
            "low": rates[int((alpha / 2) * iters)],
            "high": rates[int((1 - alpha / 2) * iters)],
            "n": attempts, "iters": iters}


def wilcoxon_ab(arm_a: list[float], arm_b: list[float]) -> dict:
    if len(arm_a) != len(arm_b) or len(arm_a) < 2:
        return {"test": "wilcoxon", "skipped": "need >=2 paired designs"}
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return {"test": "wilcoxon", "skipped": "scipy not installed"}
    stat, p = wilcoxon(arm_a, arm_b)
    return {"test": "wilcoxon", "statistic": float(stat), "p_value": float(p), "n_pairs": len(arm_a)}


def multiseed_summary(per_seed: list[float], lower_is_better: bool = False) -> dict:
    """Report best AND mean across seeds — never cherry-pick one seed (G7).
    `lower_is_better=True` for error metrics like RMSD; False for rates/DockQ."""
    if not per_seed:
        return {"n_seeds": 0, "best": None, "mean": None}
    best = min(per_seed) if lower_is_better else max(per_seed)
    mean = sum(per_seed) / len(per_seed)
    return {"n_seeds": len(per_seed), "best": best, "mean": mean,
            "std": math.sqrt(sum((x - mean) ** 2 for x in per_seed) / len(per_seed))}
