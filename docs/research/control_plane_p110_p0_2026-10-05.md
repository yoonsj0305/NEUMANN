# P1.10 P0 — Minimal Semantic Contrast + symmetric pairwise scoring

Date: 2026-10-05

P1.9 remains immutable **FAIL / P19_SEMANTIC_CAPABILITY_FAILURE**.

P1.9 successfully reduced the inherited full-S4 control cost, but only one of eight fresh semantic tasks passed the frozen selector gate. Raw top-candidate direction was 4/8. Threshold relaxation is therefore not a valid next step.

## Delete solved structure before neural scoring

After deterministic source extraction and feasibility pruning, the unresolved question is not the full CSP. It is only:

> Which source-bound entity does the single ambiguous mention denote under the public semantic instruction?

P1.10 derives a minimal semantic contrast IR:

```
{
  public semantic instruction,
  source span of "It",
  candidate bindings [
    candidate -> source entity surface/span
  ]
}
```

The neural prompt explicitly drops domains, literal values, already-resolved CSP relations, canonical candidate atoms and the evidence-alias ledger.

This is a direct application of the NEUMANN rule:

`Learn only irreducible uncertainty. Derive everything else cheaply.`

## Relative rather than absolute semantics

P1.9 independently scored each candidate as:

`FAITHFUL vs NOT_FAITHFUL`.

That exposed task-dependent absolute calibration. P1.10 instead compares two candidate bindings directly with fixed code semantics:

- A = LEFT binding is more faithful
- B = RIGHT binding is more faithful

For candidates i and j:

`L(i,j) = log P(A | i-left,j-right) - log P(B | i-left,j-right)`.

Score the swapped orientation too:

`L(j,i)`.

Then compute:

`D(i,j) = (L(i,j) - L(j,i))/2`.

A constant A/B token prior cancels algebraically. First-order left/right presentation bias is also symmetrized.

## Selection

P0 requires a unique confident Condorcet winner: candidate i must have

`D(i,j) > 0.5 nats`

for every remaining candidate j.

Otherwise the semantic controller abstains.

The 0.5-nat floor is retained from the prior conservative confidence scale rather than tuned against P1.9 task labels.

## Cost architecture

For k candidates there are k(k-1)/2 unordered pairs and both orientations are encoded in one batch.

P1.10 keeps only:

1. batch-all,
2. reverse-batch-all.

Therefore the planned neural forward count is:

`2 forwards per ambiguous item`.

The removal of the unbatched diagnostic is prospective and is motivated by P1.9's 8/8 exact equality across batch-all, unbatched1 and reverse-batch-all scores on the frozen T4 backend. P1.10 still fails closed if the two retained batch orders drift by more than 0.05 nats.

## Boundaries

P1.10 P0 is synthetic-contract work only.

- no P1.10 Gemma score has run
- P1.9 tasks are architecture/regression fixtures only and may not be rescored as P1.10 evidence
- actual P1.10 requires a new preregistered development set
- no generation, retry, hidden reference access or numeric regeneration
- deterministic feasibility and independent original verification remain mandatory
- P2 registration=false
- P2=false
- Decision3=false
- Q1-Q7 globally OPEN
