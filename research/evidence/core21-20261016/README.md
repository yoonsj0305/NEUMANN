# NEUMANN CORE-21 | Whole-source Horn AST: second information obstruction

Date: 2026-10-16. Verdict: `REPAIRED_SOURCE_INPUT_COVERAGE / LEARNED_AUTONOMOUS_INVENTION_NOT_PROVEN`. All Q1–Q7 remain OPEN.

## Pinned independent original

CHC-COMP 2026 source `ADTRem/isaplanner/goal41_000.smt2` at commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`. SHA-256 `bcf9451674dba121a13ad2ca7f09e4c3d031bfa4f2a21c6ed3e989661dab6f34`, 14 original Horn clauses.

## Counterexample to CORE-20's supposedly richer input

The CORE-20 typed AST preserved map and take definitions but *omitted* the element relation `f`, list equality and the final safety clauses. Adding a well-typed rule `(assert (forall ((X Int)) (=> true (f X X))))` creates two outputs for one input: `f(1,2)` from the source and `f(1,1)` from the added rule. For `L=[1]`, `n=1`, `take(1,map_f(L))` can be `[2]` while `map_f(take(1,L))` can be `[1]`. Hence the map/take commutation assertion required by the source safety goal is invalid in the modified source. **Isolated Z3 on the entire modified Horn original returns `unsat`.**

Despite this, the earlier CORE-20 AST hash is EXACTLY IDENTICAL on the correct and modified sources. This proves a feature-identifiability obstruction for any deterministic classifier/proposer restricted to that AST. It does NOT invalidate a separately checking full-source verifier.

## Executed fix

- `source_comprehensive_ast()` now retains **all asserted Horn clauses and declared typed relations**, constructor roles, and goal predicates; it canonically maps binder and relation names and rejects unrecognized top-level commands.
- Tested six source variants: authentic source, harmless relation alpha-renaming, and four meaning-changing modifications.
- The old partial AST collides on **3 of 4** wrong modifications; the fourth was already detectable as an extra map clause.
- The new full-clause AST distinguishes **4/4 wrong variants** and preserves source identity under the harmless name change.
- Isolated Z3 returns **`unsat` for all 4** falsified whole-source variants.
- **10/10 pytest pass, independently replayed from ZIP extraction**; fail-closed top-level protocol checks included.
- No learned checkpoint was changed or trained in CORE-21. This is classical source-encoding repair, NOT neural abstraction invention.

## Artifact identity

`NEUMANN_CORE21_WHOLE_SOURCE_GATE_20261016.zip` SHA-256 `9802a810cb5ef370ceb44e1862432b664f964e85b5056803b5d55f94b88423bd`. Zip CRC pass. The complete local Python source bundle is downloadable from the conversation, but **its ZIP bytes are not yet mirrored to GitHub**. Original upstream CHC data are not redistributed.

## Admission boundary

The next learned engine must read dependency-complete typed source and emit a new typed auxiliary definition *without target-aware human schema*, validated independently on a fresh sealed external family with a matched specialist symbolic baseline and full cost accounting. Q1–Q7 remain OPEN.