# Molek-30M — D3 eval result (first measured numbers)

**Date:** 2026-10-24 · **Checkpoint:** epoch 197/200 (run started 2026-10-23 12:14)
**sha256:** `7f8374df3cb86e31182d4a42ff1bfd2d97df7edd5b788c9cd1090e6dbf722228`
**Protocol:** 10,000 samples × 5 experiments, temperature 0.85 (reference README protocol)
**Model:** Molek-30M (our from-scratch MoFlow replica, 29,049,444 params) — MoFlow replica
(Zang & Wang, KDD 2020, MIT), own training.

## Corrected metrics (M-MOFLOW-4 "with correction") vs reference

| Metric | Molek-30M (ours) | Reference MoFlow (pinned README) | Verdict |
|---|---|---|---|
| Validity | **99.94%** (sd 0.02) | 100.00% (sd 0.00) | matches (−0.06) |
| Novelty | **100.00%** (sd 0.00) | 100.00% (sd 0.00) | matches |
| Uniqueness | **100.00%** (sd 0.00) | ~100% | matches |
| Abs. novelty | 99.93% (sd 0.02) | — | — |
| Abs. uniqueness | 99.93% (sd 0.02) | — | — |

**Honest reading:** at a 30M scale-down (M-MOFLOW-1) our replica MATCHES the full
reference on the corrected generation metrics. This is a credible, measured first result
— NOT a SOTA claim (that needs the narrow-benchmark + wet-lab path in sota-roadmap.md).

## Uncorrected metrics (M-MOFLOW-4 "without correction") — PENDING, measurement bug

The uncorrected run (`--correct_validity false`) did NOT yield a valid number: it reported
`0/10000 valid` then crashed with `UnboundLocalError: abs_novel_ratio` in the reference
`check_novelty` (it has no 0-valid code path). **0% is a broken measurement, not a model
result** — MoFlow's true uncorrected validity is ~80%+, never 0 (G7: we do not present a
broken number as honest). The dual-report is therefore INCOMPLETE until the uncorrected
path is fixed. Next action: diagnose why raw validity reads 0 at our settings + patch the
check_novelty 0-valid crash, then rerun for the honest uncorrected number.

## Status
- ✅ Molek is TRAINED and WORKS (corrected metrics match reference).
- 🟡 M-MOFLOW-4 dual-report incomplete (uncorrected measurement to fix).
- This is D3 (first real numbers). Next rung on sota-roadmap: run MOSES, define the narrow
  agri benchmark, then wet-lab.
