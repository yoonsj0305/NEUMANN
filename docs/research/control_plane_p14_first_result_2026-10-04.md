# P1.4 first actual semantic-development result — retained FAIL

Date: 2026-10-04

## Immutable evidence identity

- archive: `NEUMANN_P14_FIRST_EVIDENCE.zip`
- bytes: **61,736**
- SHA-256: `7f819cd1dd26dc94ca690b4be3e2e365b7f65882900caff78e30e3e1c647af52`
- members: 35
- unsafe paths: none
- duplicate members: none
- symlinks: none
- ZIP CRC: valid
- every archive-manifest member byte count and SHA-256: valid
- no replacement attempt

Frozen source/runtime identity:

- source head: `bba2e6a6420581edddeafdba94fbd8b60f540e56`
- tested/merged tree: `94b88cb154a102764bea6fc5d5d0a6da133b6ad6`
- bootstrap SHA-256: `602c2164a05bf3b2fca6f886bcb2217478c063f1ee46d327109588416b27c30a`
- model: `google/gemma-4-E2B-it`
- revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16, Tesla T4, frozen weights
- core audit unchanged: true
- new training: false
- frontier calls: 0
- sealed data opened: false
- historical score reuse: false

## Frozen first-result verdict

The actual experiment completed all 12 observations. Its frozen evaluator wrote:

```
P1.4 = FAIL
reason = RAW_ACCOUNTING_INCOMPLETE
P2 registration admitted = false
P2 admitted = false
Decision 3 admitted = false
```

The outer Kaggle bootstrap reported `FAILED_OR_INTERRUPTED` only because the subsequent **model-free replay process failed**. This does not mean the model experiment was partial: `report.json` is COMPLETE, `observations=12`, `error=null`, and `terminal.json` records `complete=true`, `decision=FAIL`.

The first result is not rerun or replaced.

## Why the official reason is accounting-related

Two raw items completed their Gemma generation but produced representations rejected by the strict P1.3 contract layer:

- `p14d_03`: ARITHMETIC proposal used floating literal `0.5`; P1.3 correctly rejected it with `integer literal required`.
- `p14d_06`: CSP proposal emitted malformed constraint tuples; P1.3 correctly rejected them with `three-field constraint required`.

The original P1.4 wrapper retained both failures but left their per-item `accounting_complete=false`. Therefore the preregistered evaluator stops at `RAW_ACCOUNTING_INCOMPLETE`.

This is an implementation/accounting defect in the diagnostic wrapper, not evidence that those two tasks succeeded. Their completed generation work remains charged in the retained receipts.

## Independent semantic-capability recomputation

Even if the two completed failed generations are treated as fully charged accounting, the preregistered semantic capability gate still fails. Therefore fixing accounting cannot rescue P1.4.

| Gate | Frozen threshold | Observed | Result |
|---|---:|---:|---|
| raw semantic accepted | >= 6/8 | **5/8** | FAIL |
| raw arithmetic accepted | >= 3/4 | **2/4** | FAIL |
| raw CSP accepted | >= 3/4 | **3/4** | PASS |
| mixed fallback accepted | >= 3/4 | **4/4** | PASS |
| raw semantic model calls | exactly 8 | **8** | PASS |
| mixed fallback calls | exactly 4 | **4** | PASS |

Task-level raw semantic result:

| task | intended family | proposal route | outcome | diagnosis |
|---|---|---|---|---|
| p14d_01 | arithmetic | ARITHMETIC | ACCEPTED | correct |
| p14d_02 | arithmetic | ARITHMETIC | REJECTED_BY_ORIGINAL_VERIFIER | sequential operation semantics compiled incorrectly: `(21/7)+5*4` instead of `((21/7)+5)*4` |
| p14d_03 | arithmetic | ARITHMETIC | FAILED | unsupported float literal `0.5` instead of exact rational-compatible IR |
| p14d_04 | arithmetic | ARITHMETIC | ACCEPTED | correct |
| p14d_05 | CSP | CSP | ACCEPTED | correct |
| p14d_06 | CSP | CSP | FAILED | malformed constraint surface syntax |
| p14d_07 | CSP | CSP | ACCEPTED | correct |
| p14d_08 | CSP | CSP | ACCEPTED | correct |

