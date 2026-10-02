# Q3/Q4 closure — constructed-LP mechanism

**Status: CLOSED · 2026-10-02**

- Q3: `PASS_LP_MECHANISM`
- Q4: `PASS_LP_MECHANISM`
- Next gate: Q5
- Final decision: `CLOSE_Q3_PASS_Q4_PASS_ADVANCE_Q5`

## Scope

This is a scoped research closure for the constructed LP structural-support
mechanism, not a universal claim about all forms of reasoning, structural
discovery, or compute efficiency.

## Frozen mechanism

Quotient-invariant point features -> frozen point MLP -> column ranking ->
top2m restricted solve -> original verifier -> top4m on rejection -> original
verifier -> charged Direct fallback.

## Why Q3 is closed

The final two-phase fresh holdout contained 48 unseen views across four required
cells. Both frozen model seeds recovered at least 80% of the structural savings
available from a free Oracle support in every cell.

Minimum seed-by-cell utility recovery: `0.8693019707922695`.

The mechanism therefore discovers enough useful structure, under target-free
inference and equal original-problem verification, to support the next
end-to-end question.

## Why Q4 is closed

On the same required cells and the same verified answers:

- maximum discovery burden: `0.037030755908723165`;
- maximum amortized complete/Direct ratio: `0.19252710474293702`;
- fallback-free: 12/12 in every cell for both seeds.

The frozen limits were 0.20 burden and <1.00 complete/Direct. Learned training
investment was amortized at the preregistered 10,000-query lifetime, and failed
restricted attempts plus fallback rights were charged.

## Evidence chain

- v0.0.96: representation ceiling isolated exact-basis target as bottleneck.
- v0.0.97: support-system tournament admitted B_POINT on opened development.
- v0.0.98: first fresh holdout failed m128 size+surface utility.
- v0.0.99: quotient audit proved the known surface representation defect.
- v0.0.100: one authorized quotient refit restored exact pair invariance but
  fixed top2m remained just below strict m128 utility gate.
- v0.0.101: no-training verifier-triggered top2m->top4m adaptive contract passed
  every development cell and recovered the rare m128 misses.
- v0.0.102: one final two-phase fresh holdout passed every cell for both seeds.

No second final holdout or local rescue is authorized or needed.

## Next

Q3/Q4 local tuning is frozen. Continue at Q5: scaling, harder/open-set
distribution shift, and cross-domain end-to-end validation.
