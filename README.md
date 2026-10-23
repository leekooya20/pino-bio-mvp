# PinoBio MVP-4 — generate → design → optimize

Implementation repo for the MVP-4 generative bio workstream (this repo is SEPARATE from
SciACA/lab-UI and from the master plan repo **Project Katala**).

- **UI/wiring** lives in [SciACA](https://github.com/aeodev/SciACA) — we only ship patches there (`VITE_API_BASE` compat).
- **Master plan / strategy / ledger master** lives in Project Katala (`docs/07..09`, `CLAUDE.md` G1–G11).
- **This repo owns:** from-scratch training pipelines (Kaggle-first), tool implementations, the `/v1` job API (SciACA contract), run artifacts.

## MVP-4 stack (locked)

| Function | Model | Mode |
|---|---|---|
| Generate (molecule) | **MoFlow 30M** — ours, MIT recipe | from-scratch, Kaggle 2×T4 |
| Generate (sequence) | **ProtGPT2-small ≤100M** — ours, Apache-2.0 recipe | from-scratch, Kaggle |
| Design (structure) | RFD4-Proteina 0.4B — served tool | no retrain (BSD-3) |
| Optimize (score) | ESM-2 650M — served tool | no retrain (LoRA later) |

## Layout

```
configs/           YAML configs + licenses.yaml mirror (sync from Katala master)
data/manifests/    dataset manifests (G1: license + provenance per dataset)
src/train/         pipeline modules built from third_party reference code
src/serve/         tool implementations + /v1 job API (specs: Katala docs/orchestrator.md §10)
scripts/           runnable entrypoints (--config always)
tests/             pytest; fixture = 100 molecules, reconstruction MUST be 100%
third_party/       pinned reference code (calvin-zcx/moflow · molecularsets/moses) — never modified in-place; our deltas are APPLIED PATCHES under patches/
artifacts/         run outputs (gitignored except run_meta.json)
patches/           our modifications to reference recipes, one .patch per modification ID
```

## Hard rules (from Katala `CLAUDE.md` — enforced here too)

- **G1:** no dataset enters training without a `configs/licenses.yaml` entry.
- **G3:** no training without frozen eval harness (fixture first).
- **G7:** report eval failures honestly; never round up numbers.
- **G10:** log seed + data version + config hash in every run.
- **G11:** read the real recipe/code/process/benchmarks BEFORE replicating; deviations go in the modifications ledger (`docs` in Katala `docs/08-generative-recipes.md`).

## Quick start

```bash
python scripts/fetch_thirdparty.py        # pins reference code (G11/G10: records SHA + license)
pytest tests/ -q                          # smoke: config + budget checks
python scripts/train_moflow.py --config configs/molgen-zinc250k.yaml
```

## Sync notes

- `configs/licenses.yaml` is a **mirror**: master lives in the Katala repo; update master first, then re-copy.
- SciACA contract assertions: `GET /v1/models|jobs|projects`, `POST /v1/jobs` (see Katala `specs/orchestrator.md` §10–11).
