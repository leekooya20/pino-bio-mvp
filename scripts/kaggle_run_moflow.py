"""Kaggle notebook runner for MoFlow-30M phase 1 (PinoBio MVP-4).

Usage on Kaggle:
  1. New Notebook -> File -> Import Notebook -> upload this .py (Script notebook)
  2. Settings -> Accelerator -> GPU T4 x2
  3. Add-ons -> Secrets -> add GITHUB_TOKEN (read totaly scope, PAT for this private repo) —
     NEVER paste tokens in cells (G8).
  4. Session limit is 12h / 30h weekly — the pipeline is checkpoint-resumable (G10).
"""
# %% [cell 1] clone the repo (public since 2026-10-23; secrets pattern kept for when it goes private again)
import os
import shlex
import subprocess

try:
    from kaggle_secrets import UserSecretsClient
    tok = UserSecretsClient().get_secret("GITHUB_TOKEN")
except Exception:
    tok = None
prefix = f"https://{shlex.quote(tok)}@github.com/" if tok else "https://github.com/"
subprocess.run(["bash", "-lc", f"git clone --depth 1 {prefix}leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"], check=True)
os.chdir("/kaggle/pino-bio-mvp")

# %% [cell 2] deps (rdkit via pip; keep torch as Kaggle preinstalled)
subprocess.run(["bash", "-lc", "pip install -q rdkit ordered-set tabulate structlog pyyaml tqdm seaborn networkx scipy"], check=True)  # M-MOFLOW-6: ordered-set (pure-Python) replaces orderedset (no 3.13 wheel)

# %% [cell 3] pin reference code + documented patches (G11: applies M-MOFLOW-5 shim)
subprocess.run(["python", "scripts/fetch_thirdparty.py"], check=True)

# %% [cell 4] data: download + verify (249,455 rows exact) + manifest (G1)
subprocess.run(["python", "scripts/prepare_moflow_data.py"], check=True)

# %% [cell 5] reference preprocessing: SMILES -> molecular graphs (.npz)
subprocess.run(["bash", "-lc", "cd third_party/moflow/data && python data_preprocess.py --data_name zinc250k"], check=True)

# %% [cell 6] param-budget preflight (M-MOFLOW-1: fail if > 30M) + training start
# resumable: rerun THIS cell with --resume after a session-kill; it finds the latest snapshot.
import sys

sys.path.insert(0, "scripts")
from train_moflow import main as train_main  # noqa: E402

sys.argv = ["train_moflow.py", "--config", "configs/molgen-zinc250k.yaml"]
rc = train_main()  # long-running; Kaggle user can interrupt and rerun with --resume
rc

# %% [cell 7] persist artifacts out of the session (12h wall)
subprocess.run(
    ["bash", "-lc", """
mkdir -p /kaggle/working/artifacts
cp -r artifacts/*/run_meta.json /kaggle/working/artifacts/ 2>/dev/null || true
tar -czf /kaggle/working/moflow_ckpts_$(date +%m%d-%H%M).tgz -C artifacts . 2>/dev/null || true
ls -lh /kaggle/working
"""],
    check=False,
)
