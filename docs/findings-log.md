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

## F-0019 | 2026-10-24 | Adaptation ladder recorded — CPT/SFT/LoRA for the big served ones (Stan)

- **Decision (Stan):** for served models too big to build from scratch, the ownership
  path is CPT / SFT / LoRA on their OPEN weights — ideally on our crop/agri data (the
  moat). Recorded the full ladder + per-model feasibility in `docs/model-roster.md`.
- **Honest ownership rule (G7):** adaptation = we own the ADAPTER/DELTA, not the base
  ("our agri-adapter on RFD4-Proteina", never "our model"). Only Molek/Seqgen are
  genuinely from-scratch-ours.
- **Feasible now (LoRA/SFT):** RFD4-Proteina (BSD-3, T4-LoRA), DiffDock (MIT), ESM-2
  scorer (MIT, already Tier-2). **Blocked:** Proteina-Complexa/La-Proteina/Eden (license
  TBD, G11), AgroNT (NC HOLD), Evo 2-40B (compute). 7B Evo LoRA needs a real GPU.
- **Scope note:** plan recorded only — no training started; each future run obeys G1 +
  G11 + G7.

## F-0018 | 2026-10-24 | Authoritative scope = FLORA's OUT list (incl. new DNA-gen modality)

- **Observation (Stan, FLORA policy screenshot):** FLORA's "OUT — excluded by policy"
  list IS the generate/design set, and it is explicitly OURS to execute. Full list:
  Evo 2 + Eden (DNA gen); RFD4-Proteina + Proteina-Complexa + La-Proteina (protein
  design); ProtGPT2 (protein gen); MegaMolBART + MoFlow (chem gen); AgroNT (crop DNA, NC).
- **New modality:** **DNA generation (Evo 2, Eden)** enters GenD scope — beyond molecules
  + proteins. Evo 2 license verified live (Apache-2.0 / NVIDIA Open, commercial OK), served.
- **Honest license flags:** Proteina-Complexa / La-Proteina / Eden registered in scope but
  UNUSABLE until license read live (G1/G11). **AgroNT = LICENSE HOLD** (non-commercial —
  not a safety block; never shipped commercially unless relicensed).
- **Boundary restated:** everything FLORA USES (ESM-2, AMPLIFY, ESMFold/Boltz-2/Chai,
  Plant* trio, CodonFM) is their analysis side; we only borrow ESM-2 (score) + fold models
  (§8 validate). All GENERATION = ours. Registered: licenses, roster, reading-list.
- **Scope-discipline note:** registered-only — no new builds; Molek stays the active work.

## F-0017 | 2026-10-24 | Plan-roster mapped — MegaMolBART + DiffDock registered to GenD (Stan)

