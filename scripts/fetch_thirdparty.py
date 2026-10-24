#!/usr/bin/env python
"""Pin the reference code we replicate (G11 + G10).

Clones the reference repos into third_party/ at the current HEAD, records
SHA + license + timestamp in third_party/PINNED.json, and asserts a LICENSE
file exists in each (fail fast if a repo lost its license).

Usage: python scripts/fetch_thirdparty.py
Never modify third_party code in place — our deltas are patches/ files.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TP = ROOT / "third_party"

REPOS = [
    # (name, url, expect-license-spdx)
    ("moflow", "https://github.com/calvin-zcx/moflow.git", "MIT"),
    ("moses", "https://github.com/molecularsets/moses.git", "MIT"),
]


def sh(args: list[str], cwd: Path | None = None) -> str:
    out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
    return out.stdout.strip()


def find_license(dest: Path) -> Path | None:
    """Case-insensitive LICENSE* lookup (reference repos use mixed names: moflow='License.md', moses='LICENSE')."""
    for p in sorted(dest.iterdir()):
        if p.is_file() and p.name.lower().startswith("license"):
            return p
    return None


def main() -> int:
    TP.mkdir(exist_ok=True)
    pinned: dict[str, dict] = {}
    for name, url, expect in REPOS:
        dest = TP / name
        if not (dest / ".git").exists():
            print(f"clone {name} ...")
            sh(["git", "clone", "--depth", "1", url, str(dest)])
        sha = sh(["git", "rev-parse", "HEAD"], cwd=dest)
        license_file = find_license(dest)
        if not license_file:
            print(f"FAIL: {name} has no LICENSE file — G1/G11: do not proceed", file=sys.stderr)
            return 1
        text = license_file.read_text(encoding="utf-8", errors="ignore")[:2000]
        if expect.split()[0].lower() not in text.lower():
            print(f"FAIL: {name} license text does not mention {expect} — verify manually", file=sys.stderr)
            return 1
        pinned[name] = {
            "url": url,
            "sha": sha,
            "license_expected": expect,
            "license_file": str(license_file.relative_to(ROOT)),
            "pinned_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        print(f"ok  {name} @ {sha[:12]} ({expect})")

        # Apply our documented modification patches (never silent, one file per mod ID).
        patches_dir = ROOT / "patches"
        if name == "moflow" and patches_dir.exists():
            for bf in sorted(patches_dir.glob("M-MOFLOW-*.patch")):
                try:
                    sh(["git", "apply", "--check", str(bf)], cwd=dest)   # fails loudly if context drifted
                    sh(["git", "apply", str(bf)], cwd=dest)
                    print(f"ok  applied {bf.name} to moflow")
                except subprocess.CalledProcessError:
                    # likely already applied on a re-run — verify reversibility as proof
                    sh(["git", "apply", "--reverse", "--check", str(bf)], cwd=dest)
                    print(f"ok  {bf.name} already applied")

        # M-MOSES-1 (py3.13): the moses package ships its own SA_Score/sascorer.py with
        # `from rdkit.six import iteritems`; modern RDKit (>=2024) removed rdkit.six. Same
        # class of fix as M-MOFLOW-9 but for the moses copy. Robust text replace (the file
        # is the classic stable sascorer) rather than a context-sensitive git patch.
        if name == "moses":
            sca = dest / "moses" / "metrics" / "SA_Score" / "sascorer.py"
            if sca.exists():
                txt = sca.read_text(encoding="utf-8")
                if "from rdkit.six import iteritems" in txt:
                    txt = txt.replace(
                        "from rdkit.six import iteritems",
                        "iteritems = lambda d: d.items()  # M-MOSES-1 (py3.13: rdkit.six removed)")
                    sca.write_text(txt, encoding="utf-8")
                    print("ok  applied M-MOSES-1 (sascorer rdkit.six) to moses")


    (TP / "PINNED.json").write_text(json.dumps(pinned, indent=2), encoding="utf-8")
    print(f"wrote {TP / 'PINNED.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
