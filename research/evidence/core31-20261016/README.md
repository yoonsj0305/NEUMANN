# CORE-31 · Source-compiled, goal-hidden full auxiliary AST synthesis

2026-10-16 · **CLASSICAL integrated pipeline certified; independent LEARNED abstraction invention NOT PROVEN. ALL GLOBAL Q1–Q7 OPEN.**

## Concrete gap closed
Integrates CORE28's full typed expression AST enumeration with CORE30's source-compilation of recursive SMT function definitions. Previously CORE28 supplied handwritten Python COUNT/APP/REV semantics, and CORE30 supplied a human-written auxiliary lemma schema. This system removes both of those source-specific dependencies from the **candidate-generation stage**. It masks 3 unsafe goal clauses before source semantics are compiled. Source type signatures dynamically supply the function operator catalog and original Horn recursion compiles 3 executable recursive function bodies. A generic typed term grammar then generates complete equation ASTs and independently checks them by Z3 structural induction.

### Exactly pinned original and outcomes
- CHC-COMP 2026 `ADTRem/isaplanner/goal52_000.smt2`; commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, original Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, 2,605 bytes, SHA256 `3db92ef5e5f890bf6fc0a61aefddd45bfe364fcd9b39653c9f542c59bcd372f5`.
- 3 compiled source functions, 3 masked unsafe goal clauses; goal not visible to candidate generation.
- 62 observationally eligible **full equation ASTs** after generic typed term enumeration; 3 independently inductively certified (two are syntactic variants of the SAME off-goal count/append lemma). 2 syntactic candidates solved the goal induction step, not 2 independent inventions.
- Substantial lemma: `F_count(X,F_append(A,B)) = F_count(X,A)+F_count(X,B)` **absent from unsafe goal**, generated without a human-written count/append Python implementation or explicit homomorphism formula.
- The lemma was checked by independent universal structural base and step obligations (`UNSAT` each), then goal reversal induction step `UNSAT`, reversal base `UNSAT`, and **all 11 negated actual original CHC Horn clauses UNSAT** with independently compiled SMT semantics.
- A malformed source COUNT base `0 => 1` yields **SAT** proof counterexample and is rejected. False MAX count-append relation also fails proof, with a concrete SAT witness. Relation alpha renaming preserves derived source runtime; unsafe goal editing/removal does not change compiled recursive meaning.
- External already-known tree goal47 and multi-datatype goal46: **unsupported** by same restricted compiler. No blind transfer, cross-family learned result, or neural inference.
- Measured full pipeline ~**30.2s** (separate extracted replay ~30.1s). Earlier researcher-supplied-lemma-schema CORE30 specialized pipeline remeasured **5.337s internal** in same environment. Hypothesis spaces are different; new general candidate search costs substantially more. No speed or compute improvement.
- Independent ZIP extraction plus the source inputs supplied separately: **9/9 pytest PASS**, full experiment replay with 11/11 actual original clauses PASS.

## Human and learning boundaries
- The generic bounded AST grammar (`+,-,min,max`, type-directed original function calls, literal 0/1), depth<=3, induction variable selection and **goal-specific bridge** remain researcher-coded. This is a generic equation candidate search, NOT a free-form generator of **new predicate signatures, base Horn rules and recursive Horn rules**.
- **Zero neural forward calls and training**. No scientific evidence of learned abstraction-kind invention. Goal52 already studied extensively, so NOT prospective external transfer. Q1–Q7 all remain OPEN; historical failures frozen.

## Reproducible release and binary status
- Local ZIP `NEUMANN_CORE31_SOURCE_COMPILED_BLIND_GOAL_AST_20261016.zip` **26,337 bytes**, SHA-256 **`2b6a61b3bdc20c97f58820008b4ea67816ffe4a4262427f057d55436140a8598`**.
- ZIP CRC PASS, 15 entries with 14 payload SHA-256 hashes. Includes full source, generic AST compiler/runtime, original-clause checker, per-case proof attempts, strict scientific comparison, 9 tests. Authentic upstream original is NOT redistributed; must be provided separately and hash-checked.
- This GitHub commit includes the report and identity only, **NOT the actual ZIP binary or checkpoint bytes**. Draft PR #180 remains unmerged.

## Single next gate
Freeze a trainable whole-source-to-typed-program generator that outputs a NEW auxiliary predicate signature AND base/recursive Horn rules without a task-specified theorem type. Preregister a genuinely untouched external family and match strong type-directed classical program synthesis with full cost accounting. Stop growing CORE numbers if no genuinely learned benefit is demonstrated.