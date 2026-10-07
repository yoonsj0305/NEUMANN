# P1.9 P0.1 — complementary-polarity balancing

Date: 2026-10-05

Parent: P1.9 P0 candidate-local proposition scoring.

P1.8 remains immutable **FAIL / CONTROL_WORK_ACCOUNTING_FAILURE**. No historical result is rerun or rescued.

## Why P0.1 exists

P1.9 P0 removes candidate-slot A/B/C/D permutation by giving every candidate the same output semantics. That removes one major source of arbitrary representation, but a fixed additive preference for output code A over B can still shift an absolute faithful-vs-not-faithful log-odds threshold.

P0.1 cancels that fixed code prior by scoring two complementary claims for each candidate with the same response semantics:

```
claim + : candidate is FAITHFUL
claim - : candidate is NOT_FAITHFUL

A = YES
B = NO
```

For candidate (i):

[
d_i^+ = log P(A|+)-log P(B|+)
]

[
d_i^- = log P(A|-)-log P(B|-)
]

and the balanced semantic score is

[
s_i = rac{1}{2}(d_i^+-d_i^-).
]

If a fixed additive A/B logit preference contributes the same offset (b) to both propositions,

[
(d_i^++b)-(d_i^-+b)=d_i^+-d_i^-,
]

so that fixed prior cancels exactly.

This does **not** prove immunity to prompt-dependent code interactions. Those remain an empirical question.

## Diagnostic execution modes

For (k) eligible candidates there are (2k) proposition rows.

P0.1 evaluates:
1. batch4 canonical order,
2. unbatched1 canonical order,
3. reverse batch4.

Planned forward count:

[
C_f(k)=2k+2leftlceilrac{2k}{4}ightceil.
]

For candidate counts (2/3/4/3):

[
6+10+12+10=38
]

diagnostic forwards, versus the frozen P1.8 contract's 144.

This is a planned diagnostic count only. It is not measured latency, FLOPs, energy, money, or production cost.

If later evidence shows the batch mode is numerically and semantically stable, a future separately registered fast path could evaluate only the canonical batch mode. That optimization is **not** admitted by this P0.1.

## Frozen synthetic guards

- fixed A=YES / B=NO response semantics
- complementary FAITHFUL / NOT_FAITHFUL claims
- candidate identity never encoded in output code
- zero candidate/code permutations
- max cross-mode balanced-score drift <= 0.05 nats
- winning balanced score >= 0
- top-vs-second balanced margin > 0.5 nats
- all three modes select the same candidate
- exact cost receipts
- no generation
- no retry
- no hidden reference access
- no numeric/entity regeneration

The synthetic tests explicitly add the same A/B log-odds bias to both complementary propositions and require the balanced semantic score and selected candidate to remain unchanged.

## Data boundary

P1.8 B01-B04 informed this architecture and are regression fixtures only. They must not be rescored as P1.9 evidence.

Any actual P1.9 model score requires a completely new, prospectively registered semantic-development set with independent original checkers and source/data hashes.

## Boundary

P0.1 is synthetic-contract work only. Actual P1.9 Gemma = **NOT RUN**. Development registration = **NOT REGISTERED**.

P2 registration=false. P2=false. Decision3=false. Q1-Q7 globally OPEN.
