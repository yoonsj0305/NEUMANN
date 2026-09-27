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

**v0.0.32 — Oracle Structural Compression baseline**

v0.0.32 is the first NEUMANN experiment that directly measures reduction of computational degrees of freedom.

Pre-registered controlled family:

    core dimension k ∈ {2, 4}
    apparent dimension n ∈ {4, 8, 16, 32}
    32 systems per cell
    256 systems total

Baseline:

    full n-variable system
      -> exact rational Gauss-Jordan
      -> verify original full problem

Oracle Structural Compression:

    full system
      -> oracle compression certificate
      -> retained k-variable core
      -> same exact solver
      -> reconstruction
      -> verify original full problem

First measured result:

- core pytest: **161 passed, 1 skipped**
- full-solution equivalence: **1.0**
- certificate validity: **1.0**
- verification-work parity: **true**
- KEEP: **true**

For fixed (k=2):

    n = 4   : baseline/compressed solver work = 4.47x
    n = 8   : 18.50x
    n = 16  : 75.27x
    n = 32  : 302.27x

Measured solver log-log slope:

    baseline   ≈ 2.0266
    compressed ≈ 0.0000

For fixed (k=4):

    n = 4   : 1.00x
    n = 8   : 4.74x
    n = 16  : 20.52x
    n = 32  : 85.31x

Measured solver log-log slope:

    baseline   ≈ 2.1361
    compressed ≈ 0.00018

This is an **oracle** result. Generator-provided dependency information is unavailable to a real learned system.

It does not establish that an AI can discover the compression or that total end-to-end compute is lower.

Important retained negative/boundary results:

- reconstruction work still grows with apparent problem size
- full original-problem verification still grows with apparent problem size
- compressed solver payload shrinks sharply
- the explicit v0.0.32 certificate is larger than the raw solver payload, so end-to-end byte compression is **not** demonstrated

At (k=2,n=32):

    raw solver payload          ≈ 2416.5 bytes
    compressed core payload     ≈ 56.4 bytes
    explicit certificate        ≈ 7360.6 bytes

The solver bottleneck was compressed; proof/reconstruction overhead remains.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/research/prior_art_positioning.md`
- `docs/experiments/v0.0.32.md`

### Frozen enabling results

**v0.0.31**

- matched Direct / Structural Tiny Transformers: **75,538 parameters each**
- identical learned arithmetic proxy
- Direct final verified coverage: **31/243 = 12.76%**
- Structural final verified coverage: **243/243 = 100%**
- near-negative false routes: **0%**
- result remains task-specific and is not a total-compute claim

**v0.0.30**

- Direct capacity/data frontier did not reach Structural verified coverage
- best descriptive final Direct: **28/243 = 11.52%**
- fixed Structural final: **243/243 = 100%**

**v0.0.26–v0.0.29**

Established reusable-structure amortization, learned-proposal cost accounting, authority separation, and the first matched-capacity direct-vs-structure comparisons.

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