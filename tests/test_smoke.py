"""Smoke tests: config validity + budget + G-rules presence at boot (no training)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_config(name: str) -> dict:
    return yaml.safe_load((ROOT / "configs" / name).read_text(encoding="utf-8"))


def test_molgen_config_has_g10_and_g11_markers():
    cfg = _load_config("molgen-zinc250k.yaml")
    assert cfg["run"]["seed"], "G10: seed must be pinned in config"
    assert cfg["data"]["manifest"], "G1: dataset manifest must be declared"
    assert cfg["model"]["param_budget_m"] == 30, "M-MOFLOW-1 budget marker missing"


def test_molgen_deltas_differ_from_official_reference():
    """M-MOFLOW-1: our values are intentional deviations from the official zinc250k
    values recorded in Katala docs/08-generative-recipes.md §2. Guard against someone
    silently 'restoring' the reference values without updating the mods ledger."""
    cfg = _load_config("molgen-zinc250k.yaml")["model"]
    ref = {"b_n_flow": 10, "a_n_flow": 38, "b_conv_lu": 2, "noise_scale": 0.6}
    assert cfg["b_n_flow"] != ref["b_n_flow"]
    assert cfg["a_n_flow"] != ref["a_n_flow"]


def test_license_mirror_has_mvp4_entries():
    mirror = yaml.safe_load((ROOT / "configs" / "licenses.yaml").read_text(encoding="utf-8"))
    ids = {e["id"] for sec in ("datasets", "bio_tools") for e in mirror.get(sec, [])}
    for required in ("moses-zinc250k", "uniref50", "moflow", "protgpt2", "esm2", "rfd4-proteina"):
        assert required in ids, f"G1: missing ledger entry {required}"


def test_pin_book_exists_or_skip():
    pin = ROOT / "third_party" / "PINNED.json"
    if not pin.exists():
        pytest.skip("third_party not fetched yet")
    pins = json.loads(pin.read_text(encoding="utf-8"))
    assert pins["moflow"]["license_expected"] == "MIT"
