# NEUMANN 1 · Q3 G1 | Learned minimal LATENT MEMORY STATE and all-natural-number author proofs

**Date:** 2026-10-23 KST. [PR #555](https://github.com/yoonsj0305/NEUMANN/pull/555). Exact first public-source three-stage [GitHub Actions #39957412796](https://github.com/yoonsj0305/NEUMANN/actions/runs/39957412796): **3/3 SUCCESS** (source preparation, actual CPU ML source-only inference, independent real author published recursion grader). Subsequent [FOUR FIRST ARTIFACT SHA-LOCKED independent mathematical audit #39958128397](https://github.com/yoonsj0305/NEUMANN/actions/runs/39958128397): **SUCCESS**.

## Core Q3 hypothesis

Can a learned source-driven controller select **how many internal state variables to invent** for an equation, without a fixed universal state dimension, and construct a **NEW typed reusable recursive state machine** which is proved EXACTLY equivalent to independently authored original laws for ALL natural-number inputs, not merely interpolation at observed data?

We train a small actual sklearn MLPClassifier on **288 OTHER synthetic integer sequence source-only cases**, 72 each source-verified minimal order r1..4. Labels arise from exact rational linear-algebra SOURCE RECURRENCE VERIFICATION of 16 observations, NOT any of the six external OEIS original author's recurrence coefficients. The neural features include *source Hankel singular value signatures*, making the order inference explicitly grounded in existing linear algebra and **not an unassisted discovery of Hankel rank**. The human-written program compiler takes the network's TOP1 predicted order r, recovers full exact rational recurrence coefficients and first r seeds from the 16 integer source terms, then constructs a new independently named executable program:

`DEFINE_STATE_VECTOR Z_n=(a_n,a_(n−1),…,a_(n−r+1))`

`DEFINE_COMPANION_MATRIX T_r=[exact source-inferred coefficients; subdiagonal unit shifts]`

`DEFINE_RECURSIVE_STEP Z_(n+1)=T_r·Z_n`, `EMIT a_n=Z_n[0]`.

This representation implements dynamic STATE MEMORY DIMENSION, rather than a static one- or two-term complete pre-coded output expression. However all allowed state rules, exact solver, capacity ceiling r≤4, and mathematical primitives are HUMAN GIVEN. The ML model learns only the choice of order from source numeric descriptors, not an entirely new graph-edit operator or novel mathematical semantic primitive.

## FIRST original OEIS source and exact independent evidence

Six classic PUBLIC original integer sequences from [OEIS](https://oeis.org/): `A000045 Fibonacci`, `A000032 Lucas`, `A000129 Pell`, `A001045 Jacobsthal`, `A000073 Tribonacci`, `A000078 Tetranacci`. Full original recurrence and initial-condition registry is declared in `research/q3/oeis_state_six.py` and was used exclusively by FIRST source generator and independent full-author grader, not imported/read by the inference Python source. An artifact carrying only first16 integer source observations without any author recurrence was given to inference. **Disclosure:** GitHub Actions repo checkout itself contains the original registry code, so this is runtime INPUT/IMPORT isolation, not cryptographic source secrecy; these are famous public source authors and no official private competition. It must never be sold as a truly private unseen benchmark.

First immutable artifacts from original Action #39957412796:

- Original source numeric first16 six-case **SHA256 `eb9ea1ab438d3be34c6560ffc9de8a654f96dfb818c2afb06241462bb3503284`**.
- Independently published true author recurrence plus withheld exact n16..120 each **SHA256 `4a964c4d8e5c75363012280d1ebfa8284026e34bca6e0c6eb17b303bb89b0d15`**.
- Actual MLP source-only action choice, constructed companion matrices, all five classical controls, sealed before original grader **SHA256 `2220789a6de37123303752ccfffe91acfaa3ed3f70fb1e468528a409d44d1d39`**.
- Independent exact full published author recurrence+all-integer induction result **SHA256 `77daf49d2bc90e45479653231e25197c1eb30d7c585dfbf699a774a3b729afbd`**.

Independent re-audit #39958128397 asserted all FOUR first SHAs before inspecting any exact author formula, recomputed nonzero source Hankel determinants/linear recurrence all-n proof, and tested out-of-class factorial source negative control. Audit report SHA256 **`1b552b1a1a70946c91b5f29996a16bd4a089f9699c6cadc29b0447497726a9b5`**.

## First ORIGINAL authors: learned latent dimension and minimum-state theorem

| Published original OEIS identifier | Actual first learned state order | Nonzero exact first-source Hankel determinant | Exact heldout original n16..120 | ALL natural n |
|---|---:|---:|---:|---|
| A000045 Fibonacci | **2** | −1 | 105/105 | PROVED |
| A000032 Lucas | **2** | 5 | 105/105 | PROVED |
| A000129 Pell | **2** | −1 | 105/105 | PROVED |
| A001045 Jacobsthal | **2** | −1 | 105/105 | PROVED |
| A000073 Tribonacci | **3** | −1 | 105/105 | PROVED |
| A000078 Tetranacci | **4** | 1 | 105/105 | PROVED |

Mathematical completeness: initial seeds first r are equal, exact coefficient row of the generated companion matrix T is equal to the published actual author recurrence, so by induction every emitted sequence term agrees for **all n≥0**. Independent checksum verifies all 630 exact future integer values across original six as additional checks. Minimal order lower bound is **conditional on homogeneous constant-coefficient linear recurrences**: a recurrence of order q<r would force rank(H_r)≤q<r for the r×r Hankel source matrix, yet det(H_r)≠0. Therefore no smaller such memory state dimension can represent the exact sequence across all n. Known classical Hankel linear algebra and induction, **not a new theorem**. Sixteen observations alone still do not prove the unrestricted original law uniquely; the independent original published full author definition is essential.

## Honest original controls and all-in computational boundary

| Same six original sources | Independently all-n author programs exactly proved | source verification calls | source-model test CPU |
|---|---:|---:|---:|
| **D ACTUAL learned MLP picks one latent state dimension r** | **6/6** | **6** | **0.020788211 s** |
| C random one dimension | 3/6 | 6 | 0.011845884 s |
| C fixed r2 | 4/6 | 6 | 0.011592337 s |
| C fixed r4 | 1/6 | 6 | 0.008949117 s |
| **A classical exhaustive MINIMAL rank r1..4, full same mathematics** | **6/6** | **15** | **0.025059532 s** |

Model source-only training: 288 exact source observations, training source-verifier+MLP **1.991478165 CPU seconds**. Thus D **known training+test = ~2.01227 s**, strong A test-only **0.02506 s**. D reduces candidate r checks from15 to6 (2.5× fewer) but does **NOT** win total CPU, energy, evaluation amortization, or 10× frontier. The network's rank-informative features capture precisely information that a strong classical minimal-recurrence algorithm extracts in almost no time. A same-rights complete r≤4 always discovers all D valid source answers, so D-only exact source originals above A=ZERO.

A deliberately unsupported **factorial integer source n0..15 was not accepted by any r1..4** under exact rational verification: a negative-control PASS, not a proof of all possible false-positive absence. New public OEIS originals are not secretly withheld private tasks, and training source is **synthetically constructed**, NOT another unrelated natural-corpus learned distribution.

## Scoped closure and next truly decisive task

**SCOPED PASS**: `ACTUAL_NEURAL_CHOOSES_MEMORY_STATE_DIMENSION=PASS`; `D_DYNAMIC_NAMED_COMPANION_STATE_PROGRAM_SOURCE_PROVEN=6_OF_6`; `ALL_PUBLISHED_AUTHOR_LAWS_IDENTICAL_FOR_ALL_N_BY_INDUCTION=6_OF_6`; `TRUE_MINIMAL_STATE_DIMENSION_WITHIN_LINEAR_RECURRENCE_FAMILY=6_OF_6`; `630_FIRST_UNUSED_EXACT_FUTURE_INTEGER_VALUES=PASS`; `FACTORIAL_NEGATIVE_SOURCE_NOT_ADMITTED=PASS`. Compare this to prior [PR #553 Keijzer-6 learned first FOLD_SUM exact all-n](https://github.com/yoonsj0305/NEUMANN/pull/553) and [PR #552 Livermore graph expression expansion 4/8 vs old 0/8](https://github.com/yoonsj0305/NEUMANN/pull/552).

**Not proven:** the neural model invented the linear-recurrence semantics or the Hankel concept without human assistance, or that it learns reusable macro graph syntax beyond the predefined class r≤4; learner-only correct author formulas vs classical exhaustive =0; robust independent source family or frontier parity with GPT-level general-purpose tasks; all-in 10×. **Global G1=HOLD, Q3=OPEN, Q4=OPEN, Q6 broad author transfer=OPEN, Q7 frontier=OPEN.**

Only valuable next test should bridge classes **without preselecting a linear recurrence schema**: learned variable-length `DEFINE/COMPOSE/REUSE/CONDITIONAL/REWRITE` operator construction that can independently *choose between ordinary analytic formulas, dynamic polynomial/trigonometric AST, first-order nonlinear recurrence, constant-coefficient state machine, and nonconstant difference-fold*, then win external sources under equal complete computing/oracle allowance against classical dynamic GP/CEGIS/PySR. Merely adding more public Fibonacci variants or rerunning identical synthetic classes has low information value.
