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
- Scope: MVP-4 only (moflow, protgpt2-small, rfd4 serve, esm2 serve) + SciACA /v1 compat per Katala specs §10–11. Do not invent new domains here.

If a task would violate a rule → STOP, write `BLOCKED.md`.
