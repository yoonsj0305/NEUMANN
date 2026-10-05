# P1.9 P0 — candidate-local semantic proposition selector

Date: 2026-10-05

P1.8 remains immutable **FAIL / CONTROL_WORK_ACCOUNTING_FAILURE**. Read-only post-hoc analysis shows the inherited full-S4 residual selector is not merely too slow: B01 and B04 stably prefer wrong candidates, B02 points weakly toward the correct candidate but fails the preregistered margin, and B03 is incomplete.

## Architecture change

Retain the successful P1.8 deterministic front half:

```
source-bound evidence
-> complete bounded candidate enumeration
-> deterministic feasibility pruning
-> 0 candidates: reject
-> 1 candidate: zero-neural execution
-> 2+ candidates: P1.9 candidate-local proposition scoring
```

For each remaining candidate (c_i), P1.9 asks the same binary semantic proposition:

```
Is this candidate interpretation faithful to the original public instruction and obligation?
A = FAITHFUL
B = NOT_FAITHFUL
```

Candidate identity appears only in the prompt. The output-code semantics never change between candidates. This removes the P1.8 need to average over all 24 A/B/C/D candidate-slot bijections.

## Stability and cost

For (k) eligible candidates, score identical candidate prompts under:

1. one batch containing all (k) candidates,
2. unbatched candidate scoring,
3. one reverse-order batch.

Forward count:

[
C_f(k)=1+k+1=k+2.
]

For the P1.8 B candidate counts 2/3/4/3, the prospective diagnostic count is:

[
4+5+6+5=20
]

forwards, versus 144 in the frozen P1.8 contract. This is a **planned architecture count**, not measured latency or an efficiency result.

Selection uses candidate-local log odds

[
s_i = log P(A\mid c_i)-log P(B\mid c_i).
]

P0 default guards:
- max cross-mode log-odds drift <= 0.05 nats
- top candidate log odds >= 0
- top-vs-second margin > 0.5 nats
- all execution modes choose the same candidate
- no generation or retry
- frozen model identity and complete cost receipts

## Boundaries

This P0 is synthetic-contract work only. No actual P1.9 Gemma score has run. No new development set is registered. P1.8 is not rerun or rescued. Strong future baselines must share the deterministic source extraction, feasibility pruning, compiler, specialist and original verifier.

P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 globally OPEN.


## Data boundary for the first actual P1.9 score

P1.8 B01-B04 directly informed this architecture change and are therefore opened development history. They may be used only as model-free/synthetic regression fixtures. They must not be rescored with Gemma and presented as P1.9 evidence.

Before any actual P1.9 model score, a new semantic-development set must be authored, independently checked, hashed and registered. The new set must preserve public grounding, multi-feasible candidates after deterministic pruning, no hidden expected label in model input, and independent original-task verification.
