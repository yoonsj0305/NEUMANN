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

v0.0.38 deliberately moved away from the saturated one-row affine family and
introduced exact two-row / two-target coupled blocks.

Each block has the form:

    y + z = f(core)
    y - z = g(core)

after row/column permutation and generic renaming.

The frozen v0.0.37 deployable baseline remained unchanged:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker

A new exact 2x2 block checker independently re-derived the block algebra using
Fraction arithmetic and verified the reconstructed answer against the original
full system.

Data:

- **256 systems**
- **224 active coupled-block systems**
- **32 no-compression controls**
- **8 cells × 32 systems**
- prior-signature disjointness: **PASS**
- one-row verified retention: **100%**
- block-oracle verified retention: **100%**
- unsafe reductions: **0**
- `KEEP = true`

### First measured result

Exact 2x2 block reference:

- mean retained-dimension error vs declared core: **0**

Frozen one-row pipeline over active systems:

- mean elimination recovery: **7.35%**
- mean solver-savings recovery: **11.52%**
- active-example progress rate: **56.25%**

Broad structural gap:

- active cells satisfying the retained-dimension-gap criterion: **7 / 7**

Pre-registered harder-family gates:

| Gate | Result |
|---|---:|
| H1 oracle reaches core exactly | PASS |
| H2 one-row elimination recovery ≤75% | PASS |
| H3 one-row solver-savings recovery ≤90% | PASS |
| H4 one-row accepted progress on ≥75% active examples | **FAIL** |
| H5 broad gap in ≥5 active cells | PASS |

Therefore the frozen result is:

    FAMILY_NOT_HARD_ENOUGH

### Why H4 failed

This is **not** parser blindness.

Every active cell exposed exactly the expected one-row candidates:

    candidate count = 4 × coupled-block count

The old parser sees the local affine identities.

The failure occurs in the old one-row materialization primitive. It deletes the
chosen target column and source row but does not algebraically substitute that
target into other retained rows. In a coupled block, each target still appears
in the partner row, so many individually valid affine identities cannot become
standalone full reductions and are correctly rejected by original-problem
verification.

Thus v0.0.38 uncovered a measurement-definition mismatch:

    intended H4 question:
        "can the old parser see real candidates?"

    implemented H4 question:
        "can the entire old one-row reduction primitive
         successfully materialize at least one reduction?"

Those are not equivalent.

The gate is **not** changed on the observed v0.0.38 data.

### Research consequence

Do not train a block-discovery model yet.

The next experiment must use **fresh data** and pre-register a repaired
anti-parser-blindness gate based directly on candidate visibility/algebraic
validity while keeping H1, H2, H3 and H5 unchanged.

Only after that independent replication passes should NEUMANN compare block
discovery/routing methods.

See:

- `docs/experiments/v0.0.36.md`
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