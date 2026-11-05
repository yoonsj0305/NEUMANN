# NEUMANN 1 P2.1 | Task-conditioned object transformation program induction (preregistration)

Date: 2026-11-05 KST. This contract is frozen **before inspecting any selected evaluation task content**. North Star: **Frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 remain OPEN.

## Research question
Can a generic *executable object-rewrite program constructor*, which infers object partition, role/selector, effect and parameters from original training examples, solve additional fresh public ARC-AGI-1 evaluation tasks beyond strong existing classical solvers B (P1.1), Q (P1.6 exact quotient) and P20 (P1.9 program induction with exact shape/palette pruning)? This is bounded classical program synthesis, **not** autonomous invention of a new instruction set, a JEPA, a novel neural learned policy or a frontier capability claim.

## Frozen model class
A small typed object program graph is compiled from training examples only. Object segmentations: same-color connected components and whole-foreground components with 4- or 8-connectivity; per-color all-cells grouping. Selection of a **unique** object by rank on area, top, bottom, left, right, width, height, or unique/rare color. Rewrites (all grid shape preserving): paint selected component, its bounding-box border, its bounding-box interior/holes, or erase it; alternatively move the selected object by a constant translation inferred from observed train difference (without collisions and without dropping cells). Color/translation parameters are inferred from training outputs, not task IDs or test answers. Fully typed `grid -> grid`; if a required object is ambiguous, or a rewrite cannot be safely performed, ABSTAIN.

The proposer receives original `train:[{input,output}]` and original `test:[{input}]` ONLY. It must output a compiled, task-independent executable AST or ABSTAIN. It must reproduce ALL training examples exactly including shape and every cell. If two fitting programs disagree on test predictions, ABSTAIN rather than pick a winner by hidden test correctness. All original test gold outputs enter a separate independent scorer only after all baseline and new predictions have been constructed.

## Equal comparison and fallback
- Strong unchanged **B** P1.1 object+grid classical.
- Strong unchanged **Q** P1.6 exact behavioral quotient.
- Strong unchanged **P20** P1.9 task-conditioned affine/panel AST plus safe cost pruning.
- Combined baseline only returns a grid if all independently non-abstaining baseline programs agree. If any baseline programs conflict, ABSTAIN and never use C21 as an oracle tie breaker.
- Proposed **C21** is invoked *only* when all 3 baselines abstain without conflict. False accepts are counted separately from baseline false accepts. No neural/teacher calls.
- Report all result counts, candidate programs inspected, training/test original-grid interpreter calls, source code and correctness audit. Record coarse `Date.now()` in-isolate milliseconds separately for B/Q/P20/C21, and energy, memory, full cost as UNKNOWN if unmeasured.
- C21 may be slower and is **not** under an equal-compute budget; the test probes capability headroom only, not efficiency.

## Independent public evaluation cohort
Use `fchollet/ARC-AGI` official public **data/evaluation/** at frozen upstream git commit `399030444e0ab0cc8b4e199870fb20b863846f34`. This is public ARC-AGI-1 evaluation, not any private ARC-AGI-2 benchmark, and it is potentially present in model pretraining. None of the 400 evaluation task bodies has been opened for P21 before this freeze. Select the **first 48 filenames** after sorting by unsigned FNV1a32(`neumann-q3-p21-20261105|`+filename), ties by filename. Commit selected IDs and source SHA of every arm before fetching any task body. No task substitution or later retuning on those 48.

## Predeclared first local gate
- PASS_BOUNDED_OBJECT_RULE_HEADROOM only if C21 solves at least **two** previously unsolved original evaluation tasks, ZERO newly accepted-wrong original-task predictions, ZERO loss of baseline successes, exact train-to-program replay and test-answer isolation audits PASS.
- Exactly one new task = INCONCLUSIVE (not PASS). Zero new tasks or any false accepted original output = FAIL. A baseline conflict is explicitly a safety ABSTAIN.
- Even local PASS does not mean Q3 autonomous general invention, Q4 learned discovery cost, Q6 novel-family transfer, or 10x complete system cost. Q1–Q7 stay OPEN.
- Every first result must be immutable, with no new task-specific exceptions, favorable cohort edits or retroactive threshold changes. A new experiment and task cohort are needed for retuning.
- STOP the object-grammar expansion if no additional independently verified task success; prioritize learned proposal-policy creation instead of adding more handwritten selectors.

## Before unseen task scoring
Run at least six unit/negative controls: unique component selection, ambiguous ties rejection, color paint learned from train and re-executed, grid boundary-safe movement, no output label exposure, and consistent test consensus. Regressions against already opened public development tasks are diagnostics only, never fresh evaluation.

## Scientific constraints
Classical component extraction, template-constrained enumeration and output-difference induction are established program synthesis methods. They may demonstrate new executable behavior relative to B/Q/P20, but never a genuinely new computer-science primitive. Full costs and RAM/energy currently unknown. A task-dependent original output used inside a program or an unverified generated source file is prohibited.
