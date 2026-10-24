# NVIDIA-BioNeMo coverage audit (2026-10-24)

**Why:** Stan pointed at `github.com/NVIDIA-BioNeMo` — "baka may nakalimutan ka." Our roster was
built around the OLD *BioNeMo Service* (MegaMolBART / ProtGPT2 / ESMFold / OpenFold / AlphaFold-2 /
DiffDock / ESM-2). The **current** NVIDIA-BioNeMo org (27 public repos, checked live via GitHub API)
has moved well past that. This audit maps their current zoo onto our scope and flags what to
register. **Nothing here is integrated yet** — this is a coverage map + decisions.

**Hard rule before ANY integration (G1):** NVIDIA repos commonly split **code vs weights** licenses
(e.g. GenMol ships `license_code.txt` + `license_weights.txt` + a `3rd_party/` dir). Weights are
often NVIDIA Open Model License or **non-commercial** — must be verified per-model before we serve or
adapt. Treat every row below as "license UNVERIFIED" until checked.

## New / relevant models we had NOT registered

### Generative — molecule (A1 core, ours/served)
| Model | ★ | What it is | Decision |
|---|---|---|---|
| **GenMol** | 210 | Masked discrete **diffusion**, fragment-based, SAFE representation | **Register (served alt + diffusion reference).** Directly our "diffusion = FCD frontier lever" candidate vs Molek's flow. High priority. |
| **ReaSyn** | 116 | Synthesis-pathway prediction (Chain-of-Reaction) | **Register (optimize/filter).** Synthesizability gate — can we actually *make* an agri molecule. |
| **avgflow** | 19 | Conformer generation (SO(3) averaged flow-matching) | Register (3D support for docking). Low priority. |

### Generative — protein / binder (A3/A7 core, served)
| Model | ★ | What it is | Decision |
|---|---|---|---|
| **la-proteina** | 314 | Latent flow matching, **all-atom** joint sequence+structure (backbone+side chain) | **Register (served).** Successor to Proteina; upgrades our "RFD4-Proteina" served slot. |
| **Proteina-Complexa** | 462 | **Binder design** for protein AND small-molecule targets (La-Proteina + inference-time opt) | **Register (served) — HIGH.** This is exactly our §6 binder scope; we only had RFD4-Proteina loosely. |
| **proteina** | 282 | Large flow-based backbone generator (fold-class conditioned) | Already in roster as "RFD4-Proteina"; pin to the real repo. |

### Generative — DNA / genomic (A-DNA modality, served/ours-candidate)
| Model | ★ | What it is | Decision |
|---|---|---|---|
| **CodonFM** | 102 | Codon-resolution LM, 130M coding seqs, 20k species | **Register (DNA-gen, alongside Evo2/Eden).** Crop-genomics relevant. |
| **JEPA-DNA** | 35 | Genomic foundation model (generative + joint-embedding) | **Register (DNA-gen).** |

### Docking / affinity (A-optimize loop, served)
| Model | ★ | What it is | Decision |
|---|---|---|---|
| **nvDock** | 6 | Diffusion pocket docking, all-atom, known pocket | **Register (served alt to DiffDock)** when pocket is known. |
| **dualbind** | 26 | 3D protein-ligand **binding affinity** prediction | **Register (optimize/rank).** Scoring for our generate→score loop. |
| **boltz-cp** | 62 | Boltz-2 (AF3-like co-folding + affinity) context-parallel | **Register (served, analysis-adjacent).** Strong structure+affinity. |

### Analysis / FLORA scope (NOT ours — note for the handshake)
| Model | ★ | What it is | Decision |
|---|---|---|---|
| **KERMT** | 105 | Pretrained GNN for molecular **property prediction** | FLORA/analysis (or our optimize scoring). Flag to FLORA. |
| **RNAPro** | 103 | **RNA 3D folding** (SOTA, Stanford Kaggle winners) | **NEW MODALITY (RNA)** we don't cover. Flag to FLORA; decide if RNA enters scope at all. |
| **megalodon** | 25 | (molecular model; needs a read) | Triage later. |

### Tooling + recipes + agents (not models, but useful)
| Repo | ★ | Use to us |
|---|---|---|
| **bionemo-recipes** | 876 | Training/adaptation **recipes** — directly feeds our CPT/SFT/LoRA adaptation ladder. Read for method (G11). |
| **nvMolKit** | 281 | GPU cheminformatics (similarity, conformers, geometry relax) — speeds our optimize loop. |
| **cuik-molmaker** | 38 | Molecular featurization for GNNs. |
| **bionemo-agent-toolkit** / **agent-for-lifesciences** | 496 / 3 | Agent harnesses (parallels our FLORA/GenD agents). |
| **BioNeMo-Inference-Runtime** | 80 | Fast structure-prediction inference serving. |

## Data
Nothing missing data-wise vs what we already use: their protein LMs train on **UniRef** (we use UR50
for Seqgen), molecule models on **ZINC/SAFE** (we use ZINC250k for Molek), property/affinity on public
sets. CodonFM/JEPA-DNA use large coding-sequence/genomic corpora — relevant if we pursue DNA-gen.

## Correction (G7 honesty, 2026-10-24)
On re-check of `configs/licenses.yaml`, several of these were **already registered** from the Katala
master sync — I over-stated "missed" for them: **CodonFM** (bio_tools, NVIDIA Open Model), **Proteina-Complexa**
(NVIDIA Open Model), **la-proteina** (NVIDIA Open Model), **Boltz-2** (Apache code / weights TBD). The
**genuinely NEW misses** now registered this session: **GenMol, ReaSyn, JEPA-DNA, nvDock, dualbind** (+ KERMT,
RNAPro to flag).

## Decisions taken (Stan, 2026-10-24) + licenses verified live
- **GenMol** → **served alt + our diffusion study-reference** (Molek FCD lever). License **VERIFIED**:
  code Apache-2.0, weights NVIDIA Open Model (commercial OK + attribution). `licenses.yaml:genmol`.
- **RNA (RNAPro)** → **IN SCOPE, OURS** (new modality, A9 in capability-map). License **VERIFIED**:
  Apache-2.0 + MIT portions. `licenses.yaml:rnapro`. Task (fold vs gen) + data + replicate/serve TBD.
- **ReaSyn / JEPA-DNA / nvDock / dualbind** → registered in scope, **license pending live verify** before use.
- **KERMT (property pred)** → flag to FLORA (analysis). **RNAPro analysis-side** also flagged to FLORA handshake.

## What this changes for us (honest)
- Our generative **core stays ours**: Molek (done) + Seqgen (training) are still the from-scratch,
  owned pieces. BioNeMo *serves* its generators; our edge is owned-small + agri farm-knob + honesty.
- **Biggest real gaps to register:** GenMol (diffusion molecule gen — our FCD lever), Proteina-Complexa
  (binder design), ReaSyn (synthesizability), CodonFM/JEPA-DNA (DNA-gen). These become **served** entries
  or replication candidates — not silently adopted; each needs a G1 license check (code AND weights).
- **New modality question for Stan:** RNA (RNAPro) — in or out of Katala scope?
- **UI direction (Stan):** SciACA Workbench to evolve toward the BioNeMo Lab/Playground look later
  (task tabs, model dropdown, per-item score grid, 3D viewer with confidence color-scale). Not now.
