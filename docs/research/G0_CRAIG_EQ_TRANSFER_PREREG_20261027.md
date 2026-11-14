# Craig G0 second prospective validation cohort — BEFORE source access
Date 2026-10-27 KST; existing NEUMANN Draft PR #616 only; main Q1–Q7 still OPEN.

**New frozen code** `interpolant_gate_v2.py` SHA256 **92d3c3ebf39dab6cd32bb9e32344f8cab1e8a39b5a643cc041a1b665171f5995**; previous unchanged Z3 isolated runner SHA256 1e8032820bef84e49e40c40bf43b7f702263e711000b97700b5b53b565b2c5f3. This V2 implementation removes solver-incompatible **options only from obligation-checking copies**, not original scripts, and computes transitive same-equality-class between shared first-order terms even through A-private symbols. Exact Z3 C API checks (two fresh processes, 2s each); both formula implications tested. All primitive solver, syntax parsing, congruence and candidate construction are HUMAN-CODED classical algorithms, **NO ownweight neural learning**.

V1 preceding first (fixed before earlier cctest001/002 source read) sealed GitHub commit `7bf3ff589e7e321ed1f744d0490396b56f46e41a`, first 0/2, 10/12 out-of-scope. Cctest001/002 are NOW OPENED DEV examples and post-first V2 resolved their equality conditions; those DO NOT count as prospective. This **second** prospective cohort consists of precisely 12 further uninspected ORIGINAL scripts at `ultimate-pa/smtinterpol` git commit `f65e98f05203f1d2801bf5bd121766bfcd6451ec`:
1. SMTInterpolTest/test/interpolation/cctest003.smt2
2. SMTInterpolTest/test/interpolation/trivdiseq001.smt2
3. SMTInterpolTest/test/interpolation/trivdiseq002.smt2
4. SMTInterpolTest/test/interpolation/trivdiseq003.smt2
5. SMTInterpolTest/test/interpolation/trivdiseq004.smt2
6. SMTInterpolTest/test/interpolation/ufliatest001.smt2
7. SMTInterpolTest/test/interpolation/ufliatest002.smt2
8. SMTInterpolTest/test/interpolation/ufliatest003.smt2
9. SMTInterpolTest/test/interpolation/ufliatest004.smt2
10. SMTInterpolTest/test/interpolation/uflratest001.smt2
11. SMTInterpolTest/test/interpolation/uflratest002.smt2
12. SMTInterpolTest/test/interpolation/uflratest003.smt2

Eligibility: original has exactly one `check-sat`, two named assertions A/B and exactly one `get-interpolants A B`, no other goals or scoped push/pop/unnamed assertion. Else HOLD, no replacement. Reference annotations `:interpolants` ignored by model. Only after freezing each eligible generated candidate and its hash, inspect any original stored expected interpolant output if present, never retrofit. Full unmodified source Git SHA1 must match fetched bytes before execution. Fixed code, no attempts to tune on this cohort.

Primary: whole ORIGINAL binary Craig output candidate satisfying (1) A and not I => UNSAT, (2) I and B => UNSAT, (3) no undeclared local symbols in I (restricted to A/B shared declared funcs) using separate Z3 contexts, with no error/unsupported. These are solver claims, NOT independent proof kernel or two diverse solvers. Script containing `get-proof` or multiple interpolation commands remains OUT-OF-SCOPE; first outcome preserved. Cost CPU + wall + attempt counts, no energy or paid API. Compare V2 versus frozen V1 on exactly same task input at matched resources, separately from professional SMTInterpol (JAR download blocked: NOT RUN), no global G1 admission.

If V2 yields new verified original Craig witnesses, this credits purely to **classical subexpression equality-closure and explicit Craig checks**, not learned operator creation or Q3/Q4. Any future neural G1 still needs other-author task transfer, same-rights specialist classical C, ownweight A/B/D, and whole-cost evidence. No model training now.