# NEUMANN 1 | Q3 Cross-Representation Generalization: Active Exact Numeric Function Synthesis
2026-11-08 | Addition to PR #732

## A second independently executable representation constructor

\`NeumannEngine.synthesize_numeric_function_active\` and \`RegistryEngine.synthesize_numeric_function_active\` now support a separate mathematical superfamily from the associative binary-operator module.

The constructor chooses source coordinate queries itself; derives input arity from its declared signature; enumerates rational monomial features in increasing total degree; solves the exact rational linear equations; rejects inconsistent lower degree; generates the selected degree, sparse monomial representation and an executable \`apply(...)\` function; tests a fixed number of additional source-only points before freezing.

This is **classic exact polynomial system identification** applied as an autonomous representation-construction mechanism, not novel mathematical research and not general-purpose program invention. Both maximum polynomial degree and elementary rational operators are supplied by the programmer.

## Local FIRST measured results

Run \`PYTHONPATH=. python research/q3/q3_active_numeric_first.py\`, which emits a JSON first-result artifact. Each formula was evaluated over 30 distinct active-query exploration seeds. Each learned function was checked on 200 previously unseen points per seed, **outside the source coordinate range** (source -30..30, holdout coordinates with absolute value 31..100). The oracle function is not available to the representation builder other than through the callable source query.

| Unrelated numeric problem structure | Active constructions | Exact unseen predictions | Source queries |
|---|---:|---:|---:|
| One-variable cubic | 30/30 | 6,000/6,000 | 540 |
| Two-variable quadratic interaction | 30/30 | 6,000/6,000 | 570 |
| Two-variable cubic | 30/30 | 6,000/6,000 | 660 |
| Three-variable cubic | 30/30 | 6,000/6,000 | 900 |
| Four-variable affine | 30/30 | 6,000/6,000 | 570 |
| Three-variable quartic | 30/30 | 6,000/6,000 | 1,350 |
| **Total** | **180/180** | **36,000/36,000** | **4,590** |

These are **six hand-authored polynomial formula families**, each reused across seeds. The 180 runs are not independently authored tasks or proof of arbitrary natural function generalization. Symbolic exact arithmetic prevents floating-point fitting artifacts but does not prevent overfitting beyond the polynomial prior.

Unit controls cover nonpolynomial sources and float outputs fail-closed; hard budget=3 stops at 3 distinct source calls. Inputs of unexpected arity and non-rationals fail closed on \`apply\`.

## Combined Q3 / Q4 / Q6 interpretation

- Positive: NEUMANN now automatically produces **two distinct executable representation families**: a finite-operation generator-word coordinate system and a sparse rational polynomial basis. It actively acquires necessary facts rather than receiving the complete generating observations as part of the task.
- Important negative: the constructor languages themselves were human designed. The algorithm does not invent an arbitrary new DSL or discover an independent formal proof of unrestricted semantics from data. This is scoped Q3, NOT global Q3.
- Global Q6 remains OPEN: two known mathematical superfamilies do not establish transfer into independent graph, CSP, program-repair, physics, or ARC task constructors.
- Q4 remains OPEN: no equal-accuracy and equal-information comparison with optimal polynomial interpolation, Gröbner-like algebraic synthesis, or classical CEGIS; no full discovery/inference cost comparison with frontier LLMs.
- A synthetic black box can match a polynomial on every sampled point and differ elsewhere. Therefore even 36,000/36,000 withheld results **cannot** prove universal reliability for arbitrary functions.

Highest-value follow-up: **one autonomous mechanism that creates and revises its own term language from independent-author mathematical tasks**, with frozen first-run benchmarks and proof/compute telemetry. Reuse known exact interpolation whenever it is already best; do not run neural search just to make the algorithm seem autonomous.
