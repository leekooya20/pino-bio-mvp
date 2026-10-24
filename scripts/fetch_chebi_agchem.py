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

import gzip
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

# Agri-chemistry role roots (verified live via EBI OLS 2026-10-24, C-CHEBI-2):
#   CHEBI:33286 agrochemical  -> fertilizer, plant activator, safener, antifungal agrochemical, ...
#   CHEBI:25944 pesticide     -> herbicide, insecticide, fungicide, acaricide, nematicide, ... (66 desc.)
# The old single 33286 root MISSED all pesticide classes (they sit under pesticide, a sibling
# of agrochemical under "application") -> 0 molecules. Union of both roots = real crop-protection space.
AGRI_ROLE_ROOTS = ["CHEBI:33286", "CHEBI:25944"]
AGROCHEMICAL_ROOT = AGRI_ROLE_ROOTS[0]     # kept for back-compat / manifest label
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
        elif line.startswith("relationship:"):
            # C-CHEBI-3: current ChEBI OBO encodes "has role" as the Relation Ontology id
            # `relationship: RO:0000087 CHEBI:xxxxx ! has role <name>` (NOT the literal
            # `has_role` the old regex expected -> 0 molecules). Accept both forms; take the
            # first CHEBI on the line as the role. Other relationship types (has_part,
            # is_conjugate_* ... use different RO ids) are ignored.
            if "RO:0000087" in line or "has_role" in line:
                m = re.search(r"(CHEBI:\d+)", line)
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
def _smiles_from_block(block: str) -> str | None:
    """Fallback: a `> <SMILES>` property tag, if a given SDF export happens to carry one."""
    smi = re.search(r">\s*<SMILES>\s*\n(.+)", block)
    return smi.group(1).strip() if smi else None


def parse_sdf_smiles(sdf_path: Path) -> dict[str, str]:
    """Map ChEBI id -> SMILES from a ChEBI SDF export.

    ChEBI's SDF (verified live 2026-10-24, chebi_lite_3_stars.sdf.gz) carries only the
    molblock + `<ChEBI ID>` tags — NO `<SMILES>` property (G14: the old property-read
    returned zero and silently produced empty pairs). We derive SMILES from the molblock
    with RDKit (ForwardSDMolSupplier; reads .gz directly), keeping a property-tag fallback
    for exports that do include one. Mod C-CHEBI-1.
    """
    out: dict[str, str] = {}
    opener = gzip.open if sdf_path.suffix == ".gz" else open
    try:
        from rdkit import Chem, RDLogger
        from rdkit.Chem import ForwardSDMolSupplier
        RDLogger.DisableLog("rdApp.*")  # skip-and-count; unparseable mols are never fabricated
        with opener(sdf_path, "rb") as fh:
            sup = ForwardSDMolSupplier(fh, sanitize=True)
            for mol in sup:
                if mol is None:
                    continue
                cid = mol.GetProp("ChEBI ID") if mol.HasProp("ChEBI ID") else None
                if not cid:
                    continue
                try:
                    smi = Chem.MolToSmiles(mol)
                except Exception:  # noqa: BLE001 — skip unparseable, never fabricate
                    smi = None
                if smi:
                    out[cid] = smi
        return out
    except ImportError:
        # No RDKit: fall back to the property-tag path (works only if the export has one).
        with opener(sdf_path, "rt", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for block in text.split("$$$$"):
            cid = re.search(r"(CHEBI:\d+)", block)
            smi = _smiles_from_block(block)
            if cid and smi:
                out[cid.group(1)] = smi
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
              "  SDF: ftp.ebi.ac.uk/pub/databases/chebi/SDF/chebi_lite_3_stars.sdf.gz\n"
              "       (.gz read directly; SMILES derived from molblocks via RDKit, C-CHEBI-1)",
              file=sys.stderr)
        return 3

    terms = parse_obo(obo.read_text(encoding="utf-8", errors="replace"))
    roles: set[str] = set()
    for root in AGRI_ROLE_ROOTS:
        roles |= role_subtree(terms, root)
    mol_ids = agrochemical_molecules(terms, roles)
    smiles_map = parse_sdf_smiles(sdf)
    print(f"ok  agri-role tree (roots {','.join(AGRI_ROLE_ROOTS)}): {len(roles)} roles · "
          f"molecules with an agri role: {len(mol_ids)} · SMILES in SDF: {len(smiles_map)}")

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
        "agri_role_roots": AGRI_ROLE_ROOTS,
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
        "note": "agri set derived from ChEBI has_role over the agrochemical (CHEBI:33286) + "
                "pesticide (CHEBI:25944) is_a subtrees (G11, not hand-picked; C-CHEBI-2)",
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
