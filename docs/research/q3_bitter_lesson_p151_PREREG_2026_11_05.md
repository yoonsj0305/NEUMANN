# NEUMANN 1 | P1.5.1 complete grammar / computation-sharing diagnostic
**2026-11-05 KST. PRE-REGISTERED before full-grammar diagnostic execution.**

Scientific status: **post-first-score explanatory audit on opened P1.5 tasks**, NOT new blind generalization. P1.5 first 1/32 U/E remains immutable. Global Q1–Q7 remain OPEN.

## Fixed source and task selection
Pinned original source: `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`. Previous fixed P1.5 32-task result is `docs/experiments/results/q3_bitter_lesson_p15_FIRST_COMPLETE.json`. Diagnose **first eight U/E joint failures** in original preselected file ordering, then **the one U/E joint correct positive case**. Exactly nine task IDs frozen in separate manifest; no substitutions after results.

## Causal questions
1. Was P1.5's 1,024-program cap the limiting factor, or does the full program language lack any train-consistent executable?
2. Can deterministic state sharing reduce primitive evaluations without changing the **full program candidate set, exact training consistency, or consensus original predictions**?

Both arms must inspect exactly **23 + 23² + 23³ = 12,719** length-1/2/3 program ASTs over P1.1's same frozen 23 generic grid operators, in identical order.

## Arms
- N: naive plain interpreter executes every AST from scratch across *all* original training inputs and verifies against complete training outputs; no oracle test answer access.
- M: semantic-state DAG computes a deterministic transition `state_of_all_train_views × operator → state_of_all_train_views` once and caches it across AST prefixes and observationally equivalent states. **Training-only equivalence** is safe for train fit by functional determinism; it is **not** safe to assume test-output equivalence. Thus every full program passing train must still be independently executed on all test INPUTS before unanimous original output can be returned.

All candidate AST IDs and train-consistent candidates must match exactly between N and M. Any mismatch => correctness FAIL. Scores on original test outputs are computed **after** both candidates produce their predictions and strictly independently; no adjusted training target, no test oracle use for search.

## Frozen first decision
- Completeness diagnostic: count `N_train_fit` across all 12,719 programs and enumerate cases with `H_D = ∅`. If zero across eight failures, the original 1,024-budget problem on this cohort cannot be fixed by increasing search up to depth3 in this language. It does not prove missing semantics outside this language.
- Sharing-correctness gate: all nine tasks have identical train-consistent AST set, prediction consensus/abstention and original correct/incorrect decisions.
- Sharing-cost gate: M primitive-grid interpreter calls <= 50% of N, and M study-region wall time <= 80% N across nine tasks. If either cost threshold fails, do not claim an optimization win. Wall clock from JS `Date.now` has 1ms resolution; host/cloud/model/energy costs remain unmeasured.
- A positive cost result is only a local classical search-evaluation optimization at **identical capability** in finite grammar, not learned intelligence or 10× end-to-end superiority.
- Never retune cohort, algorithm or thresholds after first complete diagnostic. Tests can audit but not convert failures.

## Constraints / degraded mode
Failed/invalid grids => invalid state. Memoization keys include **all training views**, not only one. If a program is consistent but proposed test outputs disagree with another consistent program, ABSTAIN, even if a cached train state matches. Full program identity is preserved for test execution. No eval of user code; operators loaded exclusively from trusted frozen project source.
