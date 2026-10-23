# §8 AF3-grade validation ladder (PinoBio MVP-4)

The honest structure-validation layer behind any binder/design claim. Mirrors the
AlphaFold3 evaluation (Abramson et al., Nature 2024, Fig-1 metric family) — but is
scrupulous about WHICH refold oracle produced the numbers.

Registered: `docs/benchmarks.md` §8.

## The rung ladder (honest labels, G7/G4)

| Rung | Oracle | License | af3? |
|---|---|---|---|
| 0 | **ESMFold** | MIT | false |
| 1 | **Boltz-2** | MIT | false |
| 2 | **Chai-1** | Apache-2.0 (verify at use) | false |
| 3 | **AlphaFold3** | access-gated (Abramson 2024) | **true** |

The driver uses the **best available** rung and records it. A report is `af3: true`
ONLY when AF3 actually produced it — nothing below AF3 is ever labelled AF3-grade.

## Metrics (Fig-1 family)

- **RMSD** (Kabsch-superposed Cα) — sub-2Å = well-folded.
- **interface LDDT** (iLDDT) — local contacts across the interface.
- **DockQ** (Basu & Wallner 2016) — composite of Fnat / iRMS / LRMS; CAPRI-acceptable
  ≥ 0.23. Computed exactly from components (tested).
- confidence carry-through (pLDDT / pTM / ipTM) from the oracle.

## Statistics (G7)

- **Multi-seed** sampling per design; report best + mean (never cherry-pick one seed).
- **Bootstrap CIs** on pass rates; **paired Wilcoxon** for A/B arms.
- Failures counted and reported; our numbers never blended with served-oracle numbers.

## Honesty contract

- No fabricated structures or scores: if no oracle rung is available, the run writes
  `status: "blocked"` with no metrics.
- Public "AF3-grade" language is earned only by an actual AF3 rung; every other rung is
  labelled as itself (e.g. "ESMFold-validated, NOT AF3").

## Files

- `metrics.py` — DockQ (exact), RMSD (Kabsch), CAPRI/RMSD classifiers, bootstrap, Wilcoxon.
- `ladder.py` — rung registry + best-available selection + honest labels.
- `run_validation.py` — multi-seed driver over `/v1` fold rungs → honest report.
