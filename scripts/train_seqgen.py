#!/usr/bin/env python
"""Seqgen-small PILOT trainer — GPT-2 (decoder) from scratch on the streamed UR50 pilot
corpus, crash-safe from the start (F-0015 lesson applied). PinoBio MVP-4.

Honest scope (docs/seqgen-plan.md): a faithful ProtGPT2 is infeasible on a T4, so this is a
PILOT — a genuinely-trained small protein LM (≤100M, compute-optimal 66M-class config),
labelled as such. Config validated vs NeurIPS 2024 compute-optimal table.

G10: seed + config hash + tokens-seen in run_meta. G11: GPT-2 arch + run_clm-style CLM,
BPE + <|endoftext|> delimiter (reference faithful); P-PTGPT2-1/2 deviations documented.
Crash-safe: HF Trainer save_steps -> /kaggle/working + (optional) dataset push.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAIN_FA = Path(os.environ.get("SEQGEN_TRAIN_FA",
                               str(ROOT / "data" / "external" / "uniref50_pilot" / "ur50_pilot.train.fasta")))
EVAL_FA = Path(os.environ.get("SEQGEN_EVAL_FA",
                              str(ROOT / "data" / "external" / "uniref50_pilot" / "ur50_pilot.eval.fasta")))
TOKENIZER = Path(os.environ.get("SEQGEN_TOKENIZER",
                                str(ROOT / "artifacts" / "seqgen-tokenizer" / "tokenizer.json")))
OUT = Path(os.environ.get("SEQGEN_OUT", str(ROOT / "artifacts" / "seqgen-small")))
BLOCK = 512
SEED = 20261023
MAX_STEPS = int(os.environ.get("SEQGEN_MAX_STEPS", 4000))   # pilot budget (fits one session)
MAX_TRAIN_SEQ = int(os.environ.get("SEQGEN_MAX_TRAIN_SEQ", 200_000))


def iter_seqs(path: Path, cap: int | None = None):
    seq, n = [], 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith(">"):
                if seq:
                    yield "".join(seq); seq = []; n += 1
                    if cap and n >= cap:
                        return
            else:
                seq.append(line.strip())
        if seq:
            yield "".join(seq)


def main() -> int:
    import torch
    from tokenizers import Tokenizer
    from transformers import (GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast,
                              Trainer, TrainingArguments)
    from datasets import Dataset

    if not TOKENIZER.exists():
        print(f"missing tokenizer {TOKENIZER}; run data prep + train_bpe first.", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)

    tok = PreTrainedTokenizerFast(tokenizer_object=Tokenizer.from_file(str(TOKENIZER)),
                                  eos_token="<|endoftext|>", unk_token="<unk>",
                                  pad_token="<|endoftext|>")
    vocab = tok.vocab_size
    cfg = GPT2Config(vocab_size=vocab, n_positions=BLOCK, n_ctx=BLOCK,
                     n_embd=640, n_layer=10, n_head=10, bos_token_id=tok.eos_token_id,
                     eos_token_id=tok.eos_token_id)
    model = GPT2LMHeadModel(cfg)
    nparams = sum(p.numel() for p in model.parameters())
    print(f"[P-PTGPT2-1] params: {nparams:,}")
    assert nparams <= 100_000_000, f"param budget exceeded: {nparams:,} > 100M"

    # tokenize + pack into BLOCK-size windows (CLM), EOS between sequences
    def build(path, cap):
        ids = []
        for s in iter_seqs(path, cap):
            ids.extend(tok.encode(s) + [tok.eos_token_id])
        blocks = [ids[i:i + BLOCK] for i in range(0, len(ids) - BLOCK, BLOCK)]
        return Dataset.from_dict({"input_ids": blocks, "labels": [b[:] for b in blocks]})

    print("tokenizing + packing ...")
    train_ds = build(TRAIN_FA, MAX_TRAIN_SEQ)
    eval_ds = build(EVAL_FA, 5_000)
    print(f"[data] train blocks {len(train_ds)} eval blocks {len(eval_ds)} (block {BLOCK})")

    args = TrainingArguments(
        output_dir=str(OUT), overwrite_output_dir=True, seed=SEED,
        per_device_train_batch_size=8, gradient_accumulation_steps=16,   # ~65k tokens/batch [REF]
        learning_rate=1e-3, lr_scheduler_type="constant", warmup_steps=0,  # [REF] F-0009
        max_steps=MAX_STEPS, logging_steps=50,
        save_steps=500, save_total_limit=3,     # crash-safe (F-0015)
        eval_strategy="steps", eval_steps=1000,
        fp16=torch.cuda.is_available(), report_to=[],
    )
    trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds)
    t0 = time.time()
    trainer.train()
    model.save_pretrained(OUT); tok.save_pretrained(OUT)

    ev = trainer.evaluate()
    import math
    ppl = math.exp(ev["eval_loss"]) if "eval_loss" in ev else None
    cfg_hash = hashlib.sha256(json.dumps(cfg.to_dict(), sort_keys=True).encode()).hexdigest()[:12]
    (OUT / "run_meta.json").write_text(json.dumps({
        "stage": "seqgen-small-pilot", "params": nparams, "vocab": vocab, "block": BLOCK,
        "seed": SEED, "config_hash": cfg_hash, "max_steps": MAX_STEPS,
        "train_blocks": len(train_ds), "eval_loss": ev.get("eval_loss"),
        "eval_perplexity_standalone": ppl,  # F-0008: ref published no ppl -> stand-alone only
        "elapsed_s": round(time.time() - t0, 1),
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, indent=2), encoding="utf-8")
    print(f"[seqgen] done. eval_loss={ev.get('eval_loss')} ppl(standalone)={ppl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
