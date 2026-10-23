"""§8 validation tests — exact DockQ, CAPRI/RMSD thresholds, Kabsch RMSD, ladder honesty."""
from __future__ import annotations

import os

import pytest

from benchmarks.validation.ladder import best_available, honest_label
from benchmarks.validation.metrics import (
    capri_class,
    dockq,
    is_wellfolded,
    kabsch_rmsd,
    multiseed_summary,
)


def test_dockq_perfect_and_zero():
    # perfect: fnat=1, irms=0, lrms=0 → (1 + 1 + 1)/3 = 1.0
    assert dockq(1.0, 0.0, 0.0) == pytest.approx(1.0)
    # worst: fnat=0, huge rms → ~0
    assert dockq(0.0, 1e6, 1e6) == pytest.approx(0.0, abs=1e-6)


def test_dockq_known_value():
    # fnat=0.5, irms=1.5 (→0.5), lrms=8.5 (→0.5) → (0.5+0.5+0.5)/3 = 0.5
    assert dockq(0.5, 1.5, 8.5) == pytest.approx(0.5)


def test_capri_thresholds():
    assert capri_class(0.10) == "incorrect"
    assert capri_class(0.23) == "acceptable"
    assert capri_class(0.49) == "medium"
    assert capri_class(0.80) == "high"


def test_rmsd_wellfolded_boundary():
    assert is_wellfolded(1.99) and not is_wellfolded(2.0)


def test_kabsch_identical_is_zero():
    pts = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert kabsch_rmsd(pts, pts) == pytest.approx(0.0, abs=1e-9)


def test_kabsch_translation_invariant():
    a = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
    b = [[10, 5, -3], [11, 5, -3], [10, 6, -3], [10, 5, -2]]  # same shape, shifted
    assert kabsch_rmsd(a, b) == pytest.approx(0.0, abs=1e-9)


def test_multiseed_reports_best_and_mean():
    s = multiseed_summary([3.0, 1.5, 2.5], lower_is_better=True)
    assert s["best"] == 1.5 and s["mean"] == pytest.approx(7.0 / 3)


def test_ladder_picks_highest_available_and_labels_honestly(monkeypatch):
    for v in ("ESMFOLD_ENDPOINT", "BOLTZ2_ENDPOINT", "CHAI_ENDPOINT", "AF3_ENDPOINT"):
        monkeypatch.delenv(v, raising=False)
    assert best_available() is None                       # nothing live
    monkeypatch.setenv("ESMFOLD_ENDPOINT", "http://x")
    monkeypatch.setenv("BOLTZ2_ENDPOINT", "http://y")
    r = best_available()
    assert r["name"] == "boltz2" and r["af3"] is False     # highest available, not AF3
    assert "NOT AF3" in honest_label(r)
    monkeypatch.setenv("AF3_ENDPOINT", "http://z")
    assert best_available()["af3"] is True
    assert "AF3-grade" in honest_label(best_available())


if __name__ == "__main__":
    print("run via pytest")
