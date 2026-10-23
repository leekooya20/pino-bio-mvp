# Capability map — "make sure we can deliver ALL of it" (G-blocking register)

Answer to Stan's directive (2026-10-23): every capability promised on `site/pinobio-gend.html`
and in `docs/benchmarks.md` (§6/§7/§8), mapped to **what exists today**, what blocks it, and
**which hard rule (G1–G11) it must survive**. Updated as things ship; statuses are honest.

Reproducibility trio at bottom: seed `20261023` · config `a1288cc8…` · pinned
`moflow@3611c6372602` / `moses@dd7ed6ab38e2` — every row below inherits them (G3/G10).

**Naming registry (Stan-locked 2026-10-23):** our trained weights = **Molek-30M**
(this run) / **Molek-PH-30M** (future M-MOFLOW-3 agri-head variant). Methods and
papers always say "MoFlow"; weights always say Molek; the lineage line
"MoFlow replica (Zang & Wang, KDD 2020), MIT, own from-scratch training" travels
with every public mention of the name.

---

## A. The six "It does" capabilities (GenD page)

| # | Capability | Status (2026-10-23) | Blocks / next concrete artifact | Hard-rule gate |
|---|---|---|---|---|
| A1 | **Generate novel molecular graphs** (**Molek-30M** — our from-scratch MoFlow replica @30M; naming locked by Stan 2026-10-23; lineage: Zang & Wang KDD 2020, MIT) | 🟡 **in training** — pipeline fully green through preflight (29,049,444 params), epochs running on Kaggle r1 | first `eval_summary.json` w/ corrected+uncorrected (M-MOFLOW-4) | G3/G7 (frozen harness = reference generate.py + MOSES metrics), G10 ✅ |
| A2 | **Generate novel protein sequences** (**Seqgen-small** — our ProtGPT2 replica ≤100M; lineage: Ferruz et al. Nat Commun 2022, Apache-2.0) | 🟡 **config LOCKED + data tooling built 2026-10-23** — `configs/seqgen-ur50.yaml` (P-PTGPT2-1..5); `scripts/prepare_seqgen_data.py` (live UniProt license gate, cluster-stratified subsample, sha256 manifest, G10 run_meta) + `scripts/train_bpe_seqgen.py` (BPE, vocab+sha recorded); next = run on compute | tooling → data run → first train | G11 (Methods read ✅), G1 (uniref50 entry ✅ + live-license gate in the script) |
| A3 | **Design binders/backbones** (RFD4-Proteina served) — **wrapper written** `serving/runtimes/proteina_runtime.py` (NIM HTTP, mode→task map, §7 thinking/search passthrough); deep docs read ✅ | 🟡 **wrapper ready 2026-10-23** — live on a reachable `PROTEINA_ENDPOINT` (NIM/container); honest error until then (G7) | NIM/container endpoint + 1-condition acceptance run | G4 (public claims gated by §6 PPI bench), G1/BSD-3 ✅, G7 (served metrics cited not blended) |
| A4 | **Optimize toward target properties** (M-MOFLOW-3 farm-knob) — spec: `docs/farmknob-spec.md` (ChEBI CHEBI:33286 positives, CC BY 4.0 verified 2026-10-23; sufficiency = region-rate + novelty-preserved + cost-honesty) | 🟠 after A1 baseline — head is config-registered; needs a trained base latents | conditioned `optimize-property` run vs baseline property deltas | G3/G7 (reported as ours w/ config hash), M-MOFLOW-3 ledger row ✅ |
| A5 | **Inverse-fold / structured redesign** (served tool path) | 🟠 Phase-3, behind A3 | same containers as A3 + job schema | G4 gate shared with A3 |
| A6 | **Generate→screen→optimize loop as /v1 jobs** | 🟡 **server scaffolded 2026-10-23** — `serving/` FastAPI implements the full §10.1 contract (POST/GET /v1/jobs, /v1/models[/:id], /v1/projects); task→tool map §10.2; honest `pending` results (G7) until backends land; §7 reasoning_depth+search_criteria passthrough wired; 4 serving smoke tests green | real backends attach as checkpoints/containers arrive (Molek→D2, Seqgen, RFD4 container) | G7 (no fabricated results — `measured:false`), G8 (GET auth-free, keys via env), G9 (only §10.2 tasks; unknown⇒400) |
| A7 | **Design proteins from natural language** (Pinal served, Apache-2.0) — **SCOPE ADDITION, Stan-authorized 2026-10-23** | 🟡 **wrapper written** `serving/runtimes/pinal_runtime.py` + `/v1` task `design-from-text`; repo+card read ✅ (two-stage T2struct→SaProt-T, 16B) | self-host 1.2B+SaProt-T (or online server) → `PINAL_ENDPOINT` | G9 (SERVE-first — 16B not from-scratch; explicit scope auth logged), G1 Apache-2.0 ✅, G7 (authors' wet-lab results cited not claimed) |
| A8 | **OWN natural-language layer for OUR generators** (intent heads → Molek + Seqgen) — **SCOPE ADDITION, Stan-authorized 2026-10-23** | 🟡 **spec + config + data-fetch built** — `docs/nlp-intent-spec.md` / `configs/nlp-intent.yaml` (N-NLP-1..4); `scripts/fetch_chebi_agchem.py` (G1 live CC BY 4.0 gate ✅ tested against real ChEBI; role-tree traversal over CHEBI:33286 → text↔descriptor pairs; 3 logic tests green); intent-mol trains on these free pairs | fetch ChEBI on compute → train intent-mol head (independent of Molek ckpt) → intent-seq after Seqgen | G9 (owned adapter), G1 (live gate tested), G11 (projection recipe read), G7 (OOD gate; owned ≠ served) |

## B. The "later board" (benchmarks.md)

| Item | Deliverable that makes it real | Rule gate |
|---|---|---|
| §6 PPI benchmark | fixed targets (rows+hashes), 200-attempt budget, clustered pass rate, **refold ladder ESMFold→Boltz-2→Chai** (honest "not-AF3"), comparison table ours-vs-theirs — **HARNESS BUILT 2026-10-23** (`benchmarks/ppi/`: fetch_ppi_targets + run_ppi_benchmark + metrics; honest `blocked` until backends live; 3 tests green) | G7 (failures reported, no rounding), G4 (this IS the public-claim gate) |
| §7 trajectory workbench | `/v1` job artifacts record per-stage snapshots; workbench page renders them; `reasoning_depth` + `search_criteria` passthrough — **SHIPPED IN SciACA 2026-10-23** (PR #2 → `cff7705`, `src/pages/WorkbenchPage.tsx` + `/workbench` route + rail nav; drives our `/v1` loop; honest pending stages). Backend trajectory in our serving layer; `site/workbench.html` kept as a backend-only reference demo | G9 (scope: generator tier only — no analysis heads invented), G4 |
| §8 AF3-grade validation | ladder per table; multi-seed top-confidence sampling; bootstrap CIs + Wilcoxon for our A/B arms | G7, G2 (AF3/cloud servers never used for training output), G4 |
| ProtGPT2 crop arm (P-PTGPT2-5) | rice-first manifest → our own `data/manifests/` entries at download-verify time | G1 (UniProt CC BY 4.0 — verify live at download, their honest precedent adopted) |

## C. Standing hard-rules compliance in this repo (proof pointers)

| Rule | Where it is enforced right here |
|---|---|
| G1 licenses | `configs/licenses.yaml` (mirror-synched from Katala master) + license checks in `fetch_thirdparty.py` + all manifests written at fetch-verify time |
| G2 closed-API outputs | nothing in our corpora; any future synthetic text gets generator-citation (ledger discipline adopted from PinoAI precedent) |
| G3 frozen eval harness | evals ALWAYS run the pinned reference code (generate.py), never our math |
| G4 capability gates | §6 PPI benchmark + §8 ladder = the explicit gates before any public capability language |
| G7 honest numbers | M-MOFLOW-4 dual-report (with/without correction), failures are reported (`run_meta.exit_code: 1` published, not hidden) |
| G8 secrets | token goes only to `~/.kaggle/` (never repo); no token in kernel code (public-clone fallback) |
| G10 run logging | `artifacts/run_meta.json` in every session: seed, config hash, pins, patches applied, resume flag |
| G11 recipe fidelity | `docs/reading-list.md` (Methods-read gates configs) + patches/ directory (one file per mod ID, verified fresh+reverse) + mods ledger rows M-MOFLOW-1..10 |
| G12 | this doc and all replies — English ✅ |

## D. Delivery checkpoints (what "done" means, in order)

1. **D1** — MoFlow 30M r1 completes ≥1 full epoch run on Kaggle → loss curve snippet in log
   *(expect: training RUNNING = D1 in progress right now)*
2. **D2** — r1 checkpoint tar uploaded as Kaggle dataset → I pull it locally → D1 eval
3. **D3** — honest eval report: validity/novelty/uniqueness w/ + w/o correction vs reference
   numbers (§3 benchmarks.md), labeled ours-at-30M
4. **D4** — ProtGPT2: paper Methods read → UR50+rice manifests → `seqgen-ur50.yaml` locked
5. **D5** — serving layer: RFD4 container + `/v1` FastAPI with job schema (A6)
6. **D6** — §6 PPI subset run → actually EARN the public capability language
7. **D7** — workbench page renders real job trajectories (§7); SciACA patch application
   ✅ **done 2026-10-23**: applied to `aeodev/SciACA` main as PR #1 → merge `bd50977`
   (local working clone: `C:\Users\STAN\OneDrive\Documents\SciACA`; full `npm run build`
   green). No remaining user-blocking actions.
