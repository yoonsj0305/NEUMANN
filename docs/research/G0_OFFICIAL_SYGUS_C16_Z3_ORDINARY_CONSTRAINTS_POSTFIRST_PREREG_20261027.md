# NEUMANN 1 | Official six source-candidate independent Z3 full-constraint grade POST-FIRST prereg

**2026-10-27**. This verification is **POST-FIRST** and MUST preserve native professional C original first scores. Original source `SyGuS-Org/benchmarks` pinned `13c8deb68a873635879c9a69bc78caebd340f646`; first generated candidate + raw original stdout SHA pinned from `OFFICIAL_C16_FIRST_UNGRADED_CLASSICAL_HEADROOM.json` SHA256 **`a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5`**, original artifact GitHub Actions #40490276713.

**Deterministic subset:** ALL prior 9 C native `C_PROGRAM_CANDIDATE_UNVERIFIED` rows kept in the postfirst grading denominator; 6 with only `constraint` and **no** `inv-constraint`, namely 4 BV conditional inverse (4bit) plus 2 cegist-cav18 bitvector inv problems. Other 3 originate from `Inv_Track/xujie_code2inv` with `synth-inv` / `inv-constraint` and MUST NOT be treated as verified by a simple `constraint` checker. Grade those three `HOLD_REQUIRES_INVARIANT_VC`, not FALSE or PASS.

**Independent Z3 4.13.3.0 full original semantic proof**:
- Confirm exact original Git commit and raw .sl SHA256 equals historical first record.
- Parse original balanced top-level SMT-LIB forms. Reject all tasks with inv-constraint/synth-inv, unknown language or missing/duplicate native define-fun.
- Take the historical **already-frozen** actual cvc5 1.1.2 stdout candidate `define-fun` bytes; no fresh synthesis and no oracle label access.
- Convert original top-level `declare-var` (universally interpreted in SyGuS constraints) into SMT `declare-const` free variables for proof-by-counterexample; preserve original `define-fun` helper logic and type/sorts; inject candidate function definition; form **NEGATION of AND of ALL original constraint bodies**, in fresh independent Z3 process; Z3 **UNSAT** means candidate satisfied all universal original given semantic constraints. Z3 SAT means counterexample, UNKNOWN/timeouts/parse errors become HOLD not PASS.
- Z3 validates **semantic correctness of original constraint conditions**, not necessarily membership in the supplied synthesis grammar; native published C is responsible for grammar membership. Do not infer independent full SyGuS syntactic derivation from Z3 alone.
- All 16 original paths still in report; 9 source candidate subset and 6 supported Z3 semantic verdicts, explicitly 3 invariant verification HOLD.
- Store exact independent JSON with code SHA, candidate stdout, original repo SHA, original first SHA, each status, per-check independent solver wall, and ZIP artifact before any claims.

This is **classical program solution verification**, NOT NEUMANN learned ownweight A/B; **Q1–Q7 OPEN, G1 HOLD**. The two original official full-benchmark CVC5 CPU timeouts remain benchmark-headroom candidates but require stronger method verification, not declared impossible.