"""Tests for intent-mol pure-math helpers (data/dep-independent)."""
from __future__ import annotations

from scripts.train_intent_mol import (
    config_hash,
    split_indices,
    standardize_apply,
    standardize_fit,
)


def test_standardize_roundtrip():
    rows = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]
    mean, std = standardize_fit(rows)
    assert mean == [2.0, 20.0]
    z = standardize_apply([2.0, 20.0], mean, std)
    assert z == [0.0, 0.0]  # the mean maps to zero


def test_standardize_constant_dim_no_divzero():
    rows = [[5.0], [5.0], [5.0]]
    mean, std = standardize_fit(rows)
    assert std == [1.0]  # floored, not zero
    assert standardize_apply([5.0], mean, std) == [0.0]


def test_split_deterministic_and_disjoint():
    tr, ev = split_indices(100, 0.1, seed=20261023)
    assert len(ev) == 10 and len(tr) == 90
    assert set(tr).isdisjoint(ev)
    tr2, ev2 = split_indices(100, 0.1, seed=20261023)
    assert ev == ev2  # deterministic from seed


def test_config_hash_stable():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})


if __name__ == "__main__":
    test_standardize_roundtrip()
    test_standardize_constant_dim_no_divzero()
    test_split_deterministic_and_disjoint()
    test_config_hash_stable()
    print("intent-mol math ok")
