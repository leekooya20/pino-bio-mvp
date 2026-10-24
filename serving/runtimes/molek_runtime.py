"""Molek-30M serving runtime — loads the trained checkpoint and generates molecules for
the /v1 `mol.generate` tool. Returns REAL measured results (G7); the caller
(serving/tools.py:mol_generate) only invokes this when the checkpoint exists.

Reference code untouched (G11): generation uses the pinned moflow `generate_mols` +
`check_validity`; we reconstruct the Hyperparameters exactly as train_model.py (zinc250k)
so the epoch-197 weights load. Runs where torch + rdkit + third_party/moflow are present
(GPU host / container / Kaggle inference) — not on the dev box (no torch there).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_MFLOW = ROOT / "third_party" / "moflow" / "mflow"


def _hyperparams():
    from mflow.models.hyperparams import Hyperparameters
    from data import transform_zinc250k
    atomic = transform_zinc250k.zinc250_atomic_num_list
    return Hyperparameters(
        b_n_type=4, b_n_flow=5, b_n_block=1, b_n_squeeze=19,
        b_hidden_ch=[256, 256], b_affine=True, b_conv_lu=2,
        a_n_node=38, a_n_type=len(atomic), a_hidden_gnn=[128], a_hidden_lin=[256, 64],
        a_n_flow=19, a_n_block=1, mask_row_size_list=[1], mask_row_stride_list=[1],
        a_affine=True, learn_dist=True, seed=20261023, noise_scale=0.6,
    )


_MODEL = None  # cache across calls


def _load(ckpt: str):
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    sys.path.insert(0, str(_MFLOW))
    sys.path.insert(0, str(_MFLOW.parent))  # for `from data import ...`
    import torch
    from mflow.utils.model_utils import load_model
    params_json = Path(ckpt).parent / "moflow-params.json"
    if params_json.exists():
        from mflow.models.hyperparams import Hyperparameters
        mp = Hyperparameters(path=str(params_json))
    else:
        mp = _hyperparams()
    model = load_model(ckpt, mp, debug=False)
    model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu")).eval()
    _MODEL = model
    return model


def sample(ckpt: str, inputs: dict) -> dict:
    """Generate n molecules; return {smiles, qed, logp} per molecule (G7: real results)."""
    n = int(inputs.get("n", 10))
    temp = float(inputs.get("temperature", 0.85))
    try:
        # moflow must be importable BEFORE the mflow/data imports below (F-0041: the path
        # insert used to live only in _load(), which runs too late).
        if str(_MFLOW) not in sys.path:
            sys.path.insert(0, str(_MFLOW))
        if str(_MFLOW.parent) not in sys.path:
            sys.path.insert(0, str(_MFLOW.parent))
        import torch
        from mflow.generate import generate_mols
        from mflow.models.utils import check_validity
        from data import transform_zinc250k
        from rdkit import Chem, DataStructs
        from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski, QED, rdMolDescriptors

        try:  # SA score via the pinned reference sascorer (M-MOFLOW-9 shim applied)
            from mflow.utils import sascorer
        except Exception:  # noqa: BLE001
            sascorer = None

        model = _load(ckpt)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        atomic = transform_zinc250k.zinc250_atomic_num_list
        batch = max(n, int(inputs.get("batch", min(1000, max(n * 2, 100)))))
        with torch.no_grad():
            adj, x = generate_mols(model, batch_size=batch, temp=temp, device=device)
        res = check_validity(adj, x, atomic, correct_validity=True, debug=False)

        # optional similarity-to-seed (Tanimoto, Morgan r2) if the caller gave an anchor SMILES
        seed_fp = None
        seed_smiles = (inputs.get("smiles") or "").strip().splitlines()
        if seed_smiles:
            sm = Chem.MolFromSmiles(seed_smiles[0])
            if sm is not None:
                seed_fp = AllChem.GetMorganFingerprintAsBitVect(sm, 2, nBits=2048)

        mols = []
        for smi in res["valid_smiles"][:n]:
            m = Chem.MolFromSmiles(smi)
            if m is None:
                continue
            logp = float(Crippen.MolLogP(m))
            mw = float(Descriptors.MolWt(m))
            hbd = int(Lipinski.NumHDonors(m))
            hba = int(Lipinski.NumHAcceptors(m))
            rec = {
                "smiles": smi,
                "qed": round(float(QED.qed(m)), 4),
                "logp": round(logp, 4),
                "mw": round(mw, 2),
                "tpsa": round(float(rdMolDescriptors.CalcTPSA(m)), 2),
                "hbd": hbd, "hba": hba,
                "sa": round(float(sascorer.calculateScore(m)), 2) if sascorer else None,
                # Lipinski Ro5 (all four real descriptors)
                "lipinski": (mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10),
            }
            if seed_fp is not None:
                fp = AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048)
                rec["sim"] = round(float(DataStructs.TanimotoSimilarity(seed_fp, fp)), 4)
            mols.append(rec)
        return {"status": "succeeded", "measured": True, "model": "molek",
                "molecules": mols, "truncated": len(res["valid_smiles"]) > n,
                "provenance": "Molek-30M (our from-scratch MoFlow replica, epoch 197); "
                              "corrected-validity generation, temp %.2f" % temp}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "measured": False, "model": "molek",
                "error": repr(e), "molecules": [],
                "note": "Molek generation failed; no molecules fabricated (G7)."}
