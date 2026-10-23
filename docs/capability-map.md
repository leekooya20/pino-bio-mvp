# Capability map — "make sure we can deliver ALL of it" (G-blocking register)

Answer to Stan's directive (2026-10-23): every capability promised on `site/pinobio-gend.html`
and in `docs/benchmarks.md` (§6/§7/§8), mapped to **what exists today**, what blocks it, and
**which hard rule (G1–G11) it must survive**. Updated as things ship; statuses are honest.

Reproducibility trio at bottom: seed `20261023` · config `a1288cc8…` · pinned
`moflow@3611c6372602` / `moses@dd7ed6ab38e2` — every row below inherits them (G3/G10).

---

## A. The six "It does" capabilities (GenD page)

| # | Capability | Status (2026-10-23) | Blocks / next concrete artifact | Hard-rule gate |
|---|---|---|---|---|
| A1 | **Generate novel molecular graphs** (MoFlow replica @30M) | 🟡 **in training** — pipeline fully green through preflight (29,049,444 params), epochs running on Kaggle r1 | first `eval_summary.json` w/ corrected+uncorrected (M-MOFLOW-4) | G3/G7 (frozen harness = reference generate.py + MOSES metrics), G10 ✅ |
| A2 | **Generate novel protein sequences** (ProtGPT2-small replica) | 🟠 next — tokenizer + UR50 manifest to build; 3 paper OPEN items gate the config (`docs/reading-list.md`) | `configs/seqgen-ur50.yaml` locked ONLY after Ferruz-2022 Methods read | G11 (no config before Methods read), G1 (UniRef50 entry exists ✅) |
| A3 | **Design binders/backbones** (RFD4-Proteina served) | 🟠 planned Phase-3 — license ✅ BSD-3 (GitHub API 2026-10-23), serving constraint recorded (py3.12 container ≠ Kaggle 3.13) | pinned container + 1-condition integration acceptance in `docs/06-serving-release.md` terms | G4 (capability tier gated by §6 PPI bench BEFORE public claims), G1/BSD-3 ✅ |
| A4 | **Optimize toward target properties** (M-MOFLOW-3 PH-agri head) | 🟠 after A1 baseline — head is config-registered; needs a trained base latents | conditioned `optimize-property` run vs baseline property deltas | G3/G7 (reported as ours w/ config hash), M-MOFLOW-3 ledger row ✅ |
| A5 | **Inverse-fold / structured redesign** (served tool path) | 🟠 Phase-3, behind A3 | same containers as A3 + job schema | G4 gate shared with A3 |
| A6 | **Generate→screen→optimize loop as /v1 jobs** | 🟢 wired by design — `specs/orchestrator.md` §10–11 contract drafted (tasks→tools incl. `mol.generate`, `seq.generate`, `design.backbone`), SciACA patch ready to apply | FastAPI implementation in this repo after A1 returns | G8 (no secrets in code — demo fallback pattern ✅), G6 (files only in allowed dirs ✅) |

## B. The "later board" (benchmarks.md)

| Item | Deliverable that makes it real | Rule gate |
|---|---|---|
| §6 PPI benchmark | fixed targets (rows+hashes), 200-attempt budget, clustered pass rate, **refold ladder ESMFold→Boltz-2→Chai** (honest "not-AF3"), comparison table ours-vs-theirs | G7 (failures reported, no rounding), G4 (this IS the public-claim gate) |
| §7 trajectory workbench | `/v1` job artifacts record per-stage snapshots; workbench page renders them; `reasoning_depth` + `search_criteria` passthrough | G9 (scope: generator tier only — no analysis heads invented), G4 |
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
7. **D7** — workbench page renders real job trajectories (§7) → SciACA patch application
   (waiting on Stan's apply-or-clone decision — the only user-blocked item)
