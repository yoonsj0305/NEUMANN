# NEUMANN 1 P2.4 | Exact semantics, cached source-grid feature extraction (PREREG)
2026-11-05 KST; freeze this prior to new original task selection and source-body access.

North Star **Frontier-level problem solving with minimum necessary computation**. All global Q1–Q7 remain OPEN. Previous P2.3 first result: B/Q/P20/C211 1/32 vs +teacher-free S23 2/32, new +1 `e345f17b`, zero new wrong original proposals, local INCONCLUSIVE. S23 added 10,327ms study-region and repeated feature extraction per output cell.

## Precise change (and nothing else)
P24 is a functionally equivalent implementation of **the exact original frozen P23 typed conditional AST compiler**: the same 7 shape modes, same primitive feature values, same AND/OR candidate enumeration, same action pairs, same MDL scores, same tie/ABSTAIN behavior. Only delete repeated scans inside `primitiveFacts(ctx)` by computing a per-source-grid summary once:
- Row-left and row-right `nonzero` existence prefix/suffix.
- Column-above and column-below nonzero prefix/suffix.
- Four-neighbor nonzero count.
- Foreground bounding box.
All summaries are exact. Use a `WeakMap` scoped to each `solve()` invocation, reset at its start to avoid stale results across sequential calls even if the caller mutates an input grid. Runtime `source()` and original program ASTs remain unchanged. Program correctness and ABSTAIN should therefore be identical on unchanged inputs, and no training or test oracle is used for the cache.

## Frozen first independent public original evaluation
Source official public `fchollet/ARC-AGI` `data/evaluation` pinned upstream Git SHA `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude all previously reserved public evaluation IDs **136** (P21 48, P211 48, P22 8, P23 32) then select **32** task filenames by unsigned FNV1a32(`neumann-q3-p24-20261105|`+filename), tie alphabetically. Commit manifest and exact P23/P24 source blob SHA BEFORE opening task bodies. Neither source can be edited after first scoring.

Compare **P23 vs P24 on all 32 original tasks**, not only the ones for which an earlier Direct arm would abstain, so the speed mechanism is not biased by routing. For both arms, entire train/test INPUTS are visible, original test OUTPUTS only to an independent scorer after both predictions. P23 and P24 must produce exactly identical output or identical ABSTAIN reason on **32/32** tasks, identical train-consistent program count, MDL-selected AST and zero loss of original-task correctness. Any disagreement FAIL.

**Local optimization PASS** iff:
1. exact program/ABSTAIN parity 32/32 including AST identity;
2. inclusive aggregate P23 study-region runtime / P24 study-region runtime >= **3.0x** (measured with `Date.now()` in same JS isolate, interleaved by task with the same inputs), and
3. zero new false accepted result or lost original success.
Report **10x** as a separate stretch (not a rounded threshold), total AST/candidate counts, per-task time and original accuracy. The target is local runtime, NOT full inference/training/energy/price. Run second-order tests for cache invalidation and feature equality on randomly generated scenes. No model training/teacher calls.

Previous P23 cohort may be replayed only after this first fresh run as **posthoc regression**, never a second independent first score. Keep global Q1–Q7 OPEN. No sealed ARC-AGI-2/Decision3 changes, no mainline merge.
