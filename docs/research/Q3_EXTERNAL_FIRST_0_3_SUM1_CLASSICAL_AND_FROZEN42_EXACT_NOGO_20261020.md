# NEUMANN 1 Q3 | External-source proof and the 42-weight fixed-grammar no-go

**2026-10-20 KST. Two genuinely closed, *limited* results.** Global learned-new-mathematical-structure Q3 and Q1–Q7 remain OPEN.

## 1. First genuinely separate public repository source transfer: no new result admitted

Upstream `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646` is **not** previously used `SaswatPadhi/LoopInvGen`. Three original file names and full Git blobs froze before target contents were opened in commits `25d99aa33f299996d67e393d8b6d7aa62ede2376` and `2d2a6c44424bf5f1e641321b4b748c59ed26a428`.

- Andrew Lustre `lib/Inv_Track/andrew_lustre/DRAGON_1.lus.sl`, Git blob `8490b3e25ff7d462a7405e68e742be1abb35b8f8`;
- XuJie Code2Inv `lib/Inv_Track/xujie_code2inv/1.c.sl`, blob `859bae24a9f26044a40a3c97f1d2e5fc08504f06`;
- SyGuS 2017 `comp/2017/Inv_Track/sum1.sl`, blob `5fd2e4f7841aea6ebab96d30d394819b0d2b17d6`.

The above are **separate benchmark collections**, not independently audited proof of three author identities or leakage-free algorithm source. No claims beyond independently maintained upstream repository.

