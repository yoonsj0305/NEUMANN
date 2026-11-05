# NEUMANN 1 P2.5 | Multi-branch executable decision-tree synthesis: first FAIL
2026-11-05 KST. North Star: **Frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 OPEN.

## What actually ran
A new **classical, task-local executable program compiler** generated **depth≤3 conditional ASTs** from original training input/output pairs, using typed sources (whole grid, left/right halves, top/bottom halves, ±1 source shifts), booleans from P2.4 and predicates `sourceColor == k` derived from TRAIN input colors, and leaf actions either input source value, secondary source value or a color found in TRAIN target. It derives a branching program via exact leaf feasibility, target-entropy ranking and a frozen top-12 branch beam, never seeing test gold. Multi-step IF/ELSE tree source did **not** contain a hardcoded public task ID, target output or pretrained teacher code.

Six synthetic development contracts PASS. An explicit nested executable program for `if leftPixel==rightPixel then 4 else if leftPixel==0 then 3 else 7` was derived, run on fresh deterministic random synthetic grids and returned exact targets. This is proof of mechanism, **not a real ARC success**.

## Frozen original ARC-AGI-1 public evaluation
- Selected 32 previously unexamined public `data/evaluation` tasks from pinned official upstream `399030444e0ab0cc8b4e199870fb20b863846f34` by frozen filename hash; excluded 168 previously selected evaluation IDs.
- Frozen source blobs: `experiments/q3_generated_decision_trees_p25.mjs` SHA `5c9971100865e529a2f259bac19a9c1d1658c599`, all B/Q/P20/C211/P24 baseline blobs fixed before opening selected task files.
- Eight immutable four-task first shards and [first full 32-task result](../experiments/results/q3_generated_decision_trees_p25_FIRST_COMPLETE.json).
- Combined existing Direct B/Q/P20/C211/P24 baseline solved **1/32** original tasks (ID `0c9aba6e`). Adding P25 solved **1/32**. **0** additional original task solved, **0** new false accepted outputs. The 31 new-solver invocations all returned `NO_TRAIN_CONSISTENT_TREE`.
- P25 evaluated **116,766** candidate feature-split proposals, **0** full train-consistent candidate trees, **0** node-budget exhaustion events; additional observed task-region wall time **13,664 ms**. No teacher call, neural forward or training.
- Independent source/cohort/first-result audit PASS, retaining the registered **FAIL_NO_ADDITIONAL_ORIGINAL_ABILITY** verdict. Full end-to-end dollars, RAM, energy and FLOPs not measured.

## Important limits on the negative result
This does not prove *all* decision-tree programs are incapable. Beam width 12, depth max 3, finite primitive facts and a program selection policy are restrictive. A correct program outside that beam or language may exist. It does directly show that escalating from one-guard to a bounded multi-branch version without changing representation **did not recover extra original-task capability on this preregistered sample**.

## First-principles system decision
- Do **not** keep adding narrow hand-designed conditional predicates to make the same opened tasks fit, since that would turn test answers into architecture decisions.
- Retain sound feature caching P24 and finite AST program synthesis in research-mode only, with explicit fallback ABSTAIN. Keep B/Q/P20 verified Direct as a cheap, independent baseline.
- Move Q3 to a measurable, **across-task learned program proposal distribution** with generated structural schemes, independently executable typed ASTs and a new-family heldout gate. A learner must not simply memorize teacher task IDs or rank fixed H. Test a model *against* a matched classical enumerator using the same primitives and budget, and account for teacher training/verification/fallback costs.
- This P2.5 has **no learned across-task policy**, no JEPA, no frontier accuracy, no same-capability 10x compute advantage. Global Q1–Q7 remain OPEN; no sealed benchmark or mainline changes.

## Additional risks
A JavaScript one-shot Date.now timing is noisy; a higher search beam would increase cost and might change the first result, so it requires a new cohort/version. The dense cell-wise training data from each original grid are correlated, not independent sampled tasks; don't claim statistical confidence from the number of cells. Prototype code is not sandboxed for arbitrary-generated source. The 32 sampled public eval files may be present in pretrained LLMs, but P25 made no model calls.
