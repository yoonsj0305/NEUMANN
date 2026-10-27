# NEUMANN G0 interpolation obligation verifier, independent-source prospective freeze
Date 2026-10-27 KST. No Q1-Q7 closure. All preexisting original receipts unchanged.

**Before opening any of the following external original file CONTENTS**, fix repository `ultimate-pa/smtinterpol` master **commit f65e98f05203f1d2801bf5bd121766bfcd6451ec** and 12 exact test paths:
1. SMTInterpol/web/interpolation.smt2
2. SMTInterpolTest/test/interpolation/cctest001.smt2
3. SMTInterpolTest/test/interpolation/cctest002.smt2
4. SMTInterpolTest/test/interpolation/arraytest001.smt2
5. SMTInterpolTest/test/interpolation/arraytest002.smt2
6. SMTInterpolTest/test/interpolation/arrayoffset001.smt2
7. SMTInterpolTest/test/interpolation/arrayoffset002.smt2
8. SMTInterpolTest/test/interpolation/arrayclosetest001.smt2
9. SMTInterpolTest/test/interpolation/arrayclosetest002.smt2
10. SMTInterpolTest/test/interpolation/constarr001.smt2
11. SMTInterpolTest/test/interpolation/constarr002.smt2
12. SMTInterpolTest/test/interpolation/datatype/dt_cases001.smt2

Code and unit tests were completed first, based solely on PREVIOUSLY OPENED source `ultimate-pa/ultimate` interpolation regressions:
- `interpolant_gate.py` SHA256 **c139973f10632b3b1e535ad0803cb329f9da14bfb42eb1f28f66b3edf4651e87**
- `test_gate.py` SHA256 **9f34cfd32abd25e2cd412e30259bbd16e3269054bb70e95568725e7a4ba1e705**
- unchanged Z3 backend `z3_sharedlib_solver.py` SHA256 **1e8032820bef84e49e40c40bf43b7f702263e711000b97700b5b53b565b2c5f3**, local libz3 4.13.3, no solver download, API/GPU or paid resource.
- five engineering tests PASS. In previous OPENED dev regressions simple old original two-part cases pidgeonhole5, pidgeonhole8, qfsimple, qfexists have correct Craig `I` candidates, each Z3-checked for `A & !I = UNSAT`, `I & B = UNSAT`, and candidate declared function symbols subset of shared `A/B`. qfhard and multistep mccarthy legitimately HOLD. These are NOT prospective successes.

**Prospective test**: Each fixed external original SMT-LIB script is parsed conservatively. Only one check-sat, EXACT two named assertions A and B, one flat `get-interpolants A B`, no push/pop, no unnamed asserts is eligible for automatic candidate test; other scripts are `HOLD_UNSUPPORTED_SCOPE`, never replaced. Generate trivial candidates (true/false; a shared-symbol-safe named A, its conjuncts, or complement of B) WITHOUT original interpolant answer as input. Independently check each of two Craig implication obligations in fresh Z3 process contexts with 2s solver timeout each. Z3 responses are **unverified solver assertions** not independent proof-kernel certification. Source Git blob SHA1 and input bytes SHA256 retained, exact first result frozen BEFORE any external provided reference answer, if any. This dataset consists of tests in a purpose-built SMTInterpol tool, not unseen natural science tasks; no frontier comparison.

Controls: C0 Z3 raw original script unable to fulfill interpolation goal (historical); C1 this cheap classical candidate + two obligation checker; C2 professional SMTInterpol native JAR **NOT AVAILABLE IN CONTAINER**; its official binary SHA256 is published as `8d42e87614fcdbe6fce5233b91f20563dfd9a854d999127d70cfb42853e091c7` and official software supports `get-interpolants`, but its binary couldn't be fetched; **C2 NOT RUN**. Don't claim equal-rights strong professional baseline, nor infer failed general classical algorithm. If C1 works, credit ONLY to classical Craig witness checking; no neural ownweight trained. Resource count CPU/wall script, oracle and memory/energy costs UNKNOWN.

Gate: G1 requires a genuine own-weight open-expression emitter, same-rights professional classical C2 plus independent goal verification, causal A/B and fresh cross-author task cohort. No automatic G1 from C1 HOLD.

No tool-generated status is proof that whole original is verified when original has extra commands. Source variable restriction check is conservative and syntax-level, not a complete SMT/quantifier checker. Reports must distinguish PROCESS SUCCESS, TWO Z3 CHECKS, and VERIFIED FORMAL PROOF.