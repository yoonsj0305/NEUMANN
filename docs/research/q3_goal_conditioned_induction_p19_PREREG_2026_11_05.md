# NEUMANN 1 P1.9 — Task-conditioned executable expression induction on original ARC grids
**Pre-registration frozen 2026-11-05 KST, BEFORE source implementation and test-task content fetch.**

## Unchanged North Star and scientific gap
**Frontier-level problem solving with minimum necessary computation**. Q1–Q7 globally OPEN. P1.3 GPT-6-teacher 4/4 on public tasks was an *external teacher*; P1.4 fixed library 0/24; P1.6 exact semantic quotient 3.62× operator saving at unchanged 1/24 original capability. This study asks whether a non-neural **schema-based program constructor** can expand original-task coverage without writing the task-specific completed operator into the DSL. It is a bounded form of traditional **inductive program synthesis**, not self-invention of arbitrary opcodes or learned search-policy improvement.

## Candidate language and data visibility
Input: original train input/output pairs, original test **inputs** only. Gold test answers are reachable only by a scorer after proposals. No task ID is provided to any synthesizer.

C: Schema-based constructor searches for programs with data-inferred parameters:
- **Coordinate map**: output cell samples an affine dihedral transform of input grid and an integer translation (row/column offsets within [-3,3]), with zero-padding or source-background padding, optionally inferring a consistent palette map from train pairs. Result shape is an exactly predicted train-consistent same-shape, swapped-shape or cropped bbox shape (not a hand-written ARC task).
- **Paired region expression**: infer one uniform separator row/column dividing a grid into equal-sized panels. An expression takes corresponding cells from the two panels, evaluates a finite relational predicate (equal, zero, nonzero, and/or/xor) or selects a panel value, then infers its output palette/boolean colors from train pairs. The expression AST, offsets, predicate and colors must be learned from train examples, not hard-coded per task.
- Every candidate AST is executable independently of task ID and can be replayed on new inputs satisfying its declared schema. Programs must exactly reproduce **all** original train pairs including grid shapes and palette. If no candidate or candidates disagree on test inputs, return **ABSTAIN**. Invalid/ambiguous source/background/geometry also ABSTAIN. Program code may not reference gold or input-array fingerprints.

Strong controls:
- **B**: frozen P1.1 500-program classical grid/object synthesizer.
- **Q**: frozen P1.6 exact semantic quotient (23 human operators, depth≤3).
- **C** is an *additive* proposer only when both B and Q abstain. If both produce conflicting outputs, ABSTAIN as a baseline conflict. Thus C can add capability without removing earlier verified successes but should still be measured for false acceptances.
- Count candidate AST proposals, exact train checks, original-task correct, false accepted proposals, ABSTAINs, and active path wall-clock. No model training or GPT-6 API calls during candidate search.

## Fresh external task cohort (public, NOT sealed)
Source `fchollet/ARC-AGI`, **public training**, upstream commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude all earlier public cohorts P1.0=32, P1.1=24, P1.2=24, P1.3=4, P1.4=24, P1.5=32, P1.6=24 and four earlier developer-inspected tasks = **168 unique** public IDs. Do not include any individual task bodies before freezing program source and cohort.
Choose the first **48** remaining filenames ranked by unsigned FNV-1a32 `neumann-q3-p19-20261105|` + basename, tie by filename. Freeze exact filenames and the blob SHA of C, B and Q before opening files. No substitutions after reading even if unsupported, or repeated tuning on those scored tasks.

## First-run verdict (fixed)
- **Local original-task expansion PASS** only if at least **two** original tasks that B and Q both abstain on are fully solved by C, **zero** false accepted new predictions, and no lost originally correct baseline cases. Otherwise FAIL / INCONCLUSIVE and report immutable result. Any false accept is *safety FAIL* regardless of net gain.
- Independent source/GT isolation audit and cell-wise output match required. A perfect 48 task score is neither expected nor asserted.
- Report complete per-task outcomes and compact cost: B/Q/C candidate counts, program evaluations, elapsed code-region milliseconds (coarse `Date.now`), calls and memory/energy as UNKNOWN if unmeasured. Do not call a capability difference an iso-capability speedup or a 10× cost advantage.
- The first result is immutable; any improved schema or new rule after scoring must use a *new experiment ID* and independent fresh cohort. Retain the failed first result.

## Bounded synthetic regression, not independent original result
Before reading fresh 48 bodies, train-only regressions must reproduce previous developer test tasks `25ff71a9` (one-cell shift) and `6430c8c4` (separator panel condition), and negative controls (ambiguous mapping, malformed grid, unseen palette, conflicting examples). These are already opened; they never enter fresh scores.

## Interpretation
Positive C only demonstrates *new semantic capacity from schema-constrained parameter induction* beyond previous operator catalogs; it is **not** an open-world novel instruction generator, autonomous Q3 transfer, or learned JEPA. Strong existing CEGIS/symbolic regression approaches already have this concept. Follow-on must learn to **generate entirely new operator schemas**, not keep adding hand-written candidate templates; prove task-disjoint gain and total compute advantage.

No auto-merge, no original P1.12/P2/Decision3 change, global Q1–Q7 OPEN.
