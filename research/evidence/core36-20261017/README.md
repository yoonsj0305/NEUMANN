# NEUMANN 1 / CORE-36: fixed finite probes are insufficient even with identical safety goals

**2026-10-17. Exact constructive mathematical result, researcher-authored synthetic Horn family. Global Q1–Q7: OPEN.**

## First-principles issue

The earlier 17-observation information-limit experiment used different safety goals for its two programs. CORE-36 removes that possible confounder: BOTH originals now have the **same initial state** and the **same forbidden state**, and the theorem holds for every finite *fixed* set of behavioral probes, not only the first 17.

For any finite probe set `S ⊂ N`, choose integer `k > max(S)`; choose `k = 1` if `S` is empty. Let `R(n,s)` be the reachable relation. BOTH original Horn programs have:

- Initialization: `R(0,0)`.
- Identical unsafe goal: `R(k+2,k+4) -> false`.
- P0 transition: `R(n,s) ∧ n≥0 -> R(n+1,s+1)`.
- P1 transition: `R(n,s) ∧ n≥0 -> R(n+1,s+1+ite(n≥k,2,0))`.

Every observed state-transition delta at `n∈S` equals **1 for both programs**, yet at `n=k` the deltas are respectively 1 and 3. The safety-goal representation is identical. Therefore a deterministic proposer restricted to **only** the fixed probe vector, original initial state and safety goal receives identical input and emits the same candidate for both.

## Both originals are actually safe, separately

Two distinct unbounded inductive invariants prove the 3 full quantified clauses of their respective original:

- `I0(n,s) = (n≥0 ∧ s=n)`.
- `I1(n,s) = (n≥0 ∧ s=n+2·max(0,n−k))`.

All 3 exact original Horn assertion negations for each of P0 and P1 are independently checked as **UNSAT** after source-interpreted substitution. Therefore each program individually has a full inductive safety certificate.

## Formal no-common-invariant theorem

Assume one common relation `I` satisfies both programs. Initialization gives `I(0,0)`. Repeated application of P0's original universal transition gives `I(1,1), …, I(k+1,k+1)`. Applying P1's original universal transition at `n=k+1` gives `I(k+2,k+4)`. But the **shared** error clause says this last fact is forbidden. Contradiction. Since this argument holds for arbitrary `k≥1` and every fixed finite `S` admits such a `k`, no deterministic fixed-probe-only candidate selector can always prove this Horn family, however many model parameters it has.

With the two sources drawn uniformly, any randomized selector with only the same fixed observations and common goal has success probability at most 1/2 for a single candidate. This lower bound **does not constrain** methods that inspect the full source AST, use independent verifier feedback, or make adaptive source queries.

## Actual executed local evidence

Native `libz3 4.13.3.0`, 2026-10-17, `python core36_proof.py`. Five values `k = 1, 3, 17, 29, 64`:

- Both original CHC programs fully certified: **30/30 independently negated quantified Horn assertions UNSAT**.
- Joint common-relation theorem: **5/5 UNSAT** on an exact ground-instance consequence proof DAG (no unsupported source constraints).
- Mutations: **20/20 SAT** for reachable forbidden states and wrong-source invariants.
- Neural model forwards **0**, GPU calls **0**; local script wall **0.484 s** for one run, not a universal cost claim.
- Unsupported solver results, missing native library and parser errors cannot produce PASS.

The mathematical argument is general; five numerical Z3 executions are regression evidence, **not** the basis of the universal quantifier.

## Exact replay

```bash
python research/evidence/core36-20261017/core36_proof.py
```

The script generates its own full source assertions, checks each original clause, computes logical ground consequences, rejects SAT/UNKNOWN as appropriate and writes `core36_receipt.json`. Separate archived local full implementation has four unittest regressions, source-byte SHA receipts and a noncontiguous-probe check.

## Scientific decision

**Proved:** universal limitation of a *fixed finite behavioral-probe-only* interface in an explicit Horn program family; both targets individually safe under a common goal. **Not proved:** new learned operator invention, authentic unopened external-family neural transfer, frontier performance, efficiency advantages, or any global Q closure.

**Architecture:** delete fixed-probe-only universal-interface claims. Prefer source-aware typed semantic IR, independent original proof, verifier-guided source queries only when justified, and an exactly matched strong classical fallback. Keep Q1–Q7 OPEN until a model emits a previously unprovided useful relational AST on genuinely untouched external sources and beats strong classical solvers on complete cost and proof validity.
