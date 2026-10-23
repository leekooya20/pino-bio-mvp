#!/usr/bin/env python
"""Reconstruct moflow-params.json for the recovered Molek-30M checkpoint (D3).

The training run saved per-epoch snapshots but the recovered tar did not include
moflow-params.json (the reference saves it to save_dir at init; it was lost in the
tail-end error). We rebuild it EXACTLY as train_model.py constructs the zinc250k
Hyperparameters (verified defaults, G11), so load_model accepts our epoch-197 weights
byte-for-byte.

Run with cwd = third_party/moflow/mflow:
    python scripts/reconstruct_moflow_params.py <out_path>
"""
from __future__ import annotations

import sys

sys.path.insert(0, "..")  # same as generate.py/train_model.py so `from data import` works

from mflow.models.hyperparams import Hyperparameters  # noqa: E402
from mflow.models.model import MoFlow  # noqa: E402
from data import transform_zinc250k  # noqa: E402


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "moflow-params.json"
    atomic_num_list = transform_zinc250k.zinc250_atomic_num_list  # len 10
    # zinc250k block (train_model.py:136-146) + our training args (verified from the
    # run log) + reference defaults for the unspecified ones (b_n_block/a_n_block=1,
    # learn_dist=true).
    mp = Hyperparameters(
        b_n_type=4,
        b_n_flow=5,            # our --b_n_flow 5
        b_n_block=1,           # default
        b_n_squeeze=19,        # zinc250k
        b_hidden_ch=[256, 256],  # our --b_hidden_ch 256,256
        b_affine=True,
        b_conv_lu=2,           # our --b_conv_lu 2
        a_n_node=38,           # zinc250k
        a_n_type=len(atomic_num_list),  # 10
        a_hidden_gnn=[128],    # our --a_hidden_gnn 128
        a_hidden_lin=[256, 64],  # our --a_hidden_lin 256,64
        a_n_flow=19,           # our --a_n_flow 19
        a_n_block=1,           # default
        mask_row_size_list=[1],   # our --mask_row_size_list 1
        mask_row_stride_list=[1],  # our --mask_row_stride_list 1
        a_affine=True,
        learn_dist=True,       # default true
        seed=20261023,         # our --seed (G10)
        noise_scale=0.6,       # our --noise_scale 0.6
    )
    model = MoFlow(mp)          # sanity: builds with these params
    model.save_hyperparams(out)  # exact reference serialization (train_model.py:176)
    print(f"[D3] reconstructed moflow-params.json -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
