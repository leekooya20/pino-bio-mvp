#!/usr/bin/env python
"""Farm-knob steering target (M-MOFLOW-3): descriptor STATISTICS of the ChEBI
agrochemical positives. PinoBio MVP-4, G7/G10/G11.

This is the agri moat's non-neural half: the region of descriptor space that real
agrochemicals occupy. Molek's property optimizer steers generations toward this target
(mean) while staying inside the observed band (quantiles). The neural half (text->target)
is scripts/train_intent_mol.py; both read the same ChEBI agchem pairs (G11, derived from
ChEBI's own has_role subtree, not hand-picked).

Honest (G7): pure statistics of real RDKit descriptors — nothing modelled or fabricated.
Reports exact N, per-descriptor mean/std and 5/25/50/75/95 quantiles, and the count of
positives that actually carried a parseable structure.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = ROOT / "data" / "external" / "chebi_agchem" / "pairs.jsonl"
OUT = ROOT / "artifacts" / "farm-knob"

DESCRIPTOR_KEYS = ["MolWt", "cLogP", "TPSA", "HBD", "HBA", "RotBonds",
                   "AromaticRings", "F", "Cl", "Br"]


def quantile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_vals[lo]
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def main() -> int:
    if not PAIRS.exists():
        print(f"missing {PAIRS}; run scripts/fetch_chebi_agchem.py on compute first.",
              file=sys.stderr)
        return 2
    rows = [json.loads(l) for l in PAIRS.read_text(encoding="utf-8").splitlines() if l.strip()]
    with_desc = [r for r in rows if r.get("descriptors")]
    if len(with_desc) < 20:
        print(f"only {len(with_desc)} positives with descriptors — too few for honest stats (G7).",
              file=sys.stderr)
        return 3

    stats: dict[str, dict] = {}
    for k in DESCRIPTOR_KEYS:
        vals = sorted(float(r["descriptors"][k]) for r in with_desc if k in r["descriptors"])
        n = len(vals)
        mean = sum(vals) / n
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n) or 1.0
        stats[k] = {
            "n": n, "mean": mean, "std": std,
            "p5": quantile(vals, 0.05), "p25": quantile(vals, 0.25),
            "p50": quantile(vals, 0.50), "p75": quantile(vals, 0.75),
            "p95": quantile(vals, 0.95),
            "min": vals[0], "max": vals[-1],
        }

    OUT.mkdir(parents=True, exist_ok=True)
    meta = {
        "stage": "farm-knob", "module": "M-MOFLOW-3",
        "source": "ChEBI agrochemical subtree (CHEBI:33286), RDKit descriptors",
        "n_positives_total": len(rows),
        "n_positives_with_descriptors": len(with_desc),
        "descriptor_keys": DESCRIPTOR_KEYS,
        "steering_target_mean": {k: stats[k]["mean"] for k in DESCRIPTOR_KEYS},
        "observed_band_p5_p95": {k: [stats[k]["p5"], stats[k]["p95"]] for k in DESCRIPTOR_KEYS},
        "full_stats": stats,
        "measured": True,
        "note": "pure statistics of real agrochemicals; Molek optimizer steers toward "
                "steering_target_mean within observed_band_p5_p95. Nothing modelled (G7).",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (OUT / "farmknob_target.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"ok  farm-knob target -> {OUT / 'farmknob_target.json'} "
          f"(N={len(with_desc):,} agrochemicals)")
    for k in DESCRIPTOR_KEYS:
        s = stats[k]
        print(f"   {k:>14}: mean {s['mean']:8.3f}  band[p5,p95] "
              f"[{s['p5']:8.3f}, {s['p95']:8.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
