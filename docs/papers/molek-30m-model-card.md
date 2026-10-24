# Model Card — Molek-30M

> Format per program blueprint (`PinoAI/docs/MODEL_CARD_TEMPLATE.md`), adapted for a
> molecular-graph generator.

## Model Information
- **Model Name:** Molek-30M
- **Version:** 0.1 (epoch 197/200 checkpoint)
- **Release Date:** 2026-10-24 (internal)
- **Architecture:** MoFlow invertible normalizing flow over molecular graphs
- **Parameter Count:** 29,049,444 (≤30M budget, hard-asserted)
- **Modality:** small-molecule graphs (SMILES in/out)
- **Tokenizer:** n/a (graph model; atom/bond tensors)
- **License:** MIT (reference code) — our checkpoint is ours (derivative permitted)

## Model Description
Molek-30M is PinoBio-GenD's from-scratch, compute-efficient replica of MoFlow, trained on
a single free GPU. It generates novel small-molecule graphs, made valid by valency correction (raw validity 0% in
our evaluation, under investigation), and is the base for an
agricultural property-conditioning head (crop-protection chemistry) in Project Katala.

## Parent Model (lineage)
- **Method:** MoFlow (Zang & Wang, *An Invertible Flow Model for Generating Molecular
  Graphs*, KDD 2020)
- **Reference code:** `calvin-zcx/moflow` @ `3611c6372602` (MIT)
- **Relationship:** replica with documented modifications (M-MOFLOW-1..13); faithfulness not yet established
  (see Evaluation); we own
  the trained weights, NOT the method.

## Training
- **From scratch:** yes (own checkpoint)
- **Data:** ZINC250k (249,455 mols; 224,568 train / 24,887 test)
- **Optimizer:** Adam lr 1e-3, AMP fp16, seed 20261023, 200-epoch target (ckpt @ 197)
- **Compute:** 1× Kaggle T4×2 session
- **Fine-tuning / conditioning:** farm-knob agri head (M-MOFLOW-3) — SPEC'd, NOT trained
- **Modifications:** M-MOFLOW-1 (30M scale), -2 (AMP), -4 (dual-report), -5/6/9/10/13
  (py3.13 + eval compat); see `patches/`

## Evaluation (measured)
- Corrected validity **99.95%** / novelty **100%** / uniqueness **99.99%**: matches ref MoFlow on these
  corrected metrics (they saturate near 100%, so they separate models poorly)
- Uncorrected validity **0%**; published MoFlow without correction is 63.11% (GDSS 2022, Table 2), so this is
  unexplained and under investigation, not "by design"
- FCD **23.40**, lower is better (ref 20.93, ~12% worse; GDSS 15.74 in our same harness), SNN 0.196, IntDiv 0.908
- Full report: `docs/papers/molek-30m-benchmark.md`

## Intended Uses
- Generate novel candidate small molecules for **agricultural** research (crop protection).
- Base for property-conditioned generation (farm-knob) + optimize-toward-target workflows.
- `/v1` `generate-molecule` tool in the SciACA workbench.

## Out-of-Scope Uses
- Human therapeutics / drug claims.
- Any efficacy or safety assertion (none made; wet-lab out of scope until benchmarked).
- Distributional-SOTA claims (MoFlow-family is mid-pack on FCD).

## Limitations
- Mid-pack distributional fidelity (FCD); diffusion architectures lead.
- Relies on valency correction (raw validity 0% in our evaluation vs 63.11% published for MoFlow; under
  investigation).
- No agri-conditioning or wet-lab validation yet.

## Reproducibility
Seed 20261023; pins `moflow@3611c6372602`/`moses@dd7ed6ab38e2`; checkpoint sha256
`7f8374df3cb8…`; frozen reference eval harness. Serving: `serving/runtimes/molek_runtime.py`.
