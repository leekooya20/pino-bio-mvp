"""Fetch the fixed PPI target set from the pinned RFD4-Proteina leaderboard data.json
and record per-row sha256 (G1/G10). No cherry-picking: we take every `dataset=ppi`
row as the task list and pin it.

Honest: this records the TARGETS (what to design against) and the reference columns
(their numbers, cited) — it does NOT copy any of their results into ours. Our numbers
are produced only by run_ppi_benchmark.py under our own header.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "manifests" / "ppi-targets.jsonl"
DATA_URL = "https://rfd4-proteina.org/benchmarks/data.json"


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(DATA_URL, headers={"User-Agent": "pino-bio-mvp/ppi-targets"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"STOP: could not fetch {DATA_URL}: {e!r}", file=sys.stderr)
        return 2
    snapshot_sha = sha256_text(raw)
    data = json.loads(raw)
    rows = data.get("rows", data if isinstance(data, list) else [])

    ppi_rows = [row for row in rows if str(row.get("dataset", "")).lower() == "ppi"]
    if not ppi_rows:
        print("STOP: no dataset=ppi rows found (schema may have changed).", file=sys.stderr)
        return 3

    # Unique target list (no cherry-picking); keep reference columns cited, not copied.
    targets: dict[str, dict] = {}
    for row in ppi_rows:
        t = str(row.get("target", ""))
        targets.setdefault(t, {"target": t, "reference_rows": []})
        targets[t]["reference_rows"].append({
            "model": row.get("model"), "attempts": row.get("attempts"),
            "passes": row.get("passes"), "clusters": row.get("clusters"),
            "row_sha256": sha256_text(json.dumps(row, sort_keys=True)),
        })

    entry_meta = {
        "id": "ppi-targets",
        "source_url": DATA_URL,
        "snapshot_sha256": snapshot_sha,
        "snapshot": data.get("snapshot"),
        "n_ppi_rows": len(ppi_rows),
        "n_targets": len(targets),
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "note": "fixed PPI target set; reference_rows are THEIR numbers (cited, not blended, G7)",
    }
    with MANIFEST.open("w", encoding="utf-8") as f:
        f.write(json.dumps(entry_meta) + "\n")
        for t in targets.values():
            f.write(json.dumps(t) + "\n")
    print(f"ok  {len(targets)} PPI targets ({len(ppi_rows)} rows) -> {MANIFEST}")
    print(f"ok  snapshot sha256 {snapshot_sha[:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
