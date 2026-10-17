# Q3C · Typed source-to-model-output boundary (2026-10-17)

**State: new engineering interface, NOT learned structure discovery. All global Q1–Q7 OPEN.**

## Exactly what changed
The preceding Q3B 40-weight decoder could emit only two `(Int,Int)->Bool` relations, and its first registered external source test abstained on 11- and 12-rule originals. The previous source-neutral IR recovered **6 and 7 distinct predicates with Bool and ADT argument types**, preserving all 23 original rule meanings, but there was no trustworthy interface for accepting a model-emitted relational program.

This Q3C defines **one untrusted model-output schema** `{"relations": {"original_name": typed_Bool_AST}}`. Each relation gets its original arity, exact source sorts and named formal variables; no fixed relation count. Allowed AST nodes: `arg`, `bool`, `int`, `selector` (sort-checked current/returned state), `and`, `or`, `not`, `eq`, `le`, `lt`, `add`, `sub`, `ite`. Missing, extra, ill-typed, oversized, or raw SMT expressions are denied before the solver. The compiler emits syntax only. In a real learned setup a model must supply every semantic expression; deterministic code is forbidden to invent helper lemmas.

The original 11-rule Inc-max and 12-rule Lists-3 sources are **already opened developer cases** and are fetched by pinned revision with strict source SHA256 before testing. For each original assertion, a fresh Z3 solver refutes its negation under the supplied candidate interpretations; all original rules must return UNSAT before accepting. SAT, UNKNOWN and missing checks reject.

## First actual CI scope
This initial study uses **only two intentionally wrong all-true/all-false authored programs** per original. Both must be rejected, including false when no facts are satisfiable and true when original safety goal fails. Missing relation and ill-typed relation-body mutations must be rejected before proof execution. This ensures no vacuous green-check proof, not that a model discovered a usable invariant.

Local pure-Python grammar contracts passed **5/5** before upload. GitHub independent Z3 source execution is the authoritative pass/fail test.

**Zero learned model runs, zero new training examples, zero frontier calls, no new external holdout, no Q3 close, no 10x performance claim.** This is the final interface prerequisite before meaningful neural source+goal semantic learning; further formatter or same-source proof polishing should stop.

The next true Q3 step requires training a variable-relation-count source+goal semantic AST proposer, freezing it before a completely new source-family holdout, and full original proofs plus domain-specialist classical and learned-minus matched controls. This PR remains Draft until test outcomes are recorded.
