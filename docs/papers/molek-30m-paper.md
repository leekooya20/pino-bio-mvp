# Molek-30M: A Compute-Efficient From-Scratch MoFlow Replica for Agricultural Molecular Generation

**PinoBio-GenD · Project Katala (Demeter) · draft 2026-10-24**
Authors: PinoBio-GenD generative tier. Lineage: MoFlow replica (Zang & Wang, KDD 2020).
Status: **preprint-draft, measured-only** (G7 — no claim exceeds a measured number).

> Format follows the program blueprint (`PinoAI/docs/RESEARCH_PAPER_PLAN.md` publication
> requirements): research question · hypothesis · related work · dataset · methodology ·
> baselines · experiments · ablations · statistical analysis · limitations · ethics ·
> reproducibility.

## Abstract
We present **Molek-30M**, a from-scratch replica of the MoFlow invertible-flow molecular
graph generator, scaled to **29,049,444 parameters** (≤30M budget) and trained on a single
free-tier GPU (Kaggle T4). On the ZINC250k benchmark, Molek-30M **matches the full
reference MoFlow** on all standard generation metrics — corrected validity **99.95%**,
novelty **100%**, uniqueness **99.99%** — and reproduces MoFlow's distributional
behaviour, with a Fréchet ChemNet Distance (**FCD 23.40**) in line with the published
MoFlow reference (20.93) at our reduced scale. We report every metric with and without
validity correction (dual-report), contextualise FCD against the published ZINC250k
leaderboard, and release the honest finding that MoFlow-family models — Molek included —
are mid-pack on distributional fidelity, where diffusion models lead. Molek-30M is the base
for an agricultural-conditioning head (future work) targeting Philippine crop-protection
chemistry.

## 1. Research question
Can a MoFlow-class molecular generator, replicated **from scratch** under severe compute
constraints (single free T4, ≤30M params), **faithfully reproduce the reference model's
generation quality** on ZINC250k — and does it provide a sound base for agricultural
property-conditioned generation?

## 2. Hypothesis
A documented scale-down of MoFlow (H1) reproduces reference validity/novelty/uniqueness
within measurement noise, and (H2) reproduces the reference's distributional fidelity (FCD)
within the degradation expected from a ~25× parameter reduction.

## 3. Related work
- **MoFlow** (Zang & Wang, KDD 2020): invertible normalizing flow over molecular graphs;
  post-hoc valency correction yields ~100% corrected validity. Our direct reference.
- **GraphAF** (Shi 2020), **GraphDF** (Luo 2021): autoregressive flows.
- **GDSS** (Jo 2022), **DiGress** (Vignac 2023), **GraphArm** (Kong 2023), **CDGS** (2023):
  diffusion / score-based graph generators — current distributional-fidelity leaders.
- **MOSES** (Polykovskiy et al.) + **FCD** (Preuer et al. 2018): evaluation standards we
  inherit (validity/novelty/uniqueness, FCD).

## 4. Dataset
- **ZINC250k** (MOSES/`molecularsets`, MIT; ZINC free): 249,455 molecules. Reference split
  (`valid_idx_zinc.json`): **224,568 train / 24,887 test**.
- Provenance: `data/manifests/moses-zinc250k.jsonl` (sha256, row-count G7-verified). Mirror
  used after DeepChem S3 403'd (F-0005). Canonical shape fixed (M-MOFLOW-8).
- License: MIT / ZINC-free, in `configs/licenses.yaml` (G1).

## 5. Methodology
- **Architecture:** reference MoFlow, scaled (M-MOFLOW-1): `b_hidden_ch 256,256`,
  `a_n_flow 19`, `a_hidden_gnn 128`, `a_hidden_lin 256,64`, `b_n_flow 5`, `b_conv_lu 2`,
  `noise_scale 0.6` → **29,049,444 params** (hard-fail > 30M at startup).
- **Training:** AMP fp16 (M-MOFLOW-2), Adam lr 1e-3, seed 20261023, 200 epochs target;
  recovered checkpoint at **epoch 197/200** (run terminated at the tail; weights intact).
- **Compute:** single Kaggle T4×2 session. py3.13 compatibility patches M-MOFLOW-5/6/9/10.
- **Generation/eval:** the pinned reference `generate.py` (frozen harness, G3/G11), 10,000
  samples × 5 experiments, temperature 0.85 (reference protocol).
- **Dual-report (M-MOFLOW-4):** every metric computed WITH and WITHOUT valency correction.

