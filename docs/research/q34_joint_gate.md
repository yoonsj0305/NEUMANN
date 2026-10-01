# NEUMANN 1 — Q34 Joint Gate

Updated 2026-10-01. This gate replaces serial Q3-then-Q4 development decisions.
Q3 and Q4 remain useful analytical labels, but architecture promotion is now
decided by one coupled gate.

## Development question

A structure is useful only if the system can recover enough of the available
structural savings **and** discover it cheaply enough.

For a matched case set, define:

- `C_D`: strongest independently verified Direct complete cost.
- `C_O`: post-discovery complete cost when the useful oracle structure is
  supplied for free under the same executor/verifier authority.
- `C_disc`: candidate discovery cost.
- `C_post`: candidate execution + verification + retry/fallback cost after
  discovery.
- `S_oracle = C_D - C_O`: total structural savings available in principle.
- `S_candidate = C_D - C_post`: structural savings recovered before paying
  discovery.

Aggregate over the frozen evaluation set before forming the ratios:

```
structure_utility_recovery = sum(S_candidate) / sum(S_oracle)
discovery_burden = sum(C_disc) / sum(S_candidate)
C_NEUMANN = sum(C_disc + C_post)
```

The set is ineligible when `sum(S_oracle) <= 0` or
`sum(S_candidate) <= 0`.

## Frozen internal engineering gate

A candidate architecture passes the development Q34 gate only when all are true:

1. independently verified capability/quality matches the Direct authority;
2. `structure_utility_recovery >= 0.80`;
3. `discovery_burden <= 0.20`;
4. complete cost including all retries and fallback is lower than Direct;
5. the result survives the preregistered seed/split requirements for that
   experiment.

The 80% / 20% values are engineering thresholds, not a scientific law. They
may be changed only in a future preregistration **before** new evidence is
observed. Never retune them to rescue an observed failure.

## Fallback is part of NEUMANN

Q34 does not require 100% structural recovery. A candidate may abstain and use
Direct fallback. Fallback cost and verification are charged to `C_post`.
The target is therefore a profitable, reliably identifiable subset, not a
perfect universal discoverer.

## Representation ceiling before training

No architecture receives a new training budget until its representation clears
a cheap ceiling screen. Ask whether the required useful structure is even
recoverable from the retained representation. Hidden labels/oracles may be used
only offline to estimate this ceiling; they never become inference authority.

If the representation ceiling is below the Q34 utility floor, do not train.
If the ceiling is high but the real discoverer still fails, stop blaming
representation and change the discoverer/target.

## Architecture tournament

After the ceiling screen, compare at most four materially different families
under one evaluator:

A. deterministic-first structural probe,
B. minimal learned proposer,
C. full-information small model,
D. adaptive iterative/refinement architecture.

All receive the same problem distribution, Direct comparator rights,
verification authority, failure accounting and hardware/runtime conventions.
Pareto-dominated candidates are deleted immediately.

A refinement of one family does not count as a new family unless it changes the
information/authority/computation contract materially.

## Stop / advance rule

If three materially different architecture families fail the same Q34 gate
after their representation ceilings are adequate, stop local architecture
tuning and reject the current Q3/Q4 formulation. Move one level up to the
problem representation, objective or task family.

If one architecture passes a fresh preregistered Q34 evaluation, stop polishing
Q3/Q4 and advance to Q5 with that candidate plus fallback.

The objective is not to solve Q3 and Q4 beautifully. It is to solve them only
well enough to make a legitimate Q5 end-to-end scaling test possible.
