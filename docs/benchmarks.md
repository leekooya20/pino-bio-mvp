# Benchmarks & research-paper register (PinoBio MVP-4)

Purpose (G7/G11/G8): every reported number below is **verbatim from a verified source** —
pinned reference README lines, verified paper links, or APIs checked on the date noted.
Our own evals (eval_moflow.py etc.) are reported separately, always **with AND without
validity correction** (M-MOFLOW-4), and never mixed with reference numbers.

Op: 2026-10-23 · author: GLM (pino-bio-mvp) · review basis: pinned third_party trees +
official model pages + GitHub API license reads.

---

## 1. Research papers (G11 register)

| Model | Paper | Status in our stack |
|---|---|---|
| MoFlow | Zang, C. & Wang, F. *MoFlow: An Invertible Flow Model for Generating Molecular Graphs.* **KDD 2020** — arXiv:2006.10137 (DOI 10.1145/3394486.3403104); code `calvin-zcx/moflow` (MIT, pinned `3611c6372602`) | **from-scratch replica @ 30M** (M-MOFLOW-1..8) |
| ProtGPT2 | Ferruz, N., Schmidt, S. & Höcker, B. *ProtGPT2: a deep unsupervised language model for protein design.* **Nature Communications 13, 4348 (2022)** — DOI 10.1038/s41467-022-32007-7 — recipe basis: `nferruz/ProtGPT2` HF card (Apache-2.0; 128×A100, 50 ep, block 512, batch 65536 tokens, LR 1e-3) | **from-scratch replica ≤100M** (P-PTGPT2-1..5), arm to be config-registered next |
| RFD4-Proteina | Corley, N. & Didi, K. et al. *Biomolecular design through latent reasoning with RFD4-Proteina.* 2026 preprint (UW IPD × NVIDIA) — paper: `https://rfd4-proteina.org/assets/paper/RFD4-Proteina.pdf` — code `RosettaCommons/RFD4-Proteina` (**BSD-3-Clause, verified via GitHub API 2026-10-23**, repo pushed 2026-10-22) — weights `nvidia/RFD4-Proteina` (+ Diffusers variant) | **serve as tool only** (`design.backbone`, `mol.generate` aux) — never trained by us |
| ESM-2 | Lin, Z. et al. *Evolutionary-scale prediction of atomic-level protein structure with a language model.* **Science 379, 1123–1130 (2023)** — DOI 10.1126/science.ade2537 (MIT checkpoint `esm2_t6_8M_UR50D` .. `esm2_t33_650M_UR50D`) | serve as scorer (`seq.score`), embedding novelty gate; LoRA-finetune later on our side is allowed (own weights per card terms) |
| MOSES | Tripp, A. et al. *A Fresh Look at De Novo Molecular Generation Benchmarks.* Wang Workshop on ML for Molecules (NeurIPS 2020); code `molecularsets/moses` (MIT, pinned `dd7ed6ab38e2`) | metric definitions we inherit (validity/novelty/uniqueness) via MoFlow's generate.py |

BibTeX for RFD4-Proteina (verbatim from their citation block):

```bibtex
@article{corley2026rfd4proteina,
  title        = {Biomolecular design through latent reasoning with {RFD4-Proteina}},
  author       = {Corley, Nathaniel and Didi, Kieran and Kazman, Maxwell W. and Brent, Rafael I. and others},
  year         = {2026},
  note         = {Preprint},
  url          = {https://rfd4-proteina.org/assets/paper/RFD4-Proteina.pdf}
}
```

---

## 2. RFD4-Proteina — what the site says (read 2026-10-23)

- **Task model**: unified 32-dim **chemical + conformational latent space** covering standard
  and modified amino acids, sugars, DNA, RNA; supervised with **force-field energies**;
  **intrinsic reasoning** = recurrent refinement ("thinking" budgets); **extrinsic reasoning**
  = reward-guided search steered by arbitrary scores.
