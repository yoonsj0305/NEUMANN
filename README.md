# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **Structural Compression: reducing computational degrees of freedom before solving**.

> Discover the minimal sufficient computational structure, execute only what remains, and verify the original problem.

## Research thesis freeze

After v0.0.31, NEUMANN is no longer positioned primarily as "LLM + symbolic solver", "structure-first reasoning", or "IR + solver + verifier".

Those mechanisms are treated as enabling components with substantial prior art.

The central research hypothesis is now:

> **Can an AI reduce reasoning cost by discovering a minimal sufficient computational structure before solving?**

The stronger scaling question is:

> **Does Structural Compression change how verified reasoning compute grows with problem complexity?**

Canonical target architecture:

    Raw Problem
        ↓
    Semantic Parse
        ↓
    Structural Discovery
        ↓
    Structural Compression
        ↓
    Minimal Structural IR
        ↓
    Algorithm / Solver Router
        ↓
    Specialized Execution
        ↓
    Independent Verification
        ↓
    Result
        ↓
    Canonical Structure Memory

The critical distinction is:

    Structure discovery ≠ Structural Compression

NEUMANN must not merely re-encode all variables and constraints into an IR. It should attempt to remove safely reconstructible variables, redundant constraints, equivalent states, symmetry-related distinctions, and other computational degrees of freedom before execution.

