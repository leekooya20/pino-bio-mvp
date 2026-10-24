"""CDGS generation driver (BENCH-MOL-001) — OUR thin driver over CDGS's OWN frozen code.

G1 run-only: CDGS source is cloned ephemerally on compute and NOT vendored into this repo.
This driver replicates run_lib.mol_sde_evaluate()'s GENERATION path (verbatim calls) WITHOUT
importing run_lib / evaluation (which pull in the py3.13-incompatible `moses` package). The
generated SMILES are then scored by OUR shared score_smiles_benchmark.py (identical metrics
for every model, G7, zero drift).

Run with cwd = the cloned CDGS repo root, after the Google-Drive ZINC checkpoint is staged at
exp/vpsde_zinc_cdgs_256/checkpoints/<ckpt>.pth (path via CDGS_CKPT).
"""
import functools
import glob
import os
import sys

import numpy as np
import torch

# CDGS checkpoints are torch<=1.11; torch>=2.6 defaults weights_only=True -> refuse. Restore it.
torch.load = functools.partial(torch.load, weights_only=False)

sys.path.insert(0, os.getcwd())

from configs.vp_zinc_cdgs import get_config  # noqa: E402
import datasets  # noqa: E402
import losses  # noqa: E402
import sampling  # noqa: E402
import sde_lib  # noqa: E402
from models import cdgs  # noqa: E402,F401  (registers the CDGS model via @register_model)
from models import utils as mutils  # noqa: E402
from models.ema import ExponentialMovingAverage  # noqa: E402
from utils import restore_checkpoint, tensor2mol  # noqa: E402
from rdkit import Chem, RDLogger  # noqa: E402

RDLogger.DisableLog("rdApp.*")

OUT = os.environ.get("CDGS_OUT", "/kaggle/working/cdgs_gen.smi")
N = int(os.environ.get("CDGS_N", "10000"))
BATCH = int(os.environ.get("CDGS_BATCH", "500"))


def _find_ckpt() -> str:
    env = os.environ.get("CDGS_CKPT", "")
    if env and os.path.exists(env):
        return env
    cands = sorted(glob.glob("exp/vpsde_zinc_cdgs_256/checkpoints/*.pth"))
    if not cands:
        raise FileNotFoundError("no CDGS zinc checkpoint found under exp/vpsde_zinc_cdgs_256/checkpoints/")
    return cands[-1]


def main() -> int:
    config = get_config()
    config.eval.batch_size = BATCH
    config.eval.num_samples = N
    device = config.device

    train_ds, _, test_ds, n_node_pmf = datasets.get_dataset(config)
    n_node_pmf = torch.from_numpy(n_node_pmf).to(device)
    inverse_scaler = datasets.get_data_inverse_scaler(config)

    score_model = mutils.create_model(config)
    optimizer = losses.get_optimizer(config, score_model.parameters())
    ema = ExponentialMovingAverage(score_model.parameters(), decay=config.model.ema_rate)
    state = dict(optimizer=optimizer, model=score_model, ema=ema, step=0)
    ckpt = _find_ckpt()
    print(f"[cdgs] restoring checkpoint {ckpt}")
    state = restore_checkpoint(ckpt, state, device=device)
    ema.copy_to(score_model.parameters())

    atom_sde = sde_lib.VPSDE(beta_min=config.model.node_beta_min, beta_max=config.model.node_beta_max,
                             N=config.model.num_scales)
    bond_sde = sde_lib.VPSDE(beta_min=config.model.edge_beta_min, beta_max=config.model.edge_beta_max,
                             N=config.model.num_scales)
    sampling_eps = 1e-3
    sa_shape = (config.eval.batch_size, config.data.max_node, config.data.atom_channels)
    sb_shape = (config.eval.batch_size, config.data.bond_channels, config.data.max_node, config.data.max_node)
    sampling_fn = sampling.get_mol_sampling_fn(config, atom_sde, bond_sde, sa_shape, sb_shape,
                                               inverse_scaler, sampling_eps)

    rounds = int(np.ceil(config.eval.num_samples / config.eval.batch_size))
    smiles = []
    for r in range(rounds):
        atom_s, bond_s, steps, nodes = sampling_fn(score_model, n_node_pmf)
        mols, _valid_wd = tensor2mol(atom_s, bond_s, nodes, config.data.atom_list,
                                     correct_validity=True, largest_connected_comp=True)
        for mol in mols:
            if mol is not None:
                smi = Chem.MolToSmiles(mol)
                if smi:
                    smiles.append(smi)
        print(f"[cdgs] round {r + 1}/{rounds}  total smiles {len(smiles)}")
    smiles = smiles[: config.eval.num_samples]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(smiles) + "\n")
    print(f"[cdgs] generated {len(smiles)} SMILES -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
