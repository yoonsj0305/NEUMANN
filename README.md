# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.30**

v0.0.29 established the first matched-learned-capacity task comparison:

- Structural learned path: 640 -> 8 -> 2
- Direct learned path: 640 -> 8 -> 2
- learned parameter ratio: 1.0
- learned dense weighted-sum proxy ratio: 1.0
- Structural strict verified coverage: 1.0
- Direct raw-regression strict verified coverage: 0.0

v0.0.30 now tries to **erase that gap** rather than repeat it.

The Direct side receives a pre-registered capacity/data sweep:

Training sizes:

    128, 512, 2048

Hidden widths:

    8, 16, 32, 64

For every cell, NEUMANN trains two Direct models:

1. a two-output numeric regressor
2. a stronger 81-class discrete solution classifier

The regressor is evaluated both raw and after rounding/clipping to the benchmark's known integer support [-4, 4]. This prevents strict floating-point verification from being the only reason Direct loses.

The resulting three Direct challengers are:

    raw regression
    rounded regression
    81-class discrete classification

The Structural reference is frozen at the v0.0.29 configuration:

    640 -> 8 -> 2 structural proposer
      -> deterministic compiler
      -> Gaussian elimination
      -> deterministic verifier

v0.0.30 measures the **break-even frontier**:

> How much Direct learned capacity and training data is required to reach the fixed Structural verified coverage, if any pre-registered configuration reaches it?

The validation split is evaluated before the final split. Final-grid results are descriptive only and cannot retune the sweep.

See `docs/experiments/v0.0.30.md`.

First measured v0.0.30 result:
- pytest: **155 passed**
- Direct grid: **12 pre-registered cells**
- Direct training sizes: **128 / 512 / 2048**
- Direct hidden widths: **8 / 16 / 32 / 64**
- Structural final verified coverage on new 243-system split: **1.0**
- Structural final near-negative proposal false-route: **1/243**
- Structural final compiler-gated false-route: **0**
- best validation Direct: **2048 x 64 rounded regression**
- best validation Direct verified coverage: **10.70%**
- validation break-even: **not reached**
- validation-selected Direct final coverage: **8.23%**
- observed best pre-registered final Direct: **2048 x 16 rounded regression**
- observed best final Direct verified coverage: **11.52%**
- observed final break-even: **not reached**
- best discrete 81-class final coverage: **9.88%**
- raw regression strict verified coverage: **0% in all 12 cells**
- KEEP decision: **true**

The validation-selected Direct model used roughly **8x** the Structural learned parameter state and dense weighted-sum proxy while training on **16x** as many positive systems, but still did not reach the fixed Structural verified coverage.

This is not an 8x total-compute claim. The Structural path additionally executes deterministic compilation and Gaussian elimination, and the two paths have different supervision. The supported statement is narrower: **no Direct break-even was observed inside the pre-registered v0.0.30 frontier.**

### Previous measured results

v0.0.29:
- pytest: **149 passed**
- learned architecture for both paths: **640 -> 8 -> 2**
- parameter count: **5,146 vs 5,146**
- dense weighted-sum proxy: **5,136 vs 5,136**
- Structural final verified coverage: **1.0**
- Direct raw-regression final verified coverage: **0.0**
- Direct solution RMSE: **3.123**
- Structural near-negative compiler-gated false-route: **0.0**

v0.0.28:
- neural fitted weight/bias scalars: **7,858**
- logistic fitted coefficient/intercept scalars: **1,962**
- neural/logistic parameter ratio: **4.005x**
- neural/logistic arithmetic-proxy ratio: **4.052x**
- neural known proposal and end-to-end verified coverage: **1.0**
- unsupported proposal false-route: logistic **0.10**, neural **0.0**
- unsupported final false-route after compiler gate: **0.0 for both**

v0.0.27:
- logistic coefficient/intercept scalars: **1,962**
- known proposal and end-to-end verified coverage: **1.0**
- unsupported final false-route after compiler gate: **0.0**

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
    python benchmark_v030.py

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.