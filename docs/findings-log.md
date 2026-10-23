# Findings log — discoveries, observations, unexpected behavior (G13)

Standing rule (**G13**, Stan hard rule 2026-10-23 — see `CLAUDE.md`): whenever anything
is discovered or observed during work — findings, rare events, anomalies, unexpected
scenes, quirks that break or silently fix things — it goes here **immediately**, minimum
fields: date, context, what was observed, evidence pointer, impact. No silent
discoveries. This file was seeded retroactively ONCE at rule registration with the
session's already-known observations; every future entry is same-day.

Format: newest first. `ID | date | context | observation | evidence | impact/status`

---

## F-0006 | 2026-10-23 | PowerShell text redirection mangles patch files

- **Observation:** `git diff > file` run inside PowerShell produced a patch that
  `git apply` rejected with "No valid patches in input" — the redirect wrote
  encoding-mangled bytes (mojibake artifacts also visible when re-reading files later,
  e.g. `em dash` rendered as `?` sequences in CLAUDE.md).
- **Evidence:** prep attempts on `sciaca-katala-mvp4.patch` — first apply failed
  (exit 128), regeneration via `git diff --output=<file>` succeeded (9,213 bytes,
  clean apply on fresh clone).
- **Impact:** standing fix — always use `git diff --output=` (byte-safe) for patch
  export; never PowerShell `>`/`Out-File` for anything git consumes. Related: OneDrive
  path's git CRLF warnings are benign but consistent (`LF will be replaced by CRLF`).

## F-0005 | 2026-10-23 | DeepChem S3 zinc250k went 403 anonymous

- **Observation:** the reference data host (`deepchem` S3 bucket) returns HTTP 403 to
  unauthenticated GETs as of 2026-10-23 — the reference README's canonical fetch
  instructions are no longer reproducible as written.
- **Evidence:** `scripts/prepare_moflow_data.py` fallback behavior; ledger
  M-MOFLOW-7.
- **Impact:** mirror verified instead (Kaggle `basu369victor/zinc250k`, G7-validated:
  exact filename, 249,455 rows, columns smiles/logP/qed/SAS). Rare-event note:
  mirrors are now load-bearing — row-count check is the tripwire, never skip it.

## F-0004 | 2026-10-23 | Kaggle SaveKernel requires phone-verified account

- **Observation:** kernel save/push returned 403 until the account completed
  phone verification; token auth alone (KGAT_ full-scope) was not sufficient.
- **Evidence:** OAuth flow `kaggle auth login` + verification retry, then push
  succeeded (`leexze/moflow30m-zinc250k-r1`).
- **Impact:** operational knowledge for any future Kaggle account setup; documented
  so a 403-on-push is diagnosed as verification, not credentials.

## F-0003 | 2026-10-23 | Kaggle kernel push is strict about title/id slug alignment

- **Observation:** kernel push fails on mismatch between metadata slug and title;
  aligned slugs (e.g. `moflow30m-zinc250k-r1`) push cleanly.
- **Evidence:** successful push sequence for versions 1–7.
- **Impact:** convention for all future kernels: slug == title, lowercase-hyphenated.

## F-0002 | 2026-10-23 | The reference MoFlow tree is py3.7-era against a py3.13 runtime — six independent incompat classes

- **Observation:** porting required six distinct fixes: distutils removal (py3.12+),
  `orderedset` Cython wheel unbuildable, modern RDKit dropping bundled `rdkit.six`,
  `cairosvg`/native cairo absent, plus two data-shape ops (canonical index column,
  mirror shape). Each failure was far enough in sequence that run #1–#6 each
  surfaced exactly one new class.
- **Evidence:** `patches/M-MOFLOW-{5,6,9,10}*` + ledger `Default Project/docs/
  08-generative-recipes.md` §mods M-1..10; crash logs per run.
- **Impact:** expected porting friction recorded as permanent patch files with the
  try-original-first pattern; note for ProtGPT2 phase (P-* mods will likely hit
  the same runtime-class families: old-dep wheels, moved stdlib, integration
  imports).

## F-0001 | 2026-10-23 | Governance asymmetry discovered — the design ban is constructional, not procedural

