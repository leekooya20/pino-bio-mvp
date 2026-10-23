# SOTA roadmap + claims ladder (PinoBio MVP-4)

Standing goal (Stan 2026-10-24): make our models SOTA. This file defines — honestly (G7)
— WHICH SOTA is achievable, WHAT it requires, and the exact metric thresholds, so every
run is aimed at it and no claim is made before it is earned.

## 1. Which SOTA we target (honest scope)

- ❌ **Broad global SOTA** (beat full-scale models at general generation): NOT achievable
  with 30M–100M models on our compute. We never claim it.
- ✅ **Narrow specialized SOTA**: *best at a defined agri-conditioned design task for a PH
  crop, measured on a fixed benchmark, wet-lab validated.* Achievable — the giants are not
  optimized for our narrow task. **Specialization + validation beats scale on a narrow
  problem.** This is our lane.
- ✅ **"Frontier in the Philippines"** (first-mover, most-advanced locally): honest + true
  once Molek has real numbers — but it is a FIRST claim, not a quality claim.

## 2. The four hard requirements to ACHIEVE SOTA

1. **Defined benchmark** — task + metric + fixed test set + baselines, ideally
   pre-registered. (Scaffolding exists: §6 PPI harness, §8 validation ladder, MOSES.)
2. **Beat baselines, measured identically** — our number ≥ published leaders on the SAME
   benchmark, with bootstrap CIs + significance test; ours never blended with served (G7).
3. **Experimental (wet-lab) validation** — turns "best on a benchmark" into undeniable
   SOTA. Needs the lab partner. In-silico-only SOTA is contestable.
4. **Open + reproducible** — public benchmark, open code, auditable numbers.

## 3. Per-model SOTA metric targets

| Model | SOTA metric | Beat |
|---|---|---|
| **Molek** (molecules) | MOSES: Validity / Uniqueness / Novelty / **FCD** / SNN / Scaffold; agri metric = "% valid+novel+agri-descriptor-in-range+synthesizable" | MOSES leaderboard (general) + our agri metric vs unconditioned Molek + MegaMolBART |
| **Seqgen** (peptides/proteins) | perplexity (own holdout); % globular (IUPred); pLDDT (ESMFold); novelty vs UniRef; for AMPs: % predicted-active + novel + foldable, then **assay hit-rate** | existing AMP generators (HydrAMP, AMP-GAN) + random |
| **Binders** (RFD4 path) | PPI **clustered pass rate**, designability (scRMSD<2Å), novelty (TM-score), diversity | RFD4 leaderboard |
| **Validation (§8)** | DockQ>0.23, RMSD<2Å, interface LDDT — honest rung (AF3 only when AF3 ran) | AF3-grade only on actual AF3 |

## 4. Claims ladder (what we may say, and when)

| Claim | Requires | Status gate |
|---|---|---|
| "First generative bio stack in PH" | any honest measured output + public stack | ~D3 |
| "Working / credible replica" | metrics in-range vs reference paper | D3 |
| "Competitive on benchmark X" | run X identically, match/beat with CIs | after running MOSES / §6 |
| "SOTA on narrow PH-agri task" | define benchmark + beat baselines (CIs) | achievable in-silico milestone |
| "Validated / real-world SOTA" | wet-lab confirmation | needs lab partner |
| "Global broad SOTA / frontier model" | frontier scale | ❌ not our game — never claim |

## 5. Enablers / gaps to close

1. **First real numbers** — Molek **D3 eval** (prerequisite for ANY SOTA talk).
2. **Benchmark + baselines** — run MOSES / §6 / §8 (built, need execution).
3. **Compute** — enough for full multi-seed evals; modest scale-up if needed to compete.
4. **Agri data moat** — local isolates / crop-specific data (from lab + IRRI).
5. **Wet-lab partner** — the hard dependency for requirement #3.

## 6. Honest sequencing

```
D3 Molek numbers → run MOSES (land vs leaders) → define narrow agri benchmark + beat
baselines (in-silico SOTA, CIs) → wet-lab validate one use case (undeniable SOTA) →
publish/reproduce → THEN claim "SOTA for PH-agri [task]"
```

## 7. The rule

SOTA is claimed ONLY on a benchmark we actually ran, measured identically to the leaders,
reported with CIs, never blended with served models' numbers — and the strongest claim
waits for wet-lab. Everything else is "first in PH" (true) or "credible replica" (true
after D3). No numbers → no SOTA talk.
