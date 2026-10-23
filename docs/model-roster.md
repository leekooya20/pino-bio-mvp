# Model roster — what we train, fine-tune, and serve (and what we ADD to each)

Plain answer to "which are from-scratch, which do we fine-tune, what do we add."
Three tiers. Honest about scale and ownership (G7/G9).

---

## Tier 1 — FROM SCRATCH (our own checkpoints, trained from zero)

| Model | Replica of | Trains on | What WE ADD (our moat) |
|---|---|---|---|
| **Molek-30M** | MoFlow (Zang & Wang, KDD 2020, MIT) | zinc250k (249,455 mols) | **farm-knob** agri-conditioning head (M-MOFLOW-3) · 30M scale-down (M-1) · AMP/T4 fit (M-2) · honest with/without-correction eval (M-4) · py3.13 patch chain (M-5/6/9/10) |
| **Seqgen-small** | ProtGPT2 (Ferruz et al., Nat Commun 2022, Apache-2.0) | UniRef50 subsample | ≤100M scale-down (P-1) · cluster-stratified subsample curriculum (P-2) · **our novelty gate** = their ppl rule + ESM-2 embedding + BLAST-vs-UniRef (P-3) · fine-tune hook (P-4) · **rice-first crop arm** (P-5) |

These are the ones with **genuinely our weights**. Everything is documented modifications
over a faithfully-read recipe (G11) — never a blind copy.

## Tier 2 — WE TRAIN A SMALL PART (adapters / fine-tunes on top of frozen bases)

| Thing | Base (frozen/open) | We train | Purpose |
|---|---|---|---|
| **intent-mol** (N-NLP-1) | MiniLM text encoder (Apache-2.0), frozen | a small MLP projection | words → Molek descriptor target (NL steering) |
| **intent-seq** (N-NLP-2) | ProTrek/MiniLM (MIT/Apache), frozen | a trainable matrix W | words → Seqgen control embedding |
| **Molek crop arm** (future M-MOFLOW-11) | our Molek base | conditioning fine-tune | steer toward a crop-relevant corpus |
| **Seqgen rice arm** (P-5) | our Seqgen base | fine-tune via run_clm hook (P-4), LR 1e-6 | rice → maize → coconut → mango |
| **ESM-2 LoRA** (later) | ESM-2 650M (served, MIT) | a LoRA adapter | sharper scoring for our novelty gate |

Here we **fine-tune our own checkpoints** (Molek/Seqgen arms) or **train a tiny adapter**
on a frozen open base (intent heads, ESM-2 LoRA). Small, Kaggle-feasible, owned.

## Tier 3 — SERVED ONLY (we call them; we do NOT train their weights)

| Model | Role | License | What WE ADD |
|---|---|---|---|
| **MegaMolBART** | molecule generation (alt to Molek) | Apache-2.0 | a `/v1` mol.generate alt wrapper (served, Stan 2026-10-24) |
| **DiffDock** | molecule↔protein docking / pose — **in our optimize loop** | MIT / NVIDIA Open | a `/v1` dock-ligand wrapper (we dock OUR molecules; FLORA never touches molecules) |
| **RFD4-Proteina** | binder/backbone design | BSD-3 | a `/v1` wrapper + reasoning_depth→thinking + search_criteria passthrough |
| **ESM-2** | sequence scoring | MIT | a scorer wrapper (+ optional LoRA, Tier 2) |
| **ESMFold / Boltz-2 / Chai / AF3 / OpenFold / AF2** | fold / structure validation ladder | MIT / MIT / Apache / gated / Apache / gated | honest rung selection + labels (§8); used to VALIDATE our designs |
| **Pinal** | text→protein design | Apache-2.0 | a `/v1` wrapper (16B — served, never from-scratch) |

### Plan-roster ownership (Stan's list, 2026-10-24)
- **Generative chemistry** — MoFlow (**ours**, Molek) · MegaMolBART (**ours**, served alt)
- **Protein generation** — ProtGPT2 (**ours**, Seqgen)
- **Pose prediction** — DiffDock (**ours**, served, in our optimize loop)
- **Embeddings / property prediction** — ESM1/ESM2 (**FLORA**'s analysis; we use ESM-2 served as a scorer)
- **3D structure prediction** — OpenFold / AlphaFold2 / ESMFold (**FLORA** analyzes existing proteins; we use them only to VALIDATE our designs, §8)

For served models we **add nothing to their weights** — we add wrappers, honest
passthrough, and our own adapters *beside* them. Their numbers stay cited, never blended
with ours (G7).

---

## Our scope = FLORA's "OUT" list (the authoritative boundary, Stan 2026-10-24)

FLORA's policy EXCLUDES every generate/design model (565d09). That exclusion list is
**exactly our mandate** — we execute all of it. Full enumeration with honest handling:

| Model | Modality | How we carry it | License |
|---|---|---|---|
| **MoFlow** → Molek | molecule gen | **from scratch (ours)** | MIT |
| **MegaMolBART** | molecule gen | served alt | Apache-2.0 |
| **ProtGPT2** → Seqgen | protein gen | **from scratch (ours)** | Apache-2.0 |
| **RFD4-Proteina** | protein design | served | BSD-3 |
| **Proteina-Complexa** | protein-complex design | registered; license TBD | verify at use |
| **La-Proteina** | protein design (latent) | registered; license TBD | verify at use |
| **Evo 2** | **DNA/genome gen** (new modality) | served | Apache-2.0 / NVIDIA Open |
| **Eden** | DNA gen | registered; identity+license TBD | verify at use |
| **AgroNT** | crop DNA | **LICENSE HOLD** (non-commercial) | NC — research-only |
| **DiffDock** | docking/pose (optimize loop) | served | MIT / NVIDIA Open |

New modality note: **DNA generation (Evo 2, Eden)** enters our scope here — beyond
molecules + proteins. Served-first; nothing from-scratch at genome scale.

Honest flags: Proteina-Complexa / La-Proteina / Eden are **registered in scope but not
usable until their license is read live (G1/G11)**. AgroNT is **held** — crop-relevant
but NC-licensed, so never shipped in a commercial path unless relicensed.

## One-line summary

- **From scratch (our weights):** Molek-30M, Seqgen-small.
- **We fine-tune / adapt:** our own Molek & Seqgen arms (farm/crop/rice), plus small
  owned adapters on frozen bases (intent-mol, intent-seq, later ESM-2 LoRA).
- **Served (not trained):** RFD4-Proteina, ESM-2, ESMFold/Boltz-2/Chai/AF3, Pinal.
- **What we add everywhere:** the agri moat (farm-knob, crop/rice arms), the NL intent
  layer, honest eval/validation, and the `/v1` loop — never fabricated numbers, never a
  blind copy, served ≠ ours.
