"""Kaggle eval runner for Molek-30M — D3 (PinoBio MVP-4).

Loads the recovered epoch-197 checkpoint (attached dataset leexze/molek-30m-ckpt),
rebuilds the data pipeline + moflow-params.json, and runs the HONEST eval
(M-MOFLOW-4: validity/novelty/uniqueness WITH and WITHOUT correction). This is a
SHORT run (~20-30 min, sampling only) — NOT training.

Inputs attached: leexze/molek-30m-ckpt, basu369victor/zinc250k.
Outputs: /kaggle/working/eval/eval_summary.json (+ corrected/uncorrected logs).
"""
import glob
import os
import shutil
import subprocess

# %% [cell 1] repo + deps + pinned reference code (patches) + data
subprocess.run(["bash", "-lc", "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q rdkit ordered-set tabulate structlog pyyaml tqdm seaborn networkx scipy"], check=True)
subprocess.run(["python", "scripts/fetch_thirdparty.py"], check=True)
subprocess.run(["python", "scripts/prepare_moflow_data.py"], check=True)
subprocess.run(["bash", "-lc", "cd third_party/moflow/data && python data_preprocess.py --data_name zinc250k"], check=True)

# %% [cell 2] place recovered checkpoint + reconstruct params json
run_dir = "/kaggle/pino-bio-mvp/artifacts/molek-eval"
snap_dir = run_dir + "/snapshots"
os.makedirs(snap_dir, exist_ok=True)
# robust checkpoint lookup: the dataset mount path can vary; search recursively + show tree
print("input tree:", os.listdir("/kaggle/input"))
cands = glob.glob("/kaggle/input/**/model_snapshot_epoch_197", recursive=True)
print("checkpoint candidates:", cands)
if not cands:
    raise FileNotFoundError("checkpoint not found under /kaggle/input (see tree above)")
shutil.copy(cands[0], snap_dir + "/model_snapshot_epoch_197")
subprocess.run(["bash", "-lc",
                f"cd third_party/moflow/mflow && python /kaggle/pino-bio-mvp/scripts/reconstruct_moflow_params.py {snap_dir}/moflow-params.json"],
               check=True)

# %% [cell 3] honest eval (M-MOFLOW-4: with + without correction)
rc = subprocess.run(["python", "scripts/eval_moflow.py",
                     "--config", "configs/molgen-zinc250k.yaml",
                     "--run_dir", "artifacts/molek-eval",
                     "--snapshot", "model_snapshot_epoch_197",
                     "--n_samples", "10000",      # [REF] README protocol
                     "--temperature", "0.85",     # [REF]
                     "--experiments", "5"])        # [REF]
print("eval exit:", rc.returncode)

# %% [cell 4] persist results
subprocess.run(["bash", "-lc", """
mkdir -p /kaggle/working/eval
cp -r artifacts/molek-eval/eval/* /kaggle/working/eval/ 2>/dev/null || true
echo '--- eval_summary.json ---'; cat /kaggle/working/eval/eval_summary.json 2>/dev/null || true
ls -lh /kaggle/working/eval
"""], check=False)
