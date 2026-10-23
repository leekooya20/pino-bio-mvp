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

### ProtGPT2 — Ferruz et al., Nat Commun 13, 4348 (2022) — CARD-READ ✅ / PAPER-METHODS-READ ✅ (2026-10-23)
- HF card (Apache-2.0) read: 738M / 36L, UniRef50 (≈42M seqs), 50 epochs, block 512,
  batch 1024 / 65536 tokens, LR 1e-3, custom BPE, ppl→top-1 pLDDT>90 selection rule.
- **Paper Methods read 2026-10-23 (nature.com/articles/s41467-022-32007-7), OPEN items closed:**
  1. **ppl curve → CLOSED (with a finding):** the paper publishes **NO numeric training
     perplexity** (loss is standard CLM cross-entropy, Eq. 2; no ppl value/curve in text
     or that we could grep). ⇒ we CANNOT benchmark our ≤100M ppl against theirs; our ppl
     is reported stand-alone vs our own held-out eval only (G7). See F-0008.
  2. **lr schedule → CLOSED:** **Adam β1=0.9 β2=0.999, LR 1e-3, CONSTANT** — the paper
     names no warmup/cosine/plateau/cyclic schedule. The card's bare "1e-3" = flat.
     See F-0009. (Decision for P-PTGPT2: constant-lr faithful baseline; a short warmup is
     an *allowed documented deviation* if small-scale training is unstable — ledgered.)
  3. **corpus + dedup → CLOSED:** UniRef50 **version 2021_04**, **49,874,565 seqs** total;
     **10% random holdout** → **44.88M train / 4.99M eval**. Dedup = UniRef50's own 50%-
     identity clustering (no extra dedup step). Block size **512** (main model; a 1024
     variant was also built). BPE tokenizer. Trained 128×A100, 4 days, batch 8/device
     (1024 total), 65,536 tokens/batch, DeepSpeed.
- **Status: sufficient to LOCK `configs/seqgen-ur50.yaml`** (done 2026-10-23, P-PTGPT2-1..5).

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
