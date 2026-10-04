# P1.2 first actual full-S4 controller result — retained development PASS

Date: 2026-10-04

## Evidence integrity and frozen identity

First-evidence archive:

- file: `NEUMANN_P12_FIRST_EVIDENCE.zip`
- bytes: 83,071
- SHA-256: `b27748d76b8abdba24ab11ad85f25eb4012c8c9593a12a83590bfbf8666c98ba`
- archive members: 36
- duplicate members: none
- unsafe paths / symlinks: none
- every archive-member size/SHA pin matches `archive_manifest.json`
- every experiment receipt hash matches `terminal.json`
- independent model-free replay: `integrity_valid=true`

Frozen execution identity:

- experiment/bootstrap head: `75d9843e0d893e1a34394258b14c984d461cec1c`
- source tree: `bb4deba6ec23bb5923b2d1ab2dfd4dc5b2e874c5`
- merged PR137 main has the same tree
- bootstrap SHA-256: `c8f66d3f05a672377376cb92f8d4e39f7669cd8e55a88d58a08bfaa430c5bdfe`
- model: `google/gemma-4-E2B-it`
- model revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- precision: BF16
- device: Tesla T4
- frozen weights and artifact/tokenizer identity unchanged
- code token IDs A/B/C/D: 236776 / 236799 / 236780 / 236796
- generated calls: 0
- tool calls: 0
- frontier calls: 0
- new training: false
- historical score reuse: false
- fresh/sealed validation data opened: false

## Frozen development verdict

```
P1.2 = PASS
reason = DEVELOPMENT_DIAGNOSTIC_ONLY
P2 admitted = false
Decision 3 admitted = false
fresh validation registered = false
next = FREEZE_ARCHITECTURE_THEN_REGISTER_FRESH_OPENED_VALIDATION
```

The PASS is only the preregistered opened-development gate. It is not a
capability, efficiency, unseen-generalization, frontier-gap, P2, Decision-3 or
global-Q result.

## Independent gate recomputation

The uploaded raw 24-permutation matrices were recomputed independently using
the frozen P1.2 statistic, rather than trusting the cached report summaries.

Frozen requirements and observed worst cases:

| Gate | Frozen requirement | Observed | Result |
|---|---:|---:|---|
| batch/unbatched/reversed numeric delta | <= 0.05 nats | 9.536743e-07 | PASS |
| centered full24 vs leave-4-out20 sensitivity | <= 0.50 nats | 0.162805 | PASS |
| full24 route margin | > 0.50 nats | minimum 1.433594 | PASS |
| all 6 leave-4-out20 winners | same as full24 | 72/72 stable | PASS |
| distinct task winners | >= 2 | 3 | PASS |
| dominant task winner count | <= 10/12 | 4/12 | PASS |
| across-task centered route range | >= 0.001 nats | 8.846537 | PASS |
| per-task wall | <= 120,000 ms | max 35,821.751 ms | PASS |
| controller wall | <= 540,000 ms | 391,239.381 ms | PASS |
| study wall | <= 1,800,000 ms | 464,399.554 ms | PASS |

Winner counts:

```
DIRECT      0
ARITHMETIC  4
CSP         4
PYTHON      4
```

## Raw development task diagnostics

| task | full24 winner | margin (nats) | max centered LOO20 delta | all LOO winners stable |
|---|---|---:|---:|---|
| am_math_01 | ARITHMETIC | 6.968750 | 0.154167 | yes |
| am_math_02 | ARITHMETIC | 7.467773 | 0.162069 | yes |
| am_math_03 | ARITHMETIC | 5.089193 | 0.150179 | yes |
| am_math_04 | ARITHMETIC | 6.438721 | 0.162805 | yes |
| am_code_01 | PYTHON | 6.009511 | 0.131788 | yes |
| am_code_02 | PYTHON | 5.111287 | 0.076688 | yes |
| am_code_03 | PYTHON | 5.733297 | 0.130075 | yes |
| am_code_04 | PYTHON | 4.632904 | 0.089678 | yes |
| am_plan_01 | CSP | 3.449219 | 0.130404 | yes |
| am_plan_02 | CSP | 7.079102 | 0.122319 | yes |
| am_plan_03 | CSP | 5.068685 | 0.102433 | yes |
| am_plan_04 | CSP | 1.433594 | 0.138851 | yes |

The family-looking 4/4 ARITHMETIC, 4/4 PYTHON and 4/4 CSP pattern is useful
development evidence, but these twelve items are already opened and shaped the
architecture path. It must not be treated as fresh confirmation.

## Complete accounting

- observations: 12/12
- input rows: 864
- score rows / scored code tokens: 3,456 / 3,456
- evaluated tokens: 195,912
- padded tokens: 195,912
- forward calls: 432
- startup: 73,160.168761 ms
- controller wall: 391,239.380740 ms
- whole study: 464,399.553967 ms
- max task wall: 35,821.750550 ms
- frozen core audit: unchanged
- report error: null
- energy, FLOPs, money: UNKNOWN

The 24-map controller uses exactly 3x the P1.1 mapping/forward accounting by
construction. The present PASS is an operational robustness result, not a cost
advantage claim.

## Residual interactions remain

Full-group marginalization makes the **decision statistic** robust to omitting
any one registered balanced four-map orbit, but it does not make individual
mapping logits invariant.

Observed diagnostic-only residuals:

- maximum centered pairwise orbit delta: 1.339600 nats
- maximum centered per-mapping route range: 13.450195 nats

These are intentionally reported even on PASS. P1.2 does not claim that
code/legend interactions disappeared. It claims only that the frozen full-S4
mean and its balanced leave-four-out20 perturbations are stable enough under the
registered development criterion.

## Interpretation

The progression is now:

```
P1   FAIL  bare verbalizer collapsed to ARITHMETIC 12/12
P1.1 FAIL  semantic winners recovered but 8-map subset score geometry unstable
P1.2 PASS  full-S4 mean robust to every registered balanced leave-4-out orbit
```

This is evidence that full permutation marginalization is a viable controller
representation on the opened development set. It is not evidence yet that the
same routing behavior generalizes to unseen tasks or improves end-to-end
capability/cost.

## Required next step

Freeze P1.2 unchanged. Do not tune it further on the original twelve.

Then register a **fresh opened validation** before viewing any new scores:

1. new task identities and source/provenance hashes;
2. explicit deduplication against P1/P1.1/P1.2 development inputs;
3. original independent answer/checker authority;
4. unchanged P1.2 model/tokenizer/codes/all-24 statistic and robustness rules;
5. complete controller and later executor/verifier cost accounting;
6. first-result retention with no favorable rerun;
7. validation PASS may admit P2 registration only, never Decision 3 directly.

P2 and Decision 3 remain BLOCKED. Q1–Q7 remain globally OPEN.
