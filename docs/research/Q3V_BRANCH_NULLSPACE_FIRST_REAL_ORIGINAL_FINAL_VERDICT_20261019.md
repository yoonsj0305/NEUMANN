# NEUMANN 1 · Q3U → Q3V exact source-transition relation discovery, final first-run verdict

**Date:** 2026-10-19 KST. **Verdict:** `Q3V_BRANCH_SHARED_CLASSICAL_RELATIONAL_STRUCTURE_VERIFIED / NEW_NONTRIVIAL_ORIGINAL_PROOF_CASES_2 / NEURAL_Q3_Q4_Q7_UNPROVEN`.

## First-run provenance and frozen protocol

- Exact external genuine original `SaswatPadhi/LoopInvGen` commit `6ac90265b11431c9477dfbd33e3e3380234c0499`.
- Q3U first source-only original study **[Actions #39175477988](https://github.com/yoonsj0305/NEUMANN/actions/runs/39175477988)**, immutable artifact **12153832517**, JSON SHA256 **`3f4c1fa87ea3847c53fdbedd57d50aec671fa32877b74c173d1a8a691172db4f`**, original 10 program cohort. Single explicit-transition exact affine nullspace discovered `fib_01.sl` relation automatically and proved full original safety; 9 previously unsupported by that narrow extractor. Strong classical direct SPACER 8/10 (single-run timeout/variation).
- Q3V preregistration BEFORE new execution: `docs/research/Q3V_BRANCH_COMMON_NULLSPACE_PREREG_20261019.md`, commit `6bbb52b365f5133b42b03aa12a63339e96897cdf`. It explicitly identifies this cohort as **already opened development source**, not blind test or cross-origin generalization. One frozen first execution **[Actions #39175953888](https://github.com/yoonsj0305/NEUMANN/actions/runs/39175953888)** **SUCCESS**, immutable artifact **12154287891**, raw JSON SHA256 **`0e8589cb32b797f5a3865e1186da0190cc27c3706d209b14bd5a554172326842`**.
- First original SHA sets of 10 unique source Git blobs in Q3U and Q3V match exactly. Every individual source's original Pre, Trans, Post parsed via two different parsing paths (strict custom mixed typed and Z3 native SMT-LIB), *symbolic XOR original semantics UNSAT* for each fully proved source. Both mathematical theorem checks use **the same Z3 solver**, not independent solver implementations. All original safety VCs remain source unchanged.
- Mathematical generator: enumerate *all* guard branches using bounded exact DNF; each branch has its OWN uniquely explicit integer-affine `x′ = A_j x + b_j`; no branch omitted, no nonlinear/cross-next silent approximations. Compute exact intersection of left-nullspaces `(A_j−I)ᵀ c=0` and `b_jᵀ c=0` to derive conserved primitive integer coefficients, plus all-branch reset kernels `A_jᵀ c=0` and `(b_j−b_0)ᵀ c=0`. No hard-coded FiB coefficients or target solutions. Each candidate independently checked against original `Pre⇒R` and `R∧Trans⇒R′` via UNSAT negations, and combined `I=Post∧∧R` original **all 3 source VCs**. Pre SAT + ¬Post SAT required. Source-only `Post` alone is a deliberately strong no-learned control, with direct source-only native SPACER as specialist.
- Synthetic *branched* adversarial original control automatically computed primitive `[3,0,-1,-1]` for `3i−a−b=0` over **three** source branches and full certified `Post∧R` (Post alone does NOT prove original inductive safety). Deliberately incorrect equation and mutation of just one branch INVALIDATE original full VCs. All original control obligations PASS. Synthetic tasks **are not counted among authentic successes**.

## Actual complete first ten original source results

| Original source | Exact branch matrix extraction | Derived original-certified relation | Complete original safety via Post and relations | Is it beyond Post-alone? |
|--|--:|--|--|--|
| `2017.ASE_FiB/fib_01.sl` | 1 branch | `x−y=0`, source reset | **PASS** | **YES**; already proven in Q3U |
| `2017.ASE_FiB/fib_04.sl` | 2 branches | none | **PASS** | NO, Post alone inductive |
| `2017.ASE_FiB/fib_05_x.sl` | unsupported next-on-RHS dependency | none | ABSTAIN | N/A |
| `2017.ASE_FiB/fib_07.sl` | 3 branches | **`3i−a−b=0`**, all-branch conservation | **PASS** | **YES: NEW beyond Q3U** |
| `2017.ASE_FiB/fib_08.sl` | 4 branches | none | no complete original certificate | NO |
| `2017.ASE_FiB/fib_09s.sl` | 9 branches | none | **PASS** | NO, Post alone inductive |
| `2017.ASE_FiB/fib_10.sl` | 4 branches | none | no complete original certificate | NO |
| `2017.ASE_FiB/fib_11.sl` | 2 branches | **`2i−j=0`**, all-branch conservation | **PASS** | **YES: NEW beyond Q3U** |
| `2016.SyGuS-Comp/array.sl` | unsupported next-on-RHS dependency | none | ABSTAIN | N/A |
| `others/inria-00615623_4.sl` | missing explicit full update per branch | none | ABSTAIN | N/A |

**Scored source cohort:** 10 original SOURCE FILES across 3 source FAMILY directories, **7/10** authentic source transitions represented as complete finite affine branches, **3** original-certified new coefficient equations across 3 authentic files in the SAME upstream FiB family, **5/10** total full original safety certificates via typed new relation system, **3/10** where Post-alone is NOT inductive. Exactly **2** new nontrivial *original source file certificates beyond Q3U's prior one*. Do not inflate counts into 3 independent scientific source families. All relations and safety verified with unmodified original negated VCs **UNSAT**, no unsupported source treated unsafe, and no formulas borrowed as gold published invariant answers.
**Strong direct source-only SPACER baseline 9/10** in this Q3V execution (it had 8/10 in independent earlier Q3U run; environment/order/timeout variability is not a Q3V superiority). Thus source specialist still outperforms mathematically structured nullspace on **original problem coverage**, and an efficiency 10x comparison at equal success is NOT meaningful here.

## Exact methodological boundary

- **What has now become proven**: classical source-transition **relational coefficient discovery without manually assigning coefficients**, including handling actual conditional branches, can produce original-source-certified nontrivial inductive safety proofs for authentic `fib_07.sl` and `fib_11.sl`. This is a concrete mathematical structure recovery mechanism and a candidate symbolic component for a future NEUMANN controller. Earlier proof verifier/parser soundness Q3T2 protections reused unchanged.
- **Still unproven**: NEUMANN's **LEARNED model** independently discovers new relation operators/coefficients. This entire Q3U/Q3V relation generator is **deterministic exact classical symbolic algebra**. No neural training or inference was executed in these studies. Strong source-only classical SPACER solves more originals than Q3V and remains a proper baseline. Nothing here establishes complete matching-solved Q4 ≥10× wall/energy and frontier Q7. All global Q1–Q7 remain OPEN.
- **STOP** additional hand-optimizing the already-opened FiB source cohort to manufacture apparent generalization. Next science gate needs a different never-before-opened origin group and **trained** source-conditioned coefficient/structure constructor (not hardcoded specific examples), true causal ablation (no learned coefficients), full original source 3VC, Post-only, strong same-information SPACER/strong template specialist, and complete cost receipts. Q3F CHC competition original escrow source text remains unopened. External benchmark individual re-use rights unresolved; do not redistribute source/invariant text.

PR #236 kept DRAFT. Preserve immutable failed source outcomes and both first receipts, not just green CI.
