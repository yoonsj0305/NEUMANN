# P1.2 first fresh opened validation — retained FAIL

Date: 2026-10-04

## Evidence identity

Uploaded first validation archive:

- file: `NEUMANN_P12_VALIDATION_FIRST_EVIDENCE.zip`
- bytes: 93,637
- SHA-256: `362b13d7d7006ea1c55ad33788acd11d1712e94c081d59d52b28581d3abe3444`
- archive members: 36
- unsafe paths / duplicate members / symlinks: none
- every archive member size/SHA pin matches `archive_manifest.json`
- every experiment receipt hash matches `terminal.json`
- bundled model-free replay: `integrity_valid=true`
- no replacement attempt

Frozen execution identity:

- validation source/bootstrap head: `7c9117f3ce4bf9082c9fe104dcc46734beb29ddc`
- tested/merged tree: `33c1b68c135d86deb519e83f5c800f5af8fdd51c`
- bootstrap SHA-256: `77d3e7a57459a89322ff94145a11de73452cc9ce92583e7045fa5bd755028a99`
- model: `google/gemma-4-E2B-it`
- model revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16, frozen weights, Tesla T4
- generated/tool/frontier calls: 0 / 0 / 0
- historical score reuse: false
- new training: false
- sealed data opened: false

## Frozen verdict

```
P1.2 fresh validation = FAIL
reason = TYPED_ROUTE_COMPATIBILITY_FAILURE
P2 registration admitted = false
P2 admitted = false
Decision 3 admitted = false
next = PRESERVE_FIRST_VALIDATION_FAILURE
```

This is a complete study, not a setup or numerical failure.

## Independent recomputation from raw 24-permutation matrices

All P1.2 geometry, numerical, wall and degeneracy gates pass.

| Gate | Frozen requirement | Observed worst case | Result |
|---|---:|---:|---|
| batch/unbatched/reversed numeric delta | <= 0.05 nats | 1.192093e-07 | PASS |
| centered full24 vs each LOO20 delta | <= 0.50 nats | 0.197030 | PASS |
| full24 winner margin | > 0.50 nats | minimum 0.614583 | PASS |
| all six LOO20 winners | same as full24 | 72/72 stable | PASS |
| distinct winners | >= 2 | 3 | PASS |
| dominant winner count | <= 10/12 | 6/12 | PASS |
| centered task range | >= 0.001 nats | 8.355021 | PASS |
| per-task wall | <= 120,000 ms | max 42,159.989 ms | PASS |
| controller wall | <= 540,000 ms | 426,236.293 ms | PASS |
| whole study wall | <= 1,800,000 ms | 561,838.601 ms | PASS |

The failure is therefore isolated to the separately preregistered typed-route
compatibility gate.

## Typed compatibility result

Frozen compatibility gate:

- >=10/12 overall
- >=3/4 in every domain

Observed:

```
overall               10/12  PASS
math_logic             4/4   PASS
coding                 4/4   PASS
constraint_planning    2/4   FAIL
```

Task-level result:

| task | registered compatible route | full24 winner | margin (nats) | max centered LOO20 delta | compatible |
|---|---|---|---:|---:|---|
| p12v_01 | ARITHMETIC | ARITHMETIC | 3.885742 | 0.112101 | yes |
| p12v_02 | ARITHMETIC | ARITHMETIC | 5.858073 | 0.154264 | yes |
| p12v_03 | ARITHMETIC | ARITHMETIC | 6.592122 | 0.154968 | yes |
| p12v_04 | ARITHMETIC | ARITHMETIC | 6.106771 | 0.141488 | yes |
| p12v_05 | PYTHON | PYTHON | 6.609721 | 0.064859 | yes |
| p12v_06 | PYTHON | PYTHON | 8.954102 | 0.111466 | yes |
| p12v_07 | PYTHON | PYTHON | 8.534261 | 0.097770 | yes |
| p12v_08 | PYTHON | PYTHON | 6.756299 | 0.091997 | yes |
| p12v_09 | CSP | **ARITHMETIC** | 0.614583 | 0.174674 | **no** |
| p12v_10 | CSP | CSP | 4.184896 | 0.197030 | yes |
| p12v_11 | CSP | CSP | 1.617187 | 0.074609 | yes |
| p12v_12 | CSP | **ARITHMETIC** | 1.246094 | 0.101237 | **no** |

The two misses are not marginal numerical flips. Every registered LOO20
perturbation keeps the same wrong winner on both tasks.

For p12v_09:

```
ARITHMETIC -3.355686
CSP        -3.970270
PYTHON     -4.062717
DIRECT     -5.043186
```

For p12v_12:

```
ARITHMETIC -4.335712
DIRECT     -5.581806
PYTHON     -5.663837
CSP        -5.731545
```

Thus P1.2 full-S4 successfully stabilizes the statistic, but stabilization does
not guarantee that the statistic represents executor compatibility.

## Complete accounting

- observations: 12/12
- input rows: 864
- score rows / scored code tokens: 3,456 / 3,456
- evaluated tokens: 202,968
- padded tokens: 202,968
- forward calls: 432
- startup: 135,602.304 ms
- controller wall: 426,236.293 ms
- whole study: 561,838.601 ms
- max task wall: 42,159.989 ms
- frozen core audit: unchanged
- report error: null
- energy / FLOPs / money: UNKNOWN

## Scientific interpretation

The progression is now:

```
P1        FAIL  bare verbalizer collapse
P1.1     FAIL  balanced schedules recover signal but score geometry unstable
P1.2 dev PASS  full-S4 statistic robust on opened development tasks
P1.2 val FAIL  robust statistic misroutes 2/4 fresh CSP tasks
```

This is an important distinction. The current failure is **semantic**, not
numerical or permutation instability.

It also exposes a first-principles inefficiency in the current experiment.
These interfaces already carry explicit public executor contracts:

- arithmetic rows expose `expression` + `bindings`
- coding rows expose `requirement` + `examples`
- constraint rows expose `domains` + `constraints`

For such unambiguous typed inputs, spending 24 permutations and 432 forwards
to infer an executor that the public interface contract can determine
deterministically is unnecessary computation.

This observation does **not** rescue the failed validation. It is a
post-failure architecture diagnosis and any replacement architecture requires a
new preregistration and new fresh validation.

## Recommended next architecture pivot

Do not tune code tokens, margins or the old twelve/fresh twelve.

Candidate: **contract-first hierarchical routing**.

```
public problem
    |
    v
deterministic executor-admissibility test
    |-- exactly one typed executor is admissible --> execute it directly
    |                                      (zero neural routing forwards)
    |
    |-- ambiguous / untyped / multiple admissible
                                           --> semantic fallback router
                                               --> cheapest safe executor
                                               --> original verifier
```

The deterministic layer must use executor interface contracts, never hidden
family labels or private references. P1.2 full-S4 can remain an expensive
diagnostic/fallback baseline, not the default typed router.

The current 24 opened tasks may now be used only for development/diagnosis.
Any revised router needs a new fresh validation frozen before new scores. A
future P2 should include a genuinely ambiguous/generic stratum so a trivial
schema dispatch cannot by itself establish the end-to-end NEUMANN claim.

P2 registration, P2 actual admission and Decision 3 remain BLOCKED.
Q1-Q7 remain globally OPEN.
