# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.27**

v0.0.26 established a first structural-efficiency contract: an already-valid solver-ready representation can be reused so repeated execution does not repay representation formation on every run.

v0.0.27 moves one layer upstream:

> **How much learned inference work does the current structural proposer actually use, and can that work be measured without pretending a proxy is FLOPs or energy?**

The current proposer is deliberately small:
- TF-IDF word + character features
- logistic known-vs-unknown detector
- logistic supported-family classifier
- deterministic compiler acceptance before solver authority

The v0.0.27 contract measures:
- fitted logistic coefficient/intercept scalar count
- TF-IDF IDF state separately from classifier parameters
- sparse active features per executed stage
- sparse score dot-product term proxy
- proposal coverage and abstention
- proposal false routes versus compiler-gated false routes
- end-to-end deterministic solver verification for supported tasks
- exact repeated-proposal reuse over 8 uses

It explicitly does **not** call the score proxy FLOPs, does not infer joules or GPU-memory savings, and does not generalize this TF-IDF/logistic model to an LLM.

See `docs/experiments/v0.0.27.md`.

First measured v0.0.27 result:
- fitted logistic coefficient/intercept scalars: **1,962**
- measurement/public prediction parity: **1.0**
- known proposal coverage and end-to-end verified coverage: **1.0**
- proposal-layer unsupported false-route rate: **0.10**
- final unsupported false-route rate after compiler gate: **0.0**
- one bad learned proposal was rejected by the deterministic compiler
- mean sparse score-term proxy: **60.17**
- 8 repeated exact uses: learned score-term proxy **8 → 1 equivalent inference payment**
- KEEP decision: **true**

The 10% proposal false-route is a useful result, not a hidden blemish: the learned router can be wrong while the deterministic compiler prevents that mistake from becoming solver authority.

### Previous structural-reuse result

v0.0.26 measured:
- verified answer equivalence: **1.0**
- representation-step reduction for 8 repeated executions: **8 → 1**
- mean representation/raw byte ratio: **3.86** (representation is larger)
- mean observed CI wall-time ratio: **4.07×** in favor of reuse

The wall-time ratio is a diagnostic from small Python fixtures, not a general speedup claim.

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

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.