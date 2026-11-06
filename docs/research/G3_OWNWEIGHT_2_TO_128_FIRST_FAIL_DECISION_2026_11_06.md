# NEUMANN 1 | Frozen own-weight G3 2..128 generalization FIRST: SCIENTIFIC FAIL

2026-11-06. Original trained checkpoint SHA256:
`982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc`.
Original training first [#42198111692](https://github.com/yoonsj0305/NEUMANN/actions/runs/42198111692) verified 49/49 development clauses. Original source-heldout first [#42198669136](https://github.com/yoonsj0305/NEUMANN/actions/runs/42198669136) verified 20/20 CHC clauses on init2/3 using frozen human-taught student ASTs. Independent after-FIRST archive [#42199539359](https://github.com/yoonsj0305/NEUMANN/actions/runs/42199539359) independently reproduced those 20 proofs and refuted a deliberately wrong invariant with SAT. These narrower positives remain valid.

## New first falsification

[PR #673 original symbolic N first #42200289388](https://github.com/yoonsj0305/NEUMANN/actions/runs/42200289388), preregistered **before** running to evaluate the original weights with 2 <= n <= 128 and all stage indices 0..n. The student **was never retrained**; no external original sources or original solver were called. All 127 values of N and 8,382 source-free role programs were checked against the original human-authored mathematically valid first/middle/final structure.

| Metric | First observed |
| --- | ---: |
| Correct pretrained 4-token AST roles | 8,257 / 8,382 |
| Full N configurations with **all** roles correct | 38 / 127 |
| Untrained zero-weight original controls | 0 / 8,382 |
| Human G3 generic symbolic rule | 8,382 / 8,382 |
| First counterexample | N=40, stage=40 (final stage) |
| First expected AST | [3,2,0,0] (whole array, previous value) |
| First actual model AST | [1,2,0,0] (prefix, previous value) |

**Scientific verdict:** `FAIL_FROZEN_OUT_OF_DISTRIBUTION_SYMBOLIC_N`. A previously successful external original task does **NOT** establish unbounded N. Do not cherry-pick 2..39 or retrain after seeing the N40 breakpoint and call the old gate PASS.

## Why this is the relevant bottleneck, not a reason to grow G3

The original student uses raw feature N/12 for a role classification whose desired predicate depends only on *first/middle/final* stage identity. Thus N appears as a potentially unbounded, **semantically irrelevant nuisance feature**. First and final logits are affine in N. That makes extrapolation to arbitrarily large N unsound unless the winning class has nonnegative asymptotic margin against all competing classes. This is a mathematical property of the model's fixed affine score architecture, not an empirically justified expectation.

An analytic *post-first* margin certificate is appropriate, but no new-training, target-specific edits, speculative pseudo-PASS or repeated original task use. The theorem-proved human rule remains a stronger classical baseline.

## Source-first native solver correction

In the unchanged original init2/3 result, the "CHECKER_ERROR" value from the raw Z3 original source is actually the literal stdout `timeout\n` at 15s, with SHA256 `7ed6120912d915f6ba8ef82ba3ec0b703265a0979bc0a243e0144580ad0c0b6b`. A read-only source-free audit confirmed **2/2 bounded 15-second timeouts**, not solver crash and certainly not proof of classical impossibility. Preserve the original first receipts and add the new classification as an annotation, not a rewritten result.

## Strict next research decision

**STOP unbounded G3 student training as a model architecture success.** Replacing N/12 with a human-designed semantic first/middle/final one-hot feature or applying the human generic template can repair this particular failure, but is classical engineering, not autonomous new operator discovery.

Proceed only to a distinct Q3 expression-space experiment with a verified **H0 impossibility barrier** and a learned H1 operator not present in frozen old H0. Current separate PR #672 is evaluating cross-array relational operator expressivity; its symbolic theorem alone is not own-weight discovery and all Q1..Q7 global remain OPEN.

**All measurements are first-cohort only, no favorable rescore.** Quantifier AST syntax and training labels were provided by a human; there is no global Q3/Q6 PASS, 10x total capability-equal economics or frontier recovery.
