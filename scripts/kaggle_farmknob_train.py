"""Kaggle farm-knob + intent-mol training (GPU/CPU, internet). The agri moat:

  ChEBI OBO + lite SDF (C-CHEBI-1: SMILES from molblocks via RDKit)
    -> fetch_chebi_agchem.py   : (definition, SMILES, RDKit descriptors) for the
                                 agrochemical has_role subtree (CHEBI:33286), G1 gated
    -> compute_farmknob_stats.py: descriptor steering target (M-MOFLOW-3, pure stats)
    -> train_intent_mol.py      : frozen MiniLM -> OUR MLP -> descriptor target (N-NLP-1)

Artifacts land in /kaggle/working (persist on commit). Honest (G7): license verified
live; descriptors are real RDKit calls; intent-mol recovery reported per-dimension on a
held-out split, never blended with served models.
"""
import os
import subprocess

subprocess.run(["bash", "-lc",
                "git clone --depth 1 https://github.com/leekooya20/pino-bio-mvp.git /kaggle/pino-bio-mvp"],
               check=True)
os.chdir("/kaggle/pino-bio-mvp")
subprocess.run(["bash", "-lc", "pip install -q rdkit sentence-transformers"], check=True)

# (1) fetch ChEBI (OBO 258MB + lite SDF 15MB); SMILES derived from molblocks (C-CHEBI-1)
subprocess.run(["bash", "-lc", """
set -e
mkdir -p /kaggle/working/chebi
cd /kaggle/working/chebi
echo '--- downloading ChEBI OBO + lite SDF ---'
wget -q https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo -O chebi.obo
wget -q https://ftp.ebi.ac.uk/pub/databases/chebi/SDF/chebi_lite_3_stars.sdf.gz -O chebi_lite.sdf.gz
ls -lh chebi.obo chebi_lite.sdf.gz
"""], check=True)

os.environ["CHEBI_OBO"] = "/kaggle/working/chebi/chebi.obo"
os.environ["CHEBI_SDF"] = "/kaggle/working/chebi/chebi_lite.sdf.gz"
subprocess.run(["python", "scripts/fetch_chebi_agchem.py"], check=True)

# persist the derived pairs immediately (crash-safe: survives later-stage failure)
subprocess.run(["bash", "-lc", """
mkdir -p /kaggle/working/farm-knob-out
cp -f data/external/chebi_agchem/pairs.jsonl /kaggle/working/farm-knob-out/ 2>/dev/null || true
cp -f data/manifests/chebi-agchem.jsonl /kaggle/working/farm-knob-out/ 2>/dev/null || true
wc -l /kaggle/working/farm-knob-out/pairs.jsonl || true
"""], check=False)

# (2) farm-knob descriptor steering target (M-MOFLOW-3, pure statistics)
subprocess.run(["python", "scripts/compute_farmknob_stats.py"], check=True)

# (3) intent-mol head (N-NLP-1): frozen MiniLM -> our MLP -> descriptor target
subprocess.run(["python", "scripts/train_intent_mol.py"], check=False)

# (4) persist all artifacts
subprocess.run(["bash", "-lc", """
mkdir -p /kaggle/working/farm-knob-out
cp -rf artifacts/farm-knob /kaggle/working/farm-knob-out/ 2>/dev/null || true
cp -rf artifacts/intent-mol /kaggle/working/farm-knob-out/ 2>/dev/null || true
echo '--- farmknob target ---'; cat artifacts/farm-knob/farmknob_target.json 2>/dev/null | head -60
echo '--- intent-mol run_meta ---'; cat artifacts/intent-mol/run_meta.json 2>/dev/null
ls -lhR /kaggle/working/farm-knob-out
"""], check=False)
