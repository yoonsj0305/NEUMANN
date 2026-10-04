# P1.1 first actual balanced-coded controller result — retained FAIL

Date: 2026-10-04

## Integrity and frozen identity

Uploaded first-evidence archive:

- file: `NEUMANN_P11_FIRST_EVIDENCE.zip`
- bytes: 52,833
- SHA-256: `6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec`
- archive members: 36
- unsafe paths / duplicate members / symlinks: none
- archive member hashes: all match `archive_manifest.json`
- experiment terminal pins: all match
- independent model-free replay: `integrity_valid=true`

Frozen runtime:

- experiment source head: `4e6db9926a27c94f63c8d539d0c6e57c34b49336`
- bootstrap SHA-256: `a2372bb34ba76a50e92eca3d3e6cecaa60d10606d05a332329a0b17c347d610c`
- model: `google/gemma-4-E2B-it`
- model revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16, frozen weights, Tesla T4
- model/tokenizer/artifact audit unchanged
- codes: A/B/C/D
- token IDs: 236776 / 236799 / 236780 / 236796
- all codes: distinct, single-token, non-special, exact frozen tokenizer
- generated calls: 0
- tool calls: 0
- frontier calls: 0
- new training: false
- sealed/fresh validation data opened: false

## Frozen verdict

```
P1.1 = FAIL
reason = NUMERIC_OR_PERMUTATION_INSTABILITY
P2 admitted = false
Decision 3 admitted = false
fresh validation registered = false
```

The run is complete and accounting-complete. It is not a setup failure.

## Complete accounting

- observations: 12/12
- input rows: 288
- scoring rows: 1,152
- scored code tokens: 1,152
- evaluated tokens: 65,304
- padded tokens: 65,304
- forward calls: 144
- startup: 136,019.051389 ms
- controller wall: 147,784.539878 ms
- whole study: 283,803.594684 ms
- maximum numerical batch/order delta: 5.960464477539063e-08 nats
- core audit unchanged: true
- report error: null

The failure is therefore not numerical nondeterminism between batch/unbatched/
reversed execution modes. It is the preregistered cross-schedule centered-score
invariance gate.

## Development-only route behavior

Although the frozen gate failed, the pooled route winners are highly structured:

| task | pooled winner | pooled margin (nats) | centered schedule delta (nats) | gate |
|---|---|---:|---:|---|
| am_math_01 | ARITHMETIC | 6.888672 | 0.768066 | FAIL |
| am_math_02 | ARITHMETIC | 7.164062 | 0.940918 | FAIL |
| am_math_03 | ARITHMETIC | 5.037109 | 0.771484 | FAIL |
| am_math_04 | ARITHMETIC | 6.046631 | 0.989624 | FAIL |
| am_code_01 | PYTHON | 6.377930 | 0.619141 | FAIL |
| am_code_02 | PYTHON | 5.133545 | 0.449585 | PASS |
| am_code_03 | PYTHON | 5.886841 | 0.611756 | FAIL |
| am_code_04 | PYTHON | 4.716797 | 0.543030 | FAIL |
| am_plan_01 | CSP | 3.523437 | 0.068359 | PASS |
| am_plan_02 | CSP | 6.429688 | 0.459473 | PASS |
| am_plan_03 | CSP | 4.804687 | 0.338379 | PASS |
| am_plan_04 | CSP | 1.644531 | 0.468262 | PASS |

Winner counts:

```
DIRECT      0
ARITHMETIC  4
CSP         4
PYTHON      4
```

Both preregistered Latin schedules choose the same winner on all 12 tasks.
All pooled margins are >1.64 nats. The across-task centered route-score range,
computed post-result for diagnosis only, is about 8.717773 nats.

Seven tasks exceed the frozen schedule-delta tolerance of 0.50 nats. All four
math tasks fail that tolerance, as do code tasks 01, 03 and 04. The maximum is
0.989624 nats.

The task IDs and construction make the coarse expected executor family obvious
after the fact. The 4/4 ARITHMETIC, 4/4 PYTHON and 4/4 CSP pattern is therefore
a useful development diagnostic, but it is **not** fresh capability evidence,
not a P1.1 rescue and not grounds to admit P2.

## What the failure means

P1.1 successfully removed the catastrophic P1 bare-verbalizer collapse. The
controller no longer chooses one label on all tasks, and its winner is stable
under both registered schedules.

However, the two balanced four-map schedules do not produce sufficiently
invariant centered route scores. This demonstrates a real residual
code/legend/mapping interaction beyond a fixed additive code-token prior.

The preregistered 0.50-nat criterion was intentionally evaluated as written.
Do not relax it post hoc and call P1.1 PASS.

## Recommended next architecture candidate

A clean next development revision is a **fully permutation-marginalized coded
router** over all 24 bijections between the four executor semantics and the
four frozen one-token codes:

```
S(r | x) = (1 / 24) * sum_{pi in S4}
           log P(code[pi(r)] | x, legend_pi)
```

This is stronger than choosing another favorable Latin subset. Averaging over
the complete permutation group makes the route statistic invariant to which
balanced schedule subset happened to be selected and marginalizes each route
over every code and every assignment of the other routes.

The current 12 tasks may be used only as opened development data for this
revision. A new preregistration must freeze:

- all 24 maps before scoring;
- exact tokenizer/model/runtime identity;
- complete controller cost and wall limits;
- batch/unbatched/reversed numerical checks;
- a decision-stability diagnostic that is specified before the new run;
- no P2 or Decision 3 admission from development;
- fresh opened validation still created only after architecture freeze.

Do not rerun P1.1. Preserve this result as the immutable first actual P1.1
outcome.

Q1–Q7 remain globally OPEN.
