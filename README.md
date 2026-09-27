# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.28**

v0.0.27 established an auditable learned-proposal cost contract for the TF-IDF + logistic router.

v0.0.28 asks the next controlled question:

> **Does the same structural proposal contract survive a genuinely nonlinear neural proposer, and what does that nonlinearity actually cost?**

The new proposer keeps the same TF-IDF inputs but replaces each logistic head with a one-hidden-layer MLP:

    TF-IDF
      -> 4-unit ReLU hidden layer
      -> open-set / family proposal
      -> deterministic compiler gate

The neural model still has no solver authority. Solver-ready IR must come from the deterministic compiler.

The v0.0.28 benchmark compares the neural proposer and the v0.0.27 logistic baseline on the exact same corpus and records:
- fitted model state
- layer shapes
- sparse active features
- weighted-sum term proxy
- known-task proposal and verified coverage
- unsupported proposal and final false-route rates
- exact repeated-proposal reuse

Cost superiority is **not** a KEEP condition. If the neural model is more expensive, that is retained as a negative result rather than optimized away.

See `docs/experiments/v0.0.28.md`.

### Previous measured results

v0.0.27:
- logistic coefficient/intercept scalars: **1,962**
- known proposal and end-to-end verified coverage: **1.0**
- unsupported proposal false-route rate: **0.10**
- unsupported final false-route rate after compiler gate: **0.0**
- mean sparse score-term proxy: **60.17**
- 8 repeated exact uses: **8.0x** learned-work amortization

v0.0.26:
- verified answer equivalence: **1.0**
- representation-step reduction for 8 repeated executions: **8 -> 1**
- mean representation/raw byte ratio: **3.86** (representation is larger)
- mean observed CI wall-time ratio: **4.07x** in favor of reuse

Wall-clock remains diagnostic only and is not a general speed claim.

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

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.