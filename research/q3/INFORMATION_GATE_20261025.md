# NEUMANN Q3: IDENTIFIABILITY before CERTIFIED (2026-10-25)

Research-only theorem and fast CPU regression tests. This is not neural autonomous
operator invention; Q3 global remains OPEN.

Earlier own-weight GF(3) quadratic graph RC1 classified 160/160 positive
synthetic functions correctly. Its single extra all-ones counterexample query
caught a specific 80-case cubic OOD family but is **not a universal certificate**.

Decisive adversary: `(x0-x1)*(x2-x3)*(x4-x5) % 3`.
It is zero on all 0/single/pair observations, all ones, and even any
all-ones input with one or two coordinates zero, yet nonzero for inputs
with exactly one set variable from each of its three disjoint pairs.
A separate bounded-attack study generated 160 such adversaries on top of
the frozen original 160; all legacy observations were identical.
For all possible disjoint pairs, 420 variants n8 and 3,150 variants n10,
a deterministic greedy attack-family-specific hitting set has 18/51 queries.
Do NOT generalize that special guarantee to arbitrary cubic functions.

For an arbitrary squarefree GF(3) cubic perturbation on n variables, the
unknown coefficient dimension is C(n,3). By rank-nullity at least C(n,3)
independent extra scalar observations are necessary to detect *all*
nonzero cubic perturbations. Unit triple probes attain this bound,
56 queries for n8 and 120 for n10. THIS CLAIM ASSUMES a trusted
degree<=3 multilinear target function class. The caller must furnish
a separately verified class-membership proof, not merely a string label.

Even all binary inputs are inadequate for arbitrary functions: the
explicit delta function product(1-(x_i-2)^2) modulo3 is zero on all
{0,1}^n, nonzero at (2,...,2). The executable API only returns a
**class-conditional basis completeness** status or UNKNOWN; it NEVER
returns unqualified CERTIFIED.

Full archived local evaluation in this conversation:
`NEUMANN1_Q3_VERIFIER_BREAKTHROUGH_AND_OPTIMAL_INFORMATION_GATE_20261025.zip`
18 files, SHA256 `8616165411d2d5f7980e1261d3beb7479f42e2bcc35958238463edc1823d16cf`,
clean extracted and independently rerun all assertions PASS.
Includes original frozen own-weight model archival ZIP, actual new source
and separately stored attack truth, source-only CLASSICAL 160 new cubic
function programs, entire 5,248,800-input independent domain audit, greedy
query design and mathematical proof (PROOF_AND_SCOPE_KO.md).

The new cubic proposals and greedy checker are **human-authored classical**,
NOT new NEUMANN own-weight proposals; data are post-first internal synthetic
attacks, NOT unseen external author problems. Same-rights classical
algorithms are still better than neural in this domain. Global Q3/Q4/Q6/Q7
remain OPEN. No mainline merge without verifying proof boundaries.
