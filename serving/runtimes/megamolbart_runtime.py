"""MegaMolBART runtime wrapper (served, Apache-2.0) for /v1 mol.generate alt.

G11: MegaMolBART (NVIDIA BioNeMo) is a 45M SMILES BART autoencoder for molecule
generation/representation. Verified live 2026-10-24 (model card + LICENSE). Served alt
to Molek (Stan 2026-10-24: not from-scratch). Honest (G7): no fabricated SMILES; its
numbers stay cited, never blended with Molek's.
"""
from __future__ import annotations

import json
import os
import urllib.request


def sample(endpoint: str, inputs: dict) -> dict:
    req = {"n": int(inputs.get("n", 10)),
           "seed_smiles": inputs.get("seed_smiles", ""),
           "scaled_radius": inputs.get("scaled_radius", 1.0)}
    body = json.dumps(req).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("MEGAMOLBART_API_KEY", "")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(r, timeout=int(os.environ.get("MEGAMOLBART_TIMEOUT", "120"))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "served": True, "model": "megamolbart",
                "error": repr(e), "note": "MegaMolBART call failed; no SMILES fabricated (G7)."}
    return {"status": "succeeded", "measured": True, "served": True, "model": "megamolbart",
            "molecules": payload.get("molecules", payload.get("generated", [])),
            "provenance": "MegaMolBART (NVIDIA BioNeMo, Apache-2.0) — served alt; cited not blended (G7)"}
