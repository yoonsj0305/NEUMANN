# NEUMANN P2.0 — Constraint-directed deletion of impossible candidate programs (PREREG)
**Registered 2026-11-05 KST before optimized source/first fresh task scores.** Frozen North Star: Frontier-level problem solving with minimum necessary computation; global Q1–Q7 OPEN.

## First-principles hypothesis
P1.9 generated executable rules that solved two additional public ARC-AGI-1 training tasks (B+Q 3/48 vs +C 5/48), but wasted 208,611 primitive train-pair executions on mostly inconsistent candidates. This is an opportunity to DELETE work rather than train a model or add task-specific operators.

P2.0 implements a **sound shape abstract interpreter** and **incremental palette-constraint propagation** in a strict refactor of **exactly the same frozen P1.9 candidate grammar and program execution semantics**. Candidate count/order, all original train/test input access, allowed ASTs, full train replay, program consensus/ABSTAIN and independent scorer unchanged. It does not invent new operators. Shape incompatibility may be checked cheaply before evaluating a candidate; a palette conflict may be rejected as soon as it is observed rather than replaying all remaining examples.

## Frozen comparator and self-checks
- **P19**: exact `experiments/q3_goal_conditioned_induction_p19.mjs` blob SHA `60815950cd5e7da777e20547bb7389cd0de994a7`.
- **P20**: optimized evaluator and abstract interpreter, imports P19 immutable primitive semantics.
- **Exact original-task prediction parity required 48/48** between P19 and P20 on a *new-to-both* public ARC cohort; same proposed original test outputs or same ABSTAIN, even where both wrong. Any divergence => FAIL, no performance claim.
- Work improvement mechanism PASS only if the total number of actual **P19 primitive sample executions / P20 primitive sample executions ≥ 10×** AND P20 total in-isolate task-region wall time (including shape and palette-check overhead) ≤ 0.5 P19, at the same original-task predictions. Otherwise FAIL. Candidate AST attempts cannot simply be deleted from denominator.
- Assert every candidate pruned by the shape guard has a provable impossible output shape for at least one original train pair, and every early palette conflict is truly inconsistent with some observed training output. No program with a valid original-task training replay may be pruned.
- No trained model, no JEPA/LLM calls. Mean/median per-task ratios and cumulative counts reported, without hiding small or unfavorable cases.

## Frozen new external source
Official public ARC-AGI-1 training `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude exactly **216 distinct** prior public task filenames (P1.0/1.1/1.2/1.3/1.4/1.5/1.6/1.9 cohorts + 4 preread dev). Excludes P1.7/P1.8 synthetic-only cases, not public ARC IDs. Choose first **48** remaining filenames sorted by unsigned FNV-1a32(`neumann-q3-p20-20261105|`+filename) with filename tie. Commit engine hashes and selected filenames BEFORE reading task bodies. Scoring public test originals occurs only after both P19/P20 propose from train and test INPUTS.

## Second-order risk and scope
- Observational parity on this original-task set and proof of shape-safety are different from open-world algorithm discovery; continue global Q1–Q7 OPEN.
- Shape specialization may overfit P19 grammar, not arbitrary future programs. It must never be generalized to compilers where a later operation can alter output dimensions or recover an invalid intermediate.
- `Date.now()` is low-resolution JS study timing only, not all CPU/GPU/energy/dollars. No whole-system 10× claim from local ratio.
- No post-result source edits or favorable seed selection. Failures saved as first immutable receipts.
- As a diagnostic only (not an independent new capability result), replay on previous P1.9 tasks to check equivalence and quantify pre/post optimization. Do not tune after viewing the new P2.0 cohort.