- **In-silico benchmark protocol (theirs, cited not claimed)**: a design *passes* only if
  **AlphaFold3 re-fold** + task criteria pass; **clustered pass rate** = distinct passing folds
  ÷ **200 attempts** (unclustered = passing designs ÷ 200); failures count, no replacement
  attempts. Full data: `https://rfd4-proteina.org/benchmarks/data.json`.
- **Their headline numbers (high-thinking, single-shot):** protein binding **10.6%** clustered
  pass vs BindCraft **5.9%** at ~42× throughput; small-molecule **14.3%** vs 2.4% (next-best
  RFD3, 6.1×); enzyme scaffolding **12.1%** vs 5.7%; DNA binding **3.5%** vs 0.8% (BoltzGen)
  / 0.5% (fixed-DNA RFD3). Target coverage: 22/24 protein, 77/77 small-molecule, 35/37
  enzyme, 3/3 DNA.
- **Wet-lab highlights (context, not our claims)**: CaM binders 12/18 <1 µM (Ca²⁺-dependent);
  pMHC binders w/ >100× on-target specificity; IDP binders 112 pM (YAP1) / 527 pM (Tau);
  TrkA 158/188 sub-µM unconstrained; glycan shielding 8/9 >90% oligomannose;
  phosphotriesterase best k_cat/K_M 3600 ± 500 M⁻¹s⁻¹; first de novo ligase step for
  lenacapavir (79% (S)-amine conversion).
- **Runtime constraint for serving**: quickstart expects a **fresh Python 3.12 env** with
  CUDA 12/13 (`pip install "rfd4-proteina[all-cuda13]"`). Kaggle's current runtime is
  **Python 3.13** — so serving goes through a dedicated pinned env/container (per
  `docs/06-serving-release.md`), NOT the Kaggle 3.13 training runtime. This is a serving-plan
  constraint, not a block.

**Our benchmarking posture for RFD4-Proteina (serve-only):**
1. We never claim their benchmark numbers as ours; when we cite the model, we cite their
   preprint + benchmark data URL with date accessed.
2. Our acceptance test is integration-level: pinned container → 1 condition spec → valid
   annotated CIF/backbone output → ESM-2 embed scoring path returns; latency recorded.
3. If WE ever evaluate design-suite outputs ourselves, we adopt their protocol concepts
   (structure-predictor refold check + clustered counting + fixed attempts budget) but report
   our own numbers honestly under our own header.

---

## 3. MoFlow — reference numbers we measure against (pinned `3611c6372602` README §3)

Reference model = the README's own released config ( considerably >30M; ours is the M-MOFLOW-1
scale-down). Reference reproduction of our full pipeline target (G7, exact, never rounded):

**Reconstruction (zinc250k train set)** — README §3.1: `reconstruction_rate for all the train
data: 1.0` → **invariant: 100% reconstruction, hard-fail otherwise.**

**Random generation, zinc250k, 10,000 samples × 5 experiments, T=0.85
(batch 10000, `--correct_validity true`)** — pinned README lines 131–135:

```
validity:    mean=100.00%  sd=0.00%
novelty:     mean=100.00%  sd=0.00%
uniqueness:  mean=99.99%   sd=0.01%
abs_novelty: mean=99.99%   sd=0.01%
```

QM9 reference (same protocol, lines 109–113): validity 100.00 / novelty 98.05 /
uniqueness 99.26 / abs_novelty 97.32.

**Our 30M recipe targets (M-MOFLOW-1..8)**: same eval protocol via
`scripts/eval_moflow.py` (untouched reference generate.py; runs TWICE per snapshot:
`--correct_validity true` **and** `false`), 10×10k×T0.85×5 experiments, cluster the honest
uncorrected numbers next to the corrected ones, and report BOTH labeled as ours-at-30M with
our config hash (G10). We do NOT present 30M numbers as MoFlow-official numbers.

---

## 4. ProtGPT2 — reference facts + our bench plan (P-PTGPT2-1..5)

