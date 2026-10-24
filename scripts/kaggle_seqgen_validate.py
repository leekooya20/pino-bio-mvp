"""Kaggle VALIDATION kernel — Seqgen pilot data streaming + BPE tokenizer (de-risk).

Senior-engineer de-risk step (Molek lesson: validate stages before the expensive run).
Confirms: (1) UR50 streaming early-stop works on Kaggle, (2) BPE tokenizer trains on the
pilot corpus. Small N for speed; scale up for the real pilot train after this is green.
Outputs counts + realized vocab to /kaggle/working.
"""
import os
import subprocess

subprocess.run(["bash", "-lc", "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q tokenizers tqdm"], check=True)

# (1) stream a small UR50 subsample (validation N; the real pilot uses ~1.5M)
subprocess.run(["python", "scripts/prepare_seqgen_pilot.py", "--n", "300000"], check=True)

# (2) train BPE on the streamed pilot train split
os.environ["SEQGEN_TRAIN_FA"] = "/kaggle/pino-bio-mvp/data/external/uniref50_pilot/ur50_pilot.train.fasta"
subprocess.run(["python", "scripts/train_bpe_seqgen.py"], check=True)

# (3) persist validation evidence
subprocess.run(["bash", "-lc", """
mkdir -p /kaggle/working/seqgen
cp -r data/manifests/uniref50-pilot.jsonl /kaggle/working/seqgen/ 2>/dev/null || true
cp -r artifacts/seqgen-tokenizer/run_meta.json /kaggle/working/seqgen/tokenizer_meta.json 2>/dev/null || true
cp -r artifacts/seqgen-data/pilot_run_meta.json /kaggle/working/seqgen/ 2>/dev/null || true
echo '--- pilot data manifest ---'; cat /kaggle/working/seqgen/uniref50-pilot.jsonl 2>/dev/null
echo '--- tokenizer meta ---'; cat /kaggle/working/seqgen/tokenizer_meta.json 2>/dev/null
ls -lh /kaggle/working/seqgen
"""], check=False)
