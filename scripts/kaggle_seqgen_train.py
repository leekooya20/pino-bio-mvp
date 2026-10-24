"""Kaggle Seqgen-small PILOT training kernel (GPU). Crash-safe from the start.

Stream UR50 pilot -> BPE tokenizer -> GPT-2 (66M-class) CLM training -> checkpoint + ppl.
Honest pilot (docs/seqgen-plan.md): genuinely-trained small protein LM, not a ProtGPT2
replica. ~2-3h; HF Trainer save_steps = crash-safe; outputs to /kaggle/working.
"""
import os
import subprocess

subprocess.run(["bash", "-lc", "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q transformers datasets tokenizers accelerate tqdm"], check=True)

# 1) stream UR50 pilot corpus (early-stop; ~800k seqs)
subprocess.run(["python", "scripts/prepare_seqgen_pilot.py", "--n", "800000"], check=True)

# 2) BPE tokenizer (fast: 8k vocab on 50k-seq sample)
env = dict(os.environ, SEQGEN_TRAIN_FA="/kaggle/pino-bio-mvp/data/external/uniref50_pilot/ur50_pilot.train.fasta",
           SEQGEN_VOCAB="8000", SEQGEN_BPE_MAXSEQ="50000")
subprocess.run(["python", "scripts/train_bpe_seqgen.py"], check=True, env=env)

# 3) GPT-2 pilot training (crash-safe; capped steps for one session)
env2 = dict(os.environ,
            SEQGEN_TRAIN_FA="/kaggle/pino-bio-mvp/data/external/uniref50_pilot/ur50_pilot.train.fasta",
            SEQGEN_EVAL_FA="/kaggle/pino-bio-mvp/data/external/uniref50_pilot/ur50_pilot.eval.fasta",
            SEQGEN_TOKENIZER="/kaggle/pino-bio-mvp/artifacts/seqgen-tokenizer/tokenizer.json",
            SEQGEN_OUT="/kaggle/working/seqgen-small",
            SEQGEN_MAX_STEPS="2000", SEQGEN_MAX_TRAIN_SEQ="300000")
rc = subprocess.run(["python", "scripts/train_seqgen.py"], env=env2)
print("seqgen train exit:", rc.returncode)

# 4) show result
subprocess.run(["bash", "-lc", "cat /kaggle/working/seqgen-small/run_meta.json 2>/dev/null; ls -lh /kaggle/working/seqgen-small"], check=False)
