"""PPI benchmark metrics (G7: exact, honest, ours-only).

- raw_pass_rate: passes / attempts (failures count).
- clustered_pass_rate: distinct passing clusters / attempts (same semantics as the
  reference leaderboard's `clusters/attempts`).
- bootstrap_ci: nonparametric CI on a rate (pure python, no numpy needed).
- wilcoxon_ab: paired A/B test across targets, via scipy if available else skipped.
"""
from __future__ import annotations

import random


def raw_pass_rate(passes: int, attempts: int) -> float:
    return passes / attempts if attempts else 0.0


def clustered_pass_rate(passing_clusters: int, attempts: int) -> float:
    return passing_clusters / attempts if attempts else 0.0


def bootstrap_ci(successes: int, attempts: int, iters: int = 10_000,
                 alpha: float = 0.05, seed: int = 20261023) -> dict:
    """Nonparametric bootstrap CI for a pass rate. Honest about small n."""
    if attempts == 0:
        return {"point": 0.0, "low": 0.0, "high": 0.0, "n": 0, "note": "no attempts"}
    rng = random.Random(seed)
    sample = [1] * successes + [0] * (attempts - successes)
    rates = []
    for _ in range(iters):
        draw = sum(rng.choice(sample) for _ in range(attempts))
        rates.append(draw / attempts)
    rates.sort()
    lo = rates[int((alpha / 2) * iters)]
    hi = rates[int((1 - alpha / 2) * iters)]
    return {"point": successes / attempts, "low": lo, "high": hi, "n": attempts,
            "iters": iters, "alpha": alpha}


def wilcoxon_ab(arm_a: list[float], arm_b: list[float]) -> dict:
    """Paired Wilcoxon signed-rank across targets (A vs B). scipy-optional."""
    if len(arm_a) != len(arm_b) or len(arm_a) < 2:
        return {"test": "wilcoxon", "skipped": "need >=2 paired targets"}
    try:
        from scipy.stats import wilcoxon  # type: ignore
    except ImportError:
        return {"test": "wilcoxon", "skipped": "scipy not installed; install to run A/B"}
    stat, p = wilcoxon(arm_a, arm_b)
    return {"test": "wilcoxon", "statistic": float(stat), "p_value": float(p),
            "n_pairs": len(arm_a)}
