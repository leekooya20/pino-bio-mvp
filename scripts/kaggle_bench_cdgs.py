"""Kaggle BENCH-MOL-001 — CDGS head-to-head vs Molek-30M on ZINC250k (frozen author ckpt).

G1 run-only: CDGS cloned ephemerally, NOT vendored; only measured numbers return. CDGS ships
zinc250k_property.csv + valid_idx in-repo; the ZINC checkpoint is on Google Drive (256ch). We
generate with CDGS's OWN frozen code via our thin driver (no moses import) and score with OUR
shared score_smiles_benchmark.py (identical metrics for every model, G7 zero drift).
"""
import os
import subprocess

CDGS_COMMIT = "2d498aae8e6c0d56f875d5cc463a8e0ac22c197c"
GDRIVE_256 = "1bA_6ldtwF6gTMToZGG7w1dqmOpIuWZJd"  # README: CDGS ZINC250k 256ch pretrained

subprocess.run(["bash", "-lc", f"""
set -e
git clone https://github.com/GRAPH-0/CDGS.git /kaggle/CDGS
cd /kaggle/CDGS && git checkout {CDGS_COMMIT}
git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp
"""], check=True)

# CDGS is torch1.11/PyG2.1 era. Install compatible light deps; networkx<3 for safety.
subprocess.run(["bash", "-lc",
                "pip install -q ml-collections absl-py 'networkx<3' rdkit fcd_torch gdown torch-geometric"],
               check=True)
# CDGS's models/utils.py needs torch_scatter (+ torch_sparse) — the PyG C++ companions. Pull the
# wheel matching Kaggle's exact torch+CUDA from the PyG index (source build would fail/time out).
subprocess.run(["bash", "-lc", r"""
set -e
TORCH=$(python -c "import torch;print(torch.__version__.split('+')[0])")
CUDA=$(python -c "import torch;print('cu'+torch.version.cuda.replace('.','') if torch.version.cuda else 'cpu')")
echo "torch=$TORCH cuda=$CUDA"
pip install -q torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-${TORCH}+${CUDA}.html
python -c "import torch_scatter, torch_sparse; print('torch_scatter', torch_scatter.__version__)"
"""], check=True)

os.chdir("/kaggle/CDGS")

# (1) stage the Google-Drive ZINC 256ch checkpoint into the workdir CDGS expects
subprocess.run(["bash", "-lc", f"""
set -e
mkdir -p exp/vpsde_zinc_cdgs_256/checkpoints
cd /tmp
gdown --folder https://drive.google.com/drive/folders/{GDRIVE_256} -O /tmp/cdgs256 || \
  gdown --folder {GDRIVE_256} -O /tmp/cdgs256
echo '--- downloaded tree ---'; find /tmp/cdgs256 -name '*.pth' -print
# place every .pth into the checkpoints dir CDGS reads
find /tmp/cdgs256 -name '*.pth' -exec cp -v {{}} /kaggle/CDGS/exp/vpsde_zinc_cdgs_256/checkpoints/ \\;
ls -lh /kaggle/CDGS/exp/vpsde_zinc_cdgs_256/checkpoints/
"""], check=True)

# (1b) run-only py3.13 shim: CDGS sascorer.py does `from rdkit.six import iteritems`, but modern
#      RDKit removed the bundled six (same as moflow M-MOFLOW-9). Patch to the plain py3 equivalent.
subprocess.run(["bash", "-lc", r"""
python - <<'PY'
p = '/kaggle/CDGS/sascorer.py'
s = open(p).read()
s = s.replace(
    'from rdkit.six import iteritems',
    'try:\n    from rdkit.six import iteritems\nexcept ImportError:\n    def iteritems(d):\n        return d.items()')
open(p, 'w').write(s)
print('patched CDGS sascorer.py rdkit.six shim (run-only)')
PY
"""], check=True)

# (2) generate with CDGS's own frozen code via OUR driver (no moses import; run-only)
subprocess.run(["bash", "-lc",
                "cp /kaggle/pino-bio-mvp/scripts/bench/cdgs_gen.py /kaggle/CDGS/cdgs_gen.py"],
               check=True)
os.environ["CDGS_OUT"] = "/kaggle/working/cdgs_gen.smi"
os.environ["CDGS_N"] = "10000"
os.environ["CDGS_BATCH"] = "500"
subprocess.run(["python", "cdgs_gen.py"], check=True)

# (3) same zinc250k train/test splits CDGS uses (canonical valid_idx) for scoring
subprocess.run(["bash", "-lc", r"""
python - <<'PY'
import json, pandas as pd, glob
csv = 'data/raw/zinc250k_property.csv'
df = pd.read_csv(csv)
col = 'smiles' if 'smiles' in df.columns else df.columns[0]
test_idx = set(json.load(open('data/raw/valid_idx_zinc250k.json')))
smiles = [str(s).strip() for s in df[col].tolist()]
train = [s for i,s in enumerate(smiles) if i not in test_idx]
test  = [s for i,s in enumerate(smiles) if i in test_idx]
open('/kaggle/working/zinc_train.smi','w').write('\n'.join(train)+'\n')
open('/kaggle/working/zinc_test.smi','w').write('\n'.join(test)+'\n')
print('train', len(train), 'test', len(test), 'col', col)
PY
"""], check=True)

# (4) score with OUR shared scorer (identical metrics for every model)
subprocess.run(["python", "/kaggle/pino-bio-mvp/scripts/score_smiles_benchmark.py",
                "--gen", "/kaggle/working/cdgs_gen.smi",
                "--train", "/kaggle/working/zinc_train.smi",
                "--test", "/kaggle/working/zinc_test.smi",
                "--model", "cdgs",
                "--note", "CDGS (Huang et al. AAAI 2023) frozen author zinc250k 256ch ckpt, "
                          "run-only (G1); generated via its own code, scored by our shared harness.",
                "--out", "/kaggle/working/bench-cdgs.json"], check=True)

subprocess.run(["bash", "-lc",
                "echo '=== BENCH CDGS ==='; cat /kaggle/working/bench-cdgs.json"], check=False)
