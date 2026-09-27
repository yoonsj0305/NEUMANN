# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.29**

v0.0.28 showed that adding a nonlinear proposal head did not automatically create efficiency: the tiny MLP improved proposal routing on the controlled corpus, but used about 4x the fitted classifier state and arithmetic proxy of the logistic baseline.

v0.0.29 moves from proposer-vs-proposer comparison to the first **paired direct-vs-structure task experiment**.

Two learned paths receive the same fixed-position token representation and the same one-hidden-layer, 8-unit, two-output MLP inference architecture.

Direct path:

    raw token sequence
      -> matched-capacity MLP
      -> two numeric solution values
      -> evaluation verifier

Structural path:

    raw token sequence
      -> matched-capacity MLP
      -> LINEAR / ABSTAIN
      -> deterministic compiler
      -> deterministic solver
      -> deterministic verifier

The paired benchmark is deliberately limited to deterministic generated **2x2 nonsingular integer linear systems** so the inference-capacity comparison stays interpretable.

The experiment records:
- exact learned parameter-count parity
- exact layer-shape parity
- exact dense weighted-sum proxy parity
- direct verified numeric-answer coverage
- direct solution RMSE and equation residuals
- structural proposal and verified coverage
- near-negative proposal false routes
- compiler-gated final false routes
- learned model wall-clock as diagnostic only
- deterministic solver and verifier steps separately

The direct model gets no compiler or solver output during inference. A deterministic compiler is used only on the evaluation side to construct a reference representation for answer verification.

Inference capacity is matched, but supervision cardinality is not: the structural model sees the same positive systems plus paired unsupported near-negatives so it can learn abstention. This boundary is explicit in the experiment contract.

See `docs/experiments/v0.0.29.md`.

### Previous measured results

v0.0.28:
- neural fitted weight/bias scalars: **7,858**
- logistic fitted coefficient/intercept scalars: **1,962**
- neural/logistic parameter ratio: **4.005x**
- neural/logistic arithmetic-proxy ratio: **4.052x**
- neural known proposal and end-to-end verified coverage: **1.0**
- unsupported proposal false-route: logistic **0.10**, neural **0.0**
- unsupported final false-route after compiler gate: **0.0 for both**
- 8 repeated exact neural uses: **8.0x** learned-work amortization

v0.0.27:
- logistic coefficient/intercept scalars: **1,962**
- known proposal and end-to-end verified coverage: **1.0**
- unsupported proposal false-route rate: **0.10**
- unsupported final false-route rate after compiler gate: **0.0**
- mean sparse score-term proxy: **60.17**

v0.0.26:
- verified answer equivalence: **1.0**
- representation-step reduction for 8 repeated executions: **8 -> 1**
- mean representation/raw byte ratio: **3.86** (representation is larger)

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
    python benchmark_v029.py

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.