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
        "status": "available",  # trained (epoch 197/200), evaluated + wired (G7: measured)
        "version": "1.0 · 30M (29,049,444 params) · epoch 197",
        "tagline": "De novo molecular graphs via an invertible flow, validity-checked.",
        "license": "MIT (reference)",
        "source": "Our from-scratch replica — MoFlow (Zang & Wang, KDD 2020)",
        "served": False,
        "ours": True,
        "lineage": "MoFlow replica (Zang & Wang, KDD 2020), MIT, own from-scratch training",
        "checkpoint_sha256": "7f8374df3cb86e31182d4a42ff1bfd2d97df7edd5b788c9cd1090e6dbf722228",
        # measured on ZINC250k (10k x 5, temp 0.85); corrected-validity is MoFlow's
        # capability metric. Distribution over 30k gens vs the zinc250k test split.
        # Never blended with served-model numbers (G7).
        "metrics": [
            ["Validity (corrected)", "99.95%", "10k x 5 samples, temp 0.85"],
            ["Novelty", "100%", "Absent from the 224,568 training molecules"],
            ["Uniqueness", "99.99%", "Distinct among generations"],
            ["FCD/Test", "23.40", "fcd_torch vs zinc250k test (ref MoFlow 20.93)"],
            ["IntDiv", "0.908", "Internal diversity (RDKit)"],
        ],
        "metrics_source": "docs/results/molek-30m-{D3-eval,distribution}.json",
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
        "id": "megamolbart",
        "name": "MegaMolBART (served)",
        "family": "Molecular generator (SMILES BART)",
        "areas": ["generate"],
        "status": "available",
        "version": "45M · served (alt to Molek)",
        "tagline": "SMILES autoencoder for molecule generation and representation.",
        "license": "Apache-2.0",
        "source": "NVIDIA BioNeMo (served — alt generator, not ours)",
        "served": True,
        "ours": False,
    },
    {
        "id": "diffdock",
        "name": "DiffDock (served)",
        "family": "Molecular docking (pose)",
        "areas": ["optimize"],
        "status": "available",
        "version": "v2.x · served",
        "tagline": "Blind molecule–protein pose prediction with confidence ranking.",
        "license": "MIT / NVIDIA Open Model License",
        "source": "gcorso/DiffDock · NVIDIA NIM (served, in our optimize loop)",
        "served": True,
        "ours": False,
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
    {
        "id": "pinal",
        "name": "Pinal (served)",
        "family": "Text→protein design",
        "areas": ["design", "generate"],
        "status": "available",
        "version": "16B · served (T2struc + SaProt-T)",
        "tagline": "Design candidate proteins from a natural-language description of function.",
        "license": "Apache-2.0",
        "source": "Dai et al., Nature 2026 (westlake-repl, served — not ours)",
        "served": True,
        "ours": False,
    },
]

_BY_ID = {m["id"]: m for m in MODELS}


def model_by_id(mid: str) -> dict | None:
    return _BY_ID.get(mid)
