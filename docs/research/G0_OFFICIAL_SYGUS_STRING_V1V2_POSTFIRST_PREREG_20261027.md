# NEUMANN 1 | SGI official PBE_SLIA v1-to-v2 normalization postFIRST prereg 2026-10-27

**THIS IS POST-FIRST RESEARCH** after the original independent strong C first hash `a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5` and failed four cvc5 1.1.2 parse errors on exactly four external official SyGuS original PBE_SLIA EUPHONY tasks. Preserve first as **4/16 ERROR**, never substitute or rewrite originals. Q1–Q7 OPEN, G1 HOLD.

Original pinned official repository `SyGuS-Org/benchmarks` @ `13c8deb68a873635879c9a69bc78caebd340f646`; ONLY these four preselected original source files, unchanged IDs:
1. `lib/PBE_SLIA_Track/euphony/convert-text-to-numbers.sl`
2. `lib/PBE_SLIA_Track/euphony/find-nth-occurrence-of-character.sl`
3. `lib/PBE_SLIA_Track/euphony/phone-5-short.sl`
4. `lib/PBE_SLIA_Track/euphony/35744094.sl`

Post-first *fixed* grammar-normalization single pipeline: independently published `SyGuS-Org/tools` official Python converter, exact Git checkout `master` commit recorded BEFORE conversion and frozen in result; Python `ply` and `pyparsing` dependencies; `PYTHONPATH=source_tools python3 -m sygus.bin.convert -s 1 -t 2 ORIGINAL` writes converted text to temporary .sl, no manual edits, and source/translated SHA256 captured. Require same count of `constraint` statements and one `check-synth`; if not, mark `HOLD_TRANSLATION_CONSTRAINT_CHANGE`. Native original strong cvc5 1.1.2 `--lang=sygus2` on converted file with original C budget max 12 CPU s /15 wall s /800MiB RSS. **Exactly one attempt per filename, no manual fallback or extra syntax tricks**. Freeze all original conversion stderr/stdout+native stdout, original source hash, converter Git SHA and raw original first hash.

A translated and solved candidate is NOT automatically the same semantics as original v1 program without separate formal translation validation; label `CONVERTED_CANDIDATE_UNVERIFIED`, not PASS. A timeout is a timed CLASSICAL limit *after* syntax normalization, not evidence original native v2 accepted it. A conversion failure is tool incompatibility, not AI gap. No model weights involved.

Success criteria of study: determine whether four apparent classical failures in original native screen were entirely parser/version incompatibility, and whether canonical conversion reveals real solver computational headroom. Do not combine original 16 first counts with post-first normalized claims into new prospective first.