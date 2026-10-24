# Molek-30M — Benchmark Report

**Date:** 2026-10-24 · **Checkpoint:** epoch 197/200 · sha256 `7f8374df3cb8…`
**Harness:** frozen reference `generate.py` (G3/G11) · **Protocol:** 10,000 × 5 experiments,
temperature 0.85 · **Seed:** 20261023 · All numbers measured (G7).

## 1. Generation quality — dual report (M-MOFLOW-4)

| Metric | Corrected | Uncorrected (raw) | Reference MoFlow (corr.) |
|---|---|---|---|
| Validity | **99.95%** (sd 0.02) | 0.00% (sd 0) | 100.00% |
| Novelty | **100.00%** (sd 0.00) | 0.00% | 100.00% |
| Uniqueness | **99.99%** | 0.00% | ~100% |
| Abs. novelty | 99.94% (sd 0.02) | 0.00% | — |
| Abs. uniqueness | 99.94% (sd 0.02) | 0.00% | — |

Per-experiment valid counts (of 10,000): 9996, 9998, 9994, 9990, 9995.
Uncorrected 0%: MoFlow does rely on valency correction, but published MoFlow validity without correction on ZINC250k is **63.11%** (GDSS, Jo et al. 2022, Table 2), so a 0% raw result is not explained by the architecture alone. The "stricter modern-RDKit sanitization" explanation was tested and does **not** hold: MoFlow's own `valid_mol` accepts valid molecules and rejects every over-valent one **identically** under RDKit 2022.09.5 and 2026.09.1 (research, 2026-10-24; MoFlow `valid_mol`/`construct_mol` verbatim, no model). So the 0% is **not** an RDKit-version artifact. It is **unexplained**, pending a model rerun: the likeliest remaining cause is that Molek's raw decode produces over-valent graphs far more often than published MoFlow (which correction then masks). Note too that the 63.11% figure (GDSS 2022) may use a different validity definition than MoFlow's strict `valid_mol`. **Under investigation.**

## 2. Distributional metrics (30k generations vs ZINC250k test)

| Metric | Molek-30M | Direction | Note |
|---|---|---|---|
| FCD/Test | **23.40** | ↓ | fcd_torch (= MOSES FCD) |
| SNN/Test | 0.196 | ↑ | RDKit Morgan NN |
| IntDiv | 0.908 | ↑ | internal diversity |
| IntDiv2 | 0.900 | ↑ | |

## 3. ZINC250k leaderboard context (published baselines)

Validity here is **without correction** for every row, so the column is like-for-like.

| Model | Validity w/o correction (%)↑ | FCD↓ | Family |
|---|---|---|---|
| GraphAF+FC | 68.47 | 16.02 | autoregressive flow |
| GDSS | 97.01 | **14.66** | diffusion (best FCD) |
| GraphArm | 88.23 | 16.26 | autoregressive diffusion |
| **MoFlow (ref)** | 63.11 | 20.93 | normalizing flow |
| **Molek-30M (ours)** | **0.00** (our eval, under investigation) | 23.40 | normalizing flow (replica) |
| DiGress | 91.02 | 23.06 | discrete diffusion |

GraphAF+FC, GDSS and MoFlow rows: GDSS (Jo et al. 2022) Table 2. GraphArm and DiGress rows: as previously listed,
not re-checked in this edit. Molek's corrected validity (99.95%) is not comparable to this column.

**Reading:** on FCD, Molek (23.40) is ~12% higher, i.e. worse, than the reference MoFlow (20.93; lower is better).
That is inside the pre-declared ≤1.5× tolerance (H2, ratio 1.12), but it is not a match. On validity without
correction, Molek's 0% is far below MoFlow's published 63.11% (unexplained, under investigation). MoFlow-family is
mid-pack on FCD; diffusion leads.

## 4. Reproduce
```bash
# data (G1 + G7 row-count check)
python scripts/prepare_moflow_data.py
# eval (frozen reference harness; dual with/without correction)
python scripts/eval_moflow.py --config configs/molgen-zinc250k.yaml \
  --run_dir artifacts/molek-eval --snapshot model_snapshot_epoch_197 \
  --n_samples 10000 --temperature 0.85 --experiments 5
# distributional metrics
python scripts/eval_moses_metrics.py --model_dir <snapdir> \
  --snapshot model_snapshot_epoch_197 --n_gen 30000 --out molek-moses.json
```
Pins: `moflow@3611c6372602`, `moses@dd7ed6ab38e2`. Kaggle kernels: `moflow30m-zinc250k-r1`
(train), `molek-eval-r1` (D3), `molek-moses-r1` (FCD).

## 5. Verdict
MoFlow-class replica at 30M. It matches the reference on **corrected** validity/novelty/uniqueness (metrics
that saturate near 100% for this task, so they separate models poorly). FCD is within the pre-declared ≤1.5×
tolerance but ~12% worse than the reference (23.40 vs 20.93). Raw validity is 0% vs the reference's published
63.11%, unexplained. Faithfulness to the reference is therefore **not yet established**. Honest baseline;
**not** distributional SOTA. Agri-conditioning + wet-lab = future.
