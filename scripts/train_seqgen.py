#!/usr/bin/env python
"""Seqgen-small PILOT trainer — GPT2-style protein LM from scratch (ProtGPT2 replica).

Senior-engineer scope: a bounded first pilot to prove end-to-end training + get a real
loss curve and checkpoint (NOT full convergence). Config from configs/seqgen-ur50.yaml
(validated vs NeurIPS-2024 compute-optimal 66M point: d640/10H/10L). Crash-safe from the
start (F-0015 lesson): HF Trainer saves every save_steps to a persistent dir.

Honest (G7): pilot on a UR50 subsample, ~thousands of steps — labelled a pilot, not a
faithful ProtGPT2. Perplexity reported STAND-ALONE (ProtGPT2 published none, F-0008).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_fa", default=str(ROOT / "data/external/uniref50_pilot/ur50_pilot.train.fasta"))
    ap.add_argument("--eval_fa", default=str(ROOT / "data/external/uniref50_pilot/ur50_pilot.eval.fasta"))
    ap.add_argument("--tokenizer", default=str(ROOT / "artifacts/seqgen-tokenizer/tokenizer.json"))
    ap.add_argument("--out", default=os.environ.get("SEQGEN_OUT", "/kaggle/working/seqgen-small"))
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--max_steps", type=int, default=int(os.environ.get("SEQGEN_MAX_STEPS", 3000)))
    ap.add_argument("--save_steps", type=int, default=500)
    ap.add_argument("--bsz", type=int, default=8)
    ap.add_argument("--grad_accum", type=int, default=8)
    # F-0036: cap sequences fed into the in-RAM block builder (OOM fix). A bounded pilot
    # needs ~max_steps * bsz * grad_accum * block tokens; 150k seqs covers 3000 steps.
    ap.add_argument("--max_seqs", type=int, default=int(os.environ.get("SEQGEN_MAX_SEQS", 150000)))
    args = ap.parse_args()

    import gc

    import numpy as np
    import torch
    from tokenizers import Tokenizer
    from transformers import (DataCollatorForLanguageModeling, GPT2Config, GPT2LMHeadModel,
                              PreTrainedTokenizerFast, Trainer, TrainingArguments)
    from datasets import Dataset

    # tokenizer (from the validated BPE tokenizer.json)
    tok = PreTrainedTokenizerFast(tokenizer_object=Tokenizer.from_file(args.tokenizer),
                                  eos_token="<|endoftext|>", unk_token="<unk>",
                                  pad_token="<|endoftext|>")
    vocab = tok.vocab_size
    print(f"[seqgen] tokenizer vocab {vocab}")

    def read_seqs(path):
        seq, out = [], []
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith(">"):
                    if seq:
                        out.append("".join(seq) + "<|endoftext|>"); seq = []
                else:
                    seq.append(line.strip())
        if seq:
            out.append("".join(seq) + "<|endoftext|>")
        return out

    def tokenize_blocks(seqs):
        # Flat token stream -> fixed blocks, stored as ONE compact int32 array (not a list of
        # python-int lists) and WITHOUT a labels copy (the collator derives labels). F-0036 OOM fix.
        flat = []
        for s in seqs:
            flat.extend(tok(s, add_special_tokens=False)["input_ids"])
        n = (len(flat) // args.block) * args.block
        arr = np.asarray(flat[:n], dtype=np.int32).reshape(-1, args.block)
        del flat
        gc.collect()
        return Dataset.from_dict({"input_ids": arr})

    print(f"[seqgen] tokenizing train (cap {args.max_seqs:,} seqs) / eval ...")
    train_ds = tokenize_blocks(read_seqs(args.train_fa)[: args.max_seqs])
    eval_ds = tokenize_blocks(read_seqs(args.eval_fa)[:5000])
    collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)  # labels on the fly
    print(f"[seqgen] train blocks {len(train_ds)} eval blocks {len(eval_ds)}")

    # config from configs/seqgen-ur50.yaml (P-PTGPT2-1): 10L / d640 / 10H
    cfg = GPT2Config(vocab_size=vocab, n_positions=args.block, n_embd=640, n_layer=10,
                     n_head=10, bos_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id)
    model = GPT2LMHeadModel(cfg)
    nparams = sum(p.numel() for p in model.parameters())
    print(f"[seqgen] params {nparams:,} (budget <=100M: {'OK' if nparams <= 100_000_000 else 'FAIL'})")
    assert nparams <= 100_000_000, "P-PTGPT2-1 budget exceeded"

    targs = TrainingArguments(
        output_dir=args.out, max_steps=args.max_steps,
        per_device_train_batch_size=args.bsz, gradient_accumulation_steps=args.grad_accum,
        learning_rate=1e-3, lr_scheduler_type="constant", warmup_steps=0,  # [REF] F-0009
        fp16=torch.cuda.is_available(), logging_steps=50,
        save_steps=args.save_steps, save_total_limit=3,          # crash-safe
        eval_strategy="steps", eval_steps=args.save_steps,
        report_to=[], seed=20261023, dataloader_num_workers=2,
    )
    trainer = Trainer(model=model, args=targs, train_dataset=train_ds, eval_dataset=eval_ds,
                      data_collator=collator)
    t0 = time.time()
    trainer.train()
    metrics = trainer.evaluate()
    ppl = math.exp(metrics["eval_loss"]) if "eval_loss" in metrics else None
    trainer.save_model(args.out)
    tok.save_pretrained(args.out)

    run_meta = {"stage": "seqgen-pilot-train", "model": "seqgen-small",
                "params": nparams, "vocab": vocab, "block": args.block,
                "max_steps": args.max_steps, "max_seqs": args.max_seqs, "seed": 20261023,
                "eval_loss": metrics.get("eval_loss"),
                "perplexity_standalone": ppl,  # F-0008: no reference ppl to compare
                "compare_to_reference_ppl": False,
                "train_blocks": len(train_ds), "wall_s": round(time.time() - t0, 1),
                "note": "PILOT: UR50 subsample, bounded steps; not a faithful ProtGPT2.",
                "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    Path(args.out, "run_meta.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    print("[seqgen] DONE", json.dumps(run_meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
