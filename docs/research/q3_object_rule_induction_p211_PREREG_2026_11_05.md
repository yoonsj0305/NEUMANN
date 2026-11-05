# NEUMANN P2.1.1 | New-first-run recovery after immutable P2.1 runtime abort

2026-11-05 KST. Preregistered before new evaluation task files are fetched.

## What failed, and what changes
P2.1 original first run was **BLOCKED_RUNTIME_EXCEPTION** on one of the first 12 drawn public ARC-AGI-1 evaluation bodies. The frozen source assumed output shape equals input shape inside `coloredDiff`; ARC is allowed to change output size. Failure retained unchanged as `docs/experiments/results/q3_object_rule_induction_p21_FIRST_ABORT.json`. Never count the aborted cohort as a successful blind result.

P2.1.1 changes **exactly one semantic guard**: when an original training target grid has different dimensions, the *same-shape object-motion* delta proposer returns no candidate offsets instead of indexing an undefined pixel. The original P2.1 object paint and motion schemas, selectors, consensus logic and baseline contracts remain unchanged. Separate 8/8 local tests include changed-dimension fail-closed regression. No task-specific rules introduced.

## Independent, never-used cohort and frozen code
Source official public `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34` `data/evaluation/`. Completely exclude all 48 previously reserved P2.1 evaluation IDs, of which the first 12 source bodies were fetched at the time of the abort. From remaining public 352 filenames, sort ascending unsigned FNV1a32(`neumann-q3-p211-20261105|`+filename), tiebreak by name, and choose first **48**. Freeze new cohort ID list and source SHA for C211, B, Q, P20, P19 BEFORE opening their bodies.

## Arms, decision and limitations
Exact same original-task input-only interfaces and score policy as frozen P2.1: old B, old Q, old P20, new object rewrite C211 only on complete no-conflict abstention of baseline. Every program must fit original training pairs exactly, all test predictions must agree; otherwise ABSTAIN. Scorer only opens test gold after proposals. Detect wrong accepted decisions.

First local P2.1.1 capability gate PASS iff new C211 solves **>=2** original tasks not solved by any baseline with **ZERO** additional false accepted predictions, **ZERO** baseline wins lost, independent source identity + answer-leakage audit PASS. One additional is INCONCLUSIVE; zero additional or any false accepted is FAIL. Preserve first results across all 48 without retuning.

The source rule inventory is human-specified; successful object-rule construction within this grammar is not general autonomous operator invention. No neural/JEPA training, no teacher invocation. Cost and correctness must be reported with candidate count, grid program executions and coarse `Date.now()` scoped wall time, while full-system FLOPs/energy/peak RAM/dollars UNKNOWN. All global Q1–Q7 stay OPEN, no sealed data and no production merge.

If first local gate fails, STOP object-DSL expansion and focus on learned open-ended program proposal policy. Use original first failure and current first result as two separate immutable scientific records.
