# NEUMANN 1 | Q3 Autonomous Law Proposal, Active Source Queries, Operator Construction
2026-11-08 | Research extension of PR #732 | FIRST locally executed benchmark

## Scientific verdict

**Scoped Q3 PASS**, not global Q3. The running NEUMANN core now has:
1. \`synthesize_binary_operator_active(universe, source_oracle, query_budget, ...)\` in both \`NeumannEngine\` and \`RegistryEngine\`.
2. Source-limited oracle queries chosen by the algorithm, not a human-provided identity or generator list.
3. Term trees generated mechanically from variable atoms and binary-composition syntax.
4. Observed candidate equations discovered by grouping matching expression result vectors.
5. Empirical associativity candidate used to trigger identity testing, generator-row discovery and a newly compiled generator-word intermediate representation.
6. Self-chosen long-word falsification probes before output is frozen.
7. Fail-closed on insufficient law evidence, no identity, lack of generation or source budget. Optional explicit full-table degraded mode (not discovery).

This is not arbitrary-language or meta-algorithm invention. The finite universe, binary operator interface, term grammar, associative composition compiler, oracle budgets, validation rule and abstention behavior are still human-coded inductive priors. No code-writing language model was trained.

## What was tested

Execute \`PYTHONPATH=. python research/q3/q3_active_law_first.py\`; output \`research/q3/q3_active_law_first_result.json\`. These tests used synthetic black-box laws authored in this repository. Each of five operators was tested 30 times with differing query-selection random seeds, without giving its identity, generators or law family name to the active inventor. Once the source oracle is no longer used, the benchmark checks every pair absent from the source transcript.

| Family | Size | Successful runs | Source oracle calls | Unqueried exact | Full table calls |
|---|---:|---:|---:|---:|---:|
| Relabelled cyclic group | 31 | 30/30 | 5,117 | 23,713/23,713 | 28,830 |
| Noncommutative S3 × Z5 | 30 | 30/30 | 6,307 | 20,693/20,693 | 27,000 |
| Noninvertible function monoid × Z7 | 42 | 30/30 | 9,071 | 43,849/43,849 | 52,920 |
| Set-union semilattice | 32 | 30/30 | 19,135 | 11,585/11,585 | 30,720 |
| Bounded binary string concatenation | 31 | 30/30 | 13,952 | 14,878/14,878 | 28,830 |
| **Total** | | **150/150** | **53,582** | **114,718/114,718** | **168,300** |

This is a **68.16% reduction in source oracle queries** relative to exhaustive tabulation on exactly these synthetic instances, NOT a compute time, FLOP, inference speed, or end-to-end cost reduction. In the favorable cyclic structure the saved query fraction is ~82%; in the semilattice it is only ~38%. Full table uses more queries but provides unconditional correctness on the finite declared universe. A standard monoid learner supplied with valid axioms may match or beat these queries, and there is NO strongest equal-information classical comparison yet.

## Independent falsification within this benchmark

1. The nonassociative operation \`f(a,b) = a + 2b (mod 31)\` was rejected because the equational evidence did not support associativity.
2. The left-projection operation \`f(a,b)=a\` was rejected because no two-sided identity exists.
3. Budget=15 was enforced, with exactly 15 distinct source calls and no overrun.
4. When explicitly permitted, the degraded mode acquired 25/25 cells of a size-5 nonassociative operator and answered exactly. This **does not** generalize to unseen cells.
5. **Decisive failure:** a 31-element cyclic operation was modified on exactly one pair outside the active learner's observed transcript. The learner accepted the apparent law and **predicted that pair incorrectly**. This is evidence that empirical law hypotheses are not universal proofs; the external audit catches the fault.

## Conditional mathematical justification and impossibility boundary

Suppose a finite closed binary operation is associative and has an identity. Complete rows for a generating set suffice to represent every element by a generator word; its left actions then calculate the full operation on unseen pairs. That implication is rigorously correct and uses a well-known mathematical argument.

But \`n^2\` unconstrained table values cannot be uniquely inferred from fewer than \`n^2\` arbitrary black-box answers without inductive assumptions. For every unqueried pair there exists a modified operation agreeing with the source transcript and disagreeing at that pair. Thus universal accuracy over arbitrary unknown binary operators is impossible under a subquadratic query budget. **This is not a temporary engineering bug.** It is an information-theoretic indistinguishability boundary.

The \`DiscoveredAlgebra\` result therefore exposes \`conditional_associativity=True\` and \`verified_exhaustively=False\` for sparse generalized predictions. Never treat source fit or 12 validation probes as an independent formal proof.

## Q3 / Q4 / Q6 gates

- Q3: scoped **PASS** for autonomous source-query selection, candidate equation proposals, learned generator-word IR and executable operator. Global self-invention of primitives/axioms/representations on arbitrary new tasks **OPEN**.
- Q4: source query efficiency versus full lookup is **measured**, but end-to-end 10x lower compute than strongest matched classical synthesis is **OPEN**.
- Q6: unchanged algorithm works on group, noncommutative group, noninvertible monoid, idempotent semilattice and finite strings; these share a single associative-with-identity mathematical superfamily. Transfer to unrelated algorithmic families **OPEN**.
- Frontier equivalent problem solving **OPEN**. These are transparent mathematical toy models, not ARC-AGI-2 or frontier model benchmarks.

## Next decisive research step

Use independently authored multi-domain black-box algorithm tasks and a learned/generative typed program language that is not anchored on associativity. The system must identify discriminating queries between competing causal/algorithmic hypotheses, introduce a genuinely new reusable constructor, and benchmark against equal-query classical CEGIS, grammar-based synthesis and neural baselines. Total discovery + verification + inference wall/FLOP cost must be tracked. A nontrivial counterexample and an abstention must be represented in the final score. First pass must be frozen before any target-specific tuning.
