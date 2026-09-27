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

**v0.0.31 FROZEN**

The next pre-registered research milestone is **v0.0.32 — Structural Compression Contract + Oracle Lower Bound**.

v0.0.32 deliberately does **not** start with a learned compressor. It first measures the achievable reduction on generated systems whose true dependency structure is known by construction, while requiring reconstruction and verification against the original full problem.

This separates three questions that must not be conflated:

1. does a valid compression opportunity exist?
2. can it change deterministic solver-work scaling?
3. can a learned system discover enough of that compression safely?

Only the first two belong to v0.0.32. Learned Structural Compression is reserved for the next milestone if the oracle benchmark justifies it.

### Frozen enabling result

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

First measured v0.0.31 result:
- core pytest: **155 passed, 1 skipped**
- sequence contract tests: **4 passed**
- CPU PyTorch: **2.14.0+cpu**
- Direct / Structural parameters: **75,538 / 75,538**
- parameter bytes: **302,152 / 302,152**
- identical 82-way heads
- identical learned arithmetic proxy on matched inputs
- total training examples: **8,192 / 8,192**
- Direct solved-positive examples: **8,192**
- Structural positives / near-negatives: **4,096 / 4,096**
- Direct validation verified: **29/243 = 11.93%**
- Direct final verified: **31/243 = 12.76%**
- matched Structural validation verified: **243/243 = 100%**
- matched Structural final verified: **243/243 = 100%**
- Structural near-negative proposal false routes: **0%**
- Structural compiler-gated false routes: **0%**
- frozen v0.0.29 MLP Structural on the new final split: **242/243 = 99.59%**
- KEEP decision: **true**

An early contract-only run caught text collisions with previous generated corpora before the full quality benchmark executed. The generator now enforces explicit forbidden-text exclusion; the successful v0.0.31 train/validation/final sets are mutually disjoint and disjoint from v0.0.29/v0.0.30.

This weakens the simple explanation that the earlier Direct gap was only a shallow-MLP inductive-bias artifact. It remains a narrow task-specific quality result, not a total-compute or frontier-LLM efficiency claim.

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