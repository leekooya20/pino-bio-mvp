# Molek-30M — distributional metrics (rung 2)

**Date:** 2026-10-24 · **Checkpoint:** epoch 197 · **n_gen:** 30,000 · temp 0.85
**Reference:** zinc250k test split (NOT the MOSES benchmark — Molek trained on zinc250k)
**Tools:** FCD via `fcd_torch` (= the MOSES FCD metric); IntDiv/SNN via RDKit.

## Results

| Metric | Value | Direction | Reading |
|---|---|---|---|
| **FCD/Test** | **23.40** | lower better | ⚠️ HIGH — poor distributional match (good models are single-digit/sub-1) |
| **SNN/Test** | **0.196** | higher better | ⚠️ LOW — generations far from nearest real molecule |
| **IntDiv** | 0.908 | higher better | ✅ high diversity (no mode collapse) |
| **IntDiv2** | 0.900 | higher better | ✅ high diversity |

## Honest interpretation (G7)

D3 corrected metrics were near-perfect (validity 99.95% / novelty 100% / uniqueness
99.99%). These distributional metrics tell the fuller, less flattering story:
**Molek generates valid, novel, diverse molecules that are distributionally FAR from real
zinc chemistry** (high FCD, low SNN). **Validity ≠ distributional quality.**

**Leading hypothesis:** MoFlow's validity-correction (`correct_mol`) fixes valency by
altering structures → pushes molecules off the real distribution. Known MoFlow trade-off
(correction buys validity at distributional cost). Consistent with uncorrected 0% +
corrected 99.95% + high FCD.

## Caveats / next verification (G14)
- Our generations are CORRECTED; correction-distortion likely inflates FCD. A clean FCD on
  uncorrected generations isn't possible here (uncorrected = 0 valid). 
- Possible canonicalization mismatch between generated SMILES and zinc250k.csv reference
  could add noise (same caveat class as the D3 novelty note).
- **To pin it down:** obtain MoFlow's OWN FCD baseline on zinc250k (reference number) to
  compare apples-to-apples; our 23.40 is only meaningful against that baseline.
- Diversity (IntDiv ~0.90) is genuinely strong and NOT distorted by this.

## Status
- ✅ Rung 2 measured (FCD/SNN/IntDiv). Honest mixed picture: perfect validity, strong
  diversity, POOR distributional fidelity.
- This is the number that keeps the eventual SOTA claim honest. Do NOT claim
  distributional/quality SOTA — FCD says otherwise right now.
- Next: get MoFlow's reference FCD for comparison; investigate correction-distortion.
