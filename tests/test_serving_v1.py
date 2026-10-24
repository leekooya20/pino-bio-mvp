"""Smoke test for the /v1 serving layer — contract §10/§11 shape checks.
Runs against the honest `pending` backends (no GPU, no secrets). G7: asserts
that an unavailable backend returns `measured: False` + a note, never fake output.
"""
from __future__ import annotations

import time

from fastapi.testclient import TestClient

from serving.app import app

client = TestClient(app)


def test_models_shape():
    r = client.get("/v1/models")
    assert r.status_code == 200
    ids = {m["id"] for m in r.json()}
    assert {"molek", "seqgen", "rfd4-proteina", "esm2", "esmfold"} <= ids
    # our replicas must carry a lineage line (never claim method authorship)
    molek = client.get("/v1/models/molek").json()
    assert "MoFlow replica" in molek["lineage"]
    assert molek["status"] == "available"  # trained (epoch 197), evaluated + wired
    # measured metrics are attached (G7: our numbers, never blended with served models)
    assert any("99.95" in str(v) for row in molek["metrics"] for v in row)


def test_unknown_task_is_validation_error():
    r = client.post("/v1/jobs", json={"task": "mint-coins"})
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "validation"


def _run(task: str, inputs: dict | None = None) -> dict:
    r = client.post("/v1/jobs", json={"task": task, "inputs": inputs or {}})
    assert r.status_code == 200
    jid = r.json()["id"]
    for _ in range(50):
        j = client.get(f"/v1/jobs/{jid}").json()
        if j["status"] in ("succeeded", "failed"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_molecule_pending_is_honest():
    j = _run("generate-molecule", {"n": 5})
    assert j["status"] == "succeeded"
    res = j["result"]
    assert res["measured"] is False        # G7: not a real result yet
    assert res["generated"] == []          # no fabricated molecules
    assert "Molek-30M" in res["note"]


def test_design_binder_passthrough():
    j = _run("design-binder", {"mode": "binder", "reasoning_depth": 3,
                               "search_criteria": {"plddt": 0.8}})
    res = j["result"]
    assert res["passthrough"]["reasoning_depth"] == 3      # §7 passthrough preserved
    assert res["passthrough"]["search_criteria"] == {"plddt": 0.8}
    assert res["measured"] is False


def test_design_trajectory_stages_honest():
    j = _run("design-binder", {"mode": "binder", "reasoning_depth": 2})
    traj = j["result"]["trajectory"]
    names = [s["stage"] for s in traj]
    assert names == ["latent", "topology", "sequence_structure", "contacts", "refold"]
    # adaptive allocation: the structural core gets depth+1
    core = next(s for s in traj if s["stage"] == "sequence_structure")
    assert core["reasoning_depth"] == 3
    # honest: no backend → every stage pending, not fabricated-done
    assert all(s["status"] == "pending" and s["measured"] is False for s in traj)


if __name__ == "__main__":
    test_models_shape()
    test_unknown_task_is_validation_error()
    test_molecule_pending_is_honest()
    test_design_binder_passthrough()
    print("serving smoke: all passed")
