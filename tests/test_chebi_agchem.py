"""Tests for the ChEBI agrochemical role-tree logic (the clever, data-independent part).
Uses a tiny synthetic OBO/SDF so no download is needed."""
from __future__ import annotations

from scripts.fetch_chebi_agchem import (
    agrochemical_molecules,
    parse_obo,
    parse_sdf_smiles,
    role_subtree,
)

OBO = """format-version: 1.2

[Term]
id: CHEBI:33286
name: agrochemical
def: "A substance used in agriculture or horticulture."

[Term]
id: CHEBI:24527
name: herbicide
def: "A substance used to destroy plant pests."
is_a: CHEBI:33286

[Term]
id: CHEBI:27744
name: glyphosate
def: "A phosphonic acid herbicide."
relationship: RO:0000087 CHEBI:24527 ! has role herbicide

[Term]
id: CHEBI:99999
name: aspirin
def: "A drug, not a pesticide."
relationship: has_role CHEBI:35475
"""

def _write_chebi_sdf(path, pairs):
    """Build a real ChEBI-style SDF (molblock + `> <ChEBI ID>` tag, NO <SMILES>
    property — exactly how ChEBI ships it, C-CHEBI-1) so the RDKit path is exercised."""
    from rdkit import Chem
    blocks = []
    for cid, smi in pairs:
        mol = Chem.MolFromSmiles(smi)
        block = Chem.MolToMolBlock(mol)
        blocks.append(f"{block}>  <ChEBI ID>\n{cid}\n\n$$$$\n")
    path.write_text("".join(blocks), encoding="utf-8")
    return path


def test_role_subtree_includes_children():
    terms = parse_obo(OBO)
    roles = role_subtree(terms, "CHEBI:33286")
    assert "CHEBI:33286" in roles and "CHEBI:24527" in roles  # herbicide is a child
    assert "CHEBI:35475" not in roles                          # unrelated role excluded


def test_agrochemical_molecules_selects_glyphosate_only():
    terms = parse_obo(OBO)
    roles = role_subtree(terms, "CHEBI:33286")
    mols = agrochemical_molecules(terms, roles)
    assert "CHEBI:27744" in mols      # glyphosate (herbicide role) in
    assert "CHEBI:99999" not in mols  # aspirin (drug role) out


def test_sdf_smiles_parse(tmp_path):
    # ChEBI SDF carries no <SMILES> property; SMILES is derived from the molblock (C-CHEBI-1).
    from rdkit import Chem
    sdf = _write_chebi_sdf(tmp_path / "chebi.sdf",
                           [("CHEBI:27744", "O=C(O)CNCP(=O)(O)O"),
                            ("CHEBI:99999", "CC(=O)Oc1ccccc1C(=O)O")])
    out = parse_sdf_smiles(sdf)
    # compare canonically (RDKit may re-canonicalise the input SMILES)
    want = Chem.CanonSmiles("O=C(O)CNCP(=O)(O)O")
    assert Chem.CanonSmiles(out["CHEBI:27744"]) == want


if __name__ == "__main__":
    test_role_subtree_includes_children()
    test_agrochemical_molecules_selects_glyphosate_only()
    print("chebi agchem role-tree logic ok (run `pytest` for the rdkit SDF path)")
