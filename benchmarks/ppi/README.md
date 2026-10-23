# §6 PPI binder benchmark harness (PinoBio MVP-4)

The benchmark that **earns** our public binder-design capability language (G4 gate).
It drives our own `/v1` design loop (RFD4-Proteina `design.backbone` + ESMFold/ESM-2
screening) over a fixed PPI target set and reports an honest, auditable pass rate.

Registered protocol: `docs/benchmarks.md` §6. Reference data: RFD4-Proteina leaderboard
`data.json` (snapshot 2026-10-21, repo `kierandidi/RFD4-Proteina-paper`, 3,073 rows /
19 models, sha256-pinned).

## Honesty contract (G7/G4 — baked into the harness, tested)

- **No fabrication:** if the design or fold endpoint is not live, the run emits a
  report with `status: "blocked"` and **no pass numbers** — never invented rates.
- **Not-AF3 label:** their validator is AlphaFold3. Ours is the honest ladder
  ESMFold → Chai (→ AF3 only if access appears). Every report records which **rung**
  produced the numbers; a non-AF3 rung is labelled `af3: false`.
- **Ours vs theirs never blended:** reference columns (`rfd4_proteina_*`, `bindcraft*`,
  `rfdiffusion*`) are cited from their data.json; our numbers sit under our own header
  with seed + config hash (G10).
- **Fixed target set, failures count:** targets come from the `dataset=ppi` rows (no
  cherry-picking; row hashes recorded); the attempt budget (default 200/target) counts
  failures.

## Files

- `fetch_ppi_targets.py` — pull the `dataset=ppi` rows from the pinned data.json,
  record per-row sha256 → `data/manifests/ppi-targets.jsonl` (G1/G10).
- `run_ppi_benchmark.py` — drive `/v1` jobs per target, screen, cluster, aggregate,
  write `artifacts/ppi-bench/report.json` (honest `blocked` until backends live).
- `metrics.py` — raw + clustered pass rate, bootstrap CI, Wilcoxon A/B (pure-python
  bootstrap; Wilcoxon via scipy if present, else skipped with a note).

## Run (when backends are live)

```bash
python benchmarks/ppi/fetch_ppi_targets.py
API_BASE=http://localhost:8080 python benchmarks/ppi/run_ppi_benchmark.py --attempts 200
```
