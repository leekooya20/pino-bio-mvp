"""MVP-4 tool wrappers for the /v1 serving layer.

Each tool maps a SciACA task to a backend (spec Â§10.2/Â§10.3). The guiding rule is
G7: when a backend's checkpoint/container is not available, return an honest
`pending` result â€” empty generated set + a `note` explaining why â€” NEVER fabricated
output. A trained checkpoint flips the same function to real results with no API
change.

Checkpoint/container discovery is by env + path, so nothing secret is hardcoded (G8).
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _pending(note: str, **extra) -> dict:
    out = {"status": "pending", "generated": [], "note": note, "measured": False}
    out.update(extra)
    return out


# --- mol.generate  (task: generate-molecule / explore-chemistry) â†’ Molek-30M ---
def mol_generate(inputs: dict) -> dict:
    ckpt = os.environ.get("MOLEK_CKPT", str(ROOT / "artifacts" / "molek-30m" / "model.pt"))
    n = int(inputs.get("n", 10))
    if not Path(ckpt).exists():
        return _pending(
            "Molek-30M checkpoint not available yet (run #7 training). No molecules "
            "to report â€” G7 forbids fabricating generated structures.",
            model="molek", requested_n=n,
        )
    # Real path (wired when the checkpoint lands): run the frozen reference
    # generate.py under third_party/moflow and return {smiles, qed, logp, sim}.
    from importlib import import_module  # local import keeps server boot light
    gen = import_module("serving.runtimes.molek_runtime")  # added at D2/D3
    return gen.sample(ckpt=ckpt, inputs=inputs)


# --- seq.generate  (task: design-sequence) â†’ Seqgen-small ---
def seq_generate(inputs: dict) -> dict:
    ckpt = os.environ.get("SEQGEN_CKPT", str(ROOT / "artifacts" / "seqgen-small" / "model.pt"))
    n = int(inputs.get("n", 10))
    if not Path(ckpt).exists():
        return _pending(
            "Seqgen-small checkpoint not available yet (config locked, untrained). "
            "No sequences to report (G7).",
            model="seqgen", requested_n=n,
            sampling={"top_k": inputs.get("top_k", 950),
                      "repetition_penalty": inputs.get("repetition_penalty", 1.2)},
        )
    from importlib import import_module
    gen = import_module("serving.runtimes.seqgen_runtime")
    return gen.sample(ckpt=ckpt, inputs=inputs)


# --- design.backbone  (task: design-binder) â†’ RFD4-Proteina (served, BSD-3) ---
def design_backbone(inputs: dict) -> dict:
    # Â§7 passthrough: reasoning_depth + search_criteria travel into the trajectory.
    passthrough = {
        "reasoning_depth": inputs.get("reasoning_depth"),
        "search_criteria": inputs.get("search_criteria"),
        "mode": inputs.get("mode", "free"),
    }
    endpoint = os.environ.get("PROTEINA_ENDPOINT", "")
    if not endpoint:
        return _pending(
            "RFD4-Proteina served backend not configured (needs the pinned py3.12 "
            "container; Kaggle runtime is py3.13). Set PROTEINA_ENDPOINT to go live. "
            "Backbones are not fabricated (G7).",
            model="rfd4-proteina", served=True, passthrough=passthrough,
        )
    from importlib import import_module
    client = import_module("serving.runtimes.proteina_runtime")
    return client.backbones(endpoint=endpoint, inputs=inputs, passthrough=passthrough)


# --- esm.embed scorer  (task: optimize-property) â†’ ESM-2 (served) ---
def esm_score(inputs: dict) -> dict:
    endpoint = os.environ.get("ESM2_ENDPOINT", "")
    if not endpoint:
        return _pending(
            "ESM-2 scorer endpoint not configured (set ESM2_ENDPOINT). Scores are not "
            "fabricated (G7). Note: ESM-2 is a SERVED model â€” its numbers stay cited "
            "as ESM-2's, never blended with our generators' numbers.",
            model="esm2", served=True,
        )
    from importlib import import_module
    client = import_module("serving.runtimes.esm_runtime")
    return client.score(endpoint=endpoint, inputs=inputs)


# --- esm.fold  (task: fold-*) â†’ ESMFold (served) ---
def esm_fold(inputs: dict) -> dict:
    endpoint = os.environ.get("ESMFOLD_ENDPOINT", "")
    if not endpoint:
        return _pending(
            "ESMFold endpoint not configured (set ESMFOLD_ENDPOINT). First rung of the "
            "honest fold ladder; no pLDDT fabricated (G7).",
            model="esmfold", served=True,
        )
    from importlib import import_module
    client = import_module("serving.runtimes.esm_runtime")
    return client.fold(endpoint=endpoint, inputs=inputs)


def text_design(inputs: dict) -> dict:
    """text.design (task: design-from-text) -> Pinal (served, Apache-2.0)."""
    endpoint = os.environ.get("PINAL_ENDPOINT", "")
    desc = inputs.get("description", inputs.get("prompt", ""))
    if not endpoint:
        return _pending(
            "Pinal text->protein endpoint not configured (set PINAL_ENDPOINT; 16B served, "
            "not ours). No proteins fabricated (G7). Pinal is served Apache-2.0 - its "
            "wet-lab results are the authors', cited not claimed.",
            model="pinal", served=True, description=desc,
        )
    from importlib import import_module
    client = import_module("serving.runtimes.pinal_runtime")
    return client.design(endpoint=endpoint, inputs=inputs)


# SciACA task â†’ tool (spec Â§10.2). Unknown task â‡’ validation error (Â§11).
TASK_TOOL = {
    "generate-molecule": mol_generate,
    "explore-chemistry": mol_generate,
    "design-sequence": seq_generate,
    "design-binder": design_backbone,
    "design-from-text": text_design,
    "optimize-property": esm_score,
    "fold-protein": esm_fold,
    "fold-complex": esm_fold,
}
