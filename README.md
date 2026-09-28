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

**v0.0.35 — Compression Economics Audit**

v0.0.35 keeps the frozen v0.0.34 proposal system unchanged and asks a stricter question:

> Does certified Structural Compression still save arithmetic work once the current checker's repeated successful rematerializations are counted?

The current fail-closed checker validates each tentatively accepted candidate by:

1. constructing the retained system,
2. solving it exactly,
3. reconstructing eliminated variables,
4. verifying the original full problem,

and then rematerializes the final accepted set again.

v0.0.35 audits an intentionally optimistic lower bound containing only successful materializations. It still excludes scorer work, candidate enumeration, failed-materialization hidden work, runtime overhead, memory traffic, and serialization.

### Measured result

- final examples: **256**
- methods audited: **8**
- checker parity with frozen v0.0.34: **100%**
- verified retention: **100% for every method**
- unsafe accepted reductions: **0**
- no-compression solve + verify baseline: **2047.99 arithmetic events on average**
- fraction of examples with successful-path lower-bound ratio >= 1: **100% for every method**
- `KEEP = true`

Selected methods:

| Method | Final solver ops | Final solver savings | Successful materializations | Mean lower-bound / baseline |
|---|---:|---:|---:|---:|
| learned MLP | 442.23 | 1529.42 | 8.49 | **4.62x** |
| target-leaf | **325.13** | **1646.52** | 8.68 | **4.50x** |
| Markowitz | 387.31 | 1584.34 | 8.96 | **4.68x** |

The final retained solve is cheap. The current path used to obtain and certify that retained problem is not.

### Central negative result

> **Per-candidate exact rematerialization destroys the measured solver savings on this benchmark.**

This is a failure of the current certification runtime architecture, not evidence against Structural Compression itself.

The evidence now separates three layers:

1. **Compression potential:** v0.0.32 showed large solver-work reductions when the correct reduced structure is available.
2. **Proposal capability:** v0.0.33–v0.0.34 showed that learned and deterministic scorers can safely find useful reductions.
3. **Certification economics:** v0.0.35 showed that re-solving after every tentative reduction overwhelms those gains.

The next milestone therefore does **not** train a larger utility model yet.

It must first test a bounded certification architecture that preserves exact reconstruction and original-problem verification while deleting repeated full reduced-system solves from the proposal inner loop.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/experiments/v0.0.32.md`
- `docs/experiments/v0.0.33.md`
- `docs/experiments/v0.0.34.md`
- `docs/experiments/v0.0.35.md`

### Frozen enabling results

**v0.0.34**

- removed the oracle `n-k` proposal budget from final inference
- learned proposal F1: **92.63%**
- target-leaf final solver ops: **325.13**
- learned final solver ops: **442.23**
- verified retention: **100%**
- unsafe accepted reductions: **0**
- central result: reference-rule accuracy did not predict downstream solver utility

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