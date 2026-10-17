# NEUMANN Q3 cross-source transfer attempt: pre-source lock (2026-10-17 KST)

**Decision frozen before fetching / inspecting the selected full SMT2 source files.** No cherry-picked replacements.

## Two external original target sources, new to this study
1. `chc-comp/chc-comp26-benchmarks` at commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, `hopv/lia/mochi/sum_000.smt2`.
2. SAME pinned repo commit, `eldarica-misc/LIA/llreve/fib_safe.c-1_000.smt2`.

Source records are different upstream subfamilies from the opened `llreve/square_twice` source. Both are previously public; model pretraining exposure UNKNOWN. Neither original SMT2 body is to be examined by developers before committing this contract.

## Mechanism freeze
Use the **already frozen** actual 15-weight numerical loop head `cc2b34773dd095b7980fa6365518714d896e69a64dd38a37e34cf522a64cc3e6`; same 5-number polynomial accumulator formula and previously fixed relation-candidate operator families from `research/evidence/fgsr-q3-automatic-scaffold-20261017/autonomous_scaffold_once.py`. There must be NO per-target invariant edits, prompt retries, head retraining, special-case source-derived equations, or source family substitution. Only purely source-independent parsing improvements made **before fetching any target source body** are admissible.

1. Check actual path existence and SHA. Parse original SMT2 AST and list relation signatures, original quantified Horn clause count, and supported mathematical operators. If unsupported by unchanged source-domain contract (e.g. no self-loop decrement and affine accumulator recurrence, non-int predicates, invalid Horn representation, too many relations/clauses), **ABSTAIN_UNSUPPORTED_SOURCE**. Do not treat abstain as mathematical failure to solve an answerable case; but count as a **transfer-coverage failure**.
2. If domain matches, extract source recurrence with SAME `infer_loop_candidates` logic and SAME frozen 15 weights. Run generically generated source candidate grammar and Houdini within caps: 120s wall, 250 SMT calls, 4,000ms verification call. *Both* learned and **equal-information exact classical-coefficient** heads must be evaluated without any human proofs.
3. Stronger classical comparator: pinned Z3 4.13.3 cold ORIGINAL SMT-LIB under **8-second time cap**, with no source transformation. A raw direct timeout is NOT a classical impossibility proof. Learned-removed `NONE` run on source when feasible.
4. To accept actual learned transfer on source, require **all unchanged original quantified clauses**, independently checked by a second SMT-LIB parser/verifier using source-derived `define-fun` predicates. No manual filling of missing predicate structures.
5. Attempt exactly these **two** targets. Record correct denominator **0/2, 1/2, or 2/2**, including unsupported sources. Do not retune source interpreter based on inspected holdout sources and then call it clean transfer.

## Scientific claim limits
Best possible admitted result for 2/2 is `RESTRICTED_SAME_OPERATOR_FAMILY_TRANSFER_REAL_SOURCE_CONFIRMED`, not autonomous invention of a NEW operator family. Previous author-specified grammar and classical coefficient teacher may explain any success; Q1–Q7 remain OPEN regardless. Q3 novelty/necessity requires a truly different relation/operator family and evidence of advantage over strongest classical. Record cost and contamination limitations.

**Source identity and method registered before source bodies accessed.**
