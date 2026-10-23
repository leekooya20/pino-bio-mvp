"""ESM-2 / ESMFold served runtimes for /v1 (optimize-property scorer + fold ladder).

G7 discipline: ESM-2 is a SERVED model — its scores/pLDDT are reported as ESM-2's,
never blended with our generators' numbers. G8: endpoint + optional key via env,
never committed. No score or structure is fabricated; transport errors return an
honest error dict.
"""
from __future__ import annotations

import json
import os
import urllib.request


def _post(endpoint: str, req: dict, env_key: str, timeout: int = 120) -> dict:
    body = json.dumps(req).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get(env_key, "")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    r = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def score(endpoint: str, inputs: dict) -> dict:
    try:
        payload = _post(endpoint, {"sequences": inputs.get("sequences", []),
                                   "checkpoint": inputs.get("checkpoint", "650M")},
                        "ESM2_API_KEY")
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "served": True, "model": "esm2",
                "error": repr(e), "note": "ESM-2 scorer call failed; no scores fabricated (G7)."}
    return {"status": "succeeded", "measured": True, "served": True, "model": "esm2",
            "scores": payload.get("scores"), "analysis": payload.get("analysis"),
            "provenance": "ESM-2 (Lin et al., Science 2023, MIT) — served; scores are ESM-2's, never blended (G7)"}


def fold(endpoint: str, inputs: dict) -> dict:
    try:
        payload = _post(endpoint, {"sequence": inputs.get("sequence", "")}, "ESMFOLD_API_KEY", timeout=300)
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "served": True, "model": "esmfold",
                "error": repr(e), "note": "ESMFold call failed; no pLDDT fabricated (G7)."}
    return {"status": "succeeded", "measured": True, "served": True, "model": "esmfold",
            "mean_plddt": payload.get("mean_plddt"), "ptm": payload.get("ptm"),
            "length": payload.get("length"), "files": payload.get("files"),
            "provenance": "ESMFold (served) — first rung of the honest fold ladder"}
