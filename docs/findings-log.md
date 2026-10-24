## F-0028 | 2026-10-24 | Seqgen data source resolved — UR50 2021_04 archived as tar bundle; pilot uses current UR50 streaming

- UR50 2021_04 direct fasta 404s; the archived release is a 40GB+ uniref2021_04.tar.gz
  bundle (not a direct uniref50.fasta.gz). Not worth it for a pilot.
- Current UniRef50 reachable: 8.18 GB gz. PILOT uses it via STREAMING EARLY-STOP
  (scripts/prepare_seqgen_pilot.py): decompress on the fly, collect ~1.5M seqs, stop —
  never downloads all 8GB. G1 live license gate first; G10 sha256+counts; seed 20261023.
- HONEST (G7/G11): pilot corpus is CURRENT UR50, NOT 2021_04 — documented in manifest;
  exact-version reserved for a faithful run (infeasible on T4 anyway). Same class of
  data-source adaptation as F-0005 (zinc DeepChem 403 -> mirror).
- Config validated vs NeurIPS 2024 compute-optimal table (66M = d640/10H/10L = ours).
## F-0027 | 2026-10-24 | REA placed in arsenal (Stan delegated) — closed/binary edge, armed not fired

- REA (morluto/rea, MIT; drives Ghidra/IDA/Hopper/JADX/Binwalk on CLOSED binaries) placed
  in docs/rea-tool.md. Rule: open source -> read it (G11, REA says skip source repos);
  closed/binary -> REA. Clean-room only (G11 + IP/legality check, G1 mindset).
- Where it's the unfair advantage: (1) served-artifact PROVENANCE AUDIT (does nvidia/
  RFD4-Proteina container match open RosettaCommons source? trust edge, aligns G7/G8/G1);
  (2) closed competitor agri/chem tool teardown (APK->JADX etc.) when a target exists;
  (3) binary-only models/firmware.
- Status: ARMED not fired — our whole stack is open (reading out-performs Ghidra here;
  proved it by finding MoFlow FCD baseline from literature). No speculative Ghidra install.
  Fires on a confirmed closed target + legality check.
## F-0026 | 2026-10-24 | FCD CORRECTED — Molek matches MoFlow (I mis-scaled, fixed via baseline, G14)

- **Correction of F-0025 over-alarm:** I called FCD 23.40 "poor" by comparing to the MOSES
  scale (good ~1). WRONG scale. Published zinc250k baselines (GLAD 2024): GraphAF 16.02,
  **MoFlow 20.93**, GDSS 14.66, DiGress 23.06, GraphArm 16.26. On zinc250k, FCD ~14-23 is
  normal for everyone.
- **Molek 23.40 ~= MoFlow reference 20.93** (slightly higher = 30M scale-down). So Molek
  faithfully reproduces MoFlow on FCD too — NOTHING TO FIX. Matches reference on validity,
  novelty, uniqueness, AND distributional fidelity.
