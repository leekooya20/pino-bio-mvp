# Reading register — documentation & papers per model (PinoBio MVP-4)

Practice (G11, standing task): every model we *replicate* or *serve* gets its docs +
papers read BEFORE we depend on its behavior. Statuses updated in place with dates.
Nothing here is read just to cite it — each row lists WHAT we still need to extract.

Op: 2026-10-23 · maintainer: GLM · companion to `docs/benchmarks.md` (numbers there are
verbatim-sourced; this file tracks the *reading*, not the numbers).

---

## Our replica models (from-scratch)

### MoFlow — arXiv:2006.10137 (KDD 2020, Zang & Wang) — RECIPE-READ ✅
- Paper: title/authors/DOI verified live on arXiv (2026-10-23); abstract covers the 4
  task families + "100% reconstruction of training data" invariant.
- Code README (pinned `3611c6372602`): exact zinc250k hyperparams (README table),
  reconstruction log (§3.1: `reconstruction_rate ... 1.0`), random-gen numbers (§3.2).
- **Status: sufficient for training replication.** Paper PDF deep-pass (Table 2 exact
  benchmark values per dataset) = optional later pass; our eval uses the README numbers,
  which are the operational ground truth for `generate.py`.

### ProtGPT2 — Ferruz et al., Nat Commun 13, 4348 (2022) — CARD-READ ✅ / PAPER ❌ OPEN
- HF card (Apache-2.0) read: 738M / 36L, UniRef50 (≈42M seqs), 50 epochs, block 512,
  batch 1024 / 65536 tokens, LR 1e-3, custom BPE, ppl→top-1 pLDDT>90 selection rule.
- **OPEN items for Phase-2 (paper must answer before `configs/seqgen-ur50.yaml` locks):**
  1. Reference training ppl curve (order of magnitude for our ≤100M comparisons).
  2. Whether lr 1e-3 was cosine/plateau/cyclic (card silent; paper Methods has it).
  3. Exact corpus versioning they trained on (UR50 2021-04 per our Katala docs 08)
     + any dedup details affecting our subsample stratification (P-PTGPT2-2).

### RFD4-Proteina — 2026 preprint (UW IPD × NVIDIA) — SITE-READ ✅ / DEEP-DOCS ❌ pending serving
- Site read (home, resources, leaderboard) 2026-10-23; benchmark protocol + data.json
  structure decoded (3,073 rows, revision-pinned, sha256'd).
- License: BSD-3-Clause, verified via GitHub API 2026-10-23. Weights: `nvidia/RFD4-Proteina`.
- **Pending (Phase-3 serving)**: read their docs site (`/latest/`: quickstart, installation,
  search guide, metrics, API reference) closely enough to write our `/v1` wrapper:
  condition-spec → annotated CIF, `reasoning_depth` + `search_criteria` passthrough,
  output artifact handling. Preprint PDF read is cite-only (we claim nothing of theirs).

## Our served models

### ESM-2 (facebookresearch) — Lin et al., Science 379 (2023) — REGISTERED ❌ deep-read pending
- License/citation verified earlier (MIT; `esm2_t6_8M_UR50D` … `esm2_t33_650M_UR50D`).
- **Pending (Phase-2/3 novelty gates + scoring)**: which checkpoint(s) we pin for
  embeddings (8M/650M trade-off on Kaggle CPU/T4), embedding-pooling choice for the
  novelty gate (P-PTGPT2-3), and the LoRA-finetune recipe path our own weights may use.
  Science paper read = one working session when the scorer lands.

### (Deferred models — AMPLIFY, GPN, PlantCaduceus, Geneformer, CodonFM, Evo 2)
Reading is gated by actual use. Evo 2 = tool-only per earlier decision; others wait for
the PinoAI-side A/B results before we commit any read budget.

---

## Rule these files enforce

1. No config locks (`configs/*.yaml`) or `/v1` wrappers written against a model whose
   Methods section hasn't been read yet (G11: no blind replication).
2. Every OPEN item here gets a closed line + date before the phase that needs it starts.
3. If a paper contradicts a card (like ProtGPT2's lr schedule could), the paper wins and
   the recipes doc gets corrected — with a note in our mods ledger.
