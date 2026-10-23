"""Model cards for GET /v1/models — mirror the SciACA `src/data/models.ts` shape
so cards round-trip into the UI (contract §11). Statuses are HONEST (G7): our own
models read "training"/"planned" until their checkpoints exist; served models read
"available" only for the wrapper, with a `served` flag and license.

Lineage lines are mandated for our replicas (never claim authorship of the method).
"""
from __future__ import annotations

MODELS: list[dict] = [
    {
        "id": "molek",
        "name": "Molek-30M",
        "family": "Molecular graph generator",
        "areas": ["generate", "optimize"],
        "status": "training",  # honest: run #7 in progress; no checkpoint yet (G7)
        "version": "0.1 · 30M (29,049,444 params)",
        "tagline": "De novo molecular graphs via an invertible flow, validity-checked.",
        "license": "MIT (reference)",
        "source": "Our from-scratch replica — MoFlow (Zang & Wang, KDD 2020)",
        "served": False,
        "ours": True,
        "lineage": "MoFlow replica (Zang & Wang, KDD 2020), MIT, own from-scratch training",
    },
    {
        "id": "seqgen",
        "name": "Seqgen-small",
        "family": "Protein sequence generator",
        "areas": ["generate", "design"],
        "status": "planned",  # honest: config locked, untrained (G7)
        "version": "0.1 · ≤100M",
        "tagline": "Autoregressive de novo protein sequences with per-token likelihood.",
        "license": "Apache-2.0 (reference)",
        "source": "Our from-scratch replica — ProtGPT2 (Ferruz et al., Nat Commun 2022)",
        "served": False,
        "ours": True,
        "lineage": "ProtGPT2 replica (Ferruz, Schmidt & Hocker, Nat Commun 2022), Apache-2.0, own from-scratch training",
    },
    {
        "id": "rfd4-proteina",
        "name": "RFD4-Proteina",
        "family": "Backbone design (flow matching)",
        "areas": ["design"],
        "status": "available",
        "version": "served",
        "tagline": "Unconditional, motif-scaffold and binder backbone design.",
        "license": "BSD-3-Clause",
        "source": "UW IPD × NVIDIA (served, not ours)",
        "served": True,
        "ours": False,
    },
    {
        "id": "esm2",
        "name": "ESM-2",
        "family": "Protein language model",
        "areas": ["understand", "optimize"],
        "status": "available",
        "version": "650M · served",
        "tagline": "Residue embeddings and zero-shot variant scores from sequence alone.",
        "license": "MIT",
        "source": "Lin et al., Science 2023 (served, not ours)",
        "served": True,
        "ours": False,
    },
    {
        "id": "esmfold",
        "name": "ESMFold",
        "family": "Structure prediction",
        "areas": ["understand"],
        "status": "available",
        "version": "served",
        "tagline": "Single-sequence structure prediction (first rung of the fold ladder).",
        "license": "MIT",
        "source": "Lin et al., Science 2023 (served, not ours)",
        "served": True,
        "ours": False,
    },
]

_BY_ID = {m["id"]: m for m in MODELS}


def model_by_id(mid: str) -> dict | None:
    return _BY_ID.get(mid)
