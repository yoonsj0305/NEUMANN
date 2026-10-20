# NEUMANN 1 Q3 Gate R | Original source semantics and mixed-state independent proof

**Date 2026-10-20 KST. Result: bounded Gate R source-semantic subgate PASS 2/2 + formerly UNKNOWN authentic mixed Bool/Int original safety 3VC PASS. Global Q3, full Gate R and Gate V OPEN. Pure classical proof path, no learned operator invented.**

## Exact source identities and honest posthoc scope
All real original source files were previously OPENED during G1 negative results. This study does NOT qualify as fresh blind neural-G1 transfer. Source repository SyGuS-Org/benchmarks at immutable Git revision 13c8deb68a873635879c9a69bc78caebd340f646:
- lib/Inv_Track/xujie_code2inv/1.c.sl, exact Git blob 859bae24a9f26044a40a3c97f1d2e5fc08504f06; two source OR transition branches over 10 Int state coordinates, many unspecified next-state coordinates.
- lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl, exact Git blob 8490b3e25ff7d462a7405e68e742be1abb35b8f8; 21 Bool state, 7 Int state, exactly 31 global source-declared Int nondeterministic inputs. Older source AST parser aborted UNBOUND_ORIGINAL_SYMBOL because it did not accept declared globals. No state or nondet symbol is set to a constant in this study.

## New genuinely shared source-semantic representation
The new source parser inherits earlier typed helpers and adds ONLY declared SyGuS (declare-var) inputs to the typed environment, enforcing declaration uniqueness, sort correctness, matching exact 28-state argument order, 2x original physical state for actual transitions and resource caps. Independently, Z3's native SMT parser reads original unmodified define-fun bodies from SyGuS source, with only formal SyGuS declare-var rewritten into SMT-LIB declare-const for parser compatibility. For each source Pre/Trans/Post, the typed reconstructed Boolean expression is checked for XOR-with-native UNSAT using native Z3 AND SHA-pinned standalone official cvc5 1.4.2. Pre SAT, original Trans SAT, NotPost SAT dual proved on each. If any mismatch or unsupported expression, no PASS.

Xujie's two explicit original OR branches retained AS-IS as relational constraints, NOT invented deterministic assignments for underdetermined physical next variables. Exact original Trans XOR Or(branch1,branch2) UNSAT independently in both engines; deliberately dropping branch 0 produces actual original source SAT counterexample checked by both solvers (negative control); both branches individually compatible with source Pre SAT.

First source semantic GitHub [Actions #39442974999](https://github.com/yoonsj0305/NEUMANN/actions/runs/39442974999) **SUCCESS**, original artifact #12274947706, pristine source receipt JSON SHA256 8cdb061783a6e52e2c9a603c1f17a362ccf0ae9b28bb8b26f62a50fd02fbcf03, original downloaded artifact ZIP SHA256 f32bb530971b254ef6dcbcea900e8a3d4f54738ee6dbc2924b51d5f809eb1b3f, CRC PASS. Exact original Pre/Trans/Post parity Z3+cvc5 3/3 on xujie, 3/3 on DRAGON_1. Source case wall 45.350ms and 63.192ms, entire 108.794ms on one runner excluding dependency/checkout.

## Newly CLOSED original proof gap in DRAGON_1
The same typed source parser is then connected to the previously available baseline official cvc5 SyGuS synthesizer, whose source-invariant proposal was never admitted as a safety proof. The candidate source formal Bool signature is bound to EXACT 28 original physical state sorts and names and recompiled by the typed interpreter; the original source Pre/Trans/Post are parsed and semantics-XOR certified anew against raw original source definitions. An invariant's native original 3Vcs are formed from EXACT original native predicates, not reconstructed postcondition substitutions or hidden oracle labels:
- Pre AND NOT I: **Z3 UNSAT, independent cvc5 UNSAT**
- I AND original Trans AND NOT I': **Z3 UNSAT, independent cvc5 UNSAT**
- I AND NOT original Post: **Z3 UNSAT, independent cvc5 UNSAT**
All 3/3 independently verified per backend BOTH for previously certified xujie and, importantly, FORMERLY_UNVERIFIED DRAGON_1. This resolves the prior source verifier's UNBOUND_ORIGINAL_SYMBOL uncertainty for this exact external mixed state source, and certifies actual unchanged published safety.

First second-stage source-bound Actions [#39443538225](https://github.com/yoonsj0305/NEUMANN/actions/runs/39443538225) **SUCCESS**, artifact #12274283849; original JSON SHA256 37e878dfadf50b1c601feab0db5a38a20099075b70ff97318628734f80eda5e3; downloaded artifact ZIP SHA256 e5d4d8a5a6eb012a7da8f9db20da8ffc318dab3c9c254fdf25e828e5f086df04; CRC PASS. Measured total two-source original synth + dual 3VC wall 5219.429ms, with 4949.107ms xujie and 270.043ms DRAGON_1, same one GitHub runner, NOT baseline neural iso-capability cost benchmark.

## Honest Q3 disposition
Q3_GATER_RELATIONAL_SOURCE_SEMANTICS: SCOPED_PASS (2 actual opened originals, two backends and negative control).
Q3_DRAGON_1_ORIGINAL_CLASSICAL_SAFETY: POSTHOC_SCOPED_PASS with original native Z3/cvc5 3VC 3/3 each, formerly no independent original proof.
Q3_GATE_R_LEARNED_NEW_OPERATOR: NOT_DEMONSTRATED. This new frontend can REPRESENT nonlinear multi-branch and typed mixed state, but it does not yet make a learned constructor GENERATE a useful new mathematical operator.
Q3_GATE_V_FRESH_SOURCE_CAUSAL_LEARNED_PROOF: NOT_STARTED. First published/original G1 failures unchanged.
Q3_GLOBAL=OPEN; Q1–Q7 GLOBAL OPEN; Q4/5 iso-capability end-to-end cost and Q7 frontier are not demonstrated; GPU/paid APIs used ZERO.

## Next single high-value hypothesis
Build a bounded **typed conditional relational structure proposal** for source-preserving Int+Bool/Nondet AST, with sound grammar growth and learned control only when exact classical proposal cannot achieve an equal-information result. Freeze genuinely new author-origin original programs and a strong reference cvc5 SyGuS/PDR/CEGIS, model parameters and budget BEFORE opening target code. No further training on previously opened xujie/DRAGON original. Source parser reusability is demonstrated only on these 2 actual originals, not all SyGuS.

Implementation PR #319: https://github.com/yoonsj0305/NEUMANN/pull/319
Original typed/relational check source research/evidence/q3_gater_relational_mixed_20261020/first_actual_nondet_and_branch_originals.py
Original solver-candidate independent 3VC research/evidence/q3_gater_relational_mixed_20261020/posthoc_independent_source_cvc5_invariant_3vc.py