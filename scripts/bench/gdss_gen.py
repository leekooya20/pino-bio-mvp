"""GDSS generation driver (BENCH-MOL-001) — OUR thin driver over GDSS's OWN frozen code.

G1 run-only: GDSS source is cloned ephemerally on compute and NOT vendored into this repo.
This driver (our code) imports GDSS's non-eval modules and replicates Sampler_mol.sample()'s
GENERATION path exactly (minus GDSS's own moses/NSPDK evaluation, which (a) we don't need and
(b) is py3.13-incompatible). The generated SMILES are then scored by OUR shared
score_smiles_benchmark.py — identical metrics for every model (G7, zero drift).

Run with cwd = the cloned GDSS repo root, after `data/preprocess.py` has built the npz.
"""
import functools
import os
import sys

import torch

# GDSS checkpoints pickle their model_config object; torch>=2.6 defaults weights_only=True
# which would refuse to load it. Restore the permissive default for this trusted local file.
torch.load = functools.partial(torch.load, weights_only=False)

sys.path.insert(0, os.getcwd())

from parsers.config import get_config  # noqa: E402
from utils.loader import (load_ckpt, load_data, load_device, load_model_from_ckpt,  # noqa: E402
                          load_sampling_fn, load_seed)
from utils.graph_utils import init_flags, quantize_mol  # noqa: E402
from utils.mol_utils import gen_mol, mols_to_smiles  # noqa: E402

OUT = os.environ.get("GDSS_OUT", "/kaggle/working/gdss_gen.smi")
CKPT = os.environ.get("GDSS_CKPT_CONFIG", "sample_zinc250k")  # v2 ckpt via a sibling config


def main() -> int:
    config = get_config(CKPT, 42)
    device = load_device()
    dev0 = device[0] if isinstance(device, list) else device

    ckpt_dict = load_ckpt(config, device)
    configt = ckpt_dict["config"]

    load_seed(config.seed)
    model_x = load_model_from_ckpt(ckpt_dict["params_x"], ckpt_dict["x_state_dict"], device)
    model_adj = load_model_from_ckpt(ckpt_dict["params_adj"], ckpt_dict["adj_state_dict"], device)
    sampling_fn = load_sampling_fn(configt, config.sampler, config.sample, device)

    load_seed(config.sample.seed)
    train_graph_list, _ = load_data(configt, get_graph_list=True)   # node-count dist for init_flags
    init_f = init_flags(train_graph_list, configt, 10000).to(dev0)

    x, adj, _ = sampling_fn(model_x, model_adj, init_f)

    # --- GDSS's exact mol reconstruction (copied from Sampler_mol.sample, verbatim) ---
    samples_int = quantize_mol(adj)
    samples_int = samples_int - 1
    samples_int[samples_int == -1] = 3
    adj = torch.nn.functional.one_hot(torch.tensor(samples_int), num_classes=4).permute(0, 3, 1, 2)
    x = torch.where(x > 0.5, 1, 0)
    x = torch.concat([x, 1 - x.sum(dim=-1, keepdim=True)], dim=-1)

    gen_mols, _ = gen_mol(x, adj, configt.data.data)
    gen_smiles = [s for s in mols_to_smiles(gen_mols) if len(s)]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(gen_smiles) + "\n")
    print(f"[gdss] generated {len(gen_smiles)} SMILES -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
