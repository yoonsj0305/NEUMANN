# NEUMANN 1 P0.9: discover local causal scope + rule semantics jointly

**FROZEN before first P0.9 scoring, 2026-11-03 KST.** Previous P0.8 first receipt immutable. Frozen North Star unchanged; global Q1–Q7 OPEN.

## Question
P0.8 was told the radius, binary alphabet and boundary. P0.9 must infer **smallest sufficient radius r ∈ {0,1,2}, boundary type**, and entire data-defined truth table from training input/output, not source reference. r=0 boundary canonical `none`; r>0 boundary either `periodic` or `zero-pad`. This is bounded structural induction within a predefined candidate family, not unbounded novel instruction-set creation.

## Frozen source split
- Seed 20261109; exactly 20 tasks: 4 radius-0 none, 4 radius-1 periodic, 4 radius-1 zero-pad, 4 radius-2 periodic, 4 radius-2 zero-pad, in that order.
- Per-task deterministic random truth-table generation using `default_rng(base_seed + task_index*101)`. For r≥1 **source** samples rules until outputs truly depend on both furthest neighbor bits (irreducible radius). This is a declared source distribution, **not** selection on task success, model outputs or test scores.
- Per task 5 training binary sequences with lengths [89,97,113,131,149] and independent source at seed `base_seed+index*101+11`. Independent held-out source at `+911`: 1D lengths [173,211], two explicit row-wise 2D test arrays 3×181 and 5×199. No favorable resampling for coverage.
- The learner receives **only train input/output pairs**, never source radius, boundary, rule table, task index or held-out answers. Independent loop-based reference and scorer see source only after inference.

## Frozen local gate
- All 20 programs uniquely determine correct radius, boundary and table, with complete context coverage and exact training replay.
- Independent exhaustive local certificate for 20/20 plus 40/40 held-out 1D and 40/40 row-wise 2D exact predictions.
- Seven negative controls refuse with typed reasons: undercoverage, contradiction, invalid output dimensions, invalid alphabet, radius-3 nonlocal target, boolean-radius AST, invalid boundary.
- If more than one model with the same minimal radius but different boundary is consistent, ABSTAIN_AMBIGUOUS_BOUNDARY. No post-hoc choosing.
- Any miss => immutable P0.9 FAIL. No post-result seeds/gates/logic replacement.

## Strong comparisons & safeguards
- Restricted earlier r=1 periodic baseline on same tasks; failures imply unequal capability, hence no iso-capability time comparisons.
- An **optimal classical adaptive-radius and boundary search** computes essentially the same sufficient statistics as this design; no neural/JEPA or 10× advantage relative to that strong Direct.
- Count candidates, input cells, CPU-region ns, compiled programs, verification, fallback. FLOPs, energy, RAM if unmeasured and dollars remain UNKNOWN.
- Strict typed AST (reject bool radius even though Python `True == 1`), boundary-enforced execution and ABSTAIN on malformed/out-of-domain scenes. No sealed data or mainline integration.

## Scope
A successful pilot shows bounded discovery of hidden *structural scope and semantics*, not transfer to another semantic family, autonomous general code invention, matched frontier capability, or any global Q3–Q7 closure. These remain OPEN until independently proven.
