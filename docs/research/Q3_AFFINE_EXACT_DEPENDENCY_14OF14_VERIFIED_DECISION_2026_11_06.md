# NEUMANN 1 | Exact affine semantic-dependence post-FIRST result and proof

Date: 2026-11-06. Draft PR #680. Original PR #678 learned first remains an immutable **FAIL 2/6**.

## Actual CI evidence
- [Actual successful isolated run #42206332670](https://github.com/yoonsj0305/NEUMANN/actions/runs/42206332670)
- Original corpus: the already-opened 8 source-free ASTs from #676 and 6 adversarial ASTs from #678. No new external original CHC source or held-out benchmark accessed.
- Analytic coefficient normal form agrees with independently emitted existential Z3 semantic collision checks **14/14**.
- Analytic dependency checks use **0 Z3 queries**. Independent SMT control uses **14 queries**.
- Same-runner 14-call measured sums: analytic Python perf_counter segment **0.24011 ms**; Z3 independent proof subprocess wall **140.361 ms**. Ratio **584.57x (Estimate from this exact measurement)**, comparing a Python AST operation with full Z3 startup+solver subprocess. It is **NOT** a whole application, training, deployment or 10x Q4 efficiency result. Measurements are neither repeated across runners nor an unselected external sample.
- Full artifact: https://github.com/yoonsj0305/NEUMANN/actions/runs/42206332670/artifacts/13496143611.
- Additional unit tests: cancellation, commuted affine indices, unknown nonlinear and malformed AST fail-closed.

## Mathematical correctness within the declared grammar
Let the supported source-value update expression be a linear form

`F(S,b,i) = c_0 + c_b*b + c_i*i + sum_j a_j*S[h_j(b,i)]`,

where `h_j` are affine integer index functions. The normalizer expands expressions by structural induction on typed AST nodes: constants and variables are base cases; addition, negation and constant multiplication preserve the linear form; source-array selection adds a symbolic source atom. Combining coefficients of identical normalized affine indices is an exact algebraic identity.

- If **all a_j=0**, the expression is source-independent for every S,b,i; hence an H0 representation omitting S suffices for this output value.
- If **some a_j != 0**, collect canonical distinct affine index functions. As there are finitely many, choose integer b and nonnegative i outside the finite union of equal-index hyperplanes, so their selected integer positions are distinct. Choose two unrestricted source arrays that differ at exactly the position whose coefficient is nonzero; then their output values differ with unchanged destination and metadata. Thus source dependence has a genuine H0 collision.

This implication depends critically on unbounded integers, unrestricted array interpretations, and a finite set of affine source-independent index terms. It is invalid without rechecking semantics under aliasing, constrained arrays, overflow, mixed nonlinear or nonaffine index operations.

**Important interpretation:** "source-independent" refers only to the single update-value expression and the declared H0 information boundary, not automatic completeness of any loop invariant or external program solver.

## Decision
For this precise typed affine class, **delete the learned lexical source-read selector** and use exact algebraic normal form; invoke a separate SMT semantic oracle only on unsupported cases, or ABSTAIN on solver UNKNOWN. Do not spend learning budget on a decision that can be made soundly and directly by algebra.

Still unproven: model-driven semantic operator construction not available in the human grammar, independent all-original-clause proof, cost superiority over equal-rights strong classical, cross-formalism transfer, Frontier performance. Global Q3/Q4/Q5/Q6/Q7 remain OPEN.
