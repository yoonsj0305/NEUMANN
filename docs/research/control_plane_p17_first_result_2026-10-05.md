# P1.7 first actual source-bound development result — retained FAIL

Date: 2026-10-05

## Evidence identity reported by the frozen Kaggle run

- archive: `NEUMANN_P17_FIRST_EVIDENCE.zip`
- bytes: **86,633**
- SHA-256: `97f84b6e5f0980fdc815dbb3678502e0e23b1459af1b68e1630361379a254bad`
- ZIP members reported by the in-session verifier: **35**
- ZIP CRC reported: **PASS**
- no replacement attempt

The first attempt is immutable and must not be rerun or replaced.

The conversation-side copy available at result-retention time was not a usable copy of the archive, so this checkpoint records the exact frozen-run receipts supplied from Kaggle but does not claim independent byte-for-byte archive ingestion. Independent archive ingestion remains pending until the verified 86,633-byte ZIP is transferred successfully.

## Frozen study result

The actual study completed all 12 registered obligations:

```
study status = COMPLETE
observations = 12
core unchanged = true
report error = null

P1.7 verdict = FAIL
reason = TASK_WALL_CAP

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

The outer bootstrap reported `FAILED_OR_INTERRUPTED` only because the subsequent model-free replay process exited nonzero. That replay failure is secondary and does not change the frozen study verdict.

## Strong positive result: unique source-bound path

All eight unique obligations passed end to end with **zero model calls and zero neural forward calls**:

```
p17d_01 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_02 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_03 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_04 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_05 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_06 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_07 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_08 CSP         ACCEPTED  model_calls=0  forwards=0
```

Each reached the specialist and independent original verifier:

- tool calls: 8
- verifier calls: 8
- accepted: 8/8

This is opened-development evidence that, inside the P1.7 bounded grammar, deterministic source-span evidence extraction plus exact compilation can eliminate neural control work entirely when interpretation is unique.

It does **not** establish open-set/general semantic competence, P2 readiness, or global Q1-Q7 closure.

## Ambiguous stratum: selector runtime failure

All four ambiguous obligations failed before specialist execution:

| task | model calls | neural forwards | tool/verifier calls | retained failure |
|---|---:|---:|---:|---|
| p17d_09 | 1 | 7 | 0 / 0 | partial/wrong candidate receipt |
| p17d_10 | 1 | 36 | 0 / 0 | selector wall cap |
| p17d_11 | 1 | 31 | 0 / 0 | partial/wrong candidate receipt |
| p17d_12 | 1 | 36 | 0 / 0 | selector wall cap |

Observed aggregate neural work:

- model calls: **4**
- neural forward calls: **110**
- generated calls: **0**
- evaluated tokens: **183,042**
- padded tokens: **183,042**

The registered path expected 144 forwards for four complete 36-forward full-S4 selections. The first and third ambiguous tasks timed out partway; the second and fourth completed all 36 forwards but exceeded the frozen selector wall budget before admission.

Therefore this first result does **not** provide a semantic winner/loser judgment for any ambiguous candidate. The bottleneck is the cost/runtime of the diagnostic full-S4 selector itself.

## Runtime accounting

Reported study receipts:

- frozen-core startup: **104,631.266 ms**
- whole study: **666,819.197 ms**
- maximum accelerator allocated: **10,830,349,312 bytes**
- maximum accelerator reserved: **12,060,721,152 bytes**
- peak process RSS: **12,195,471,360 bytes**
- energy / FLOPs / money: UNKNOWN

The first ambiguous task also bears lazy frozen-core startup inside its item wall. Later ambiguous tasks show that even without first-startup cost, the 36-forward selector can still violate the selector wall budget.

The frozen evaluator checks the task wall gate before later accounting/capability gates, so the official reason remains exactly `TASK_WALL_CAP`. The aggregate report also records `accounting_complete=false` because all four ambiguous selection attempts failed before complete admitted selection.

## Replay failure is a separate infrastructure defect

The archived model-free replay stopped with:

```
ValueError: P1.7 semantic replay drift: execution
```

Root cause in the replay code: it compared the entire `execution` object byte-for-byte between retained evidence and a fresh model-free reconstruction. `execute_selected()` includes a newly measured local `complete_ms` field, so two semantically identical executions are not timing-identical.

The replay contract is repaired prospectively to compare only:

```
accepted
executed
answer
error
```

while separately requiring retained and replayed execution timings to be finite. The repair does not change any task receipt, cost, frozen verdict, gate, candidate, answer, or admission state and performs no model inference.

## Scientific interpretation

P1.7 materially changes the localization of the problem.

Previous failures were dominated by generated representation syntax and regenerated operand drift. P1.7's source-bound deterministic path removes those failure modes on all eight unique opened obligations:

```
source evidence
-> complete bounded interpretation
-> exact compiler
-> specialist
-> original verifier
```

with neural work = 0.

The remaining first-result bottleneck is now:

```
bounded ambiguity
-> expensive neural selector
```

rather than raw semantic serialization.

More importantly, the four registered ambiguous tasks themselves expose an architectural inefficiency. Their public rule is to select the pronoun binding that makes the stated finite constraints jointly satisfiable. Candidate satisfiability can be tested deterministically from the candidate IR without private references or the original verifier.

Thus the cheapest safe cascade should test deterministic feasibility **before** invoking a neural selector:

```
source-bound candidate set
        ↓
deterministic candidate feasibility pruning
        ↓
0 candidates -> reject
1 candidate  -> select with zero neural work
2..K viable  -> bounded neural choice only if ambiguity genuinely remains
        ↓
canonical compiler
        ↓
specialist
        ↓
independent original verifier
```

This is not a post-hoc rescue of P1.7. The P1.7 ambiguous tasks are opened and may only inform the next architecture.

A future fresh study should include both:
1. ambiguities that deterministic feasibility uniquely resolves, and
2. ambiguities where multiple candidates remain feasible and a neural semantic choice is genuinely necessary.

Otherwise a new benchmark would merely encode the answer into deterministic satisfiability.

## Boundary

P1.7 first actual remains permanently:

```
FAIL / TASK_WALL_CAP
```

P1.7 is not rerun.
P2 registration remains BLOCKED.
P2 actual remains BLOCKED.
Decision 3 remains BLOCKED.
Q1-Q7 remain globally OPEN.
