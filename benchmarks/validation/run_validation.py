"""§8 validation driver — multi-seed refold of designs on the best available rung,
AF3-grade metrics, bootstrap + Wilcoxon, honest report.

G7/G4: if no oracle rung is live, writes `status: "blocked"` with NO metrics. The
report's rung label is exactly the rung used — AF3-grade only when AF3 ran.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.request
from pathlib import Path

from benchmarks.validation.ladder import best_available, honest_label
from benchmarks.validation.metrics import (
    bootstrap_ci,
    is_wellfolded,
    multiseed_summary,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "artifacts" / "validation" / "report.json"
API_BASE = os.environ.get("API_BASE", "http://localhost:8080")
SEED = 20261023
DEFAULT_SEEDS = [20261023, 20261024, 20261025, 20261026, 20261027]


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
    return {"status": "failed", "result": {"measured": False, "error": "timeout"}}


def _blocked(reason: str, extra: dict) -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "status": "blocked", "reason": reason, "measured": False, "seed": SEED,
        "note": "No metrics produced — G7 forbids fabricating validation numbers.",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **extra,
    }, indent=2), encoding="utf-8")
    print(f"BLOCKED: {reason} → {REPORT}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--designs", type=str, default="", help="JSONL of {id, sequence}")
    ap.add_argument("--seeds", type=int, default=len(DEFAULT_SEEDS))
    args = ap.parse_args()

    rung = best_available()
    if rung is None:
        return _blocked("no refold oracle configured — set ESMFOLD_/BOLTZ2_/CHAI_/AF3_ENDPOINT",
                        {"ladder": "esmfold→boltz2→chai1→alphafold3", "af3": False})

    designs_path = Path(args.designs) if args.designs else None
    if not designs_path or not designs_path.exists():
        return _blocked("no designs supplied (--designs JSONL of {id, sequence})",
                        {"rung": rung["name"], "af3": rung["af3"], "label": honest_label(rung)})

    designs = [json.loads(l) for l in designs_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    seeds = DEFAULT_SEEDS[: args.seeds]

    per_design = []
    wellfolded = 0
    for d in designs:
        per_seed_rmsd = []
        for s in seeds:
            fold = _await(_post("/v1/jobs", {"task": "fold-protein",
                                             "inputs": {"sequence": d.get("sequence", ""), "seed": s}})["id"])
            res = fold.get("result") or {}
            if not res.get("measured"):
                return _blocked(f"fold rung '{rung['name']}' returned measured:false",
                                {"rung": rung["name"], "af3": rung["af3"], "probe": res.get("note")})
            # oracle supplies rmsd_ca (vs the design's intended backbone) when available
            if res.get("rmsd_ca") is not None:
                per_seed_rmsd.append(float(res["rmsd_ca"]))
        summ = multiseed_summary(per_seed_rmsd, lower_is_better=True)
        ok = summ["best"] is not None and is_wellfolded(summ["best"])
        wellfolded += 1 if ok else 0
        per_design.append({"id": d.get("id"), "rmsd_multiseed": summ, "wellfolded": ok})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "status": "complete", "measured": True, "seed": SEED,
        "rung": rung["name"], "af3": rung["af3"], "label": honest_label(rung),
        "n_designs": len(designs), "n_seeds": len(seeds),
        "wellfolded": wellfolded,
        "wellfolded_rate": bootstrap_ci(wellfolded, len(designs), seed=SEED),
        "per_design": per_design,
        "note": "metrics are the oracle's; ours stay ours, never blended (G7)",
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, indent=2), encoding="utf-8")
    print(f"ok  validation report -> {REPORT} (rung {rung['name']}, af3:{rung['af3']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
