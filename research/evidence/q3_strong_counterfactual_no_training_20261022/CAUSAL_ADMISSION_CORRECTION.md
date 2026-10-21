# Q3 causal admission correction | 2026-10-22

## Historical evidence remains valid

PR #441, #442, #443 correctly certified that every **frozen** modulus option m=2..20 fails four synthetic out-of-range prime-step programs, and that the trained continuous constructor generates valid new **parameter instances** outside the frozen list (16/16 full original Z3+cvc5 safety proofs). Those achievements must remain archived unchanged.

But those runs only tested the model knockout against an **untrained random initialization**, not against a competent untrained source-conditioned prior.

## Exact stronger causal control

The constructor is `candidate(f, observations) = max(2, round(f * median(abs(next-current))))`. On its training/held-out deterministic sources `x' = x + k`, the normalized observation is exactly `k`.

For `f = sigmoid(6) = 0.9975273768433653`, the difference between `f*k` and `k` is below 0.5 for every **integer k ≤ 202**. Thus the same exact AST constructor with frozen `theta = 6` and **ZERO gradient updates** reproduces the correct modulus parameter for all former OOD k=23,29,31,37. A completely zero-model coefficient `f=1` likewise does so.

PR #444, Action **39689918315**, independently executed this stronger control against the SHA-256-pinned official original PR #442 artifact, and re-ran **Z3 and pinned cvc5 original source Init, Consecution, Goal**, not merely numeric comparison.

| Original source family | Archived learned | Untrained theta=6 | No-model f=1 | Matched exact GCD |
| --- | ---: | ---: | ---: | ---: |
| Deterministic `x'=x+k` (4 k ×4 seeds) full safety | **16/16** | **16/16** | **16/16** | **16/16** |
| New nondeterministic `x'=x+k OR x'=x+2k`, 25 source-valid observations per branch, full safety | **0/16** | **0/16** | **0/16** | **16/16** |

Every invalid nondeterministic candidate had an independent Z3+cvc5 **SAT consecution counterexample**, not just an unverified model prediction. The exact classical GCD of the same 50 mixed observations recovered k and achieved 16/16 independently proven full original safety.

## What the evidence now permits us to say

**PASS:** Learned continuous construction produces validated out-of-list operator *instances* on a bounded synthetic original source family.

**REJECT stronger causal claim:** Numeric gradient learning was **not causally necessary** for those 16 correct outputs relative to a strong untrained, same-interface fixed-prior control. The previous 0/16 random initialization knockout was insufficient to establish necessity.

**FAIL generalization on this semantic shift:** The frozen trained source-normalized median representation fails all 16 genuinely different nondeterministic transition programs. Exact classical GCD survives unchanged. This new stress set is posthoc synthetic research, not pre-registered external real-source generalization.

**OPEN:** Invented operator primitives, learned uniqueness over strongest classical source solver, cross-family real source-first-blind transfer, amortized compute superiority, global Q3/Q4/Q6, frontier and 10×.

## Architecture change

1. Keep independent exact original-source safety authority; never promote proposed ASTs directly to verified.
2. **Delete** this redundant trained scale fitting in deterministic constant-step sources; reuse zero-fit exact extraction.
3. Add a causal admission gate: compare every apparent learned gain not merely with random initialization but also the best source-conditioned **no-training** estimator with the same source access and output rights.
4. Add new transition-branch and nondeterminism holdouts so observation median shortcuts cannot masquerade as general structural invention.
5. Require a genuinely new operator structure not reducible to a trivial source statistic or already available strong classical source solver before changing Q3 from OPEN.

This is a scientific tightening of PR #443, not removal or relabeling of its immutable raw evidence.