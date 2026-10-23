# NEUMANN 1 P2 | Same FROZEN neural structural action + source-verifier repair, four independent OEIS originals

**Date:** 2026-10-23 KST. [PR #557](https://github.com/yoonsj0305/NEUMANN/pull/557). [First original 3-stage independent mathematical proof #39959183874](https://github.com/yoonsj0305/NEUMANN/actions/runs/39959183874) 3/3 **SUCCESS**. [Separate first-receipt SHA-locked polynomial-step impossibility proof #39959831944](https://github.com/yoonsj0305/NEUMANN/actions/runs/39959831944) **SUCCESS**. Real public ORIGINAL source author formulas from OEIS: [A007406/A007407](https://oeis.org/A007406), [A007408/A007409](https://oeis.org/A007408), [A075135](https://oeis.org/A075135) and [A025550/A025547](https://oeis.org/A025550).

## Mechanism actually tested

FIRST [PR #556 Keijzer author source experiment](https://github.com/yoonsj0305/NEUMANN/pull/556) showed generic recurrence program invention based on observed exact rational differences, but trained small MLP did NOT select the necessary `DEFINE_RECURRENCE` in Keijzer6. It chose OLD_CLOSED_FORM, scored 2/4 versus A full 3/4. Rather than retrain the MLP on this exposed test, P2 freezes EXACT SAME model joblib artifact from its first pre-original training job in [Actions #39957688283](https://github.com/yoonsj0305/NEUMANN/actions/runs/39957688283), byte SHA256 `de625e81f68418d2613983c20011901f887415e76a7b82ef4ef9fe2bb26874e5`. No new NN weights/architecture/hyperparameter changes or use of new OEIS target original functions before first original source predictions. A **HUMAN-WRITTEN GENERIC SOURCE-VERIFIER COUNTEREXAMPLE RETRY** policy now executes neural's FIRST action; if its full source measurement verifier rejects any program, it executes the alternate graph STRUCTURE action. All source oracle calls and revisions are recorded. This is real executable structure correction, but the retry rule itself is not neural-invented/learned.

Test population four externally published OEIS rational-valued FUNCTION sequences, each generating original 48 consecutive positive-integer exact rational observations with full target SUM expression withheld from inference artifact. These are deliberately POSITIVE rational recurrence family cases, not random OEIS benchmark nor independent private challenge. Competitors share same exact y rational precision, identical human-provided recurrence DEFINE executor and old analytic atom library. Numbers must not be treated as global out-of-distribution success probabilities.

FIRST original source SHA256 `9286c3109827a250b276fe1dde2e4d7776e50059f24b4675f19f8d18dad445a0`; first true publisher expression artifact SHA256 `44c74c3ed6df0c2bbbae3589b1cb263073c210848ea23c8f58855ababddeceef`; first sealed BEFORE gold model/source candidates SHA256 `e1988151809eb01c272b258aebd18320ff54da76c04e9905ac0034a07d51bbc2`; full original independent exact-infinite-induction grade SHA256 `9af815d126626fdf8d680c7bdb314123ecc5f3b5b642466e03cbfdeccc147b5e`. Strict after-grade source/gold/pred/grade SHA immutability checked by CI; no retuning same four original grades.

## Whole original mathematically-certified FULL positive-integer domain

| Published original authored function ratio | Program automatically created from SOURCE measurements without exact author formula | Full original induction |
|---|---|---|
| OEIS A007406/A007407: `SUM_{k=1}^n 1/k²` | `M(1)=1; M(n+1)=M(n)+1/(n+1)²` | PASS all n>=1 |
| OEIS A007408/A007409: `SUM_{k=1}^n 1/k³` | `M(1)=1; M(n+1)=M(n)+1/(n+1)³` | PASS all n>=1 |
| OEIS A075135 generalized `SUM_{k=1}^n 1/(3k-2)` | `M(1)=1; M(n+1)=M(n)+1/(3n+1)` | PASS all n>=1 |
| OEIS A025550/A025547 `SUM_{k=1}^n 1/(2k-1)` | `M(1)=1; M(n+1)=M(n)+1/(2n+1)` | PASS all n>=1 |

Both initial and successor identities checked against independent published original finite sum by a **GENERIC finite-sum induction theorem** in the independent third job, not just source numerical interpolation. FIRST **4/4** whole published author functional identities verified from newly constructed M. The named `M` and exact rational DELTA macro have not been predeclared as `harmonic_2`, `harmonic_3`, `odd_harmonic`, etc. BUT the ability to define `M(n+1)=M(n)+f(n)`, the finite rational first-difference interpolation grammar and the mathematical induction checker are human implemented, and original published family is intentionally recurrence-compatible.

| Same real published four OEIS original mathematical entire sequences | whole-domain exact | source only verifier calls | source only process CPU |
|---|---:|---:|---:|
| D FIRST frozen pretrained MLP decides ONE graph action | **2/4** | 31 | 0.07619s |
| D prior frozen MLP then human-coded source-verifier STRUCTURE REPAIR | **4/4** | 35 | 0.04021s |
| C old pre-existing finite classical unary closed grammar only | **0/4** | 40 | 0.02793s |
| C generic recurrence compiler untrained | **4/4** | 15 | 0.02040s |
| A same semantic rights all two actions classical | **4/4** | 55 | 0.04421s |

**Actual verified structure correction +2 original author functions** over unchanged prior neural policy, source failures did trigger a second action on A075135 and A025550, while prior fixed NN selected recurrence correctly for A007406 and A007408. Same-rights classical C RECURSE is superior in verifier calls/cost (4/4 with 15 vs 35); **NO neural-exclusive full author solutions and NO end-to-end training+eval advantage**. Individual CPU times include CI noise and cannot support high-confidence 10×.

## Extra SHA-locked mathematically strict representation necessity for ALL four new macros

[Strict postgrade original source/gold/first-predictions/first-grade SHA proof #39959831944](https://github.com/yoonsj0305/NEUMANN/actions/runs/39959831944) PASS, certificate SHA256 `0818d44368d3101d83e495abee66880c9cc5e16f0e5b8b8f82be013f85c063b0`. All four first source-generated rational recurrence increments reduce to nonpolynomial rational functions in integer n: denominator polynomial degrees respectively **2,3,1,1** with coprime numerator 1. No arbitrary polynomial increment `P(n)` of ANY DEGREE can agree at every positive integer: otherwise `q(n)P(n)=1` for infinitely many integer n, hence the identity holds as a polynomial, contradiction since q has degree>0. Scope: this excludes a polynomial first-difference update in the specified representation language, **not** every possible nonrecursive elementary-special-function expression (e.g. polygamma), nor does it prove that numerical observations uniquely determine an unrestricted original law. Elementary known maths, zero new mathematical theorem priority.

## Research contract after this first result

`NEW_SOURCE_DEFINED_NONHUMAN_REGISTERED_RECURSIVE_OPERATOR_M=SCOPED_PASS` (specific operator parameters auto-source-derived; general recursion kernel supplied by human).
`FOUR_NEW_OEIS_AUTHOR_ENTIRE_FUNCTIONS_GENERATED_AND_INDUCTIVELY_VERIFIED=SCOPED_PASS`.
`VERIFIER_BASED_STRUCTURAL_REPAIR_ADDS_TWO_TRUE_AUTHOR_SOLUTIONS_W_SAME_FROZEN_NN=SCOPED_PASS` (retry programmed by human).
`FOUR_NONPOLYNOMIAL_RATIONAL_DELTA_MINIMALITY=ELEMENTARY_MATH_PROVED`.
`NEURAL_INVENTS_GENERIC_RECURSION_KERNEL=NO`.
`LEARNER_EXCLUSIVE_VS_CLASSICAL_SAME_RIGHTS=ZERO`.
`NEURAL_POLICY_BEATS_SIMPLE_CLASSICAL=NO`.
`GLOBAL_Q3=OPEN`, `G1=HOLD`, `Q4_TOTAL10X=OPEN`, `Q6_STRONG_NEW_AUTHOR_GENERALIZATION=OPEN`, `Q7_FRONTIER=OPEN`.

**Next admissible decisive test, not another cherry-picked harmonic family:** freeze complete learner-controlled `DEFINE/REUSE/REWRITE` recursive program grammar, pre-register a randomized mixed external author family including NEGATIVE cases and more varied recurrence steps, compare real learned search to strong same-rights CEGIS/classical, and require a D-only solution or objectively matched cost improvement. Reusing positive-only OEIS examples or manually rerunning the same source cannot close G1.
