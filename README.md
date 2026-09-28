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

**v0.0.36 — Cheap-First Residual Headroom**

v0.0.36 tests whether any learned residual policy is worth building **after** the strongest cheap structural component has already run.

The frozen cheap component is:

    target-leaf @ threshold 0.10
        ↓
    deterministic checker

The residual teacher begins only from the actually certified target-leaf state and may not undo those accepted reductions.

The untouched audit set contains:

- **256 systems**
- **8 scale cells × 32 systems**
- signatures disjoint from all v0.0.33–v0.0.35 data
- verified retention: **100%**
- unsafe accepted reductions: **0**
- `KEEP = true`

### First measured result

Full-system baseline:

- mean solver ops: **1928.96**

Frozen target-leaf:

- mean solver ops: **202.32**
- mean solver savings: **1726.64**
- mean accepted reductions: **9.59**

Empty-start dynamic greedy utility:

- mean solver ops: **144.63**
- mean solver savings: **1784.34**
- mean trial materializations: **282.79**

Cheap-first residual dynamic utility:

- mean solver ops: **47.24**
- mean total solver savings: **1881.72**
- mean residual additions: **2.60 reductions**
- mean residual trial materializations: **29.45**

Thus the hybrid reduced the solver work remaining after target-leaf by approximately **76.65%**.

It also reduced retained-system solver work by approximately **67.34%** relative to the empty-start dynamic greedy teacher.

### Pre-registered continuation gates

All three gates passed:

| Gate | Measured | Required |
|---|---:|---:|
| residual headroom recovery | **268.78%** | ≥50% |
| positive residual rate | **55.47%** | ≥25% |
| teacher materialization reduction | **89.58%** | ≥50% |

Decision:

    PROCEED_LEARNED_RESIDUAL

The recovery ratio exceeds 100% because the cheap-first hybrid reaches a lower solver-work state than empty-start greedy utility. This is a **path-dependence result**, not evidence of global optimality.

### Architecture consequence

The measured architecture is now:

    cheap structural prior
        ↓
    certified compression
        ↓
    state-aware residual policy
        ↓
    deterministic checker
        ↓
    exact execution
        ↓
    original-problem verification

This is materially different from either:

- pure learned compression, or
- expensive utility search from the raw problem.

A cheap deterministic prior changes the search trajectory and sharply reduces the state space explored by the residual utility stage.

Teacher-search work also fell sharply:

- full dynamic successful-trial solver ops: **103,621.68**
- residual successful-trial solver ops: **1,073.43**

This is approximately a **98.96% reduction** in that measured teacher-work component.

This still does **not** establish end-to-end total-compute superiority because invalid-materialization partial work and other deterministic overhead are not fully instrumented.

### Scale structure

Residual value is strongly heterogeneous.

At apparent dimension `n=32`:

- `k=2`: positive residual rate **96.875%**
- `k=4`: positive residual rate **100%**

At smaller cells residual value can be sparse.

Therefore v0.0.37 should build the **smallest adequate state-aware residual predictor**, while keeping cheap residual heuristics and an activation/router possibility as mandatory baselines rather than assuming a universal neural policy.

See:
- `docs/experiments/v0.0.35.md`
- `docs/experiments/v0.0.36.md`

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