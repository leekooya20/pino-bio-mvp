# NLP intent layer — natural language → OUR generators (owned)

Directive (Stan, 2026-10-23): *"add NLP to our models"* — not just serving Pinal, but
giving **our own** generators (Molek, Seqgen) a natural-language front-end we own.

This is capability **A8** and is distinct from A7 (served Pinal):

| | A7 Pinal | **A8 NLP intent (this)** |
|---|---|---|
| Whose model | theirs (16B, served) | **ours** |
| What we own | nothing (we call it) | **the projection heads + their training** |
| Compute | their GPU / online server | Kaggle T4 (heads are tiny) |

## Architecture — frozen open encoder + OUR trained projection

```
natural-language intent  ──►  [open text encoder, frozen]  ──►  text embedding e_t
                                                                      │
                                                 OUR trained projection W (small)
                                                                      │
                 ┌────────────────────────────────┴─────────────────────────────┐
                 ▼                                                                ▼
   intent-mol head (N-NLP-1)                                     intent-seq head (N-NLP-2)
   text → Molek descriptor target vector                        text → Seqgen control embedding
   (steers the farm-knob region)                                (prefix/condition, Pinal/SaProt-T style)
```

Only the **projection heads** are trained and owned. The base text encoder is frozen
and open-licensed, so the whole owned part is tiny and Kaggle-trainable (G9: this is an
owned *adapter*, not a from-scratch 16B — honest about scale).

## Owned modifications (ledger IDs)

| ID | What | Trains on | Steers |
|---|---|---|---|
| **N-NLP-1** `intent-mol` | text → molecular descriptor-target vector | **ChEBI** (CC BY 4.0): each entry's natural-language *definition* ↔ its RDKit descriptors — free (text, molecule) pairs | Molek farm-knob (M-MOFLOW-3 region steering) |
| **N-NLP-2** `intent-seq` | text → Seqgen control embedding (trainable matrix W, Pinal's p(s|c,t) pattern) | UniProt annotation text ↔ sequence (G1 live-verify at download) | Seqgen-small conditioning |
| **N-NLP-3** | retrieval grounding option: use **ProTrek** (MIT, protein-text aligned) text encoder for the protein arm instead of MiniLM | — | sharper protein-text alignment |
| **N-NLP-4** | honest intent gate: an out-of-distribution flag when a prompt is far from any training-pair cluster (don't pretend to understand arbitrary text) | — | both |

## Base encoders (open, G1-verified live 2026-10-23)

| Encoder | License | Use |
|---|---|---|
| `sentence-transformers/all-MiniLM-L6-v2` | **Apache-2.0** (LICENSE file) | general-English molecule-intent arm (384-d) |
| `westlake-repl/ProTrek_650M` text encoder | **MIT** | protein-intent arm (protein-text aligned) |

## What "enough" means (G7 sufficiency, mirrors the farm-knob)

Trained intent heads count as working only when, on held-out (text, target) pairs:
1. **recovery** — predicted descriptor/control target lands near the true target of the
   described molecule/protein (reported per-dimension, not a single blended score);
2. **steering effect** — Molek/Seqgen conditioned on the predicted target actually shift
   toward the described region vs unconditioned (with novelty preserved);
3. **honest OOD** — prompts outside training-pair clusters are flagged (N-NLP-4), not
   silently answered.
Hard-fail reported in the ledger; nothing claimed before measured.

## Hard-rule map

| Rule | Here |
|---|---|
| G9 scope | Stan-authorized scope addition 2026-10-23; owned adapter, NOT a from-scratch large model |
| G1 licenses | MiniLM Apache-2.0 + ProTrek MIT + ChEBI CC BY 4.0 + UniProt (live-verify) — all in `configs/licenses.yaml` |
| G11 fidelity | projection approach read from Pinal (trainable W: e_t → PLM space) + SaProt-T; documented, not blind |
| G7 honesty | untrained now → no claims; OOD gate; owned numbers never blended with served Pinal/ESM-2 |
| G10 | `configs/nlp-intent.yaml` carries seed + will carry config hash at first run |

## Status

DRAFT design + config locked 2026-10-23. Implementation order: **intent-mol first**
(N-NLP-1) because its training pairs (ChEBI text↔descriptors) come free with the
farm-knob data — it can train the moment ChEBI is fetched, independent of Molek's
checkpoint. intent-seq (N-NLP-2) follows Seqgen. Nothing measured yet.
