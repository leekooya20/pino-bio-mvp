# CLAUDE.md — agent rules for this repo (subset + pointers to the master)

Master contract: `Default Project/CLAUDE.md` (G1–G12). Read it first. The subset below is
binding inside **pino-bio-mvp**:

- **G12 (communication):** always answer in English, even if the team writes in Taglish.
- **Agent split (Demeter):** this repo is the GENERATIVE tier (PinoAI-GenD). Coordination
  with the analysis agent (PinoAI/phfm, design-by-construction-banned) goes through
  `Default Project/docs/10-agent-handshake.md` — never edit their repo, never touch
  their ledger/sphere. Capability split is final: we generate/design/optimize; they
  embed/score/screen.

- **G1** No dataset/script enters a run without a `configs/licenses.yaml` entry (this repo mirrors the master — keep in sync).
- **G3** No training without the frozen eval harness (fixture: reconstruction == 100% for MoFlow — the reference's own invariant, G11-verified).
- **G7** Report eval misses honestly. Never round up benchmark numbers.
- **G10** Every run writes `artifacts/<run>/run_meta.json` (seed, config hash, data version pin, third_party SHA).
- **G11** Recipe fidelity: read real recipe + full code + process + benchmarks BEFORE replicating. Deltas are documented modification IDs (M-*/P-*), applied as patches — never silent, never a blind copy.
- **G13 (findings, Stan 2026-10-23):** every finding / observation / unexpected behavior — rare, anomalous, undocumented, or "strange but it worked" — MUST be recorded in `docs/findings-log.md` the moment it is noticed. Date, context, evidence pointer, impact. No silent discoveries; retroactive seeding is allowed only at registration time. Applies during runs, evals, fetches, docs work — everything. **Especially binding on model training runs:** the run log is fetched the instant a run terminates and every epoch milestone, loss anomaly, spike, NaN, timing oddity, or silent restart it shows gets its own findings entry.
- **G14 (research-before-execute, Stan 2026-10-24):** when an action, approach, or claim
  carries uncertainty, CONDUCT RESEARCH FIRST (papers, docs, licenses, prior art,
  benchmarks, landscape) to verify it is correct BEFORE executing. Verify, don't assume.
  Extends G11 (recipe read before replication) to every significant decision. If research
  shows the plan is wrong, correct it and note why (findings log).
- Scope: MVP-4 only (moflow, protgpt2-small, rfd4 serve, esm2 serve)
  **+ (scope addition, Stan-authorized 2026-10-23) Pinal served (text→protein, Apache-2.0,
  SERVE-first — never from-scratch; G9 honored by serving).**
  **+ (scope addition, Stan-authorized 2026-10-23) OWNED NLP intent layer (A8): frozen
  open text encoder + OUR trained projection heads → Molek/Seqgen; owned adapter, tiny,
  never a from-scratch large model (G9). Spec docs/nlp-intent-spec.md.** + SciACA /v1 compat per Katala specs §10–11. Do not invent new domains here.

If a task would violate a rule → STOP, write `BLOCKED.md`.
