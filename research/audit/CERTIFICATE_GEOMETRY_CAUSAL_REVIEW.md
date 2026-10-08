# Why a correct shortlist used to complete the certificate

**Decision: HOLD_LEARNING.** A new source analysis explains a structural boundary
of the successful LP mechanism. It does not replace Q34 PASS, Q5 FAIL or M106 FAIL.
No optimizer, neural forward, fitting or new problem generation was performed.

## The ideal original generator supplies more than a sparse answer

`lp_basis_headroom_v082._generate_case()` builds an invertible m-by-m matrix B,
a strictly positive vector x_B, b=B x_B, a dual y*, and costs
c=A^T y*+d. Reduced slack d is zero on B and strictly positive outside B.
v088 uses this generator, rescales columns, and retains original validated labels.
v100 trains weighted BCE on those reference-basis membership labels. The human
designed quotient and the 433-scalar ranking network do not generate a new IR.

In exact arithmetic, every feasible x satisfies

    c^T x - b^T y* = d^T x >= 0.

An optimum therefore has no positive mass outside B. Invertibility fixes x_B
uniquely, and all its m entries are positive. If a selected column set contains B,
its restricted primal optimum is the same original optimum. Complementary
slackness forces any restricted optimal dual y to satisfy

    B^T y = c_B.

Since B is invertible, y=y*. Thus it also satisfies every omitted original dual
inequality. The shortlist contains enough information to recover BOTH the answer
and the original certificate. This property follows from the constructed family,
not from a learned general certificate-completion skill.

These are standard LP duality/complementarity arguments, not a new NEUMANN
theorem. The background is [Boyd and Vandenberghe, Convex Optimization,
optimality conditions](https://web.stanford.edu/~boyd/cvxbook/bv_cvxslides.pdf).

## The opened BP transfer loses this property

For the retained BP optima, positive support S has s=m/8 columns. It remains
full column rank, but `A_S^T y=c_S` has m-s unconstrained dual directions.
Because b=A_S x_S, all those directions also leave b^T y unchanged. The correct
primal and equal objective alone do not constrain the omitted inequalities.
A restricted optimal dual can therefore fail `A^T y <= c` on the original LP.
It is not legitimate to weaken that original verifier.

The original BP generator's planted feasible support is not used as authority
here. The analysis uses the preserved, original-verifier-accepted Native witness.
It does not assert uniqueness of the BP optimum or of its support. At the frozen
floating tolerance, stationarity and rank are numerical diagnostics; the exact
argument above is about the ideal generator, not every floating input.

| Retained originals | Positive support | Numerical rank | Active-equality dual nullity |
|---|---:|---:|---:|
| v088 training, 48 | m = 32 or 64 | m, all 48 | 0, all 48 |
| M106 transfer, 16 | m/8 = 2, 4, 8 or 16 | m/8, all 16 | 14, 28, 56 or 112 |

Maximum active stationarity error was 9.80e-15 in training and 1.90e-10 in BP.
Every retained witness passed the unchanged original numerical certificate.
The BP inactive minimum reduced slack was -2.79e-10, within the frozen checker
tolerance; it is not an exact strictly-positive-slack claim. Original training's
inactive slack minimum was 0.191934 after normalization.

## What this explains, and what remains unresolved

The existing M106 replay contains 19 first-timed restricted attempts with an
optimal primal but a rejected dual, over 13 candidate paths and 7 originals.
Pairing those primals with an already retained Native dual passes 19/19 offline.
This is consistent with the certificate-completion boundary above. Many other
shortlists failed to recover the primal; this analysis does not explain those
ranking failures. The separately measured feature degeneration is another
concrete distribution change, not an isolated causal ablation.

The registered Phase2 already tested paying for certificate completion. Minimum
norm dual worked on 5/16 originals; 11/16 needed a full original dual LP. The paid
dual route was slower than Strong Native. Even free support AND free optimal dual
gave only 4.091x geometric mean and 0/16 tenfold cases. For that adapter, all 16
tenfold discovery budgets are negative before neural discovery is added.

Therefore no new relational model, support-cardinality learner, or certificate
loss is justified in this opened BP family now. The reusable lesson is narrower:
**a sufficient answer representation need not be a sufficient cheap-certificate
representation.** Future economic screening must include the certificate's
structural degrees of freedom and completion cost, alongside execution savings.
No G1/G2 or Frontier claim follows.

## Reproduction and evidence

`python research/audit/analyze_certificate_geometry.py` reads the hash-verified
v088 archive and M106 source/report only, rechecks existing witnesses, and
computes SVD under one numerical thread. `linprog` and `milp` fail closed during
the analysis. It writes 64 original-level diagnostic rows, not 64 fresh tasks.
The SVD rank threshold is `max(shape)*machine_epsilon*largest_singular_value`.

`CERTIFICATE_GEOMETRY_DIAGNOSTICS.csv/.json` retain per-original ranks, residuals
and source hashes. `M106_RETAINED_DIAGNOSTICS.csv/.json` and
`BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.csv/.json` supply the separate existing
attempt and timing evidence. Missing lifecycle, energy and memory costs remain
UNKNOWN; no times from different machines were combined.
