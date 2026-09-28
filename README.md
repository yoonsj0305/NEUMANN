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

**v0.0.38 — Coupled-Block Harder Structural Family Gate**

v0.0.38 introduced exact two-row / two-target coupled compression after the
original affine family became saturated by local heuristics.

New motif:

    y + z = f(core)
    y - z = g(core)

The frozen v0.0.37 local pipeline was carried forward unchanged:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker

The new 2x2 block checker uses exact Fraction arithmetic, re-derives the
reconstruction algebra from the original rows, and verifies the reconstructed
answer against the original full system.

Data:

- **256 final systems**
- **224 active systems**
- **32 no-compression controls**
- verified retention: **100%** on both paths
- unsafe reductions: **0**
- `KEEP = true`

### Measured result

Exact block oracle:

- retained-dimension error: **0**
- broad retained-dimension gap: **7 / 7 active cells**

Frozen one-row pipeline:

- elimination recovery: **7.35%**
- solver-savings recovery: **11.52%**
- active-example accepted-progress rate: **56.25%**

Pre-registered gate result:

    H1  PASS
    H2  PASS
    H3  PASS
    H4  FAIL
    H5  PASS

Therefore:

    FAMILY_NOT_HARD_ENOUGH

### What failed

The old parser was **not blind**. Every active cell exposed the expected local
one-row candidates.

The issue is deeper: the frozen one-row materializer cannot substitute an
eliminated target into its coupled partner row. Most locally valid one-row
identities therefore cannot become globally sufficient reductions and are
correctly rejected by original-problem verification.

This is a primitive-completeness boundary, not a parser failure.

### What remains valid

The exact 2x2 block primitive safely reached the declared core across all active
cells with 100% original-problem verification and zero unsafe block reductions.

So the multi-row primitive is retained.

The pure-coupled generator is not.

### Next research move

Do **not** relax H4 after seeing the result.

Do **not** retune the frozen local thresholds or train a block scorer yet.

The next gate is:

    v0.0.38.1
        = Mixed Local + Coupled Harder-Family Gate

It will add easy one-row leaves alongside coupled blocks so the old pipeline
makes genuine measurable progress before saturating, while multi-row headroom
still remains.

The original H1-H5 thresholds stay unchanged.

See:

- `docs/experiments/v0.0.37.md`
- `docs/experiments/v0.0.38.md`

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