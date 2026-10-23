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

### RFD4-Proteina — 2026 preprint (UW IPD × NVIDIA) — SITE-READ ✅ / DEEP-DOCS READ ✅ (2026-10-23)
- Site read (home, resources, leaderboard) 2026-10-23; benchmark protocol + data.json
  structure decoded (3,073 rows, revision-pinned, sha256'd).
- License: BSD-3-Clause, verified via GitHub API 2026-10-23. Weights: `nvidia/RFD4-Proteina`.
- **Deep docs READ 2026-10-23** (rfd4-proteina.org/latest, RosettaCommons/RFD4-Proteina
  README, NVIDIA NIM overview). Facts that shaped `serving/runtimes/proteina_runtime.py`:
  - **Serving path = NVIDIA NIM synchronous HTTP endpoint** → we never run RFD4 in-process
    (it needs Linux x86_64 + py3.12 + CUDA GPU); this cleanly resolves the py3.12-vs-3.13
    conflict. See F-0010.
  - Two input dialects: annotated mmCIF (self-contained) OR condition spec (YAML/JSON +
    attached structures as NAMED FILES in the body, never filesystem paths).
  - Tasks = sampler trajectory, not the design problem: `generation`, `motif_scaffolding`,
    `partial_diffusion`, `inverse_folding`. A binder = `generation` with target atoms held
    (coord/seq conditioning) + epitope hotspots.
  - **`thinking_low`/`thinking_high`** = compute budget → our §7 `reasoning_depth` maps onto
    it; reward-guided beam search config → our §7 `search_criteria` maps onto it.
  - Params 4.34e8 (trunk 1.78e8 + AE 2.56e8), latent flow-matching, self-cond off, no MSA,
    design length ≤1024 tokens. NVIDIA verification = 87 annotated-mmCIF inputs / 12
    conditioning families.
- **Status: sufficient — wrapper written** (`serving/runtimes/proteina_runtime.py`). Live
  use gated on a reachable `PROTEINA_ENDPOINT` (NIM/container).

## Our served models

### Pinal — Dai et al., Nature 2026 (s41586-026-11205-z) — REPO+CARD READ ✅ (2026-10-23, scope addition)
- **Scope addition authorized by Stan 2026-10-23** (text→protein design fits our tier).
- Repo read (westlake-repl/Denovo-Pinal, Apache-2.0) + HF card + Nature/bioRxiv abstract:
  two-stage — **T2struct** (natural language → 3Di structure tokens) then **SaProt-T**
  (structure+text → sequence). 16B total; checkpoints SaProt-T 760M / T2struc-1.2B /
  T2struc-15.5B. 1.2B+760M run on 1 GPU (~1 min/10 designs, A40); 15B needs ≥40GB.
  Built on SaProt (MIT) + ProTrek (MIT). Synthetic data: 1.7B protein-text pairs via
  ProTrek retrieval + LLM annotation.
- **SERVE-first (G9):** 16B is not from-scratch on our compute; wrapper
  `serving/runtimes/pinal_runtime.py` written (honest pending until `PINAL_ENDPOINT`).
- **Pending (optional deep pass):** Nature full Methods (T2struct scaling curve, the
  SaProt-T text-projection matrix detail) when/if we self-host — cite-only; their
  wet-lab GFP/enzyme results are theirs (G7), never claimed as ours.

### NLP intent heads (OWNED, A8) — MiniLM (Apache-2.0) / ProTrek (MIT) + Pinal projection recipe — READ ✅ (2026-10-23)
- Base encoders read: all-MiniLM-L6-v2 card (Apache-2.0, 384-d, frozen) + ProTrek
  (MIT, protein-text aligned, Nat Biotech 2025). Projection recipe read from Pinal
  (trainable W: text embedding → PLM space, p(s|c,t)) + SaProt-T — G11 satisfied.
- Owned part = the projection heads only (intent-mol N-NLP-1, intent-seq N-NLP-2);
  spec `docs/nlp-intent-spec.md`, config `configs/nlp-intent.yaml`.
- **Status: sufficient to build intent-mol** once ChEBI text↔descriptor pairs are
  fetched (free with the farm-knob). intent-seq follows Seqgen.

### ESM-2 (facebookresearch) — Lin et al., Science 379 (2023) — REGISTERED ❌ deep-read pending
- License/citation verified earlier (MIT; `esm2_t6_8M_UR50D` … `esm2_t33_650M_UR50D`).
- **Pending (Phase-2/3 novelty gates + scoring)**: which checkpoint(s) we pin for
  embeddings (8M/650M trade-off on Kaggle CPU/T4), embedding-pooling choice for the
  novelty gate (P-PTGPT2-3), and the LoRA-finetune recipe path our own weights may use.
  Science paper read = one working session when the scorer lands.

### Generative OUT-list models (FLORA excludes → ours, Stan 2026-10-24)
- **Evo 2** (DNA/genome generation, Apache-2.0/NVIDIA-Open, served) — license verified live;
  deep docs read gated on actual serving (new DNA-generation modality).
- **Proteina-Complexa · La-Proteina** (protein design) — registered; **read + license verify
  BEFORE any dependence** (G11). serve/replicate decision deferred.
- **Eden** (DNA gen) — identity + license to confirm before any read/use.
- **AgroNT** (crop DNA) — **LICENSE HOLD** (non-commercial); do not read for commercial use.

### (Deferred analysis-side models — AMPLIFY, GPN, PlantCaduceus, Geneformer, CodonFM)
Reading gated by actual use; these are FLORA's analysis tools, not our generative scope.

---

## Rule these files enforce

1. No config locks (`configs/*.yaml`) or `/v1` wrappers written against a model whose
   Methods section hasn't been read yet (G11: no blind replication).
2. Every OPEN item here gets a closed line + date before the phase that needs it starts.
3. If a paper contradicts a card (like ProtGPT2's lr schedule could), the paper wins and
   the recipes doc gets corrected — with a note in our mods ledger.
