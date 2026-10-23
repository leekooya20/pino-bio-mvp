"""Pinal runtime wrapper (served, Apache-2.0) for the /v1 text.design tool.

G11: written AFTER reading the Pinal repo (westlake-repl/Denovo-Pinal) + model card
+ Nature/bioRxiv abstract on 2026-10-23. Facts that shape this wrapper:

- Pinal is a TWO-STAGE text->protein framework: T2struct (natural language -> 3Di
  structure tokens) then SaProt-T (structure + text -> amino-acid sequence). 16B total.
- Checkpoints: SaProt-T 760M, T2struc-1.2B, T2struc-15.5B. The 1.2B + 760M pair runs
  on a single GPU (~1 min / 10 designs on an A40); 15B needs >=40GB. We SERVE it
  (self-host or online server) — it is NOT ours and NOT from-scratch (G9).
- Inference signature (repo): PinalDesign(desc, num, temperature, saprot_sample_type,
  multinomial_temperature, ...) -> list of designed sequences sorted by per-token prob.

This module POSTs to a self-hosted/served Pinal HTTP endpoint. It never fabricates a
sequence; transport errors return an honest error (G7). Results are labelled served;
Pinal's wet-lab validation (GFP + enzymes) is the authors' result, cited not claimed.
"""
from __future__ import annotations

import json
import os
import urllib.request


def _build_request(inputs: dict) -> dict:
    return {
        "description": inputs.get("description", inputs.get("prompt", "")),
        "num": int(inputs.get("n", 10)),
        "temperature": float(inputs.get("temperature", 1.0)),
        "saprot_sample_type": inputs.get("saprot_sample_type", "multinomial"),
        "multinomial_temperature": float(inputs.get("multinomial_temperature", 0.3)),
        # which trunk: "T2struc-1.2B" (default, 1-GPU) or "T2struc-15B" (>=40GB)
        "t2struc": inputs.get("t2struc", "T2struc-1.2B"),
    }


def design(endpoint: str, inputs: dict) -> dict:
    req = _build_request(inputs)
    body = json.dumps(req).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("PINAL_API_KEY", "")  # G8: via env, never committed/logged
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(r, timeout=int(os.environ.get("PINAL_TIMEOUT", "300"))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "served": True, "model": "pinal",
                "error": repr(e), "note": "Pinal call failed; no protein fabricated (G7).",
                "request_echo": req}
    return {
        "status": "succeeded", "measured": True, "served": True, "model": "pinal",
        "sequences": payload.get("sequences", payload.get("proteins", [])),
        "scores": payload.get("scores"),      # per-token probability ranking, if returned
        "description": req["description"],
        "provenance": "Pinal (Dai et al., Nature 2026, westlake-repl, Apache-2.0) — served; "
                      "method + any wet-lab result are the authors', cited not blended (G7)",
    }