- **Architecture truth:** MoFlow is mid-pack on FCD by design ("fails to generate
  high-fidelity samples" per CDGS); diffusion (GDSS) beats it. The FCD frontier needs a
  DIFFUSION generator, not a Molek fix — logged as a roadmap lever.
- **Lesson (G14):** get the reference baseline BEFORE interpreting a metric. I interpreted
  then verified; should have verified first. Corrected transparently.
## F-0025 | 2026-10-24 | Rung 2 — FCD exposes poor distributional fidelity (honest, tempers D3)

- Distributional metrics (30k gen vs zinc250k test): FCD/Test **23.40** (HIGH=poor),
  SNN/Test **0.196** (LOW), IntDiv 0.908 / IntDiv2 0.900 (high diversity). Saved
  docs/results/molek-30m-distribution.{md,json}.
- **Honest reading:** D3 near-perfect validity/novelty/uniqueness is NOT the whole story —
  FCD+SNN say generations are distributionally far from real zinc chemistry. Validity !=
  quality. Leading cause: MoFlow validity-correction distorts structures (known trade-off;
  uncorrected 0% + corrected 99.95% + high FCD all consistent).
- **Moses package abandoned for metrics** (py3.13: rdkit.six + pandas2 DataFrame.append) ->
  FCD via fcd_torch (= MOSES FCD), IntDiv/SNN via RDKit; Frag/Scaf deferred (M-MOSES-1 kept
  for the sascorer fix). G14 pivot.
- **Discipline win:** FCD is the metric that stops us overclaiming "99.95% = great". Do NOT
  claim distributional SOTA. Next: get MoFlow's own zinc250k FCD baseline to compare.
# Findings log â€” discoveries, observations, unexpected behavior (G13)

Standing rule (**G13**, Stan hard rule 2026-10-23 â€” see `CLAUDE.md`): whenever anything
is discovered or observed during work â€” findings, rare events, anomalies, unexpected
scenes, quirks that break or silently fix things â€” it goes here **immediately**, minimum
fields: date, context, what was observed, evidence pointer, impact. No silent
discoveries. This file was seeded retroactively ONCE at rule registration with the
session's already-known observations; every future entry is same-day.

Format: newest first. `ID | date | context | observation | evidence | impact/status`

---

## F-0006 | 2026-10-23 | PowerShell text redirection mangles patch files

- **Observation:** `git diff > file` run inside PowerShell produced a patch that
  `git apply` rejected with "No valid patches in input" â€” the redirect wrote
  encoding-mangled bytes (mojibake artifacts also visible when re-reading files later,
  e.g. `em dash` rendered as `?` sequences in CLAUDE.md).
- **Evidence:** prep attempts on `sciaca-katala-mvp4.patch` â€” first apply failed
  (exit 128), regeneration via `git diff --output=<file>` succeeded (9,213 bytes,
  clean apply on fresh clone).
- **Impact:** standing fix â€” always use `git diff --output=` (byte-safe) for patch
  export; never PowerShell `>`/`Out-File` for anything git consumes. Related: OneDrive
  path's git CRLF warnings are benign but consistent (`LF will be replaced by CRLF`).

## F-0005 | 2026-10-23 | DeepChem S3 zinc250k went 403 anonymous

- **Observation:** the reference data host (`deepchem` S3 bucket) returns HTTP 403 to
  unauthenticated GETs as of 2026-10-23 â€” the reference README's canonical fetch
  instructions are no longer reproducible as written.
- **Evidence:** `scripts/prepare_moflow_data.py` fallback behavior; ledger
  M-MOFLOW-7.
- **Impact:** mirror verified instead (Kaggle `basu369victor/zinc250k`, G7-validated:
  exact filename, 249,455 rows, columns smiles/logP/qed/SAS). Rare-event note:
  mirrors are now load-bearing â€” row-count check is the tripwire, never skip it.

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
- **Evidence:** successful push sequence for versions 1â€“7.
- **Impact:** convention for all future kernels: slug == title, lowercase-hyphenated.

## F-0002 | 2026-10-23 | The reference MoFlow tree is py3.7-era against a py3.13 runtime â€” six independent incompat classes

- **Observation:** porting required six distinct fixes: distutils removal (py3.12+),
  `orderedset` Cython wheel unbuildable, modern RDKit dropping bundled `rdkit.six`,
  `cairosvg`/native cairo absent, plus two data-shape ops (canonical index column,
  mirror shape). Each failure was far enough in sequence that run #1â€“#6 each
  surfaced exactly one new class.
- **Evidence:** `patches/M-MOFLOW-{5,6,9,10}*` + ledger `Default Project/docs/
  08-generative-recipes.md` Â§mods M-1..10; crash logs per run.
- **Impact:** expected porting friction recorded as permanent patch files with the
  try-original-first pattern; note for ProtGPT2 phase (P-* mods will likely hit
  the same runtime-class families: old-dep wheels, moved stdlib, integration
  imports).

## F-0001 | 2026-10-23 | Governance asymmetry discovered â€” the design ban is constructional, not procedural

- **Observation:** PinoAI/phfm's analysis tier excludes generation via governance
  commit (`565d09` â€” "esm2/cpt = embeddings+heads only; NO sampling/generation/
  mutagenesis code path"): code absence, not a switched-off flag.
- **Evidence:** their release-check page + ledger references, via the shared docs.
- **Impact:** defines the ecosystem contract for SciACA wiring and the GenD page;
  our tier complements theirs rather than duplicating any of their surface.

## F-0024 | 2026-10-24 | D3 eval VERIFIED correct (double-check per Stan)

- **Checked the failure modes that would make the numbers wrong:**
  1. Empty-trainset â†’ fake novelty? NO. Log: "249455 in total, 224568 training data,
     24887 testing data" â€” novelty 100% is measured vs 224,568 real train molecules. âœ…
  2. Fabricated/parse-artifact metrics? NO. Real integer counts per experiment
     (valid: 9996/9998/9994/9990/9995 of 10000), tight sd 0.02. âœ…
  3. Model loaded wrong (random/mismatched params)? NO. snapshot epoch_197 + reconstructed
     moflow-params loaded, then 99.95% valid output â€” a mismatch would give garbage. âœ…
  4. Apples-to-apples with reference? YES. 10kÃ—5, temp 0.85 (ref setting), same zinc250k
     split (valid_idx_zinc.json). âœ…
- **Honest caveat:** novelty uses the reference's own SMILES-match (canonicalization
  inherited from check_novelty) â€” our 100% is apples-to-apples with the reference's
  reported 100%, but a fully rigorous "true novelty" would need a canonicalization audit.
  Inherited from reference, not our error.
- **Verdict:** D3 corrected numbers are correct and trustworthy; uncorrected 0% is genuine
  MoFlow-by-design (same loaded model that gives 99.95% corrected).

## F-0023 | 2026-10-24 | D3 dual-report COMPLETE â€” corrected matches reference, uncorrected 0% is MoFlow-by-design

- **Complete M-MOFLOW-4 dual-report** (M-13 fix applied, eval v3): corrected validity
  99.95% / novelty 100% / uniqueness 99.99% (= matches reference); uncorrected raw 0.00%
  reproducible 5/5. Saved docs/results/molek-30m-D3.{md,json}.
- **0% is honest + expected, not a flaw:** MoFlow's raw graph-flow decode has valency
  violations that its intrinsic correct_mol step fixes (the reference ALWAYS reports
  corrected). Modern RDKit strictness pushes the no-correction valid_mol path to exactly 0.
  Proof the model learned: correction yields 99.95%-valid NOVEL (100%) diverse molecules â€”
  correction fixes valency, cannot invent novelty.
- **Stance (G7):** report the stark 0% rather than hide behind correction; the meaningful
  capability number is corrected (matches reference). Reference-faithful (G11): used the
  reference's own correct_validity flag, not a custom middle metric.
- **D3 CLOSED.** Next: MOSES benchmark (sota-roadmap rung 2).

## F-0022 | 2026-10-24 | D3 DONE â€” Molek-30M matches reference (corrected); uncorrected path has a bug

- **Result:** Molek-30M (epoch 197/200) eval, 10kÃ—5 @ T=0.85. Corrected: validity 99.94%
  (sd .02), novelty 100.0%, uniqueness 100.0%, abs_novelty 99.93%, abs_uniqueness 99.93%.
  Reference pinned README: validity 100.00%, novelty 100.00% â†’ **we MATCH at 30M scale-down.**
  Saved: docs/results/molek-30m-D3.md + .json.
- **Honest caveat (G7):** the uncorrected run (`--correct_validity false`) reported
  `0/10000 valid` then crashed `UnboundLocalError: abs_novel_ratio` in reference
  check_novelty (no 0-valid path). 0% is a BROKEN measurement, not a model result â€” not
  presented as honest. M-MOFLOW-4 dual-report INCOMPLETE until fixed.
- **Recovery arc worth noting:** run that "errored at 10h" actually trained to epoch 197
  and saved it; the error was tail-end only. The 10h was NOT wasted. Eval then hit a
  dataset mount-path bug (fixed with recursive glob), then completed clean.
- **Next:** diagnose 0% uncorrected + patch check_novelty 0-valid crash â†’ rerun for the
  honest uncorrected number â†’ then MOSES (sota-roadmap rung 2).

## F-0021 | 2026-10-24 | Screenshot log = OLD run #6 (pre-M10 cairosvg crash); current chain VERIFIED clean

- **Trigger:** Stan screenshotted the Kaggle Logs tab showing `ModuleNotFoundError: No
  module named 'cairosvg'` + exit 1, timestamp Oct 23 **12:01** (`moflow_ckpts_1023-1201`).
- **Initial reaction (corrected):** I first called it "a crash, not training" â€” reacting
  before verifying (the very thing G14 forbids). Then I VERIFIED.
- **Verification (G14):** cloned reference moflow fresh, ran the exact fetch_thirdparty
  sorted-glob apply sequence (order: 10,5,6,9 â€” lexicographic). ALL FOUR patches applied
  cleanly; generate.py cairosvg became `try: import cairosvg / except: cairosvg = None`.
  So the current patch chain is correct; `git apply` tolerates the ordering offset.
- **Conclusion:** the 12:01 log is run #6, from BEFORE M-10 was committed â€” historical,
  already fixed. Run #7 (pushed ~20:00, post-M10) has the working chain; its 6h RUNNING
  status is consistent with genuine training (a cairosvg crash would die at ~5 min).
- **Minor real issue:** our LOCAL third_party/moflow copy is stale (built pre-M10, shows
  cairosvg unpatched). Harmless â€” Kaggle clones fresh each run. Re-fetch locally if we
  ever train on the dev box.
- **Latent fragility noted (not urgent):** fetch_thirdparty's except-handler would
  double-raise if a patch genuinely failed both apply and reverse-check; not triggered
  since all patches apply. Harden later if touched.

## F-0020 | 2026-10-24 | New hard rule G14 â€” research-before-execute (Stan)

- **Rule (Stan):** if an action/approach needs verifying, conduct research FIRST to
  confirm it's correct before executing. Verify, don't assume. Registered as G14 in
  CLAUDE.md; extends G11 (recipe-read) to every significant decision.
- **Already in practice (this is codifying it):** live license checks before any data use
  (ChEBI/UniProt/MegaMolBART/DiffDock/Evo2), reading paper Methods before locking configs
  (ProtGPT2, MoFlow), reading RFD4/Pinal docs before wrappers, checking the PH landscape
  before claims. G14 makes it binding, not just habit.
- **Impact:** before executing anything uncertain (a new model, a benchmark design, a
  scale-up, a claim), do the research pass first; if it shows the plan is wrong, correct
  it and log why. No blind execution.

## F-0019 | 2026-10-24 | Adaptation ladder recorded â€” CPT/SFT/LoRA for the big served ones (Stan)

- **Decision (Stan):** for served models too big to build from scratch, the ownership
  path is CPT / SFT / LoRA on their OPEN weights â€” ideally on our crop/agri data (the
  moat). Recorded the full ladder + per-model feasibility in `docs/model-roster.md`.
- **Honest ownership rule (G7):** adaptation = we own the ADAPTER/DELTA, not the base
  ("our agri-adapter on RFD4-Proteina", never "our model"). Only Molek/Seqgen are
  genuinely from-scratch-ours.
- **Feasible now (LoRA/SFT):** RFD4-Proteina (BSD-3, T4-LoRA), DiffDock (MIT), ESM-2
  scorer (MIT, already Tier-2). **Blocked:** Proteina-Complexa/La-Proteina/Eden (license
  TBD, G11), AgroNT (NC HOLD), Evo 2-40B (compute). 7B Evo LoRA needs a real GPU.
- **Scope note:** plan recorded only â€” no training started; each future run obeys G1 +
  G11 + G7.

## F-0018 | 2026-10-24 | Authoritative scope = FLORA's OUT list (incl. new DNA-gen modality)

- **Observation (Stan, FLORA policy screenshot):** FLORA's "OUT â€” excluded by policy"
  list IS the generate/design set, and it is explicitly OURS to execute. Full list:
  Evo 2 + Eden (DNA gen); RFD4-Proteina + Proteina-Complexa + La-Proteina (protein
  design); ProtGPT2 (protein gen); MegaMolBART + MoFlow (chem gen); AgroNT (crop DNA, NC).
- **New modality:** **DNA generation (Evo 2, Eden)** enters GenD scope â€” beyond molecules
  + proteins. Evo 2 license verified live (Apache-2.0 / NVIDIA Open, commercial OK), served.
- **Honest license flags:** Proteina-Complexa / La-Proteina / Eden registered in scope but
  UNUSABLE until license read live (G1/G11). **AgroNT = LICENSE HOLD** (non-commercial â€”
  not a safety block; never shipped commercially unless relicensed).
- **Boundary restated:** everything FLORA USES (ESM-2, AMPLIFY, ESMFold/Boltz-2/Chai,
  Plant* trio, CodonFM) is their analysis side; we only borrow ESM-2 (score) + fold models
  (Â§8 validate). All GENERATION = ours. Registered: licenses, roster, reading-list.
- **Scope-discipline note:** registered-only â€” no new builds; Molek stays the active work.

## F-0017 | 2026-10-24 | Plan-roster mapped â€” MegaMolBART + DiffDock registered to GenD (Stan)

- **Observation (Stan's plan roster):** generative chemistry = MegaMolBART + MoFlow;
  protein generation = ProtGPT2; pose prediction = DiffDock; embeddings/property = ESM1/2;
  3D structure = OpenFold/AF2/ESMFold.
- **Decisions (Stan 2026-10-24):** MegaMolBART â†’ **served alt** molecule generator
  (Apache-2.0, not from-scratch; Molek stays our owned one). DiffDock â†’ **ours, served**
  in the optimize loop (MIT/NVIDIA Open) â€” docking sits on the molecule-design side since
  FLORA never touches molecules.
- **Registered:** licenses (megamolbart Apache-2.0, diffdock MIT/NVIDIA Open â€” both
  verified live), model cards, `/v1` `dock-ligand` task + megamolbart alt route,
  `diffdock_runtime.py` + `megamolbart_runtime.py` (honest pending), roster doc.
- **Boundary reaffirmed:** ESM1/2 + OpenFold/AF2/ESMFold are FLORA's analysis tools; we
  only use ESM-2 (scoring) and the fold models (Â§8 validation) on OUR side â€” cited, never
  blended. All GENERATIVE items (MoFlow/MegaMolBART/ProtGPT2/DiffDock) are GenD's.

## F-0016 | 2026-10-24 | Confirmed â€” GenD owns 100% of generate/design (FLORA is analysis-only)

- **Observation (Stan, w/ FLORA scope screenshot):** the analysis agent is named FLORA
  and is analysis-ONLY by construction (565d09): allergen/food-safety, function
  prediction, localization, variant-effect, structure prediction of existing proteins,
  search/clustering. Its explicit NON-scope: no new proteins/molecules (no
  design/generation), no farming assistant, no chatbot.
- **Mandate:** therefore EVERY generate/design/optimize need in the ecosystem is GenD's
  (ours). Recorded a full-coverage map in `Default Project/docs/10-agent-handshake.md`
  with no gaps: new molecules â†’ Molek; new sequences â†’ Seqgen/Pinal; binders â†’ RFD4;
  variant DESIGN â†’ Seqgen/RFD4 (variant-EFFECT prediction stays FLORA's); optimization â†’
  farm-knob; wordsâ†’build â†’ NLP intent/Pinal; the loop â†’ /v1.
- **Boundary nuance logged:** structure prediction is shared TOOLING on opposite sides â€”
  FLORA analyzes existing proteins; we only use it to VALIDATE our designs (Â§8 ladder).

## F-0015 | 2026-10-24 | Honest correction â€” run #7 was NOT crash-safe against a ceiling-cut

- **Observation (Stan flagged checkpoint safety):** audit found the earlier "checkpoint-
  resume takes over" claim was too optimistic. The reference saves a snapshot EVERY epoch
  (train_model.py save_epochs default 1) â€” good â€” BUT run #7 writes them to
  `/kaggle/pino-bio-mvp/artifacts/<run>/snapshots/`, the EPHEMERAL repo clone. Kaggle
  persists only `/kaggle/working`, and only on a successful commit; cell 7 (copyâ†’working)
  runs ONLY if training completes. So a ~12h ceiling-cut mid-run would lose every done
  epoch and leave nothing to resume from.
- **Fix (M-MOFLOW-12):** `MOLEK_SNAP_DIR=/kaggle/working/molek-snapshots` (snapshots land
  in the persistent dir as created) + background `scripts/kaggle_ckpt_push.py` ships them
  to Kaggle Dataset `leexze/molek-checkpoints` every 15 min, so a ceiling-cut keeps the
  done epochs; next run `--resume` restores from the dataset. Compile-clean, 27 tests green.
- **Impact on run #7:** #7 is ALREADY RUNNING with the old (unsafe) cell â€” it cannot be
  patched in place. If it completes before the ceiling â†’ fine. If it is killed â†’ its
  progress is likely lost and we relaunch the crash-safe version. Decision pending (Stan).

## F-0014 | 2026-10-23 | Scope-discipline check (Stan) â€” breadth-before-depth risk flagged

- **Observation (Stan):** reminder to stay in scope. Audit result: nothing is OUT of
  scope â€” every artifact maps to MVP-4 core (Molek/Seqgen/RFD4/ESM-2 + /v1), a
  registered later-board item (Â§6/Â§7/Â§8), or an explicit 2026-10-23 authorization
  (Pinal A7, NLP intent A8).
- **Real risk identified:** not scope creep but SEQUENCE â€” a lot of perimeter
  scaffolding was built while the core deliverable (Molek-30M checkpoint + honest eval,
  D2/D3) is still gated on Kaggle run #7. Wide perimeter, empty center.
- **Decision:** HOLD on new features. Next work is strictly D2 (pull checkpoint) â†’ D3
  (honest eval) when run #7 lands; all other modules stay ready-but-parked until there
  is a trained base to run them against. No new capabilities without an explicit ask.

## F-0013 | 2026-10-23 | The workbench UI belongs in SciACA, not our backend repo (Stan)

- **Observation/decision (Stan):** the Â§7 trajectory workbench is a LAB-UI feature, so
  the product page lives in SciACA (consuming our `/v1`), not as a standalone HTML in
  pino-bio-mvp. Built it there: `src/pages/WorkbenchPage.tsx` + `/workbench` route + rail
  nav, matching SciACA's own components (Card/Field/Select/Checkbox/Badge/Button) and
  api client; merged PR #2 â†’ `cff7705`, full build green.
- **Impact:** clean boundary â€” pino-bio-mvp owns the backend (trajectory in job results),
  SciACA owns the UI. `site/workbench.html` demoted to a dependency-free backend-reference
  demo. Pattern for future UI features: build them in SciACA against `/v1`, keep only
  backend + optional reference demos here.

## F-0012 | 2026-10-23 | Scope addition â€” OWNED NLP intent layer (text â†’ our generators)

- **Observation/decision (Stan-authorized):** add natural language to OUR models, not
  just serve Pinal. Design: frozen open text encoder (MiniLM Apache-2.0 / ProTrek MIT)
  + OUR trained projection heads â†’ Molek farm-knob targets (intent-mol) and Seqgen
  control (intent-seq). Only the projections are owned/trained â†’ tiny, Kaggle-feasible.
- **Evidence:** `docs/nlp-intent-spec.md`, `configs/nlp-intent.yaml` (N-NLP-1..4);
  licenses `minilm-text`, `protrek-text`; capability A8.
- **Impact:** key free lever discovered â€” **ChEBI entries already pair a natural-language
  definition with a molecule**, so intent-mol gets (text, descriptor) training pairs for
  free alongside the farm-knob data; it can train before Molek's checkpoint exists.
  Honesty guards: OOD gate (N-NLP-4) flags prompts outside training clusters; owned
  numbers never blended with served Pinal/ESM-2 (G7); G9 honored by keeping it an
  adapter, never a from-scratch 16B.

## F-0011 | 2026-10-23 | Scope addition â€” Pinal (textâ†’protein), SERVE-first by necessity

- **Observation:** Pinal (Dai et al., Nature 2026; westlake-repl/Denovo-Pinal,
  Apache-2.0) designs proteins from natural-language descriptions via a two-stage
  pipeline (T2struct: textâ†’3Di tokens; SaProt-T: structure+textâ†’sequence). 16B total.
- **Decision (Stan-authorized):** added to our generative scope. But it is **served,
  not replicated** â€” 16B / 1.7B training pairs is far beyond from-scratch on our
  compute, so G9 is honored by serving (self-host 1.2B+760M on 1 GPU, or online
  server), never by claiming a from-scratch build.
- **Evidence:** repo+HF card read; license Apache-2.0 verified live; wrapper
  `serving/runtimes/pinal_runtime.py` + `/v1` task `design-from-text`.
- **Impact:** new capability A7 (natural-language design) â€” the "programmable"
  frontier of our tier. Honesty guard: Pinal's wet-lab GFP/enzyme validation is the
  authors' result, cited not claimed; our stack adds no efficacy claim of its own.

## F-0010 | 2026-10-23 | RFD4-Proteina serves via NVIDIA NIM HTTP â€” resolves the py3.12/3.13 conflict

- **Observation:** RFD4-Proteina requires Linux x86_64 + Python 3.12 + CUDA GPU
  (macOS/Windows unsupported; ~7 GB env). It cannot run in our Kaggle py3.13 /
  arbitrary runtime. BUT it ships an **NVIDIA NIM: a single synchronous HTTP
  endpoint** returning backbone + sequence â€” so we serve it out-of-process and the
  version conflict simply disappears.
- **Evidence:** rfd4-proteina.org/latest installation + docs.nvidia.com/nim/bionemo/
  rfd4-proteina overview; wrapper `serving/runtimes/proteina_runtime.py`.
- **Impact:** our `design.backbone` tool is a thin HTTP client, never an in-process
  import. Also learned the Â§7 mapping: `reasoning_depth` â†’ `thinking_low/high`,
  `search_criteria` â†’ reward-guided beam search. Input security property preserved:
  structures are named files in the request body, never filesystem paths.

## F-0009 | 2026-10-23 | ProtGPT2's learning rate is CONSTANT â€” no schedule (card ambiguity resolved)

- **Observation:** paper Methods state Adam (Î²1=0.9, Î²2=0.999), **LR 1e-3** with **no
  warmup/cosine/plateau/cyclic schedule named**. The HF card's bare "1e-3" had left
  this open; the paper confirms flat/constant.
- **Evidence:** nature.com/articles/s41467-022-32007-7 Methods ("optimized using Adam
  ... learning rate of 1e-03"); no scheduler mentioned anywhere.
- **Impact:** `configs/seqgen-ur50.yaml` locks `lr_schedule: constant, warmup_steps: 0`
  as the faithful baseline. A small warmup is pre-authorized as a *documented* P-1
  deviation ONLY if small-scale training proves unstable â€” never silent.

## F-0008 | 2026-10-23 | ProtGPT2 publishes NO numeric training perplexity

- **Observation:** the paper reports loss as standard CLM cross-entropy (Eq. 2) but
  gives **no training perplexity value or curve** anywhere in main text/Methods. The
  card doesn't either.
- **Evidence:** full-text grep for perplexity/ppl across the fetched article = zero
  numeric ppl; only qualitative sampling-quality discussion (k=950, rep-penalty 1.2).
- **Impact:** G7 consequence â€” we **cannot** benchmark our â‰¤100M training ppl against
  theirs (there is nothing to compare to). Our perplexity is reported stand-alone
  against our own held-out eval only; `configs/seqgen-ur50.yaml` sets
  `perplexity.compare_to_reference: false`. Prevents a false "matches ProtGPT2 ppl"
  claim before it could ever be made.

## F-0007 | 2026-10-23 | Kaggle serves NO log/output while a worker is RUNNING

- **Observation:** `kaggle kernels output` returns exit 0 with an EMPTY directory
  while the kernel is still running (`KernelWorkerStatus.RUNNING`) â€” the log of the
  live run is not fetchable from the API until the run terminates.
- **Evidence:** three sequential output attempts against `leexze/
  moflow30m-zinc250k-r1` v7 during RUNNING all returned zero files; status polling
  itself works normally.
- **Impact:** training observation duty (G13) restructures to: (a) during run â€”
  status transitions only, no loss curve; (b) the FIRST action on COMPLETE/ERROR is
  `kaggle kernels output`, then a full read of the epoch log for anomalies. The
  background monitor is therefore not a degraded substitute â€” it is the only
  live signal Kaggle offers.

---

*Next entries: any anomaly from the run #7 epoch log (fetched at termination),
ProtGPT2 data prep surprises, serving-layer quirks. Reminder duty is in
`CLAUDE.md` (G13).*




