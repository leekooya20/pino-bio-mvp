"""Kaggle Seqgen-small PILOT training (crash-safe, GPU). Bounded first run to get a real
loss curve + checkpoint end-to-end. UR50 streaming (validated) -> BPE (validated) -> GPT2
from scratch (10L/d640) -> checkpoint + perplexity. HF Trainer saves every save_steps to
/kaggle/working (persists on commit; bounded 3000-step run fits one session).
"""
import os
import subprocess

subprocess.run(["bash", "-lc", "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q transformers datasets accelerate tokenizers tqdm"], check=True)

# (1) UR50 pilot stream (validated path) — 300k seqs
subprocess.run(["python", "scripts/prepare_seqgen_pilot.py", "--n", "300000"], check=True)

# (2) BPE tokenizer (validated 10k vocab / 100k-seq cap)
os.environ["SEQGEN_TRAIN_FA"] = "/kaggle/pino-bio-mvp/data/external/uniref50_pilot/ur50_pilot.train.fasta"
os.environ["SEQGEN_VOCAB"] = "10000"
os.environ["SEQGEN_BPE_MAXSEQ"] = "100000"
subprocess.run(["python", "scripts/train_bpe_seqgen.py"], check=True)

# (3) GPT2 pilot train from scratch (crash-safe saves every 500 steps)
os.environ["SEQGEN_OUT"] = "/kaggle/working/seqgen-small"
subprocess.run(["python", "scripts/train_seqgen.py",
                "--tokenizer", "/kaggle/pino-bio-mvp/artifacts/seqgen-tokenizer/tokenizer.json",
                "--max_steps", "3000", "--save_steps", "500"], check=True)

# (4) persist
subprocess.run(["bash", "-lc", """
echo '--- seqgen run_meta ---'; cat /kaggle/working/seqgen-small/run_meta.json 2>/dev/null
ls -lh /kaggle/working/seqgen-small
"""], check=False)
