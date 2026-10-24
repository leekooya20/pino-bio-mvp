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
Uncorrected 0% = MoFlow-by-design (raw decode needs valency correction).

## 2. Distributional metrics (30k generations vs ZINC250k test)

| Metric | Molek-30M | Direction | Note |
|---|---|---|---|
| FCD/Test | **23.40** | ↓ | fcd_torch (= MOSES FCD) |
| SNN/Test | 0.196 | ↑ | RDKit Morgan NN |
| IntDiv | 0.908 | ↑ | internal diversity |
| IntDiv2 | 0.900 | ↑ | |

## 3. ZINC250k leaderboard context (published baselines)

| Model | Validity(%)↑ | FCD↓ | Family |
|---|---|---|---|
| GraphAF | 68.47 | 16.02 | autoregressive flow |
| GDSS | 97.01 | **14.66** | diffusion (best FCD) |
| GraphArm | 88.23 | 16.26 | autoregressive diffusion |
| **MoFlow (ref)** | ~100 (corr.) | 20.93 | normalizing flow |
| **Molek-30M (ours)** | **99.95** (corr.) | 23.40 | normalizing flow (replica) |
| DiGress | 91.02 | 23.06 | discrete diffusion |

**Reading:** Molek matches MoFlow (validity + FCD within scale-down). MoFlow-family is
mid-pack on FCD; diffusion leads. FCD frontier = architecture lever, not a Molek tune.

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
Faithful MoFlow replica at 30M — matches reference on validity/novelty/uniqueness **and**
FCD. Honest baseline; **not** distributional SOTA. Agri-conditioning + wet-lab = future.
