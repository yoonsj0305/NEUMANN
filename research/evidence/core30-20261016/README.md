# NEUMANN CORE-30 | Source-to-recursive-definition compiler and independent certificate

**2026-10-16. Experimental verdict: HUMAN-IMPLEMENTED SOURCE RECURSIVE SEMANTICS REMOVED FROM BOTH PROPOSER AND PROOF STAGE IN ONE KNOWN CHC SOURCE. ALL Q1–Q7 REMAIN OPEN.** This is a CLASSICAL compiler, not a trained neural system.

## The concrete removed dependency
Previously CORE-29 mined bounded Horn relations from original clauses but its Z3 checker loaded human-authored total recursive definitions for count/append/rev. CORE-30's typed `compiler.py` instead reads authentic original Horn clauses, automatically infers structurally decreasing input and functional output slots, solves original constraints, synthesizes conditional recursive SMT functions and outputs `F_count`, `F_append`, `F_rev`. The **copied proof bridge's human definitions were deleted** and its default `PREFIX=None`; all verifier calls load only the generated prefix.

## Source identity
CHC-COMP 2026 source `ADTRem/isaplanner/goal52_000.smt2`, upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, official Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, 2,605B, SHA256 `3db92ef5e5f890bf6fc0a61aefddd45bfe364fcd9b39653c9f542c59bcd372f5`. Exact identity verified before original certificate.

## Executed source-first pipeline
- Generic bounded Horn least fixed point from original: **258 count facts, 121 append facts, 43 reverse facts**, used to examine 726 grounded input combinations. Four-operator human-provided grammar selects plus uniquely.
- Typed compiler synthesizes **3 total recursive SMT definitions** using actual Horn head/body clauses, not human hard-coded function semantics.
- Independent Z3 lemma base/inductive checks: **2/2 UNSAT** (count-append); reverse-count lemma **2/2 UNSAT**.
- Each authentic ORIGINAL Horn implication negated and checked separately: **11/11 UNSAT** with generated total interpretations. This certifies a satisfying model of original safe Horn program, NOT a claim that the whole CHC source returns UNSAT.
- **2 false-lemma controls SAT** and **4 poisoned authentic-source controls SAT**; corrupted count base changes the compiled semantics and blocks the plus homomorphism. Relation renaming still produces correct model; hiding goals leaves compilation unchanged.
- Full source→finite interpretation→candidate→recursion synthesis→inductive proof end-to-end approximately **5.2 seconds CPU** in this environment (one run); not an economically matched headroom measure.
- From an independently extracted release with only the pinned exact benchmark supplied separately: **pytest 11/11 PASS**, full 11/11 source proof replay PASS, archive SHA manifest all match.

## Critical limitations (do not upgrade to Q3/Q4 pass)
- The theorem **language** (off-goal count-append homomorphism and 4 candidate arithmetic ops) and the **inductive proof schema** remain research-authored.
- The input source was thoroughly examined during CORE-27–29. This is DEVELOPMENT, not blind other-family transfer.
- The generic compiler covers just a **restricted one-recursive-ADT and functional CHC subset**. Previously known `goal43` source ABSTAINS due to ambiguous recursion and `goal46` ABSTAINS due to multiple datatypes. These do NOT count as neural inference failures; no new target-specific patch was made.
- **Zero neural forward calls, zero neural training**. It cannot prove learned invention of any new abstraction language or an exact frontier-level/10x efficiency result. Its strongest comparison is another symbolic solver because IT IS symbolic.
- Q1–Q7 all remain OPEN, unchanged historical freezes and failures.

## Reproduction archive
`NEUMANN_CORE30_SOURCE_RECURSION_CERTIFIED_20261016.zip`, **27,223 bytes**, SHA-256 **`7edea8ea3d786f1e263a2017844efad1ccd3256009e7ab55a21277a1f8149c27`**, **16 entries**, internal per-file hash manifest and CRC PASS. Includes `compiler.py`, source-independent theorem bridge with removed manual recursion implementations, bounded Horn interpreter, classical candidate miner, full source-checker, tests and evidence receipts. Fetch pinned third-party SMT source separately using `fetch_pinned.py`; source omitted from ZIP pending license verification.

**Remote GitHub status:** this PR retains the textual research audit and ZIP identity. Raw ZIP bytes and model checkpoints are NOT uploaded to GitHub; they remain downloadable from the ChatGPT conversation. This PR stays draft.

## ONLY NEXT DECISIVE EXPERIMENT
Freeze a learner that consumes the complete typed Horn source and writes a full *NEW* typed helper predicate including base and recursive rules, without researcher-specified lemma schema. Independently prove it under original constraints and transfer to different untouched external families, compared against an identically privileged strong classical synth engine at full train+parse+proof+verify costs. All Qs remain OPEN until proven.