All eight raw items selected the intended broad specialist family. The failure moved **inside semantic representation construction**, not route-family choice.

## Mixed typed fallback result

All four mixed typed tasks passed the original verifier:

```
p14d_09 -> ARITHMETIC -> ACCEPTED
p14d_10 -> ARITHMETIC -> ACCEPTED
p14d_11 -> CSP        -> ACCEPTED
p14d_12 -> CSP        -> ACCEPTED
```

Each fallback used 36 neural forward calls, for 144 total. All six registered LOO winners were stable on all four tasks. Worst observed:

- numeric batch/order delta: `4.76837158203125e-07` nats
- centered full24/LOO20 sensitivity: `0.1659505218075843` nats
- minimum full24 winner margin: `1.2057291658517593` nats

Thus the mixed masked-full-S4 path worked on this opened development diagnostic, although it remains expensive and does not establish economic advantage.

## Complete measured work

- 12/12 observations
- raw Gemma generation calls: 8
- raw input tokens: 1,547
- raw output tokens: 515
- summed raw generation time: 42,830.961 ms
- mixed fallback calls: 4
- mixed neural forward calls: 144
- mixed evaluated/padded tokens: 67,104
- mixed score rows/scored code tokens: 1,152 / 1,152
- model startup: 117,888.579 ms
- whole study: 723,101.583 ms
- longest task: 61,689.538 ms
- max allocated accelerator memory: 10,394,046,976 bytes
- energy / FLOPs / money: UNKNOWN

## Replay failure is secondary infrastructure failure

The archived model-free replay failed on `p14d_03` because the record contains a parsed proposal object, but that proposal is **not an admissible P1.3 typed contract**. The replay tried to call `_routing_from_proposal` without treating contract rejection as a legitimate retained first-result failure and raised:

```
ValueError: integer literal required
```

A replay repair may teach the model-free verifier how to replay retained invalid-proposal failures. It must not change the original task receipts, frozen decision, thresholds, model behavior, or admission state, and must not trigger a new inference run.

## Scientific interpretation

The progression is now:

```
P1       FAIL  verbalizer prior collapse
P1.1    FAIL  subset permutation interaction
P1.2dev PASS  full-S4 representation stability on opened development
P1.2val FAIL  stable semantic compatibility error on typed CSP
P1.3    PASS  deterministic contract-first typed dispatch, zero neural forwards
P1.4    FAIL  raw semantic representation construction
```

P1.4 gives a sharper localization:

1. **route-family identification is not the current raw bottleneck** on these eight items; all eight proposals chose the intended ARITHMETIC/CSP family.
2. **surface-valid executable IR construction is the bottleneck**:
   - exact arithmetic sequencing can be semantically changed by ordinary expression generation;
   - equivalent numeric surface forms can violate a strict exact grammar;
   - constraint relations can drift from the registered IR syntax.
3. The original verifier correctly rejects semantic mistakes, and P1.3 correctly rejects malformed typed representations.
4. Therefore simply retrying the same free-form JSON generator is not the preferred next step.

## Next architecture candidate

The next candidate should move one layer further toward NEUMANN's structural thesis:

```
raw language
    ↓
semantic sketch / typed atoms
    ↓
deterministic canonical compiler
    ↓
P1.3 admissibility
    ↓
specialist executor
    ↓
original verifier
```

The model should identify **minimal semantic structure**, not write the final executable expression/constraint JSON freely when deterministic compilation can guarantee representation validity.

A new version must be preregistered on new opened development inputs before model scores. The current P1.4 twelve are now opened diagnostic evidence. P1.4 is not rerun.

P2 registration remains BLOCKED.
P2 actual remains BLOCKED.
Decision 3 remains BLOCKED.
Q1-Q7 remain globally OPEN.