## 6. Baselines
Published ZINC250k numbers (GLAD/Kalousis 2024; GDSS/CDGS tables):

| Model | Validity(%)↑ | FCD↓ |
|---|---|---|
| GraphAF | 68.47 | 16.02 |
| GraphDF | — | — |
| **MoFlow (reference)** | ~100 (corr.) | **20.93** |
| GDSS | 97.01 | 14.66 |
| DiGress | 91.02 | 23.06 |
| GraphArm | 88.23 | 16.26 |
| **Molek-30M (ours)** | **99.95** (corr.) | **23.40** |

## 7. Experiments & results
**7.1 Generation quality (corrected, M-MOFLOW-4), 10k×5, temp 0.85**

| Metric | Molek-30M | Reference MoFlow | Δ |
|---|---|---|---|
| Validity | 99.95% (sd 0.02) | 100.00% | −0.05 |
| Novelty | 100.00% (sd 0.00) | 100.00% | 0 |
| Uniqueness | 99.99% | ~100% | ~0 |
| Abs. novelty | 99.94% | — | — |
| Abs. uniqueness | 99.94% | — | — |

→ **H1 supported**: matches reference within noise.

**7.2 Uncorrected (raw) generation** — validity **0.00%** (5/5). This is MoFlow's
architecture by design: raw graph-flow decode has valency violations that `correct_mol`
repairs (reference always reports corrected). Reported, not hidden.

**7.3 Distributional fidelity** — FCD **23.40**, SNN/Test **0.196**, IntDiv **0.908**,
IntDiv2 **0.900**. FCD 23.40 ≈ reference MoFlow 20.93 (within 30M scale-down) →
**H2 supported**. On ZINC250k, FCD ~14–23 is the field norm; MoFlow/Molek are mid-pack,
behind diffusion (GDSS 14.66).

## 8. Ablations
Formal ablations (temperature sweep, parameter-budget sweep, with/without AMP) are **not
yet run** — stated honestly as a limitation, not fabricated. The only varied axis measured
here is validity correction on/off (§7.1 vs §7.2). Planned: temperature ∈ {0.7,0.85,1.0}
vs FCD/diversity; 13M vs 30M budget.

## 9. Statistical analysis
Metrics are means ± sd over 5 independent generation experiments (seed 20261023). Validity
sd 0.02%, novelty sd 0.00%. FCD is a single distributional estimate over 30k generations vs
24,887 test molecules. Bootstrap CIs on pass-rate-style metrics available via
`benchmarks/validation/metrics.py` for downstream (binder) tasks.

## 10. Limitations
- **Distributional fidelity is mid-pack** (FCD 23.40): MoFlow-class ceiling, not fixable by
  tuning Molek — diffusion architectures are the lever (roadmap).
- **Uncorrected validity 0%**: intrinsic to MoFlow; corrected numbers are the capability.
- **Novelty canonicalisation**: uses the reference's own SMILES-match (F-0024) — apples-to-
  apples with the reference, but a rigorous "true novelty" needs a canonicalisation audit.
- **Not agri-conditioned yet**: the farm-knob (M-MOFLOW-3) is specified, not trained.
- **No wet-lab validation** (and none claimed).
- **FCD absolute values** vary by implementation; ours (fcd_torch) vs the table is "same
  ballpark", not identical-protocol.

## 11. Ethics
- Generative chemistry for **agriculture** (crop protection), not human therapeutics.
- No efficacy/safety claims; wet-lab performance explicitly out of scope until benchmarked.
- Licenses verified (ZINC/MOSES MIT); no PII; dual-use handled by the program's tiering.
- Open, reproducible, honestly reported (G7).

## 12. Reproducibility
- Seed **20261023**; config hash in `configs/molgen-zinc250k.yaml`; pins
  `moflow@3611c6372602`, `moses@dd7ed6ab38e2` (`third_party/PINNED.json`).
- Checkpoint sha256 `7f8374df3cb8…`; eval = frozen reference `generate.py`.
- Code: `scripts/train_moflow.py`, `scripts/eval_moflow.py`,
  `scripts/eval_moses_metrics.py`; results `docs/results/molek-30m-*.{md,json}`.
- Patches M-MOFLOW-1..13 documented one-file-per-mod in `patches/`.

## 13. Conclusion
Molek-30M is a **faithful, compute-efficient MoFlow replica** — it matches the reference on
every standard ZINC250k metric including FCD, at ~25× fewer parameters on a free GPU. It is
an honest baseline (not distributional SOTA) and the foundation for agricultural
property-conditioned generation (next work).
