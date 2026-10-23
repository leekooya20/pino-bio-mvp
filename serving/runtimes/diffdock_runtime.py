"""DiffDock runtime wrapper (served) for the /v1 dock-ligand tool.

G11: DiffDock (gcorso, MIT; NVIDIA-trained v2.2+ under NVIDIA Open Model License) is a
generative diffusion docker — it samples protein–ligand poses (position, orientation,
torsions) with no binding-pocket input, then ranks them with a confidence model.
Verified live 2026-10-24 (repo + NVIDIA NIM card).

This sits on OUR molecule-design side (Stan decision 2026-10-24): we dock OUR generated
molecules against targets inside generate→screen→optimize. FLORA never touches molecules.

Honest (G7): no fabricated poses; transport error → honest error. Poses/scores are
DiffDock's, cited not blended.
"""
from __future__ import annotations

import json
import os
import urllib.request


def dock(endpoint: str, inputs: dict) -> dict:
    req = {
        "ligand": inputs.get("ligand_smiles", inputs.get("smiles", "")),
        "protein": inputs.get("target_pdb", ""),
        "num_poses": int(inputs.get("num_poses", 10)),
    }
    body = json.dumps(req).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("DIFFDOCK_API_KEY", "")  # G8: via env only
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(r, timeout=int(os.environ.get("DIFFDOCK_TIMEOUT", "300"))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "served": True, "model": "diffdock",
                "error": repr(e), "note": "DiffDock call failed; no pose fabricated (G7).",
                "request_echo": req}
    return {"status": "succeeded", "measured": True, "served": True, "model": "diffdock",
            "poses": payload.get("poses", []),
            "confidences": payload.get("confidences"),
            "provenance": "DiffDock (gcorso MIT / NVIDIA Open) — served; poses are DiffDock's, cited not blended (G7)"}
