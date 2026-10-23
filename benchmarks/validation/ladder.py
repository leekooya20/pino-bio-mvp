"""Honest refold-oracle ladder (§8). The driver validates on the BEST AVAILABLE rung
and labels the report with exactly that rung — AF3-grade language is reserved for an
actual AF3 rung.

Availability is by env endpoint (G8: no keys in code). Rungs ascend in fidelity; AF3 is
access-gated (Abramson 2024) and never assumed.
"""
from __future__ import annotations

import os

# rung order: low → high fidelity. af3 True ONLY on the AF3 rung.
RUNGS = [
    {"rung": 0, "name": "esmfold", "license": "MIT", "af3": False, "env": "ESMFOLD_ENDPOINT"},
    {"rung": 1, "name": "boltz2", "license": "MIT", "af3": False, "env": "BOLTZ2_ENDPOINT"},
    {"rung": 2, "name": "chai1", "license": "Apache-2.0 (verify at use)", "af3": False, "env": "CHAI_ENDPOINT"},
    {"rung": 3, "name": "alphafold3", "license": "access-gated", "af3": True, "env": "AF3_ENDPOINT"},
]


def available_rungs() -> list[dict]:
    return [r for r in RUNGS if os.environ.get(r["env"], "")]


def best_available() -> dict | None:
    """Highest-fidelity rung that is configured; None if nothing is live."""
    avail = available_rungs()
    return max(avail, key=lambda r: r["rung"]) if avail else None


def honest_label(rung: dict) -> str:
    if rung["af3"]:
        return "AF3-grade (AlphaFold3 oracle)"
    return f"{rung['name']}-validated, NOT AF3 — rerun on AF3 before any AF3-grade claim"
