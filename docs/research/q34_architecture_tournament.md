# Q34 Architecture Tournament — post-v0.0.96 plan

This document turns the v0.0.96 representation-ceiling result into the next
development protocol. It is a design freeze, not a performance result.

## Target

Stop optimizing exact-m basis prediction as the primary objective.

The tournament output is a **verified support program**:

```
problem
  -> cheap support/discovery proposal
  -> restricted native execution
  -> original-problem verification
  -> direct fallback if needed
```

Fallback is part of the architecture and is charged.

## Four materially different families

### A. Deterministic-first

Use the strongest cheap observable-only deterministic/classical support
proposal already available in the repository. No learned inference is required.
This family establishes the floor that learning must beat.

### B. Minimal learned support proposer

Use a pointwise/small learned scorer to produce a support only. It is not asked
to predict the final exact basis. The restricted solver does the remaining
combinatorial/numerical work.

### C. Full-information small model

Preserve all columns through the learned structural stage and emit a support
only at the end. This tests whether richer interactions help enough to justify
their cost without requiring exact-basis generation.

### D. Adaptive iterative support

Begin with the cheapest small support, execute/verify, and expand only when the
certificate fails, for example `m -> 2m -> 4m -> Direct` under a frozen rule.
This is genuinely adaptive computation, not another fixed-depth graph rerank.
The verifier/failure signal may choose whether to expand, but hidden labels may
not enter inference.

## Representation ceiling first

Before any new fitting for B/C/D, estimate each family's support ceiling on
opened development data. A family below the Q34 0.80 utility floor receives no
training budget.

Where an existing frozen model/heuristic already instantiates the family, reuse
it before training anything new.

## Common evaluator

Every family receives identical:

- input distribution and split,
- hardware/runtime/thread conventions,
- original-problem verifier,
- Direct fallback rights and deadline,
- failed-attempt accounting,
- training-amortization convention,
- strongest matched Direct comparator.

Report:

- verified capability,
- useful-support / no-full-fallback incidence,
- `structure_utility_recovery`,
- `C_discovery`,
- `C_post`,
- complete `C_NEUMANN`,
- peak memory when the clean tournament implementation can measure it,
- fallback rate.

## Q34 promotion gate

Use `docs/research/q34_joint_gate.md`:

- verified quality parity,
- structure utility recovery >=0.80,
- discovery cost <=20% of recovered pre-discovery savings,
- complete cost < Direct,
- preregistered seed/split requirements.

Pareto-dominated families are deleted immediately.

## Stop rule

If three materially different families have adequate representation ceilings
but fail the same Q34 gate, stop local discoverer tuning. Reject the current
Q3/Q4 formulation and move to a higher-level representation/objective/task
redesign.

If one family passes Q34 on a fresh preregistered evaluation, stop polishing
Q3/Q4. Carry that candidate plus fallback directly into Q5 scaling and
cross-domain tests.

## Immediate v0.0.97 order

Run the tournament in information-efficient order:

1. A deterministic-first and B frozen minimal learned support routes with no
   new training;
2. D adaptive support using the same frozen scores if possible;
3. C full-information route only if its extra cost can still fit the Q34
   discovery budget;
4. train a new model only if an untrained/frozen family has adequate ceiling
   but leaves a clearly identified residual gap.

This ordering makes model training the last, not the first, response to failure.
