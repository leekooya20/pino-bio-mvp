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
relationship: has_role CHEBI:24527

[Term]
id: CHEBI:99999
name: aspirin
def: "A drug, not a pesticide."
relationship: has_role CHEBI:35475
"""

SDF = """
CHEBI:27744
> <SMILES>
O=C(O)CNCP(=O)(O)O

$$$$
CHEBI:99999
> <SMILES>
CC(=O)Oc1ccccc1C(=O)O

$$$$
"""


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


def test_sdf_smiles_parse():
    smi = parse_sdf_smiles(SDF)
    assert smi["CHEBI:27744"] == "O=C(O)CNCP(=O)(O)O"


if __name__ == "__main__":
    test_role_subtree_includes_children()
    test_agrochemical_molecules_selects_glyphosate_only()
    test_sdf_smiles_parse()
    print("chebi agchem logic ok")
