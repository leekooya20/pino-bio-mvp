# Farm-knob spec — M-MOFLOW-3 sufficiency pass (draft 2026-10-23)

Directive (Stan, 2026-10-23): **make sure the farm-knob is ENOUGH.** This document
is the design gate for M-MOFLOW-3: what the agri conditioning head consumes, what
"enough" means measurably, and what may not be claimed until measured (G7).
No implementation touches reference training code (adds-only discipline holds).

## 1. What the farm knob currently is (and is not)

- Registered in `configs/molgen-zinc250k.yaml`: `heads: [qed, plogp, piloc-hydrophobic]`
  — an agri-directed descriptor head alongside the reference QED/logP heads.
- **NOT yet implemented or trained.** Run r1 (Molek-30M, in flight on Kaggle) is the
  faithful base replica. The knob mounts after the base exists. Status in
  `docs/capability-map.md` A4 reflects this honestly.

## 2. What "enough" must mean — three measurables (the sufficiency gate)

Steering counts as "enough" only when, on a fixed n and seed, against the
positive reference set:

1. **Region rate** — an adequately high fraction of steered generations falls inside
   the positive set's interquartile band on the steering descriptors
   (per-descriptor percentile reported; no single headline blend).
2. **Novelty preserved** — steered outputs are NOT nearest-neighbor copies of the
   positives: nearest-neighbor Tanimoto distribution vs the base model's reported
   side by side; any region-rate gain must not come from memorization.
3. **Cost honesty** — base-model validity/novelty/uniqueness reported with AND
   without correction (M-MOFLOW-4), and the *delta* from steering reported with its
   own uncorrected twin. A knob that trades validity for region-rate is reported as
   exactly that, not hidden.

Hard-fail: if region rate does not beat the unsteered base WITH novelty preserved,
the farm knob is classified "not yet enough" and the ledger says so. G7 governs.

## 3. Positive reference set — ChEBI agrochemical role tree (verified today)

| Fact | Verified value (2026-10-23) |
|---|---|
| Role root | **agrochemical = CHEBI:33286** ("substance used in agriculture or horticulture") |
| Child roles | herbicide CHEBI:24527 · insecticide CHEBI:24852 · fungicide CHEBI:24127 |
| Real molecules carry the role | glyphosate CHEBI:27744, malathion CHEBI:6651, carbendazim CHEBI:3392, … |
| Structures | ChEBI FTP SDF (2★/3★ variants; LITE has molfile+id+name+star) |
| Role resolution | ontology OWL/OBO (also mirrored on GitHub `ebi-chebi/Chebi`) |
| License | **CC BY 4.0** — verified live: GitHub `LICENSE` file, ChEBI training pages, ChEBI 2.0 continuity note |
| Registration | `configs/licenses.yaml` id `chebi-agchem` (PLANNED — manifest + sha256 written at fetch-verify time, G1) |

Use discipline: we consume **descriptor statistics** of the positives (medians
and IQR bands) plus steering targets — not bulk redistribution. Attribution ships
with any release (C5 analog adopted from the phfm governance precedent).

## 4. Descriptor panel (RDKit-computable; pruned by data, not by taste)

Candidate steering descriptors, all deterministic RDKit calls:

| Descriptor | Agrochemical rationale |
|---|---|
| cLogP (Crippen) | foliar uptake / cuticle permeability window |
| MW | formulation + systemicity constraints |
| TPSA | mobility (xylem-transportive actives are polar) |
| HBD / HBA counts | membrane + protein-interaction balance |
| rotatable bonds | conformational accessibility |
| aromatic ring count · heteroaromatic count | **halogenated heteroaromatics dominate agrochem scaffolds** |
| halogen counts (F/Cl/Br separately) | signature metabolite-stability trick of the industry |
| amine / amide / ester counts | active-class frequency drivers (carbamates, organophosphates analog structs, anilinopyrimidines, benzimidazoles) |

Pruning rule: compute all on positives; any descriptor whose positive distribution
is degenerate (IQR ≈ 0) or non-discriminative vs zinc250k background is dropped
— the panel ships with the pruning table in `run_meta`, not as a hand-picked list.

## 5. Mechanism (adds-only, reference-compatible)

1. **Head**: `piloc-hydrophobic` head regresses the descriptor vector — trained on
   RDKit-computed descriptors of zinc250k during the joint property-head pass
   (same paradigm the reference already uses for QED/logP; no new labels invented).
2. **Steer**: after Molek-30M exists, gradient moves in z toward the target
   descriptor vector = median of the ChEBI positives (same z-space optimization
   style as the reference `optimize_property.py`; our target is a *distribution
   region*, not a single-score increase).
3. **Eval**: the three sufficiency measurables above, dual M-4 reporting, fixed n,
   seed + config hash in run_meta (G10).
4. **Later arm (optional, ledgered as M-MOFLOW-11 only when its manifest exists)**:
   crop-corpus-conditioned fine-tune if steering alone proves weak. Not before.

## 6. PinoAI resources — what was taken, what doesn't exist

Scanned (Stan's authorization, read-only): `C:\PinoAI` data lanes are **PH-language
corpora + planned bio-analysis**; no molecular/agrochemical data exists there
(`corpus_sources.yaml` is the PH-Corpus register; "ploc" = local-language
Wikipedia extraction).

**Adopted by analogy — that is the real resource**: their governance machinery —
per-source license re-reading, C1 provenance (sha256 per file at fetch), C4
takedown discipline, C5 attribution-at-release. Those conventions are now binding
for the ChEBI farm-knob data per this spec and the `chebi-agchem` license entry.

## 7. Center-of-gravity honesty

- The positive set is *global* agrochemistry (ChEBI is not PH-specific); the
  Philippines-first claim lives in the eventual crop-corpus arm, not here.
- Steering is toward the **descriptor region of known agrochemicals** — NOT a claim
  of pesticidal efficacy. Efficacy language is forbidden until any §6-style
  benchmark exists (and molecule-level wet-lab claims are permanently out of scope
  for this tier, G7/G4).
- Spec status: DRAFT design gate. Nothing measured. Registered in
  `docs/capability-map.md` A4. Implementation order: after D2 checkpoint pull +
  D3 base eval, never before (G11: mount the knob on a proven base).
