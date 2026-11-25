# NEUMANN 1 | Q3 failure diagnosis and counterexample-driven representation repair
Date: 2026-11-08 | PR #732 extension | Explicit scientific limitations

## Problem redefinition
We want an executable system to infer a new task-relevant representation and operation, **not** select a named math method from a fixed router. It must actively choose missing source queries, repair a false representation, transfer to structures with different algebraic premises, and compute its whole cost. The current work does not prove universal meta-algorithm invention.

## Root causes, with evidence
1. Previous monoid completion assumes associativity and identity. Source-only law sampling cannot prove either. Single-cell source-invisible mutation defeats the test even when in-family accuracy is 100%.
2. Exact polynomial identification still uses a human-given monomial/degree search grammar. Matching synthetic functions do not imply the system can invent an unfamiliar meta language.
3. Neither method encodes a **non-associative, non-polynomial row/column relation** in an adaptive coordinate basis. This is a real capability gap, not an extra testing problem.
4. A new relational rank learner initially accepted a one-factor model with a hidden second factor in one of 120 synthetic cases (119/120 correct). The naive validation sampler wasted probes across rows without ensuring coverage of novel underobserved rows.
5. Source query savings do not automatically imply lower CPU wall time. In locally cheap synthetic oracles, full-table computation can be quicker.

## Implemented architectural correction
Added `neumann1/active_rank_inventor.py` to both production interfaces:
- Autonomous source oracle queries with a hard budget.
- Find a rational row-space basis and an invertible pivot-column submatrix, no latent factors or operation formula supplied.
- **Invent a new coordinate representation** for each row using the sampled pivot columns, and an executable new relation `f(a,b)=u(a)·v(b)`.
- Cross-check all observed cells; first validate **underobserved distinct rows**, then probe remaining cells.
- On any falsifying source cell, query its full row, increase the rank if independent, and rebuild the representation. If the rank is capped or the evidence contradicts a proposed basis, abstain.
- `require_exhaustive=True` refuses to provide unconditional predictions without a full exact original table.
- An external *trusted rank upper bound* equal to a witnessed rank yields a **conditional mathematical derivation** (the code cannot prove the premise from finite samples). The default result is empirical, never certified universal.

**Why the conditional proof holds:** If the true finite matrix M over Q has rank at most r and the independently observed r basis rows are linearly independent, they span all rows. Choose r independent columns C so that W=M[R,C] is invertible. For every row i, the representation u_i=M[i,C]W^{-1}; then for every column j, M[i,j]=u_i M[R,j]. New input pairs are evaluated with the **constructed** coordinate representation. This is standard exact rank factorization, not an original theorem, and no low-rank claim is identifiable without its premise.

## Local first repair result (same-author synthetic, with seed repetition)
Source command: `PYTHONPATH=. python research/q3/q3_active_rank_first.py`.

| Source-defined relation | Size per instance | Cases | Unqueried exact | Source calls | Repair events |
|---|---:|---:|---:|---:|---:|
| Random rational rank 3 | 45 × 54 | 20 | 36,080/36,080 | 12,520 | 0 |
| Random rational rank 5 | 45 × 54 | 20 | 32,680/32,680 | 15,920 | 0 |
| Rectangular relation rank 2 | 60 × 65 | 20 | 64,880/64,880 | 13,120 | 0 |
| Bipartite graph adjacency rank 2 | 60 × 65 | 20 | 63,872/63,872 | 14,128 | 0 |
| Hidden second latent factor rank 2 | 45 × 54 | 20 | 37,679/37,679 | 10,921 | **20** |
| Exact rational-valued rank 3 | 45 × 54 | 20 | 36,080/36,080 | 12,520 | 0 |
| **Total** | | **120/120** | **271,271/271,271** | **79,129** | **20** |

Full-table source baseline requires **350,400** observations for exactly these instances. The new method uses **77.42% fewer source queries**, approximately **4.43× fewer** (full/source). This is not inference CPU/FLOP or end-to-end wall-time superiority, and full-table baseline is weaker than matched optimized classical rank factorization.

Diagnostic before the corrective query policy was 119/120 because hidden_rank seed=1 escaped randomized validation; the modified policy and source counterexample repair gave 120/120 in the same local suite. This is **replay after debugging**, not a frozen independent first validation. The 120 seeds do not constitute 120 different independently authored mathematical families.

## Crucial adverse results and degraded mode
- Source-limited errors cannot guarantee discovery of **every** rare exception. A modified oracle differing on one never-queried entry still defeats the learner. No algorithm can rule out this exception given the same transcript without stronger assumptions.
- A zero source matrix is rejected rather than promoted as an unjustified global rank-zero guarantee.
- Invalid numeric output, budget overrun, and unknown domains fail closed.
- High-integrity requests may set `require_exhaustive=True`; the system then refuses extrapolated outputs.
- A claimed rank upper bound must be an **external trusted contract**, not mistaken for an empirical certificate.

## Actual Q3/Q4/Q6 interpretation
- **Q3 scoped PASS:** The system actively generates an additional executable representation not expressible by the earlier associative-monoid or small polynomial constructor, and it self-repairs a discovered hidden factor. **Global Q3 OPEN** because the entire rank-factor method and expression primitives remain human-coded; the AI did not autonomously invent a wholly new meta-algorithm.
- **Q4 query-efficiency result only:** 77.42% fewer calls than exhaustive full table. The new method can be slower on cheap local CPU source oracles, and optimal classical matrix completion may match or beat it. **10× full-cost Q4 OPEN**.
- **Q6 scoped extension:** Unchanged code works on exact numeric relations and a synthetic graph adjacency structure, beyond finite monoids and polynomial-value functions. These are same-author tasks and matrices of known low rank. **Universal external Q6 OPEN**.
- **Evidence:** Tests plus replay are in GitHub Actions, `.github/workflows/q3_active_invention.yml`. Keep PR unmerged if CI fails, never mark global PASS.

## Most important next change
Research effort should now go into **a learned, task-independent generator for new program languages and search procedures**, not expanding the number of hand-coded inductive solvers. Use tasks authored by an independent external source; compare against exact classical matrix completion, polynomial interpolation, CEGIS, and an equivalent-accuracy transformer at matched query, wall-time and CPU/FLOP budgets. Freeze the discovery policy before external holdout, and report source, failed probes, repair costs, verification, and execution in one ledger.
