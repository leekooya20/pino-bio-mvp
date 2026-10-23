"""Drive the §6 PPI binder benchmark over our own /v1 design loop.

For each fixed target: POST `design-binder` jobs (RFD4-Proteina via /v1), screen each
backbone through the fold ladder (ESMFold first, honest `af3:false`), cluster the
passes, and aggregate raw + clustered pass rate with a bootstrap CI.

G7/G4 honesty, enforced in control flow:
- If the design or fold backend returns `measured: false` (not live), the run STOPS
  and writes `status: "blocked"` with NO pass numbers. We never fabricate a rate.
- The validator rung is recorded; a non-AF3 rung is labelled `af3: false`.
- Our numbers are written under our own header with seed + config hash (G10);
  reference numbers stay in the manifest, cited, never merged in.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

from benchmarks.ppi.metrics import bootstrap_ci, clustered_pass_rate, raw_pass_rate

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "manifests" / "ppi-targets.jsonl"
REPORT = ROOT / "artifacts" / "ppi-bench" / "report.json"
API_BASE = os.environ.get("API_BASE", "http://localhost:8080")
SEED = 20261023


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}{path}", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API_BASE}{path}", timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))


def _await(job_id: str, timeout_s: int = 1800) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        j = _get(f"/v1/jobs/{job_id}")
        if j["status"] in ("succeeded", "failed"):
            return j
        time.sleep(2)
    return {"status": "failed", "result": {"error": "timeout", "measured": False}}


def _blocked(reason: str, extra: dict) -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "status": "blocked", "reason": reason, "measured": False,
        "seed": SEED, "note": "No pass rates produced — G7 forbids fabricating benchmark numbers.",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **extra,
    }, indent=2), encoding="utf-8")
    print(f"BLOCKED: {reason} → {REPORT}")
    return 0


def cluster_passes(backbones: list[str]) -> int:
    """Placeholder clustering: distinct passing structures. Wired to a real
    sequence/structure clustering (e.g. Foldseek/mmseqs) when backbones are live."""
    return len({hash(b) for b in backbones})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=200)
    ap.add_argument("--targets", type=int, default=0, help="limit targets (0 = all)")
    args = ap.parse_args()

    if not MANIFEST.exists():
        return _blocked("target manifest missing — run fetch_ppi_targets.py first", {})

    lines = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = lines[0]
    targets = [l for l in lines[1:] if "target" in l]
    if args.targets:
        targets = targets[: args.targets]

    # Probe the loop once; if the backend isn't live, block honestly (no fake run).
    probe = _post("/v1/jobs", {"task": "design-binder",
                               "inputs": {"mode": "binder", "n": 1}})
    probe_job = _await(probe["id"], timeout_s=120)
    pres = (probe_job.get("result") or {})
    if not pres.get("measured", False):
        return _blocked(
            "design-binder backend not live (measured:false) — set PROTEINA_ENDPOINT and rerun",
            {"target_set": {"n_targets": len(targets), "snapshot_sha256": meta.get("snapshot_sha256")},
             "attempts_budget": args.attempts, "validator_plan": {"rung": "esmfold", "af3": False},
             "probe": pres.get("note")})

    # Live path (runs when RFD4 + fold endpoints are configured).
    per_target = []
    for t in targets:
        job = _await(_post("/v1/jobs", {"task": "design-binder", "inputs": {
            "mode": "binder", "target_pdb": t.get("target"), "n": args.attempts,
            "seed": SEED}})["id"])
        res = job.get("result") or {}
        backbones = res.get("backbones", [])
        # screen: fold each, pass if designable (threshold applied by the fold tool chain)
        passes = 0
        passing = []
        for bb in backbones:
            fold = _await(_post("/v1/jobs", {"task": "fold-protein",
                                             "inputs": {"sequence": bb}})["id"]).get("result") or {}
            if fold.get("measured") and (fold.get("mean_plddt") or 0) >= 70:
                passes += 1
                passing.append(bb)
        clusters = cluster_passes(passing)
        per_target.append({
            "target": t.get("target"), "attempts": args.attempts,
            "passes": passes, "clusters": clusters,
            "raw_pass_rate": raw_pass_rate(passes, args.attempts),
            "clustered_pass_rate": clustered_pass_rate(clusters, args.attempts),
            "ci": bootstrap_ci(passes, args.attempts, seed=SEED),
        })

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "status": "complete", "measured": True, "seed": SEED,
        "validator": {"rung": "esmfold", "af3": False,
                      "label": "NOT AF3 — honest ladder rung; rerun on AF3 before any public claim"},
        "target_set": {"n_targets": len(targets), "snapshot_sha256": meta.get("snapshot_sha256")},
        "attempts_budget": args.attempts,
        "ours": per_target,
        "reference_note": "their numbers remain in data/manifests/ppi-targets.jsonl, cited not blended (G7)",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, indent=2), encoding="utf-8")
    print(f"ok  report -> {REPORT} ({len(per_target)} targets, esmfold rung, af3:false)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
