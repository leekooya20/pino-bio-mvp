# Seqgen-small — training plan + feasibility (senior-engineer scope, 2026-10-24)

Second owned from-scratch model (ProtGPT2 replica). Goal: reach the same
"trained + measured" bar as Molek, HONESTLY scoped to our compute.

## 1. Feasibility verdict (why a pilot, not a faithful replica)

| | Reference ProtGPT2 | Seqgen-small (ours) |
|---|---|---|
| Params | 738M (36L, d1280) | ~66–85M (10L, d640, 10H) |
| Compute | 128×A100 × 4 days | 1× Kaggle T4, ≤12h/session |
| Data | UR50 2021_04, 49.87M seqs, ~billions of tokens | UR50 subsample, ~0.5–1B tokens (pilot) |

A faithful replica is **impossible** on a T4 (≈3-4 orders of magnitude less compute). So
Seqgen-small is an honest **pilot** — a genuinely-trained small protein LM, labelled as
such (never claimed as "ProtGPT2-equivalent"). Same honesty posture as Molek = "MoFlow@30M".

## 2. Config is principled (external validation, G14)

NeurIPS 2024 *Training Compute-Optimal Protein LMs* param table includes **66M: d_model
640, head_num 10, layers 10** — matching our `configs/seqgen-ur50.yaml` (n_embd 640,
n_head 10, n_layer 10). Our scale-down sits on a published compute-optimal point, not a
guess. P-PTGPT2-1 is sound.

## 3. Pilot training budget (one crash-safe T4 session)

- Model ~66–85M, block 512, fp16, grad-accum to the reference 65,536 tokens/batch (P-1/2).
- T4 throughput ≈ 15–25k tok/s → ~0.5–0.9B tokens in one ≤12h session.
- That is a real pilot (pretrain signal + usable checkpoint + loss curve), not full
  convergence. Scale over multiple sessions via resume if the pilot is healthy.

## 4. Data sourcing (the real gate)

- Source: UniProt previous-releases `release-2021_04/uniref/uniref50/uniref50.fasta.gz`
  (G11-faithful version). Full file is multi-GB — we do NOT need all 49.9M seqs for a pilot.
- **Streaming early-stop subsample:** stream the gz, decompress on the fly, collect ~1–2M
  sequences (P-PTGPT2-2 curriculum), STOP — avoids downloading tens of GB. (Upgrade to
  `prepare_seqgen_data.py` for the pilot.)
- G1: license gate already in `prepare_seqgen_data.py` (live UniProt check before any read).
- BPE tokenizer trained on the subsample (`train_bpe_seqgen.py`, P-PTGPT2-2).

## 5. Crash-safety FROM THE START (apply Molek lesson F-0015)

Unlike Molek run #7, Seqgen uses M-MOFLOW-12 pattern from day one: per-epoch/step
checkpoints written to a persistent dir + pushed to a Kaggle Dataset, so a ceiling-cut
never loses progress and resume is clean. No "10h-at-risk" repeat.

## 6. Eval plan (honest, M-MOFLOW-4 / F-0008 lessons)

- **Perplexity** on our own held-out split — reported STAND-ALONE (ProtGPT2 published no
  numeric ppl, F-0008; nothing to compare against — no false "matches ProtGPT2 ppl").
- **Generation sanity:** % parseable sequences, length distribution, aa-propensity vs
  natural (ProtGPT2's own check).
- **Novelty gate (P-PTGPT2-3):** ESM-2 embedding novelty + BLAST-vs-UniRef (anti-memorization).
- **Structure (later):** %globular (IUPred), ESMFold pLDDT distribution — the §8 ladder.

## 7. Execution order (isa-isahin)

1. Upgrade `prepare_seqgen_data.py` → streaming early-stop subsample (pilot-tractable).
2. Build crash-safe Seqgen training Kaggle kernel (M-12 pattern) + BPE step.
3. Run data-prep + BPE (validate data path, license gate, tokenizer).
4. Pilot train (one session, crash-safe) → first loss curve + checkpoint.
5. Eval: perplexity (own holdout) + generation sanity → "Seqgen-small pilot" result.
6. Scale via resume if healthy; wire into `/v1` seq.generate.

## Honesty banner
Seqgen-small is a PILOT (compute-optimal 66M config, UR50 subsample, ~1B tokens) — a real
trained protein LM, NOT a ProtGPT2-equivalent. Every number reported stand-alone + honest.
