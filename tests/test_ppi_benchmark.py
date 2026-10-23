"""Tests for the §6 PPI benchmark harness — metrics + the G7 honest-blocked path."""
from __future__ import annotations

import json
from pathlib import Path

from benchmarks.ppi.metrics import bootstrap_ci, clustered_pass_rate, raw_pass_rate


def test_rates_exact():
    assert raw_pass_rate(37, 200) == 37 / 200
    assert clustered_pass_rate(0, 200) == 0.0
    assert raw_pass_rate(0, 0) == 0.0  # no div-by-zero


def test_bootstrap_ci_brackets_point():
    ci = bootstrap_ci(37, 200, iters=2000, seed=1)
    assert ci["low"] <= ci["point"] <= ci["high"]
    assert ci["n"] == 200


def test_blocked_when_manifest_missing(tmp_path, monkeypatch):
    # Point the harness at a non-existent manifest → must block, never fabricate.
    import benchmarks.ppi.run_ppi_benchmark as r
    monkeypatch.setattr(r, "MANIFEST", tmp_path / "nope.jsonl")
    monkeypatch.setattr(r, "REPORT", tmp_path / "report.json")
    monkeypatch.setattr("sys.argv", ["run", "--attempts", "200"])
    rc = r.main()
    assert rc == 0
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "blocked"
    assert report["measured"] is False
    assert "fabricat" in report["note"].lower()


if __name__ == "__main__":
    test_rates_exact()
    test_bootstrap_ci_brackets_point()
    print("ppi metrics ok (run via pytest for the blocked-path test)")