Reference training (HF card, Apache-2.0): 738M, 36-layer GPT-2 arch, 50 epochs over UniRef50
(≈42M sequences), block 512, final ppl not asserted on the card — **we do not quote a
reference ppl number until read from their paper directly (pending, marked OPEN).**

Selection rule (from card): generate 150 candidates per prompt, order by ppl, keep top-1
predicted pLDDT > 90 for AlphaFold eval.

**Our ≤100M bench plan** (executed through `configs/seqgen-ur50.yaml`, P-PTGPT2-1..4):
1. Tokenizer parity: our BPE vs their custom add-BPE — loss/interpolated-ppl on a held-out
   UR50 slice (same seed/train steps as reference, scaled budget).
2. Selection gate parity: their ppl+top-pLDDT rule **plus ours** (P-PTGPT2-3): ESM-2
   embedding-similarity novelty + BLAST-vs-UniRef check.
3. Crop arm (P-PTGPT2-5): rice-first fine-tune/curriculum vs base — compared on our own
   crop novelty report (homolog holdout discipline adopted from the PinoAI ESM-2-arm benchmark
   design: clustered/novelty-aware, fixed attempts, honest asymmetric-baseline disclosure).
4. OPEN items: reference ppl/on-set numbers from the paper (to be transcribed from the PDF
   at Phase-2 start); exact UR50 corpus dates pinned at download (G1 manifest).

---

## 5. When does benchmarking run? (the "after this" question)

| Stage | Benchmark |
|---|---|
| MoFlow 30M train run (running now on Kaggle, r1) | reconstruction on train split (100% invariant) → random-gen eval via `scripts/eval_moflow.py` (with/without correction) → `eval_summary.json` |
| ProtGPT2-small (next phase after UR50 manifest) | ppl on held-out slice → selection-gate outputs → novelty gates |
| RFD4-Proteina serving (Phase-3 tools) | integration acceptance (1 design call, ESM-2 score pass-through, latency); their benchmarks cited, never blended with ours |
| Design loop (SciACA `/v1`) | end-to-end job: generate → ESM-2 score → record honest pass/fail counts under our header |

Rule for all four rows (G7): **any number in a model card, paper, or report produced by us
carries (a) its seed, (b) its config hash (G10), (c) with/without-correction labels for
MoFlow, (d) dataset/eval provenance from `data/manifests/`.**

---

## 6. PLANNED (later): PPI binder benchmark against their protocol — Stan's pick

Source view (verbatim, Stan 2026-10-23): `https://rfd4-proteina.org/leaderboard.html?dataset=ppi&criterion=ppi&condition=paper&metric=clustered&targetMetric=clustered&af3=true&log=true&sort=rate&target=`

Underlying data is fully reproducible (`https://rfd4-proteina.org/benchmarks/data.json`,
checked 2026-10-23): snapshot `2026-10-21`, source repo `kierandidi/RFD4-Proteina-paper` @
revision `18b7fc2cdbb14e71…`, **3,073 rows / 19 models**, row schema
`run_id, model, protocol, dataset, target, attempts, scored, passes, clusters,
generation_gpu_s, af3_gpu_s, timing_basis, source_sha256…` — i.e. per-target attempts /
passes / clusters / GPU-time incl. AF3, sha256-pinned.

Plan (runs AFTER serving layer ships; dependencies noted):
1. **Targets**: take the `dataset=ppi` rows as our task list (fixed target set — no
   cherry-picking; record the row hashes).
2. **Budget**: match their `attempts` convention (200/target counted, failures count).
3. **Refold validator**: theirs is AlphaFold3. Our substitute (ESMFold → Chai, local,
   honest-labeled) is NOT AF3 — reported separately as ours; if AF3 access ever appears,
   rerun before any public claim.
4. **Metric**: clustered pass rate (distinct passing folds / attempts), same counting
   semantics; report ALSO raw pass rate.
5. **Comparison**: their `rfd4_proteina_*` / `bindcraft*` / `rfdiffusion*` rows are
   REFERENCE COLUMNS; our loop's own cached numbers go under our header with config hash
   (G10) — never blended.