First attempt [GitHub PR #313](https://github.com/yoonsj0305/NEUMANN/pull/313), [official Actions #39428449359](https://github.com/yoonsj0305/NEUMANN/actions/runs/39428449359) SUCCESS technical (scientific **0/3** learned and **0/3** strong classical). Original full evidence JSON SHA256 `0daf8dc6782e7aca9c594b71a83856b20370d8fb6ebeef69540ae1296addfd7a`, official artifact #12266717807 ZIP SHA256 `ab8bb42ee3dac811e145dc7d25308013cb27d6bd16826a32d7aec4d6793008b4`, CRC PASS.

- Lustre source original contains mixed Bool + Int and nested helper functions: existing source parser returns `UnsupportedOriginal:UNBOUND_ORIGINAL_SYMBOL`, classification **UNSUPPORTED**, not model math failure.
- Code2Inv source original contains branching `or` with many auxiliary states, existing next-state extractor returns `NEXT_COORDINATE_MISSING`, classification **UNSUPPORTED**, not learned mathematical failure.
- `sum1.sl` parses: original native Pre/Trans/Post semantic parity, source exact co-clock offset initial+step independent Z3+cvc5 PASS. But initial source-only invariant misses a conditional exit-bound fact, original Post bad VC **SAT** in both learned and classical. No proof; this is a genuine bounded deficiency of the *shared* source controller, not evidence neural impossibility.

Historical external original first 0/3 **PERMANENT**, no after-the-fact reevaluation score inflation.

## 2. Posthoc extra classical semantics closes external `sum1.sl` published source safety

After the source was opened, [PR #314](https://github.com/yoonsj0305/NEUMANN/pull/314) froze a *generic* source-only guard-disjunction miner, not a human-coded answer: from original Trans literal `clock <= static`, enumerate every source Pre-provable initial constant `u0` for each +1 clock u, propose `(u == u0) OR (u <= static)`, and certify source-only initial validity and induction (not using original Post) with **Z3 and independent official pinned cvc5 1.4.2**. Enumerate and preserve rejected candidates.

- For `sum1.sl`, initial/source-derived co-clock relation `sn=i−1` was already validated in first PR313. The new source-only controller tried two guards, discarded noninductive `i=1 ∨ i<=n` (original induction SAT), and automatically retained the 2-solver certified `sn=0 ∨ sn<=n` (original Pre UNSAT bad, source Trans inductive UNSAT bad). No target original Post informed the selector.
- With this one new classical source fact and the existing original clock relation, the **original published unmodified** Pre→I, I∧Trans→I′, I→Post three bad VCs are each Z3 UNSAT and separately cvc5 1.4.2 UNSAT. This is **authentic external original SAFE, POSTHOC_CLASSICAL_SCOPED_PASS**.
- Importantly, **ABLATE all learned polynomial candidates** and retain only proved classical co-clock relation + guarded frontier: STILL original Z3/cvc5 3VC 3/3. `learned_generates_nontrivial_polynomial=False`. Neural causal contribution to this original safety proof **zero**. The exact classical with same information solves it identically.
- Freeze old guardless source original Post SAT negative control. All original SHA and typed semantic XOR parity reverified and preserved. No changed pretrained weights, no source edits.

Verified [official GitHub Actions #39429524853](https://github.com/yoonsj0305/NEUMANN/actions/runs/39429524853) **SUCCESS**, raw source JSON SHA256 `4c830335068ede794c9557f3a8ea04df47dc17d892c9e334432c01be2852f8b2`, original artifact #12266999440 ZIP SHA256 `c6876bb2efa8478aeb89539c060c5cb88d12e27b7aaa5ca8b56d88362128d4d3`, CRC PASS.

## 3. Exact universal mathematical ceiling of the current fixed trained 42-weight model: CLOSED NO-GO

This is the decisive scope closure, unlike repeatedly test-driving new programs in a predeclared polynomial grammar. The authentic *first* trained operator [PR #310](https://github.com/yoonsj0305/NEUMANN/pull/310) weights SHA256 `563c6be70fade6db755425a5756b6fdd89503ada5727bf31f49ad195ec041a78`, original synthetic-trained receipt JSON SHA256 `993e7ce6ce116bedce68efa66ada4a42ea1913629730ec1b914bdfc60316f513`. The weights are an exact 6×7 integer matrix divided by **5040**, taking six coefficients of ΔF(t), degree≤5, to seven coefficients of F(t), degree≤6.

Define classical exact difference matrix `B` (6×6) by `B[r,j]=binomial(j+1,r)` for 0≤r≤j, zero otherwise. Let `L` be the 6×6 submatrix of nonconstant learned polynomial output coefficients. Then using **exact rational arithmetic**, not numeric tolerances:

```
B * L = I_6  (exact SymPy equality, all rational entries)
det(B) = 720 != 0
F(0) = 0
Delta(F)(t) == input_polynomial(t) identically for all rational
coefficients of polynomial degree <=5
```

Since Δ on polynomials of degree≤6 with zero constant is invertible (a periodic polynomial over characteristic 0 must be constant), the antidifference operator is UNIQUE. Therefore this specific first frozen trained 42-weight operator is mathematically identical to complete classical exact SymPy polynomial antidifference on **ALL** rational coefficient inputs within its grammar, not just 64 sampled synthetic holdouts or six source examples. Six independent basis `t^0..t^5` exactly reproduce symbolic classical summation; mutation of one original trained integer weight violates the matrix identity as negative control.

**Consequence:** within this fixed degree≤5 polynomial delta and zero-initial degree≤6 output function family, current learned map has **ZERO possible strict function/accuracy expressivity advantage** over same-input exact classical antidifference. It did not invent a new operator; it learned one preexisting exact finite-dimensional classical linear transformation. This says NOTHING definitive about runtime (compiled matrix inference may be cheaper), general ML architecture with richer structures, safe generalization to other input grammar, frontier performance or unsolved global Q3. It eliminates wasting more training/proofs trying to show unique mathematical structure in THIS fixed form.

Authenticated [PR #315](https://github.com/yoonsj0305/NEUMANN/pull/315) [independent actual GitHub CI #39430292389](https://github.com/yoonsj0305/NEUMANN/actions/runs/39430292389) **SUCCESS**. Original JSON exact SHA256 `640c0b33d086f023fb62f2c8f843b7aba99e5f8e5022c66d7c2d0b2ee8f1f8db`, artifact #12266724671 ZIP SHA256 `c66ebc105de8e613c53ca274a577c1813b6ab86cec4b33046b57115cf7100e51`, CRC PASS.

## Truthful research ledger

- `Q3_EXTERNAL_CROSS_CORPUS_FIRST_FROZEN_42W=0/3` fixed.
- `Q3_SUM1_EXTERNAL_PUBLISHED_SAFETY_POSTHOC_CLASSICAL=DUAL_ORIGINAL_3VC_PASS`.
- `Q3_SUM1_NEURAL_POLYNOMIAL_CAUSAL_ABLATION=NO_NEURAL_CONTRIBUTION`.
- **`Q3_FROZEN_42W_UNIQUE_NEW_MATH_OPERATOR_WITHIN_PREDECLARED_POLYNOMIAL_GRAMMAR=NO_GO_CLOSED_BY_EXACT_THEOREM`.**
- `Q3_LEARNED_NEW_GRAMMAR_BEYOND_FIXED_DEGREE_5=NOT_PROVEN`.
- `Q3_FRONTIER_PERFORMANCE_10X_ALL_IN=NOT_PROVEN`.
- **`GLOBAL_Q3=OPEN`, `GLOBAL_Q1_Q7=OPEN`.**

**Next concrete project decision:** make this exact 42-weight operator part of a deterministic classical / lookup backend if fast, but **STOP calling its training evidence of operator invention**. If pursuing Q3, study a model that *constructs a new operator/grammar outside predefined polynomial integration*, with genuinely safely verified external heldout families, equal-information strong classical controls, no target leakage, and training+verification total cost. Otherwise use it as a cost-efficient component and progress other Q1–Q7.