- **Observation:** PinoAI/phfm's analysis tier excludes generation via governance
  commit (`565d09` — "esm2/cpt = embeddings+heads only; NO sampling/generation/
  mutagenesis code path"): code absence, not a switched-off flag.
- **Evidence:** their release-check page + ledger references, via the shared docs.
- **Impact:** defines the ecosystem contract for SciACA wiring and the GenD page;
  our tier complements theirs rather than duplicating any of their surface.

## F-0011 | 2026-10-23 | Scope addition — Pinal (text→protein), SERVE-first by necessity

- **Observation:** Pinal (Dai et al., Nature 2026; westlake-repl/Denovo-Pinal,
  Apache-2.0) designs proteins from natural-language descriptions via a two-stage
  pipeline (T2struct: text→3Di tokens; SaProt-T: structure+text→sequence). 16B total.
- **Decision (Stan-authorized):** added to our generative scope. But it is **served,
  not replicated** — 16B / 1.7B training pairs is far beyond from-scratch on our
  compute, so G9 is honored by serving (self-host 1.2B+760M on 1 GPU, or online
  server), never by claiming a from-scratch build.
- **Evidence:** repo+HF card read; license Apache-2.0 verified live; wrapper
  `serving/runtimes/pinal_runtime.py` + `/v1` task `design-from-text`.
- **Impact:** new capability A7 (natural-language design) — the "programmable"
  frontier of our tier. Honesty guard: Pinal's wet-lab GFP/enzyme validation is the
  authors' result, cited not claimed; our stack adds no efficacy claim of its own.

## F-0010 | 2026-10-23 | RFD4-Proteina serves via NVIDIA NIM HTTP — resolves the py3.12/3.13 conflict

- **Observation:** RFD4-Proteina requires Linux x86_64 + Python 3.12 + CUDA GPU
  (macOS/Windows unsupported; ~7 GB env). It cannot run in our Kaggle py3.13 /
  arbitrary runtime. BUT it ships an **NVIDIA NIM: a single synchronous HTTP
  endpoint** returning backbone + sequence — so we serve it out-of-process and the
  version conflict simply disappears.
- **Evidence:** rfd4-proteina.org/latest installation + docs.nvidia.com/nim/bionemo/
  rfd4-proteina overview; wrapper `serving/runtimes/proteina_runtime.py`.
- **Impact:** our `design.backbone` tool is a thin HTTP client, never an in-process
  import. Also learned the §7 mapping: `reasoning_depth` → `thinking_low/high`,
  `search_criteria` → reward-guided beam search. Input security property preserved:
  structures are named files in the request body, never filesystem paths.

## F-0009 | 2026-10-23 | ProtGPT2's learning rate is CONSTANT — no schedule (card ambiguity resolved)

- **Observation:** paper Methods state Adam (β1=0.9, β2=0.999), **LR 1e-3** with **no
  warmup/cosine/plateau/cyclic schedule named**. The HF card's bare "1e-3" had left
  this open; the paper confirms flat/constant.
- **Evidence:** nature.com/articles/s41467-022-32007-7 Methods ("optimized using Adam
  ... learning rate of 1e-03"); no scheduler mentioned anywhere.
- **Impact:** `configs/seqgen-ur50.yaml` locks `lr_schedule: constant, warmup_steps: 0`
  as the faithful baseline. A small warmup is pre-authorized as a *documented* P-1
  deviation ONLY if small-scale training proves unstable — never silent.

## F-0008 | 2026-10-23 | ProtGPT2 publishes NO numeric training perplexity

- **Observation:** the paper reports loss as standard CLM cross-entropy (Eq. 2) but
  gives **no training perplexity value or curve** anywhere in main text/Methods. The
  card doesn't either.
- **Evidence:** full-text grep for perplexity/ppl across the fetched article = zero
  numeric ppl; only qualitative sampling-quality discussion (k=950, rep-penalty 1.2).
- **Impact:** G7 consequence — we **cannot** benchmark our ≤100M training ppl against
  theirs (there is nothing to compare to). Our perplexity is reported stand-alone
  against our own held-out eval only; `configs/seqgen-ur50.yaml` sets
  `perplexity.compare_to_reference: false`. Prevents a false "matches ProtGPT2 ppl"
  claim before it could ever be made.

## F-0007 | 2026-10-23 | Kaggle serves NO log/output while a worker is RUNNING

- **Observation:** `kaggle kernels output` returns exit 0 with an EMPTY directory
  while the kernel is still running (`KernelWorkerStatus.RUNNING`) — the log of the
  live run is not fetchable from the API until the run terminates.
- **Evidence:** three sequential output attempts against `leexze/
  moflow30m-zinc250k-r1` v7 during RUNNING all returned zero files; status polling
  itself works normally.
- **Impact:** training observation duty (G13) restructures to: (a) during run —
  status transitions only, no loss curve; (b) the FIRST action on COMPLETE/ERROR is
  `kaggle kernels output`, then a full read of the epoch log for anomalies. The
  background monitor is therefore not a degraded substitute — it is the only
  live signal Kaggle offers.

---

*Next entries: any anomaly from the run #7 epoch log (fetched at termination),
ProtGPT2 data prep surprises, serving-layer quirks. Reminder duty is in
`CLAUDE.md` (G13).*
