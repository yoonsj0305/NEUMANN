# CORE-25 frozen-ahead typed relational invariant gate | preregistration before inspecting heldout source clauses

2026-10-16. Development-only. Keep North Star/Q1–Q7 OPEN and preserve all historic evidence.

## Training task and output language
Develop on synthetic Horn relations with 2- or 3-input typed ADT arguments and existing development problem goal46. Use **one immutable learned relation generator** that consumes **all clauses** and **all source type declarations**, not only the last goal. The generator emits one new, typed relational Horn invariant AST of the form `R(args) => (arg_i = Nil(T_i) => arg_j = Nil(T_j))` with learned i and j (not a memorized predicate name); produce explicit output as a typed formula and independently induct it, including the original full source unsafety goal. Candidate may instead abstain.

This is a meaningful **new invariant KIND relative to CORE-24's function-composition theorem**, but the *nil implication grammar is supplied by the researcher*; thus even success would NOT establish unprovided abstraction-language invention. Do not relabel it as such.

## Hard no-leakage conditions
- Train solely on generated typed Horn source *before opening heldout clause bodies*; choose exact positive/negative examples with a semantics-grounded independent verifier rather than a label embedded in the neural input.
- Hold out all user-defined data constructors and actual multi-datatype signatures of the sealed sources.
- Freeze source extractor, neural weights, candidate grammar, per-source time budget and verifier before reading heldout goals.
- Baseline: exhaustive typed invariant enumeration + independent SMT certification given exactly the same AST candidates and data. Report both total candidates, proof calls, training, wall. No advantage without beating it.
- Fail closed on parser mismatch, unsupported syntax, timeouts, verifier errors. Record raw original Git blobs.

## Immutable heldout external originals (metadata only, content not inspected)
Repository `chc-comp/chc-comp26-benchmarks` at `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`
1. `ADTRem/isaplanner/goal47_000.smt2`, Git blob `e2e8696480c7a6d3619a780453088999a5d187eb`, 2,126 bytes
2. `ADTRem/isaplanner/goal48_000.smt2`, Git blob `f2c9f3160f90d3231f7ed71e8c5ea4815755d1eb`, 3,920 bytes
3. `ADTRem/isaplanner/goal50_000.smt2`, Git blob `bec4891e62d9a01c2a179e5d09d3552e2a53fbbf`, 4,198 bytes
4. `ADTRem/isaplanner/goal52_000.smt2`, Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, 2,605 bytes

The four files have NOT been opened/decoded for semantic target selection. Evaluate in the order listed after model freeze; all 4 outcomes retained and no target-aware code patch.

## Admission
PASS for *restricted learned nil-shape transfer* only if frozen neural emits well-typed nontrivial invariant and independent original source proves without source modifications, on at least one of four untouched heldouts. For Q3 novelty or Q4 economic advantage, this restricted grammar is INSUFFICIENT; require independently new relation type, strong full-system baseline, resource parity. Q1–Q7 stay OPEN.