# NEUMANN 1 · Q3 DRAGON_2 least affine inductive closure (2026-10-21)

## Scientific question
Can we completely resolve the formerly UNKNOWN `DRAGON_2` full-program affine XOR space without more neural training and without mistaking 64 observed SMT states for complete reachable semantics?

**This PR is a prospective algorithm run on an already OPENED authentic source, not a new blind learned operator.** It deliberately preserves first learned XOR4 result **0/2** under immutable SHA256 `5e9c7f5d1e4039d5a7e3b7edd90857684d8d7ac14b3ab10589b76c2102c2e47b`; source is `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`, exact original `DRAGON_2.lus.sl` Git blob `17f0cea250008e9e3575d38181f7e40804501dde`. Goal-support variable masking unchanged. Global learned Q3 stays OPEN.

## Proof idea: do not sample fixed finite states and guess
For eligible original Boolean state vector `x` of dimension `n=20`, maintain finite actual original-model rows `S`. Define `H = affine_GF2_hull(S)` by exact bitwise Gaussian elimination (kernel of augmented rows `(x,1)`).

1. Require actual original `Pre` SAT, add that state to `S`.
2. Query **full original** `Pre AND NOT H(x)`. If SAT, add the model `x` to `S`.
3. Otherwise query **full original** `H(x) AND Trans(x,x') AND NOT H(x')`. If SAT, add the model `x'` to `S`.
4. Each counterexample must increase augmented row rank by exactly one. This gives an **at-most n further additions** algebraic convergence bound.
5. When **both** original queries are UNSAT, certify final global inductive 2VC for the *whole conjunctive basis* using original Z3 and independently pinned cvc5. UNKNOWN/timeouts fail closed. All original Pre/Trans/Post semantics also undergo custom/native Z3+cvc5 parity.
6. Enumerate every singleton/pairwise affine relation in the final hull, individually verify actual original 2VC under independent Z3+cvc5, and compare **source-proved** rank to full algebraic nullity.

**Minimality theorem:** any affine inductive invariant `K` containing all original Pre states must contain the initial model. If all rows in `S` belong to `K`, affine closure forces `H(S) subset K`; each original successor from `H(S)` therefore belongs to `K`, and so does the next inserted successor model. Induction over every added witness shows `H(S) subset K`. At convergence, `H` is itself original-program inductive and thus the **smallest affine inductive superset of Pre** in the declared Boolean coordinate projection. This is not merely observational rowspace; it includes universally quantified transitions from every current affine-hull state via a counterexample search.

## Controls, admission, degraded mode
* Synthetic even 4-variable XOR transition: expected 1 genuine 4-way invariant and 0 pairwise relation dimensions (**GO control**).
* Synthetic totally unconstrained 4-Bool Pre/Trans: expected affine kernel nullity 0 (**NO_GO control**).
* Historical real FIRST learned 0/2 SHA preserved before any new analysis.
* Original source Git blob identity + native/custom semantic equivalence in Z3 and cvc5 unchanged.
* After convergence, independent dual-solver final Pre + consecution **UNSAT** is required to call full affine space certified.
* Unknown, changed source, wall budget, unexpected rank event, solver disagreement: **ABSTAIN**. Do not upgrade any Q3 learning claim.
* If full source-certified affine rank equals individually dual-proved 1/2-var invariant span rank, claim strong no-independent-wider-affine structure **only** for this exact source/variables. If not, the independent higher-order structural headroom remains and is a classical exact source finding, *not* evidence of new learned math.
* No new training, no neural forwards, no GPU, no paid API. Record exact wall clock, solver evidence and hashes; no unsupported performance multiplier.

## Execution / immutable evidence
Workflow: `.github/workflows/q3-dragon2-exact-affine-inductive-fixpoint.yml`.

Source: `research/evidence/q3_exact_GF2_all_arity_20261021/dragon2_exact_affine_inductive_fixpoint.py`.

Success in GitHub Actions is not itself a scientific pass: read the uploaded original JSON, exact original dual 2VC, `scientific_status` and returned nullity. On UNKNOWN/ABSTAIN, preserve evidence and stop. This experiment **cannot** close learned Q3 or full original published Post 3VC.
