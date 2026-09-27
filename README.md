# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.31**

v0.0.30 gave the Direct shallow-MLP path up to 16x more positive training data and up to 8x the learned inference arithmetic proxy, plus integer rounding and an exact 81-class formulation. No Direct break-even was observed inside that pre-registered frontier.

v0.0.31 attacks the strongest remaining simple explanation:

> perhaps Direct failed because a fixed-position MLP is the wrong sequence/algorithmic inductive bias.

The new experiment uses a small learned Transformer and matches Direct and Structural much more tightly.

Both paths use the exact same:
- categorical tokenization
- numeric scalar channel
- learned token embeddings
- learned positional embeddings
- 2 Transformer encoder layers
- d_model = 64
- 4 attention heads
- feed-forward width = 128
- identical 82-way output head
- 12 fixed training epochs
- total training cardinality = 8,192

Direct receives **8,192 unique solved positive systems**.

Structural receives:
- 4,096 positive systems
- 4,096 paired near-negatives

So Direct is deliberately favored with twice as many positive solved examples while total training cardinality stays equal.

Direct:

    raw text
      -> Tiny Transformer
      -> one of 81 exact solution-pair classes
      -> evaluation verifier

Structural:

    raw text
      -> identical Tiny Transformer
      -> LINEAR / abstain semantics
      -> deterministic compiler
      -> Gaussian elimination
      -> deterministic verifier

The compiler is unavailable to Direct inference. It is used there only as an evaluation oracle.

PyTorch remains an **experiment-only dependency**. It is installed in a separate CI job and is not added to the NEUMANN core wheel dependencies.

See `docs/experiments/v0.0.31.md`.

### Previous measured results

v0.0.30:
- pytest: **155 passed**
- pre-registered Direct cells: **12**
- Structural final verified coverage: **243/243 = 100%**
- validation-best Direct: **2048 examples, width 64, rounded regression**
- validation-best Direct verified coverage: **26/243 = 10.70%**
- validation-selected Direct final coverage: **20/243 = 8.23%**
- descriptive best pre-registered final Direct: **28/243 = 11.52%**
- best 81-class Direct final coverage: **24/243 = 9.88%**
- Direct break-even reached: **no**

v0.0.29:
- learned architecture for both paths: **640 -> 8 -> 2**
- parameter count: **5,146 vs 5,146**
- dense weighted-sum proxy: **5,136 vs 5,136**
- Structural final verified coverage: **1.0**
- Direct raw-regression final verified coverage: **0.0**

v0.0.28:
- neural/logistic parameter ratio: **4.005x**
- neural/logistic arithmetic-proxy ratio: **4.052x**
- neural known proposal and end-to-end verified coverage: **1.0**
- unsupported final false-route after compiler gate: **0.0 for both**

v0.0.27:
- logistic coefficient/intercept scalars: **1,962**
- known proposal and end-to-end verified coverage: **1.0**
- unsupported final false-route after compiler gate: **0.0**

v0.0.26:
- verified answer equivalence: **1.0**
- representation-step reduction for 8 repeated executions: **8 -> 1**

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
    # v0.0.31 requires optional CPU PyTorch in its separate CI job
    python benchmark_v031.py

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.