6. **Front-end**: the plan's real point — our design loop (RFD4-Proteina as
   `design.backbone` tool + ESM-2 scoring) has to clear a PPI sub-set BEFORE we claim
   any binder-design capability to users/partners.

OPEN: whether we run this on Kaggle GPU quota vs local GPU — decided at serving time.

---

## 7. PLANNED (later): "Unified Latent Reasoning" trajectory workbench — Stan's pick

Reference (site §Unified Latent Reasoning, screenshot 2026-10-23): an enzyme-design
trajectory — latent point cloud → global topology → sequence + structure (× leurs adaptive
depth) → fine-scale contacts → AF3 refold — with **adaptive reasoning depth** per stage
(×2 / ×5 / ×2) and **time-dependent search criteria** checkboxes (large interface area ×2,
many interface H-bonds ×5, high AF3 interface confidence ×2).

Scope split (honest, G7):

| Piece | Who does it |
|---|---|
| Adaptive thinking budgets (low/med/high), multi-recourse refinement | **theirs** — it's native RFD4-Proteina behavior; we expose it as a `reasoning_depth` job parameter through our `/v1` tool wrapper |
| Reward-guided search with arbitrary criteria | **theirs** (code ships search; BSD-3) — our wrapper maps time-dependent criteria (interface area, H-bond count, confidence) onto their search interface |
| AF3 refold gate | **theirs only for their published numbers**; our loop gates with ESMFold/Chai (honest "not-AF3" label) until AF3 access exists |
| Trajectory visualization (stage panels, latent snapshots, per-stage metrics) | **ours** — a SciACA-designable workbench page fed by our `/v1` job artifacts |
| Multi-molecule demos (peptide–DNA linkage, glycan/phospho stories) | **theirs** via model capability — we reproduce as demo recipes, never claiming their wet-lab results |

Order of work: (1) serving layer ships `reasoning_depth` + `search_criteria` passthrough,
(2) job artifacts record per-stage snapshots (for the workbench UI), (3) the PPI benchmark
(§6) validates capability claims BEFORE any public-facing demo language.

---

## 8. PLANNED (later): AF3-grade refold validation stack — Stan's pick

Source (verbatim link, Stan 2026-10-23): Abramson, J. et al. *Accurate structure prediction
of biomolecular interactions with AlphaFold 3.* **Nature 630, 493–500 (2024)** —
DOI 10.1038/s41586-024-07487-w (Fig. 1).

What we adopt from their Fig-1 methodology for OUR eval claims (upgrade of §6 step 3):
- **Metrics**: pocket-aligned ligand RMSD < 2 Å (ligands/covalent mods); interface LDDT
  (protein–nucleic-acid); LDDT (monomers); **DockQ > 0.23** (protein–protein & antibody
  interfaces) — the same thresholds their panels use.
- **Sampling protocol**: rank by **top-confidence sample out of N model seeds × diffusion
  samples** (theirs: 5 seeds × 5 diffusion samples; 1,000 seeds for antibody pose ranking) —
  multi-seed confidence-ranked selection becomes our default for any structure-level claim.
- **Statistics**: exact binomial 95% CIs / 10,000-sample bootstrap + two-sided Wilcoxon
  signed-rank comparisons (their choices) — adopted for our A/B arms.

Validator ladder (license-honest):

| Run | Validator | License / access note |
|---|---|---|
| Now | ESMFold (MIT) + local AF-class open models | servable; labeled "not-AF3" |
| Next | **Boltz-2** (already in our Katala tool list, MIT) | AF3-class; our primary refold validator |
| Cross-check | Chai (Apache-2.0 per Katala catalog) | second opinion, seed-matched |
| Gold | AlphaFold 3 itself | **not freely servable by us** (Google terms — verify terms at the time; server access is the practical path). Their numbers stay THEIRS; ours cite the ladder above |

If/when real AF3 access exists, we re-run the §6 PPI benchmark under the exact Fig-1
protocol and relabel claims accordingly. Until then: everything stays honest-labeled as
"AF-class open validator".



