# NEUMANN CORE-33 | Frozen learned full typed auxiliary-rule AST emission

2026-10-16, DEVELOPMENT ONLY. **Q1–Q7 OPEN**. Do not promote this to autonomous invention, external CHC transfer, frontier parity or economic advantage.

## New evidence
- A **817-parameter CPU model** trained on 9,604 field-action rows from 2,500 synthetic ADT constructor configurations, held out **all exactly-two-recursive-child constructors** (train arities 0/1/3). Training wall 0.4575s, training row errors 0.
- Frozen checkpoint SHA256 `03ea72e886678d3a25edb606e96f2125af57b8d6441d8ba441211037dcee8a91`.
- The model predicts constructor **base constant and inclusion/exclusion of each typed scalar/recursive field**. A **researcher-designed generic typed decoder** emits a NEW predicate signature and **complete base/recursive Horn clauses** plus an SMT executable witness. The output language is an intentionally restricted linear additive fold.
- Initial synthetic list and **held-out binary-tree recursive branching factor** (two modes each): **4/4 typed programs**, **8/8 independent Z3 universal base/step property checks UNSAT**, generated Horn syntax+consistency Z3 SAT **4/4**.
- WITHOUT touching weights, 20 differently named binary-tree datatypes x 2 goals: **40/40 neural program candidates** exactly match the trivial symbolic program, **80/80** independent target-rule Z3 checks UNSAT; the identical exact classical builder is **40/40** too. A bad base and a missing recursive child produce genuine independent **SAT** counterexamples.
- Paired generation-only totals for 40 programs: neural **38.942 ms**, classical exact **0.414 ms**, about **94x classical advantage**. Neural Z3 verification total ~1769 ms vs classical ~1695 ms. Neural training + checkpoint load add to its costs. Exact classical builder is strictly more economical for this constrained task.

## Information-theoretic goal dependency
Same typed source ADT can demand *different* auxiliary programs: list `(link 2 (link 3 empty))` has **constructor_count=3** (including the base constructor) and **sum_data=5**. A deterministic **single-output, source-only** model given identical source without a distinguishing goal must give the same program for both; under equally weighted mutually exclusive requests its wrong-answer fraction is **at least 50%**. This lower bound does not apply to goal-conditioned models or multi-candidate systems. Correct target context is necessary, without disclosing the unseen intermediate lemma.

## Scope of scientific claims
**The researcher supplied task mode (`node_count` or `sum_data`), the entire additive fold AST grammar and typed emission skeleton, and the independently checked target properties.** The learner only makes binary field/bias choices. It does NOT read authentic unseen CHC Horn program bodies, synthesize a completely new helper predicate LANGUAGE, or discover the goal itself. The 40 typed variants are renamed SYNTHETIC binary trees within the same family, NOT a validated public external cross-family benchmark. No Q gate closes.

## Reproducibility
`NEUMANN_CORE33_LEARNED_FULL_HELPER_PROGRAM_20261016.zip` **19,452 bytes**, SHA256 **`38891c6f62abfed8065c98f211861b19afed3530dd2f237c30c3a8e2760b29ba`**, raw Zip CRC PASS, **9/9 source/checkpoint/receipt manifest hashes PASS**. Independently unzipped replay: pytest **11/11 PASS**, 40/40 frozen decoded programs and **80/80** independent property checks pass. No external third-party benchmark source needed or included.

Development failure record: first generated SMT-law checks had selector-vs-quantifier binder name collisions; after fixing binders, an incorrect human expected value for constructor_count was corrected (nil constructor counts as 1). No failed evidence was relabeled as success. Global Q1–Q7 remain OPEN.

## Next only decisive scientific gate
Model must consume complete authentic Horn rules + explicit task objective, WITHOUT a researcher-given intermediate helper kind; output a genuinely new typed predicate with signature, base and recursive steps, prove original source goal and compare to a strongest same-grammar classical synthesizer including training/verification cost. Stop tuning toy constructor-choice models if the exact classical builder already wins.

**GitHub binary archive status:** this branch contains text report and checksum identity only, NOT the original ZIP/model-weight bytes. PR #180 remains draft.