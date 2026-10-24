"""Kaggle BENCH-MOL-001 — GDSS head-to-head vs Molek-30M on ZINC250k (frozen author ckpt).

G1 run-only: GDSS is cloned ephemerally here and NOT vendored into our repo; only the measured
numbers return. GDSS ships zinc250k.csv + valid_idx + the pretrained checkpoint in-repo, so no
external data download. Generation uses GDSS's OWN frozen code via our thin driver; scoring uses
OUR shared score_smiles_benchmark.py (identical metrics for every model, G7 zero drift).
"""
import os
import subprocess

GDSS_COMMIT = "24cc490e0c5b39cbd265fda33ab2bc8b528d4454"

subprocess.run(["bash", "-lc", f"""
set -e
git clone https://github.com/harryjo97/GDSS.git /kaggle/GDSS
cd /kaggle/GDSS && git checkout {GDSS_COMMIT}
git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp
"""], check=True)

# GDSS is py3.7/torch1.10 era. networkx<3 restores from_numpy_matrix; the rest are light deps.
subprocess.run(["bash", "-lc",
                "pip install -q 'networkx<3' easydict pyyaml rdkit fcd_torch torch-geometric"],
               check=True)

os.chdir("/kaggle/GDSS")

# (0) run-only device patch: GDSS's VESDE indexes a CPU tensor (discrete_sigmas) with a CUDA
#     index -> fine on torch 1.10, a RuntimeError on torch 2.x. Move to device BEFORE indexing.
subprocess.run(["bash", "-lc", r"""
python - <<'PY'
p = '/kaggle/GDSS/sde.py'
s = open(p).read()
s = s.replace('self.discrete_sigmas[timestep - 1].to(t.device)',
              'self.discrete_sigmas.to(t.device)[timestep - 1]')
open(p, 'w').write(s)
print('patched sde.py VESDE device indexing (run-only)')
PY
"""], check=True)

# (1) build the kekulized npz GDSS's loader needs for init_flags (from its in-repo zinc250k.csv)
subprocess.run(["python", "data/preprocess.py", "--dataset", "ZINC250k"], check=True)

# (2) generate with GDSS's own frozen code via OUR driver (no moses import; run-only)
subprocess.run(["bash", "-lc",
                "cp /kaggle/pino-bio-mvp/scripts/bench/gdss_gen.py /kaggle/GDSS/gdss_gen.py"],
               check=True)
os.environ["GDSS_OUT"] = "/kaggle/working/gdss_gen.smi"
subprocess.run(["python", "gdss_gen.py"], check=True)

# (3) prepare the SAME zinc250k train/test splits GDSS uses (canonical valid_idx) for scoring
subprocess.run(["bash", "-lc", r"""
python - <<'PY'
import json, pandas as pd
df = pd.read_csv('data/zinc250k.csv')
col = 'smiles'
test_idx = set(json.load(open('data/valid_idx_zinc250k.json')))
smiles = [s.strip() for s in df[col].tolist()]
train = [s for i,s in enumerate(smiles) if i not in test_idx]
test  = [s for i,s in enumerate(smiles) if i in test_idx]
open('/kaggle/working/zinc_train.smi','w').write('\n'.join(train)+'\n')
open('/kaggle/working/zinc_test.smi','w').write('\n'.join(test)+'\n')
print('train', len(train), 'test', len(test))
PY
"""], check=True)

# (4) score GDSS generations with OUR shared scorer (identical metrics for every model)
subprocess.run(["python", "/kaggle/pino-bio-mvp/scripts/score_smiles_benchmark.py",
                "--gen", "/kaggle/working/gdss_gen.smi",
                "--train", "/kaggle/working/zinc_train.smi",
                "--test", "/kaggle/working/zinc_test.smi",
                "--model", "gdss",
                "--note", "GDSS (Jo et al. 2022) frozen author zinc250k ckpt, run-only (G1); "
                          "generated via its own code, scored by our shared harness.",
                "--out", "/kaggle/working/bench-gdss.json"], check=True)

subprocess.run(["bash", "-lc",
                "echo '=== BENCH GDSS ==='; cat /kaggle/working/bench-gdss.json"], check=False)
