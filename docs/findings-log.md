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