- **Observation (Stan's plan roster):** generative chemistry = MegaMolBART + MoFlow;
  protein generation = ProtGPT2; pose prediction = DiffDock; embeddings/property = ESM1/2;
  3D structure = OpenFold/AF2/ESMFold.
- **Decisions (Stan 2026-10-24):** MegaMolBART → **served alt** molecule generator
  (Apache-2.0, not from-scratch; Molek stays our owned one). DiffDock → **ours, served**
  in the optimize loop (MIT/NVIDIA Open) — docking sits on the molecule-design side since
  FLORA never touches molecules.
- **Registered:** licenses (megamolbart Apache-2.0, diffdock MIT/NVIDIA Open — both
  verified live), model cards, `/v1` `dock-ligand` task + megamolbart alt route,
  `diffdock_runtime.py` + `megamolbart_runtime.py` (honest pending), roster doc.
- **Boundary reaffirmed:** ESM1/2 + OpenFold/AF2/ESMFold are FLORA's analysis tools; we
  only use ESM-2 (scoring) and the fold models (§8 validation) on OUR side — cited, never
  blended. All GENERATIVE items (MoFlow/MegaMolBART/ProtGPT2/DiffDock) are GenD's.

## F-0016 | 2026-10-24 | Confirmed — GenD owns 100% of generate/design (FLORA is analysis-only)

- **Observation (Stan, w/ FLORA scope screenshot):** the analysis agent is named FLORA
  and is analysis-ONLY by construction (565d09): allergen/food-safety, function
  prediction, localization, variant-effect, structure prediction of existing proteins,
  search/clustering. Its explicit NON-scope: no new proteins/molecules (no
  design/generation), no farming assistant, no chatbot.
- **Mandate:** therefore EVERY generate/design/optimize need in the ecosystem is GenD's
  (ours). Recorded a full-coverage map in `Default Project/docs/10-agent-handshake.md`
  with no gaps: new molecules → Molek; new sequences → Seqgen/Pinal; binders → RFD4;
  variant DESIGN → Seqgen/RFD4 (variant-EFFECT prediction stays FLORA's); optimization →
  farm-knob; words→build → NLP intent/Pinal; the loop → /v1.
- **Boundary nuance logged:** structure prediction is shared TOOLING on opposite sides —
  FLORA analyzes existing proteins; we only use it to VALIDATE our designs (§8 ladder).

## F-0015 | 2026-10-24 | Honest correction — run #7 was NOT crash-safe against a ceiling-cut

- **Observation (Stan flagged checkpoint safety):** audit found the earlier "checkpoint-
  resume takes over" claim was too optimistic. The reference saves a snapshot EVERY epoch
  (train_model.py save_epochs default 1) — good — BUT run #7 writes them to
  `/kaggle/pino-bio-mvp/artifacts/<run>/snapshots/`, the EPHEMERAL repo clone. Kaggle
  persists only `/kaggle/working`, and only on a successful commit; cell 7 (copy→working)
  runs ONLY if training completes. So a ~12h ceiling-cut mid-run would lose every done
  epoch and leave nothing to resume from.
- **Fix (M-MOFLOW-12):** `MOLEK_SNAP_DIR=/kaggle/working/molek-snapshots` (snapshots land
  in the persistent dir as created) + background `scripts/kaggle_ckpt_push.py` ships them
  to Kaggle Dataset `leexze/molek-checkpoints` every 15 min, so a ceiling-cut keeps the
  done epochs; next run `--resume` restores from the dataset. Compile-clean, 27 tests green.
- **Impact on run #7:** #7 is ALREADY RUNNING with the old (unsafe) cell — it cannot be
  patched in place. If it completes before the ceiling → fine. If it is killed → its
  progress is likely lost and we relaunch the crash-safe version. Decision pending (Stan).

## F-0014 | 2026-10-23 | Scope-discipline check (Stan) — breadth-before-depth risk flagged

- **Observation (Stan):** reminder to stay in scope. Audit result: nothing is OUT of
  scope — every artifact maps to MVP-4 core (Molek/Seqgen/RFD4/ESM-2 + /v1), a
  registered later-board item (§6/§7/§8), or an explicit 2026-10-23 authorization
  (Pinal A7, NLP intent A8).
- **Real risk identified:** not scope creep but SEQUENCE — a lot of perimeter
  scaffolding was built while the core deliverable (Molek-30M checkpoint + honest eval,
  D2/D3) is still gated on Kaggle run #7. Wide perimeter, empty center.
- **Decision:** HOLD on new features. Next work is strictly D2 (pull checkpoint) → D3
  (honest eval) when run #7 lands; all other modules stay ready-but-parked until there
  is a trained base to run them against. No new capabilities without an explicit ask.

## F-0013 | 2026-10-23 | The workbench UI belongs in SciACA, not our backend repo (Stan)

- **Observation/decision (Stan):** the §7 trajectory workbench is a LAB-UI feature, so
  the product page lives in SciACA (consuming our `/v1`), not as a standalone HTML in
  pino-bio-mvp. Built it there: `src/pages/WorkbenchPage.tsx` + `/workbench` route + rail
  nav, matching SciACA's own components (Card/Field/Select/Checkbox/Badge/Button) and
  api client; merged PR #2 → `cff7705`, full build green.
- **Impact:** clean boundary — pino-bio-mvp owns the backend (trajectory in job results),
  SciACA owns the UI. `site/workbench.html` demoted to a dependency-free backend-reference
  demo. Pattern for future UI features: build them in SciACA against `/v1`, keep only
  backend + optional reference demos here.

## F-0012 | 2026-10-23 | Scope addition — OWNED NLP intent layer (text → our generators)

- **Observation/decision (Stan-authorized):** add natural language to OUR models, not
  just serve Pinal. Design: frozen open text encoder (MiniLM Apache-2.0 / ProTrek MIT)
  + OUR trained projection heads → Molek farm-knob targets (intent-mol) and Seqgen
  control (intent-seq). Only the projections are owned/trained → tiny, Kaggle-feasible.
- **Evidence:** `docs/nlp-intent-spec.md`, `configs/nlp-intent.yaml` (N-NLP-1..4);
  licenses `minilm-text`, `protrek-text`; capability A8.
- **Impact:** key free lever discovered — **ChEBI entries already pair a natural-language
  definition with a molecule**, so intent-mol gets (text, descriptor) training pairs for
  free alongside the farm-knob data; it can train before Molek's checkpoint exists.
  Honesty guards: OOD gate (N-NLP-4) flags prompts outside training clusters; owned
  numbers never blended with served Pinal/ESM-2 (G7); G9 honored by keeping it an
  adapter, never a from-scratch 16B.

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
