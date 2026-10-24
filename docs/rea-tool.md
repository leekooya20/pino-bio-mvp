# REA in our arsenal — where "Reverse Engineer Anything" is the unfair advantage

Tool: `morluto/rea` (MIT) — MCP + CLI that drives Ghidra / IDA / Hopper / JADX / Binwalk
on CLOSED / COMPILED targets (native, Electron, firmware, packaged, APK, browser).
Decision (Stan delegated, 2026-10-24): placed below; armed, fired only on real targets.

## The rule (honest, from REA's own docs + our G-rules)
- **Open source → do NOT use REA.** Read the code/papers (G11). We just demonstrated this:
  found MoFlow's published FCD baseline + its known distributional weakness from literature
  in minutes. REA explicitly says "skip for ordinary source-repository analysis."
- **Closed / binary / shipped-only → REA is unbeatable.** That's its lane.
- **Clean-room always (G11 + REA's design):** study BEHAVIOR, rebuild independently. Never
  copy code or assets. Reverse-engineering a third party's shipped product has IP/legal
  weight → a quick legality/scope check (G1/export-review mindset) before any teardown.

## Where it's the edge for a PH agri-bio program

1. **Served-artifact provenance audit (first, cleanest mission).**
   Verify a served model's shipped binary/container actually matches its claimed open
   source — e.g., does `nvidia/RFD4-Proteina` (NIM container / weights) match the open
   `RosettaCommons/RFD4-Proteina` source? REA's famous "compile → byte-for-byte match"
   trick. Ethical, in-scope, and a TRUST unfair-advantage: we can *prove* our served
   models are what they claim (aligns with G7 verify-don't-assume, G8, G1 provenance).

2. **Closed competitor agri/chem tool teardown (the big play, when one exists).**
   Commercial pesticide/agrochem predictors, crop-disease ID apps (APK → JADX), or
   binary-only crop-AI tools: dissect how a feature works, rebuild clean-room for PH crops.
   Needs a CONFIRMED target + legality check first.

3. **Binary-only model / firmware** in the crop-tech space (devices, edge models) — if we
   ever need to understand one we can't get source for.

## Current status
- **Armed, not fired.** Our entire scientific stack is open source → no REA target today
  (reading beats Ghidra on open code). REA's first real mission = a served-artifact
  provenance audit OR a confirmed closed competitor target.
- **Trigger:** a concrete closed/binary target + a 2-minute legality/scope check. Then I
  clone `morluto/rea`, run its readiness check, point it at the target, and report
  clean-room findings.
- Not speculatively installing Ghidra/IDA "just in case" — that's waste, not maximizing.

## One-line
REA = our reverse-engineering edge for CLOSED things. Open things we out-read. We keep it
sharp and fire it only where it's genuinely unbeatable — starting with proving our served
models are legit, and ready for any closed competitor tool the moment one appears.
