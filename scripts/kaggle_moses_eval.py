"""Kaggle runner — Molek-30M MOSES-library distributional metrics (rung 2).

Loads the epoch-197 checkpoint (dataset leexze/molek-30m-ckpt), generates 30k molecules,
and computes FCD/SNN/Frag/Scaf/IntDiv/Novelty via the pinned MOSES library vs the
zinc250k test split. HONEST: not a MOSES-leaderboard entry (Molek trained on zinc250k).
Short GPU run (~15-30 min). Outputs /kaggle/working/moses/molek-moses.json.
"""
import glob
import os
import shutil
import subprocess

# %% [cell 1] repo + deps (+ fcd_torch for FCD) + pinned reference + data
subprocess.run(["bash", "-lc", "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q rdkit ordered-set tabulate structlog pyyaml tqdm seaborn networkx scipy pandas fcd_torch"], check=True)
subprocess.run(["python", "scripts/fetch_thirdparty.py"], check=True)
subprocess.run(["python", "scripts/prepare_moflow_data.py"], check=True)
subprocess.run(["bash", "-lc", "cd third_party/moflow/data && python data_preprocess.py --data_name zinc250k"], check=True)

# %% [cell 2] checkpoint + reconstructed params
run_dir = "/kaggle/pino-bio-mvp/artifacts/molek-eval"
snap_dir = run_dir + "/snapshots"
os.makedirs(snap_dir, exist_ok=True)
print("input tree:", os.listdir("/kaggle/input"))
cands = glob.glob("/kaggle/input/**/model_snapshot_epoch_197", recursive=True)
if not cands:
    raise FileNotFoundError("checkpoint not found under /kaggle/input")
shutil.copy(cands[0], snap_dir + "/model_snapshot_epoch_197")
subprocess.run(["bash", "-lc",
                f"cd third_party/moflow/mflow && python /kaggle/pino-bio-mvp/scripts/reconstruct_moflow_params.py {snap_dir}/moflow-params.json"],
               check=True)

# %% [cell 3] distributional metrics: FCD (fcd_torch) + IntDiv/SNN (RDKit), no moses pkg
os.makedirs("/kaggle/working/moses", exist_ok=True)
rc = subprocess.run(["bash", "-lc",
    "cd third_party/moflow/mflow && "
    "python /kaggle/pino-bio-mvp/scripts/eval_moses_metrics.py "
    f"--model_dir {snap_dir} --snapshot model_snapshot_epoch_197 "
    "--n_gen 30000 --batch 10000 --temp 0.85 "
    "--out /kaggle/working/moses/molek-moses.json"])
print("dist eval exit:", rc.returncode)

# %% [cell 4] show result
subprocess.run(["bash", "-lc", "cat /kaggle/working/moses/molek-moses.json 2>/dev/null; ls -lh /kaggle/working/moses"], check=False)
