# P1 first real non-generative controller result — retained FAIL

Date: 2026-10-03

## Frozen result

- Frozen head: `81d004cf91251ef523e734756548c6cd694ac54e`
- Model: `google/gemma-4-E2B-it` at revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16, Tesla T4, frozen weights
- 12/12 opened public tasks complete
- 144 scoring rows, 72 forward calls
- generated calls: 0
- tool calls: 0
- accounting complete: true
- core audit unchanged: true
- replay integrity valid: true

Archive: `NEUMANN_P1_FIRST_EVIDENCE.zip`
- bytes: 22,762
- SHA-256: `38d489dde092e86eea6a9f2276bc15fcfa574c463e18ececf161037dfd95cb38`

Frozen verdict:

```
P1 = FAIL
reason = DEGENERATE_ROUTE_SELECTION
P2 admitted = false
Decision 3 admitted = false
```

Winner counts are ARITHMETIC 12, DIRECT 0, CSP 0, PYTHON 0. This is a valid
first result and must not be rescued by changing labels, thresholds or rerunning
the same P1.

## Complete accounting

- evaluated tokens: 13,464
- padded tokens: 13,680
- scored label tokens: 252
- whole study: 197,380.417596 ms
- startup/load: 141,126.102264 ms
- centered score range: 5.696547150611877 nats
- batch/unbatched delta: 0 on every task
- normal/reversed-candidate-order delta: 0 on every task

The observed failure is therefore not runtime instability, order instability,
generation, tool execution, incomplete accounting, or identity drift. The
teacher-forced scoring path ran cleanly and collapsed to one verbalizer.

## Raw canonical scores

| task | DIRECT | ARITHMETIC | CSP | PYTHON |
|---|---:|---:|---:|---:|
| am_math_01 | -22.030994 | -8.567444 | -24.030994 | -20.280994 |
| am_math_02 | -20.633591 | -8.377771 | -21.946091 | -18.258591 |
| am_math_03 | -25.204988 | -7.567803 | -23.204988 | -20.329988 |
| am_math_04 | -21.418282 | -7.273219 | -21.918282 | -17.230782 |
| am_code_01 | -19.187164 | -5.025303 | -17.390289 | -12.312164 |
| am_code_02 | -18.685741 | -4.578770 | -17.623241 | -11.487499 |
| am_code_03 | -18.100353 | -4.643928 | -17.600353 | -11.397228 |
| am_code_04 | -19.725861 | -4.996583 | -19.132111 | -12.936798 |
| am_plan_01 | -16.502176 | -6.199816 | -11.627177 | -13.752177 |
| am_plan_02 | -17.591627 | -6.725527 | -13.841628 | -14.716628 |
| am_plan_03 | -18.869074 | -5.740227 | -13.837823 | -12.681573 |
| am_plan_04 | -21.175879 | -7.272598 | -15.488379 | -16.738379 |

## Post-result diagnosis

The candidate verbalizers are not tokenization matched:

- DIRECT: one token, 35357
- ARITHMETIC: four tokens, 1425 / 13655 / 54849 / 2011
- CSP: one token, 210396
- PYTHON: one token, 185267

P1 used mean per-token log likelihood. That removes a simple summed-length
penalty but does not remove verbalizer/tokenization prior. The route prompt also
does not provide an explicit legend binding each candidate string to an executor
contract.

There is nevertheless context-sensitive movement below the dominant offset:
math has ARITHMETIC first on 4/4, code has PYTHON second on 4/4, and planning
has CSP second on 3/4. Mean PYTHON-minus-ARITHMETIC changes from about -11.08
nats on math to -7.22 on code; mean CSP-minus-ARITHMETIC changes from about
-14.83 on math to -7.21 on planning.

As an explicitly post-hoc diagnostic only, subtracting each route's mean across
these same twelve tasks yields PYTHON on all four coding tasks, CSP on all four
planning tasks, and a DIRECT/ARITHMETIC 2/2 split on math. This is not
confirmatory evidence, not a P1 rescue, and not grounds to admit P2.

## Next architecture candidate

Do not merely rename the bare labels. The next opened-development controller
should remove arbitrary verbalizer identity from the routing statistic.

A principled candidate is permutation-marginalized coded choice:

1. include an explicit semantic legend for the four executor contracts;
2. use four neutral single-token codes;
3. rotate route-to-code mapping through a balanced deterministic permutation set;
4. teacher-force only the code token, with no generation;
5. aggregate each route after it has occupied every code equally.

For balanced permutations π_k:

```
S(route | x) = mean_k log P(code_{π_k(route)} | x, legend_{π_k})
```

A fixed additive code-token prior then cancels by construction rather than being
estimated from task labels. Any such change is a new architecture version and
requires a new preregistered opened-development diagnostic, followed by fresh
opened validation before P2. P2 and Decision 3 remain blocked.
