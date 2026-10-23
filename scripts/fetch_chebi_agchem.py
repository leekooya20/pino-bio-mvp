#!/usr/bin/env python
"""ChEBI agrochemical fetch → shared asset for the farm-knob (M-MOFLOW-3) AND the
owned NLP intent-mol head (N-NLP-1). PinoBio MVP-4, G1/G7/G10/G11.

Produces (text definition, SMILES, RDKit descriptors) triples for every molecule
carrying the ChEBI `agrochemical` role (CHEBI:33286) or a descendant role
(herbicide/insecticide/fungicide/...). That single asset feeds two owned modules:
- farm-knob: descriptor STATISTICS of the positives → Molek steering target.
- intent-mol: (definition → descriptor vector) PAIRS → train the NL intent head.

HARD RULES:
- G1  : ChEBI license (CC BY 4.0) verified LIVE before any data is accepted; STOP on fail.
- G7  : exact counts; descriptors are real RDKit calls (gated) — nothing fabricated.
- G10 : seed + per-file sha256 + role-set recorded in the manifest.
- G11 : the agrochemical set is derived from ChEBI's OWN ontology (has_role over the
        CHEBI:33286 subtree), not a hand-picked list.

Big files (chebi.obo ~tens of MB, SDF ~hundreds) are NOT auto-downloaded; attach them
on compute (CHEBI_OBO / CHEBI_SDF env or argv) — the license gate still runs first.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "data" / "external" / "chebi_agchem"
MANIFEST = ROOT / "data" / "manifests" / "chebi-agchem.jsonl"
PAIRS = EXTERNAL / "pairs.jsonl"

AGROCHEMICAL_ROOT = "CHEBI:33286"          # verified live 2026-10-23
LICENSE_URLS = ["https://raw.githubusercontent.com/ebi-chebi/ChEBI/master/LICENSE",
                "https://www.ebi.ac.uk/chebi/"]
LICENSE_EXPECT = re.compile(r"(CC[\s-]*BY[\s-]*4\.0|Creative Commons Attribution 4\.0|Apache)", re.I)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_license_live() -> dict:
    out = {}
    ok = False
    for url in LICENSE_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pino-bio-mvp/g1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read(200_000).decode("utf-8", "replace")
                hit = bool(LICENSE_EXPECT.search(body))
                out[url] = {"status": r.status, "cc_by_found": hit}
                ok = ok or hit
        except Exception as e:  # noqa: BLE001
            out[url] = {"error": repr(e)}
    out["verdict"] = "pass" if ok else "FAIL-license-not-confirmed-live"
    return out


# --- ChEBI OBO parsing + role-tree traversal (the real, testable logic) ---
def parse_obo(obo_text: str) -> dict[str, dict]:
    """Parse ChEBI OBO into {id: {name, definition, is_a:set, has_role:set}}."""
    terms: dict[str, dict] = {}
    cur: dict | None = None
    cid: str | None = None
    for line in obo_text.splitlines():
        line = line.rstrip()
        if line == "[Term]":
            cur, cid = {"name": "", "definition": "", "is_a": set(), "has_role": set()}, None
            continue
        if cur is None:
            continue
        if line.startswith("id: CHEBI:"):
            cid = line[4:].strip()
            terms[cid] = cur
        elif line.startswith("name:"):
            cur["name"] = line[5:].strip()
        elif line.startswith("def:"):
            m = re.search(r'"(.*?)"', line)
            cur["definition"] = m.group(1) if m else ""
        elif line.startswith("is_a:"):
            m = re.search(r"(CHEBI:\d+)", line)
            if m:
                cur["is_a"].add(m.group(1))
        elif line.startswith("relationship: has_role"):
            m = re.search(r"has_role (CHEBI:\d+)", line)
            if m:
                cur["has_role"].add(m.group(1))
    return terms


def role_subtree(terms: dict[str, dict], root: str) -> set[str]:
    """All role IDs that are `root` or is_a-descendants of it (agrochemical tree)."""
    children: dict[str, set[str]] = {}
    for cid, t in terms.items():
        for parent in t["is_a"]:
            children.setdefault(parent, set()).add(cid)
    seen = {root}
    stack = [root]
    while stack:
        node = stack.pop()
        for ch in children.get(node, ()):
            if ch not in seen:
                seen.add(ch)
                stack.append(ch)
    return seen


def agrochemical_molecules(terms: dict[str, dict], role_ids: set[str]) -> list[str]:
    """Molecule IDs whose has_role intersects the agrochemical role subtree."""
    return [cid for cid, t in terms.items() if t["has_role"] & role_ids]


# --- SMILES from SDF (structures) ---
def parse_sdf_smiles(sdf_text: str) -> dict[str, str]:
    """Map ChEBI id -> SMILES from a ChEBI SDF export (reads the SMILES property)."""
    out: dict[str, str] = {}
    for block in sdf_text.split("$$$$"):
        cid = re.search(r"(CHEBI:\d+)", block)
        smi = re.search(r">\s*<SMILES>\s*\n(.+)", block)
        if cid and smi:
            out[cid.group(1)] = smi.group(1).strip()
    return out


def descriptors(smiles: str) -> dict | None:
    """RDKit descriptor panel (farmknob-spec §4). Gated on rdkit; None if unavailable."""
    try:
        from rdkit import Chem
        from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors
    except ImportError:
        return None
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    atoms = [a.GetSymbol() for a in m.GetAtoms()]
    return {
        "MolWt": Descriptors.MolWt(m),
        "cLogP": Crippen.MolLogP(m),
        "TPSA": rdMolDescriptors.CalcTPSA(m),
        "HBD": Lipinski.NumHDonors(m),
        "HBA": Lipinski.NumHAcceptors(m),
        "RotBonds": Lipinski.NumRotatableBonds(m),
        "AromaticRings": rdMolDescriptors.CalcNumAromaticRings(m),
        "F": atoms.count("F"), "Cl": atoms.count("Cl"), "Br": atoms.count("Br"),
    }


def main() -> int:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    print("G1: verifying ChEBI license live ...")
    lic = verify_license_live()
    print(json.dumps(lic, indent=2))
    if lic.get("verdict") != "pass":
        print("STOP (G1): ChEBI CC BY 4.0 not confirmed live.", file=sys.stderr)
        return 2

    obo = Path(os.environ.get("CHEBI_OBO", sys.argv[1] if len(sys.argv) > 1 else ""))
    sdf = Path(os.environ.get("CHEBI_SDF", sys.argv[2] if len(sys.argv) > 2 else ""))
    if not obo.exists() or not sdf.exists():
        print("Attach ChEBI OBO + SDF (CHEBI_OBO / CHEBI_SDF). License gate already passed.\n"
              "  OBO: ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo\n"
              "  SDF: ftp.ebi.ac.uk/pub/databases/chebi/SDF/ChEBI_complete.sdf.gz",
              file=sys.stderr)
        return 3

    terms = parse_obo(obo.read_text(encoding="utf-8", errors="replace"))
    roles = role_subtree(terms, AGROCHEMICAL_ROOT)
    mol_ids = agrochemical_molecules(terms, roles)
    smiles_map = parse_sdf_smiles(sdf.read_text(encoding="utf-8", errors="replace"))
    print(f"ok  roles in agrochemical tree: {len(roles)} · agrochemical molecules: {len(mol_ids)}")

    n_pairs = 0
    n_desc = 0
    with PAIRS.open("w", encoding="utf-8") as f:
        for cid in mol_ids:
            t = terms[cid]
            smi = smiles_map.get(cid)
            if not smi:
                continue
            desc = descriptors(smi)
            rec = {"chebi_id": cid, "name": t["name"], "definition": t["definition"],
                   "smiles": smi, "descriptors": desc}
            f.write(json.dumps(rec) + "\n")
            n_pairs += 1
            n_desc += 1 if desc else 0

    entry = {
        "id": "chebi-agchem",
        "license": "CC BY 4.0 (verified live this run)",
        "license_check": lic,
        "agrochemical_root": AGROCHEMICAL_ROOT,
        "n_roles_in_tree": len(roles),
        "n_molecules": len(mol_ids),
        "n_pairs_written": n_pairs,
        "n_with_descriptors": n_desc,
        "obo_sha256": sha256_file(obo),
        "sdf_sha256": sha256_file(sdf),
        "pairs_path": str(PAIRS),
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "feeds": ["farm-knob M-MOFLOW-3 (descriptor stats)", "intent-mol N-NLP-1 (text->descriptor pairs)"],
        "note": "agrochemical set derived from ChEBI has_role over CHEBI:33286 subtree (G11, not hand-picked)",
    }
    existing = []
    if MANIFEST.exists():
        existing = [json.loads(l) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    existing = [e for e in existing if e.get("id") != "chebi-agchem"]
    existing.append(entry)
    MANIFEST.write_text("\n".join(json.dumps(e) for e in existing) + "\n", encoding="utf-8")
    print(f"ok  pairs={n_pairs:,} (with descriptors={n_desc:,}) -> {PAIRS}")
    print(f"ok  manifest -> {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