Every learned reduction remains advisory. A compression certificate and independent checks retain execution authority.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/research/prior_art_positioning.md`
- `docs/experiments/v0.0.32.md`

## Current engineering baseline

**v0.0.62 — Residual motif screen after native MIP presolve (descriptive)**

Three previously inspected MIPLIB instances were screened for equality
leaves, exact duplicate columns and disconnected components after native
HiGHS presolve. The new fixed-cost flow example `beasleyC3` has none of
these simple residual motifs; `n5-3` has five tiny separate components
totaling 11 of 2,139 presolved variables. No new reducer or speed claim
follows. See `docs/experiments/v0.0.62.md`.

**v0.0.61 — Original-MIP affine reduction, corrective capability gate (negative)**

The v0.0.60 frozen objective/gap conjunction was unattained by either arm;
its timing ratio was not an iso-capability result. In a separately frozen,
explicitly post-result-calibrated v0.0.61 rerun, all six trials met the
corrected objective/gap gate and passed original-MIP verification. The
763-variable affine reduction was 1.313× slower than native HiGHS on median
complete-path time (9.871 vs 7.520 s). It remains out of the runtime.
This is a nonblind, single-instance negative gate, not an independent
holdout or scaling result. See `docs/experiments/v0.0.60.md` and
`docs/experiments/v0.0.61.md`.

**v0.0.59 — Bounded affine elimination against native LP presolve (negative)**

On one nonblind MIPLIB instance's continuous LP relaxation, a verified
substitution removed 763 variables but rewrote 763 bound rows. The full
candidate path was 10.18× slower than the original LP with native HiGHS
presolve (161.74 vs 15.89 ms median). This is a local negative gate, not
a MIP or general impossibility result. See `docs/experiments/v0.0.59.md`.

**v0.0.58 — Existing-presolve workload triage (descriptive)**

Across 240 official MIPLIB benchmark instances, trivial presolve already
removes at least half the variables in 20. A stronger native HiGHS presolve
on one hash-pinned aggregation-rich example removes 796/2,500 variables,
where the raw trivial presolve removes only 29. This is an opportunity-screen
correction, not a NEUMANN speedup or solve result. See
`docs/experiments/v0.0.58.md`.

**v0.0.57 — Verified-compute floor and leaf opportunity (descriptive)**

On the 13 previously inspected original matrices, iterative degree-at-most-one
graph peeling reaches at most 3.39% of variables; none meets the 10% screening
heuristic. This nonblind structural count is not a numeric compression or
runtime result. Full original-equation verification and explicit output also
impose a linear input/output floor on the total path. See
`docs/experiments/v0.0.57.md`.

**v0.0.56 — Corrective natural-matrix reuse audit (negative gate)**

The v0.0.55 first audit aborted on a frozen forward-error threshold, while
the original-equation backward error remained small. The corrective protocol
retains every source and comparator and declares its updated numerical
criterion before the next complete audit. Across all 13 unmodified originals,
three had repeated components but none delivered the required end-to-end
advantage; seven of ten no-repeat cases had >10% scanning overhead. The
generic component scan is stopped. See `docs/experiments/v0.0.56.md`.

**v0.0.55 — Unmodified matrix reuse incidence (invalid numerical gate)**

All 13 original NIST BCSSTRUC1 stiffness matrices test how often exact
identical components actually occur, with a scan-and-abstain path charged
against native full solves. The protocol is in `docs/experiments/v0.0.55.md`.
The first audit aborted on the frozen forward-error tolerance for `bcsstk13`;
no reuse-incidence conclusion follows from this run.

**v0.0.54 — Component splitting versus reuse (positive controlled ablation)**

The mechanism ablation compares exact factor reuse against an equally
decomposed baseline that independently factors each component. Both verify
the original assembled equations. Reuse lowered full-path time by >=20% on
4/4 large cases, separating reuse from decomposition in this repeated-copy
workload. See `docs/experiments/v0.0.54.md`.

**v0.0.53 — Exact real-matrix component reuse (positive controlled gate)**

A controlled workload interleaves repeated copies of two pinned NIST matrices.
It tests whether full-path exact factorization reuse, including component
detection and original-equation verification, beats a fixed strong native
SuperLU baseline. All 4/4 large cases beat fixed NATURAL by >=20%; the
`bcsstk09` 16-copy case was 11.0× faster. This mixes decomposition and reuse;
the next ablation must separate them. See `docs/experiments/v0.0.53.md`.

**v0.0.52 — Real numerical matrix ordering audit (negative gate)**

Four pinned NIST BCSSTRUC1 sparse matrices test a cheap external RCM order
against SuperLU's native ordering policies, charging full-path work and
checking the original equations. The data are fetched separately. The
predeclared >=20% threshold was met on 0/4 matrices; native NATURAL was
fastest on all four. No learned orderer was trained. The complete first
audit and limitations are in `docs/experiments/v0.0.52.md`.

**v0.0.51 — PACE external ordering opportunity gate (no model trained)**

On all 28 PACE 2017 public minimum-fill graphs with at most 128 vertices,
16 bounded min-fill restarts left no >=10% arithmetic-proxy headroom over
the stronger of min-degree/min-fill in the 11 sparse cases. This is an
external graph-only negative gate, not an exact optimum or verified numeric
solve. See `docs/experiments/v0.0.51.md`.

**v0.0.50 — Sparse ordering opportunity gate (no model trained)**

On 48 fresh 12-node SPD graph Laplacian systems, min-degree/min-fill left
no >=10% sparse scalar-operation headroom versus globally optimal
symbolic order. The optimum search was far costlier than an exact solve.
This family is saturated for learned ordering claims; see
`docs/experiments/v0.0.50.md`.

**v0.0.49 — Matched topology cost audit (no model trained)**

96 exact counterfactual pairs matched dimension, nonzero count and original
column-incidence histogram. Every pair changed F3's retained dimension
by two, but none showed a robust F3-to-F1 cost reversal: caching remained
beneficial on the retained-support side. This is a negative gate result,
not learned structural intelligence. See `docs/experiments/v0.0.49.md`.

**v0.0.48 — Cost-gate opportunity audit (no model trained)**

On 128 fresh exact n=16 systems, a one-feature original-incidence gate
separated all high-degree cases from dense and control cases. Only five
robust cost winners conflicted with it (pre-registered minimum: 16), so
the audit did not justify training a learned gate. All exact answers
verified; local timing is diagnostic, not a deployment claim. See
`docs/experiments/v0.0.48.md` and `python benchmark_v048_smoke.py`.

**v0.0.47 — Row-overlap boundary (contract only)**

F3's exact two-row support-pair candidates cannot overlap one row in a
nonsingular square residual: four target columns would occupy only three
rows. The [contract and audit](docs/experiments/v0.0.47.md) checks singular
overlap, full-rank repair, and disjoint controls on 384 fresh integer
matrices. This is not a new learned model or a performance improvement.
Run `python benchmark_v047_smoke.py` for a small contract check.

**v0.0.46 — Cached exact candidates and dense abstention (research)**

An incremental candidate cache preserves v0.0.45's exact high-incidence
reductions on a fresh 96-case arm while cutting derivation/checker calls
from 56 to 9.5 per system. Paired local full-path time was 0.764× frozen
F1 on that arm. On 96 dense systems F3 abstained and exactly matched F1,
but still ran 1.017× as long; controls were also slightly slower. Thus the
result is conditional and synthetic, not a general performance claim or a
trained model. The pre-registered 224-system audit is documented in
`docs/experiments/v0.0.46.md`; run `python benchmark_v046_smoke.py` or
`python benchmark_v046.py`.

**v0.0.45 — Exact Schur cost audit (research only)**

On 224 fresh exact systems, an experimental deterministic F2 repaired both
v0.0.44 structural gaps: all 96 high-incidence systems matched the full
oracle, and all 96 dense systems admitted an exact two-variable Schur
elimination. Yet measured full-path execution was slower than frozen F1:
paired median ratios 1.060 and 1.487. F2 is kept as a research baseline,
not promoted as a performance upgrade. See `docs/experiments/v0.0.45.md`
and run `python benchmark_v045_smoke.py` or `python benchmark_v045.py`.

**v0.0.44 — Adversarial structural boundary audit**

The frozen indexed method was challenged with two fresh generated families.
All 224 final answers verified against the original systems. It missed a
valid high-incidence block in every one of 96 cases; it also missed both
independently valid exact Schur witnesses in all 96 dense alternative cases.
The 32 controls remained uncompressed. The production materializer cannot
currently substitute eliminated targets into retained equations, so the
dense witnesses are references rather than available actions. See
`docs/experiments/v0.0.44.md`; run `python benchmark_v044_smoke.py` or
`python benchmark_v044.py`. No learned model was trained in this audit.

**v0.0.43 — Incremental indexed peeling**

This freezes v0.0.42 E2 and indexes residual low-incidence row pairs. On a
fresh 224-system audit, the same verified reductions and solutions were
selected on all 192 active cases; indexed pair examinations fell to 4.44%
in the coefficient arm and 0.73% in each overlap arm. The 32 controls stayed
uncompressed without rejected whole-system proposals. Paired local timing
ratios ranged from 0.855 to 0.893, but this does not measure energy or
general-purpose performance. See `docs/experiments/v0.0.43.md` and run
`python benchmark_v043_smoke.py` or `python benchmark_v043.py`.

**v0.0.42 — Nonunit parser and residual-incidence peeling**

This experiment tested two deterministic repairs to the v0.0.41 failure
modes on fresh generated exact systems. E1 removes the unit-only 2x2 target
restriction. E2 also peels validated low-incidence blocks from the remaining
row set. Neither method trains a learned block model. The pre-registered
protocol is `docs/experiments/v0.0.42.md`; the fresh 224-system audit passed
and E2 recovered 100% of oracle solver savings on all three active arms.
Run `python benchmark_v042.py` for the audit or `python benchmark_v042_smoke.py`
for a bounded correctness check. E2 examined 1,305.5 row pairs per active
system on average; solver arithmetic savings exclude discovery and checking.

**v0.0.41 — Anti-shortcut causal audit**

The v0.0.40 deterministic result was challenged on three separate
synthetic arms: generic nonunit invertible 2x2 coefficients, cross-block
overlap, and both together. Candidate visibility is measured separately from
verified downstream compression. The audit is pre-registered in
`docs/experiments/v0.0.41.md`; no learned block scorer was trained. The
224-system audit passed its integrity and verification gates. Nonunit block
coefficients exposed a candidate-visibility limit; cross-block overlap
exposed a conflict/selection bottleneck. Run
`python benchmark_v041.py` for the frozen 224-system audit, or
`python benchmark_v041_smoke.py` for a bounded correctness check.

**v0.0.40 — Coupled-Block Discovery / Routing Gauntlet**

v0.0.40 moved from family design to actual structure discovery on a fresh
256-system audit set.

No learned block model was trained.

The validated v0.0.38.1 mixed family was held fixed:

- easy local one-row leaves,
- coupled exact 2x2 blocks,
- generic variable names,
- row/column permutation,
- exact original-problem verification.

The frozen local pipeline remained:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker

v0.0.40 then compared deterministic routing/discovery variants.

### Result

The selected method under the pre-registered tie-break was:

    D4 = incidence router + row/target component graph

It achieved:

- solver-savings recovery: **100%**
- elimination recovery: **100%**
- block precision: **100%**
- block recall: **100%**
- block F1: **100%**
- verified retention: **100%**
- unsafe reductions: **0**

Decision:

    KEEP_DETERMINISTIC_DISCOVERY

Therefore a learned block scorer is **not justified** on this family.

### Performance-equivalent deterministic winners

D2, D3, and D4 all recovered the full measured verified compression value.

D2:

    incidence router
        +
    exact candidate-overlap block discovery

D3:

    incidence router
        +
    sparse shared-unit block discovery

D4:

    incidence router
        +
    2-row / 2-target component graph

All three reached:

    100% solver-savings recovery
    100% elimination recovery
    100% block recall
    100% verified retention

D4 is the formal winner only because the frozen tie-break counted fewer
row-pair examinations.

That does not prove D4 has lower total discovery cost, because D4 instead
examines graph edges and unlike cost units are intentionally kept separate.

### Most important finding: routing before discovery

D1 used the old local-first pipeline before exact block discovery.

It still achieved:

- solver-savings recovery: **98.20%**
- elimination recovery: **95.02%**

but block recall dropped to:

    86.46%

because the local stage consumed coupled targets before block discovery.

Average coupled targets consumed locally:

    D1 = 0.7109
    D2 = 0

After adding a trivial incidence router:

    target incidence == 1
        -> local path

    target incidence > 1
        -> reserve for multi-row path

block recall became:

    100%

with easy-leaf routing precision/recall also:

    100% / 100%

So the current structural lesson is not "use a better block scorer."

It is:

    route structural degrees of freedom correctly
        before
    consuming them with local reductions.

### Current validated architecture on this family

    raw exact system
        ↓
    incidence-aware structural router
        ├── local one-row path
        └── multi-row reserved path
        ↓
    deterministic block discovery
        ↓
    exact independent algebra checker
        ↓
    exact retained solve
        ↓
    reconstruction
        ↓
    original full-system verification

### Saturation boundary

This mixed 2x2 family is now saturated by cheap deterministic structure.

Do not train a block-discovery neural model on it.

The next research family must remove at least one shortcut:

- fixed +/-1 coupled coefficients,
- clean two-row/two-target connected components,
- absence of distractor overlaps,
- absence of cross-block dependencies,
- single block size,
- incidence-perfect routing.

Only if deterministic methods leave pre-registered verified downstream
headroom should learned structural discovery be reconsidered.

See:

- `docs/experiments/v0.0.38.1.md`
- `docs/experiments/v0.0.40.md`

### Frozen enabling results

**v0.0.33**

- oracle-cardinality scaffold (B=n-k)
- learned elimination recovery: **72.02%**
- learned oracle solver-savings recovery: **84.93%**
- verified retention: **100%**
- unsafe accepted reductions: **0**

**v0.0.32**

- oracle Structural Compression benchmark
- full-solution equivalence: **1.0**
- fixed-k oracle-compressed solver slope: approximately **0**
- explicit certificate byte overhead retained as a negative result

**v0.0.31**

- matched Direct / Structural Tiny Transformers: **75,538 parameters each**
- Direct final verified coverage: **12.76%**
- Structural final verified coverage: **100%**

## Persistent privilege

Public persistent execution requires:

    exact manifest authorization
      + lifecycle-compatible declaration
      + exact-manifest PASS lifecycle attestation

Only then can the public persistent builder create a reusable worker.

## Lifecycle conformance attestation

Attestation currently supports persistent-compatible classes:
- `STATELESS`
- `CACHE_ONLY`

Minimum prototype PASS gate:
- at least 3 explicit conformance cases
- at least 2 warm repetitions per case
- warm persistent mode: 100% pass
- recycled mode: 100% pass
- compile/solve/verify cross-generation mode: 100% pass
- expected semantic subset equivalence: 1.0

Execution modes:

### Warm
Repeated cases reuse the same worker.

### Recycled
Worker is recycled at case boundaries.

### Cross-generation
`max_requests_per_worker=1` forces compile, solve, and verify through separate worker generations.

## Exact-artifact binding

Attestation records are bound to:
- plugin ID
- exact manifest SHA-256
- declared worker state class
- explicit conformance corpus SHA-256

The attestation itself also has a canonical SHA-256 digest.

Therefore:

    changed manifest + old attestation → reject

even when the logical plugin ID is unchanged.

## Runtime enforcement

Public persistent builder behavior:

| Evidence | Result |
|---|---:|
| no attestation registry | reject |
| no attestation for exact manifest | reject |
| stale attestation for another digest | reject |
| FAIL attestation | reject |
| exact PASS attestation | allow |

## Bootstrap boundary

Attestation must test a candidate before persistent privilege exists.

NEUMANN therefore has an internal conformance-only persistent builder that bypasses only the attestation requirement while still enforcing:
- manifest validation
- exact-manifest authorization
- activation policy
- lifecycle compatibility
- out-of-process execution

It is intentionally **not exported as a public NEUMANN API**.

## Important boundary

A PASS attestation is deterministic evidence over a finite declared corpus.

It is **not**:
- formal verification
- proof for all possible inputs
- proof against adaptive malicious behavior
- publisher identity
- OS sandboxing

v0.0.25 adds a durable append-only attestation ledger with:
- exact manifest / corpus / attestation digest binding
- ISSUE / REVOKE evidence history
- hash-chain integrity verification on reload
- optional trusted-head rollback detection
- use-time evidence checks before every persistent dispatch

A local hash chain still cannot detect rollback to an older valid prefix without a trusted external head.

See `docs/experiments/v0.0.25.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v024.py
    python benchmark_v025.py
    python benchmark_v026.py
    python benchmark_v027.py
    python benchmark_v028.py
    python benchmark_v029.py
    python benchmark_v030.py
    # v0.0.31 requires optional CPU PyTorch in its separate CI job
    python benchmark_v031.py

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.
