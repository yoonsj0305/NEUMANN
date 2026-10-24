# NEUMANN 1 Q3 | Source-inferred differential equation yields an executable NEW named derived operator M(x)

**Status:** ACTUALLY EXECUTED on local CPU in this conversation, 2026-10-24. Development-only known public author Keijzer7/8/9, not a first blind source-family admission and **not a neural model**. Python source-and-grade files are committed here byte-for-byte from actually run local evidence:
- source-only inference Git blob SHA1 `0667a68b6889642c63f977d948377c2a520b4f5f`; binary SHA256 `1ced6f92a8ed1dd82c8b0f642223730787d3f96446467778dfa351945a914804`;
- independent author true-expression grader binary SHA256 `ea5d7d1751fb1eb1f35bea7e9b4966e1182d81f139ed38221ce26ec6fae7597c`.
- The actual **complete reproducible 16-file research archive**, attached to this conversation (not GitHub), ZIP SHA256 `08c42f79a1590c66a11e6aad721d303774d0ef990b5707eaf4091aa9d642843a`, per-file manifest SHA256 `059884149c87a9b8f45f892c00f6c8f7e479f59a5e54959ceea6b17debacbd6e`.

## Research question and algorithm

Prior #550 produced `b**(k*x)` via human primitives `EXP,LOG`. This experiment instead asks whether one can construct a reusable *derived higher-level FUNCTION* by inferring a differential LAW from numeric source, without selecting from a list of complete `asinh` expressions. The program sees 48 source x-y points per task and searches FOUR HUMAN-SUPPLIED ODE candidate families by nonlinear least squares, exact rational coefficient projection (denominator≤128) and held-out source numeric verification. It emits executable symbolic defining equations for a new `M(x)` (a named initial-value problem), not only one finite input-output table.

The previously known author formulas appear only in an external developer grading JSON and *are absent from the inference source module and inference source numeric JSON* (but remain available on the same development computer, so this is NOT independent cryptographic gold isolation). The **strong same-family classical solver** uses exactly the same human-coded differential library, so it will produce the same program.

## ACTUAL public source full-domain mathematical identities

| Public Keijzer original (already exposed to project) | Newly inferred M(x) defining IVP | Independently exact author mathematical identity |
|---|---|---|
| Keijzer-7 `log(x)` | `M'(x)=1/x, M(1)=0` | **PASS** x≥1 |
| Keijzer-8 `sqrt(x)` | `M'(x)=1/(2 sqrt(x)), M(0)=0` | **PASS** x>0 by derivative and x=0 by continuous extension |
| Keijzer-9 `log(x+sqrt(x²+1))` | `M'(x)=1/sqrt(x²+1), M(0)=0` | **PASS** x≥0 |

For each case the independent reviewer (different Python program, not importing inference module) checks `sympy.simplify(diff(author,x)-inferred_RHS)==0` and `sympy.simplify(author(anchor)-source_inferred_initial)==0`. Fundamental theorem of calculus / uniqueness within connected real domain then certifies the **whole analytic author function**, not merely 48 fitted points. Keijzer8 x=0 is a derivative singularity, so uniqueness is on x>0 plus initial continuity; do not state derivative defined at0.

**First negative run explicitly preserved:** first source-only predicted numeric SHA `f68a91fb9985f18aa5999d25877b39a01ff2e58dcc2b743a90605ceab128b8c5`, true whole-domain math grade `98f2e75850dcc17169e01bdd810da7dde24d0b7dd5f2e30c4716e81faefe260d`; **2/3** because Gauss-Legendre numerical integration of x^(-1/2) near boundary x=0 was inaccurate. Development-only remedy derived the exact elementary integral `2*A*(sqrt(x+B)-sqrt(B))` for the inverse-square-root-linear ODE, preserving original 48 x-y, and reran candidate family parameters and mathematical grade. Result V2 **3/3**; source pred SHA `1ca8b8ea0cec5aedb196b2f1589f2ae13a8f0f28df6de6243a23a6ea210baa96`, grade SHA `bc3def49b2ec680b3adb1b8a8ae9cec915a834f62e5edfbd9d12121f2bf1b217`.

**Code-level source/grade separation V3:** Remove entire public-author original expression registry and prepare/grade functions from the source-only module, physically retain exact same source numeric JSON, and execute source inference again. It still yields **3/3**; inference SHA `b5fb8c46686a64e5215e6ecf8eda8304dc54c611dbe97f176dff34f073499114`; separate source-import-independent original verifier grade SHA `b00fd2098a6375cd8532b6f35bac72ed98ecdf5f8ff0304b1150851d1ea67b44`. Same computer, NOT three physically isolated cloud jobs.

**Independent source holdouts and negatives:** **303** additional off-source-grid numeric probe points (101 per Keijzer) have max normalized error `4.3007126425796683e-14`, **5** nonmatching/noisy controls from Neat3 trig product, Neat4 log sum, sine, quintic, perturbation of Keijzer9 have **zero** false exact admissions; audit SHA `c00a6b8485e033c135f4962e28e34aec577e7b385079c822dbd722b811e0e98a`. Restricted prior fixed one-term atom language `x^d, d1..4; log(x+k),sqrt(x+k), k=0,1,2` on SAME 48 x-y yields **2/3**, SHA `78f5dedaf987582d7045f7a1762c5ae958a51e003b480f161e78c12aaad76c52`; it misses Keijzer9. This baseline is NOT the strongest classical GP/ODE solver and DOES NOT have same ODE syntax rights. The scoped uplift is EXPRESSIVITY of named IVP M, not neural algorithm efficacy.

**Provenance:** DSO published benchmark CSV original Git commit `8348d5b08d1eef6170fdbfd222a492ded990ea12`, original blob `229c99495c819dc65f9f7ac304fd8460d6b46d3a`. 48 custom original author-grid x-y per task. This was a public already examined development suite, not official Keijzer test.

## Scientific decision

- `SOURCE_FITTED_NEW_EXECUTABLE_DERIVED_IVP_SYMBOL=SCOPED_PASS`.
- `ORIGINAL_AUTHOR_FULL_DOMAIN_MATHEMATICAL_IDENTITY=DEV_PASS_3_OF_3`.
- `303_EXTRA_POINTS_ZERO_MISMATCH=PASS`, `5_NEGATIVE_CONTROLS_ZERO_WRONG=PASS`.
- `SOURCE_AND_TRUE_FUNCTION_IN_SEPARATE_INFERENCE_AND_GRADE_CODE=PASS` but NOT independent file-system isolation.
- `NOVEL_NEURAL_SELF_CREATED_OPERATOR_PRIMITIVE=NOT_PROVED`, **there is no NN in this study**.
- `STRONG_CLASSICAL_SAME_RIGHTS_EXCLUSIVE_AUTHOR_SOLUTIONS=0`.
- `G1=HOLD`; global `Q3/Q4/Q6/Q7=OPEN`. No 10×/frontier claim.
- Already created [PR #564](https://github.com/yoonsj0305/NEUMANN/pull/564)/[PR #565](https://github.com/yoonsj0305/NEUMANN/pull/565) attempting the **different** PR554 neural Keijzer+Neat12 first external grading. These are execution-only and **must not merge**. They have not yet produced Q3 original grade, so cannot claim first novel NN result.

**Next decisive model experiment:** train the controller to choose whether to `DEFINE_NEW_IVP` and to propose/compose the *differential RHS AST itself* from prior verification and counterexample rewards, and score new independent author problems with full GP/CEGIS same compute rights; do NOT just add hand-authored derivative families to pass more opened public Keijzer examples.
