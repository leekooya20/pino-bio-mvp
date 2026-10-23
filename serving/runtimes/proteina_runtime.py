"""RFD4-Proteina runtime wrapper (served, BSD-3) for the /v1 design.backbone tool.

G11: written AFTER reading the RFD4-Proteina docs (rfd4-proteina.org/latest,
RosettaCommons/RFD4-Proteina README, NVIDIA NIM overview) on 2026-10-23. Key facts
that shape this wrapper:

- RFD4-Proteina needs Python 3.12 + CUDA + an NVIDIA GPU, Linux x86_64 ONLY. We do
  NOT run it in-process (our runtime is Kaggle py3.13 / arbitrary). Instead we talk
  to its **NVIDIA NIM synchronous HTTP endpoint** — a single POST returns backbone
  + sequence. This is why serving goes through a pinned container/endpoint, never
  the training runtime (see docs/findings-log F-0010).
- Input dialects: (1) a self-contained annotated mmCIF, or (2) a condition spec
  (YAML/JSON + attached structure files carried as NAMED FILES in the body, never
  filesystem paths — a security property we preserve).
- Tasks select how the sampler runs the trajectory, not the design problem:
  generation · motif_scaffolding · partial_diffusion · inverse_folding. A binder is
  `generation` with the target atoms held + epitope hotspots.
- Compute budget knob is `thinking_low` / `thinking_high` — our §7 `reasoning_depth`
  maps onto it. Reward-guided beam search is configured by metrics/criteria — our
  §7 `search_criteria` maps onto that.

This module makes the real HTTP call to PROTEINA_ENDPOINT. It never fabricates a
backbone; on any transport error it returns an honest error dict (G7). It claims
nothing of RFD4-Proteina's as ours — results are labelled served.
"""
from __future__ import annotations

import json
import os
import urllib.request

# our design.backbone `mode` → RFD4 task (docs: task = sampler trajectory)
_MODE_TASK = {
    "free": "generation",
    "binder": "generation",      # + target held by coord/seq conditioning + hotspots
    "motif": "motif_scaffolding",
    "partial": "partial_diffusion",
    "inverse": "inverse_folding",
}

# §7 reasoning_depth → RFD4 thinking budget (docs: thinking_low/thinking_high)
def _thinking(reasoning_depth) -> str:
    try:
        d = int(reasoning_depth)
    except (TypeError, ValueError):
        return "thinking_low"
    return "thinking_high" if d >= 2 else "thinking_low"


def _build_request(inputs: dict, passthrough: dict) -> dict:
    mode = inputs.get("mode", "free")
    task = _MODE_TASK.get(mode, "generation")
    req: dict = {
        "task": task,
        "num_replicates": int(inputs.get("n", 1)),
        "thinking": _thinking(passthrough.get("reasoning_depth")),
    }
    if inputs.get("length") is not None:
        req["length"] = int(inputs["length"])
    if inputs.get("seed") is not None:
        req["seed"] = int(inputs["seed"])
    # binder/motif: target structure + hotspots carried as condition spec
    if inputs.get("target_pdb"):
        req["input_dialect"] = "condition_spec"
        req["target_structure"] = inputs["target_pdb"]   # named file content, not a path
        if inputs.get("hotspots"):
            req["hotspots"] = inputs["hotspots"]
    # §7 reward-guided search criteria passthrough
    if passthrough.get("search_criteria"):
        req["search_criteria"] = passthrough["search_criteria"]
    return req


def backbones(endpoint: str, inputs: dict, passthrough: dict) -> dict:
    req = _build_request(inputs, passthrough)
    body = json.dumps(req).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    # G8: an optional API key is read from env, never hardcoded, never logged back.
    key = os.environ.get("PROTEINA_API_KEY", "")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        r = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(r, timeout=int(os.environ.get("PROTEINA_TIMEOUT", "300"))) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error", "measured": False, "served": True, "model": "rfd4-proteina",
            "error": repr(e), "note": "RFD4-Proteina NIM call failed; no backbone fabricated (G7).",
            "request_echo": req,
        }
    # Normalize to the §10.3 output schema; keep served provenance explicit.
    return {
        "status": "succeeded", "measured": True, "served": True, "model": "rfd4-proteina",
        "backbones": payload.get("backbones", payload.get("pdbs", [])),
        "designability": payload.get("designability"),
        "novelty": payload.get("novelty"),
        "diversity": payload.get("diversity"),
        "passthrough": passthrough,
        "provenance": "RFD4-Proteina (Baker Lab × NVIDIA, BSD-3) — served; metrics are theirs, cited not blended (G7)",
    }
