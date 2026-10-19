# Q2 Original-Source-Bound Proof Trust Audit | 2026-10-19

Result: SCOPED PASS, not global Q2 or Q1-Q7.

## Root cause
The legacy replay_exported_queries(receipt) only checked that three self-hashed SMT-LIB documents each solved UNSAT. It did not establish that the documents were derived from trusted original Pre, Trans and Post. Three attacker-supplied (assert false) assertions with recomputed hashes actually passed the legacy unbound replay. This is a vulnerability of untrusted receipt replay, NOT retroactive invalidation of prove_source original inductive VC generation.

## Repair
New replay_original_source_bound(trusted_original_path, receipt) requires exact trusted source bytes/hash and original inductive certificate type; independently rebuilds the original parsed Pre, Trans, Post and inferred invariant, rechecks actual original 3VC conditions and matches source route/invariant/semantic XOR. Serialized SMT2 SHA differs even for genuine identical VCs because Z3 reorders metadata and let bindings; therefore the repaired verifier parses each received and reconstructed script, and compares raw unsimplified Z3 assertion sexpr ASTs (never logical equivalence, because all UNSAT formulas are equivalent to false). It does not admit source-only SPACER decisions as inductive proof certificates. Legacy unbound solver-only replay remains for historical compatibility but MUST NOT be used as evidence of an original source proof.

## Frozen actual test evidence
Preregistered before implementation in Issue #245 comment 6260892966. Pinned already-opened LoopInvGen commit 6ac90265b11431c9477dfbd33e3e3380234c0499. Exactly two legitimate actual source programs: 2013.OOPSLA_Hola/hola.05.sl (structural) and 2015.FMCAD_Acceleration/bk-nat.sl (Post-only).
Initial Actions #39208746245 failed before original execution due to Python module import path; preserved artifact 12166810931. After environment-only PYTHONPATH repair, Actions #39208914861 recorded first genuine strict verifier FAIL (legitimate proofs rejected). Diagnostic Actions #39209125579 identified identical original proof/invariant but different SMT document SHA hashes only, preserved. No source/gates altered.
First corrected valid Actions #39209341553 SUCCESS. Artifact 12166564686 with GitHub ZIP digest sha256:29715c3fd9ece093ca3bc4b811f1faa92ca99bd8525cea15d337a0b6077950f7; original result JSON SHA256 df0a2ee008822ea2d0cd35a38009eaa8bfa1aec0bbaf20d26d389317a76c17b0. Legacy forged triple UNSAT accepted TRUE, 2/2 legitimate source-bound replay PASS, all 6 hostile classes rejected: forged triple unsat with recomputed hashes, forged/rehashed invariant, missing third VC, changed proof status, cross-source receipt reuse and modified source bytes. Original 18-source Q3 CLI regression Actions #39209341510 remained SUCCESS.

## Scientific scope
Q2_ORIGINAL_SOURCE_BOUND_ARCHIVAL_REPLAY = PASS_SCOPED. Q2_LEGACY_UNBOUND_UNSAT_REPLAY = NOT_ORIGINAL_PROOF_AUTHORITY. Q3_BOUNDED_3VC = PRESERVED. Q3_LEARNED_NEW_OPERATORS, GLOBAL_Q1_Q7 = OPEN.
The strict verifier reuses the same frozen source-level generator and Z3 backend, not a fully independent proof assistant. Two opened sources are audit regressions, not Q6 transfer evidence. No model/GPU/API/training/sealed cohort access. Generic QA without trusted formal semantics cannot inherit this particular 3VC certification.

Source: experiments/q3_source_prove.py; research/evidence/q2-source-bound-proof-integrity-20261019/first_trusted_original_redteam.py; .github/workflows/q2-original-source-proof-binding.yml.
Research links: https://github.com/yoonsj0305/NEUMANN/issues/245 and https://github.com/yoonsj0305/NEUMANN/pull/246 and https://github.com/yoonsj0305/NEUMANN/actions/runs/39209341553.