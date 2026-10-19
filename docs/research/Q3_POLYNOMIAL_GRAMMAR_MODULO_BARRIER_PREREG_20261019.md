# Q3 mathematical structural grammar barrier and finite synthetic modular transfer prereg

Date 2026-10-19. **The sole high-value next falsifier after PR #297**. Our source-trained polynomial models have no unique proof advantage over exact same-monomial classical solvers. We must stop iterating on this representation and prove an expressivity boundary, then exercise a typed escape-hatch without falsely calling that learned invention.

## Mathematical claim frozen before machine checks

For every integer `k>=2` and finite nonnegative degree `d`, there is **no polynomial P with rational coefficients** satisfying `P(n)= n mod k` at *all* nonnegative integers `n`. **Proof:** `P(0)=P(k)=P(2k)=...=0` implies `P` has infinitely many distinct roots and is identically zero; but `P(1)=1`. A bounded degree `d` already has a finite contradiction witness from `n=0,k,...,d*k,1`. The evaluation Vandermonde matrix has determinant `k^(d(d+1)/2) * product_{j=1}^d j!`, nonzero for k>=2. This holds for any finite monomial grammar degree and is stronger than PR #297's linear-algebra instance.

All bounded original solver experiments must preserve the exact statement: `k in [2,3,4,5], d in [0,...,5]`, 24 real-linear existential coefficient SAT checks, each with Z3 AND independent cvc5 1.4.2. Exactly `UNSAT` from both = PASS for scoped bounded machine checks; mathematical argument above independently establishes the unbounded theorem. Positive control: finite interpolation CAN agree with finite examples (not evidence of universal identity), and fails at next unseen point.

## FROZEN posthoc synthetic transfer diagnostic (not a new author-family original G1)

Construct a small **author-created** counter/program, with public semantics: `Pre: i=0,r=0`; `Trans: i'=i+1, r'=if r=k-1 then 0 else r+1`; `Post: r=i mod k`. k is a positive fixed program parameter >1, but not a secret original answer-key.

The decoder is explicitly supplied a **typed `mod` primitive**, and its trainable neural part only learns to estimate integer k from 48 source-reachable residue observations. Train k=2..6 (5 programs), first 48 successive source states. **The source-only period statistic `max observed remainder` is computed classically**, feed to *two trainable model coefficients* `alpha, beta` with SciPy analytic gradient L-BFGS-B and real labels k. Test k=7,8,9,11 **before** verifying any heldout solver output; model outputs `r=i mod round(alpha*max(r)+beta)`, plus mandatory `i>=0,0<=r<k` helper. This expression is outside all fixed polynomial-output grammars but its **operator syntax is supplied, not model-invented**. Original synthetic counter native Z3 and cvc5 full 3VC for each k, with negative helper-only Post SAT.

**STRONG CLARIFYING BASELINE:** exact classical `max(r)+1` receives the same information, emits the SAME expression, does not need any learned weights, expected cheaper. The neural candidate is therefore NOT unique over classical and cannot close Q3 global. Synthetic transfer across k values is not across truly independent external original author families. Stop this approach if classical dominates, retain as executable module/grammar requirement only.

## Frozen interpretation

`Q3_FINITE_POLYNOMIAL_REMAINDER_EXPRESSIVITY=THEOREM_PASS` can be closed if math, bounded solver and mutation controls agree. `Q3_SYNTHETIC_NEURAL_MOD_COMPOSITION=SCOPED_PASS` only when neural trained and original synthetic counters' 3VCs pass on all heldout. Q3 model invents an **operator beyond predeclared grammar** = FALSE. GLOBAL Q1-Q7 OPEN, Q7 BLOCKED, no frontier claims, no 10x full-cost claim. No use of paid AI or GPU. Prior real-original and first blind FAIL records remain intact.

Scientific related work: DreamCoder (2021), LILO (ICLR 2024) already construct higher-level neural-symbolic libraries; this study is NOT a new architecture novelty claim.