#!/usr/bin/env python
"""BPE tokenizer trainer for Seqgen-small (ProtGPT2 replica, G10/G11).

Reference (G11, docs/reading-list.md): ProtGPT2 tokenizes with a BPE algorithm
(Gage) over the UniRef50 amino-acid alphabet (25 letters incl. X/B/U/O/Z), with
sequences delimited by <|endoftext|>. We learn the BPE on OUR subsample
(P-PTGPT2-2) and record vocab size + tokenizer.json sha256 (G10) so the exact
tokenizer is reproducible.

No blind copy: we keep the reference tokenization family and special token, and
document the single deviation (BPE trained on our subsample, not the full corpus).
Requires `tokenizers` (HF). Run after prepare_seqgen_data.py.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import os as _os
TRAIN_FA = Path(_os.environ.get(
    "SEQGEN_TRAIN_FA",
    str(ROOT / "data" / "external" / "uniref50_2021_04" / "ur50_subsample.train.fasta")))
OUT_DIR = ROOT / "artifacts" / "seqgen-tokenizer"
EOS = "<|endoftext|>"              # [REF] sequence delimiter used by ProtGPT2
VOCAB_SIZE = 50_000               # target; realized size recorded in run_meta (G7)


def iter_sequences(path: Path):
    seq: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith(">"):
                if seq:
                    yield "".join(seq)
                    seq = []
            else:
                seq.append(line.strip())
        if seq:
            yield "".join(seq)


def main() -> int:
    try:
        from tokenizers import Tokenizer, models, trainers, pre_tokenizers
    except ImportError:
        print("need `pip install tokenizers` (HF) — not bundled here.", file=sys.stderr)
        return 3
    if not TRAIN_FA.exists():
        print(f"missing {TRAIN_FA}; run scripts/prepare_seqgen_data.py first.", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    trainer = trainers.BpeTrainer(
        vocab_size=VOCAB_SIZE,
        special_tokens=[EOS, "<unk>"],
        show_progress=True,
    )
    print(f"training BPE on {TRAIN_FA} (target vocab {VOCAB_SIZE:,}) ...")
    tok.train_from_iterator(iter_sequences(TRAIN_FA), trainer=trainer)
    out = OUT_DIR / "tokenizer.json"
    tok.save(str(out))

    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    realized = tok.get_vocab_size()
    meta = {
        "stage": "seqgen-tokenizer",
        "algorithm": "bpe",
        "trained_on": str(TRAIN_FA),
        "special_tokens": [EOS, "<unk>"],
        "target_vocab": VOCAB_SIZE,
        "realized_vocab": realized,       # G7: record what was actually produced
        "tokenizer_sha256": sha,
        "mods": ["P-PTGPT2-2 BPE learned on our subsample (ref learned on full corpus)"],
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (OUT_DIR / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"ok  tokenizer -> {out} (vocab {realized:,}, sha256 {sha[:12]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
