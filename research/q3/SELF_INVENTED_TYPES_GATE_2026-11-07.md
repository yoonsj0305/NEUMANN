# NEUMANN 1 | Q3 self-generated data-type representations and learned operators

Scientific receipt. 2026-11-07. **Q3_GLOBAL OPEN.** Q4 OPEN. Q6 OPEN.

## Frozen first result 1: generated state variant types

PR #705: https://github.com/yoonsj0305/NEUMANN/pull/705
Original GitHub Actions #42343626953:
https://github.com/yoonsj0305/NEUMANN/actions/runs/42343626953
Immutable result artifact #13562583424.

Human-coded starting class: finite subsequential transducer, generic
Variant and Cases runtime, consistency-based state partition learning.

Machine-invented from I/O: number of state constructors (1, 2, 3 or 4),
transition case table, emitted output chunks, content-addressed executable
operator definition and persistent data-type declarations.

- Prefix-observed synthetic tasks: **42/42 original problems**, **1008/1008**
  long heldout sequences exact. This requires richer prefix I/O supervision.
- Ordinary complete-input-to-complete-output tasks, no intermediate traces:
  **88/88**, **2112/2112** long heldouts exact. This class was equal-length
  outputs and position-alignable. This includes 48 fresh extra seeded random
  state machines not used in the earlier pilot.
- 41 and 86 distinct learned executable program definitions respectively.
  These are not 127 distinct fundamental computational type constructors.
- Restricted prior pointwise-map expressivity witnesses in 32 and 79 tasks.
  Across 130 problems, 111 had explicit dependence on prefix or output growth.
- Persistent library ran: invent, reuse, invent, reuse, invent, reuse
  with three different learned state transition laws.
- No hidden state-count, state labels, target transition table, target
  program code or task-family labels were given to the learning engine.

## Frozen first result 2: creates different representation kinds

PR #706: https://github.com/yoonsj0305/NEUMANN/pull/706
GitHub Actions #42344107792:
https://github.com/yoonsj0305/NEUMANN/actions/runs/42344107792
Immutable result artifact #13562917055.

Fixed generic hypothesis candidates were HUMAN-CODED:
(a) finite Variant finite-output state, and
(b) safe integer accumulator plus a synthesized recursive symbolic formula.
A fixed description-length policy chooses the shorter TRAIN-consistent one.

Newly learned task data and semantics:
- 65 synthetic problems and 1560 longer heldout input sequences.
- **61/65 problems** completely exact on all their heldouts.
- **1526/1560 individual heldouts** exact.
- 60 models selected new symbolic integer state, five chose finite Variant.
- 678 correct heldouts emitted at least one integer value absent from all
  corresponding TRAIN output values. A frozen finite transducer with
  fixed emissions cannot emit those new symbols, but the learned numeric
  recursive update program can.
- Four partial generalization failures: random affine tasks #9, #10,
  #35 and #40. In those cases the selector chose a finite machine that
  overfit the source constraints; no automatic correctness claim is made.
- Persistent heterogeneous language invented a sum type/operation, reused
  it, invented a different modular-3 finite type, reused it, invented a
  signed-balance recursive arithmetic operator, then reused it.
- Runtime aborts numeric output with absolute magnitude above 100,000,000.
  Unknown finite transitions and unsupported input structures ABSTAIN.
- No trained neural discovery policy or external original ARC test involved.

## Formal relative expressivity counterexamples

Previous elementwise map/filter-only language: if output length equals input
length and values are retained, output at position i cannot depend on earlier
input positions. For cumulative parity:
input [1,0] -> [1,1], but input [0,1] -> [0,1].
This violates pointwise permutation equivariance; the previous RESTRICTED
map/filter language cannot express this rule without an added state operator.

A finite machine whose transition outputs are a fixed subset of the labels
observed during TRAIN cannot emit new labels outside that set. A new
generated symbolic integer-state update can compute the output
[1,2,...,60] for sixty unseen input ones. It emits output symbols absent
from the finite machine's original table.

This is a limited relative expressivity separation, not a proof that
general classical programming languages cannot implement these functions.

## Negative controls and broader research relevance

Previous actual ARC original generalization remains OPEN:
- #700 frozen join-type reuse on 233 distinct ARC-AGI-2 originals: 0/233.
- #701 unchanged finite case-function inventor on those: 0/233.
- #702 source-exposed graph/coordinate invention: 1/233 exact.
- #703 same frozen graph inventor on 432 old ARC originals: 0/432.

Graph, tree, variable-shaped spatial, noncausal reverse, and unforeseen
recursive data types are NOT demonstrated by these new finite/integer
hypothesis generators. The finite-state merging idea and learned grammar
approach are established in grammatical inference and DreamCoder.
Relevant references:
- DreamCoder PLDI 2021 https://doi.org/10.1145/3453483.3454080
- Grammatical inference and RPNI state-merging:
  https://ijcai.org/proceedings/2005/186

## Decision

**Scoped PASS:** Data-only new Variant and Integer-state representations,
execution semantics generated as named typed ASTs, cross-task persistence,
automatic reuse and a failure-triggered decision to invent a DIFFERENT type.

**Global Q3 OPEN:** Both representation-constructor families and model
selection rule were written by the programmer. The system did NOT generate
a genuinely unforeseen THIRD representation-constructor algorithm, train a
neural discovery policy, or demonstrate robust cross-domain external-original
transfer. Synthetic targets were defined by the experiment designer.
No 10x compute efficiency, state-of-the-art or research novelty claim.

The next decisive test must freeze the entire mechanism and require
unforeseen independently authored structure families. A PASS requires a new
constructor schema and executor not installed by human programmers, plus
repeat source-excluded transfer. Otherwise report OPEN or FAIL.
