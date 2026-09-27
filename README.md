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

**v0.0.33 — Learned Structural Compression Proposal**

v0.0.32 established that an oracle dependency certificate could reduce the retained solver dimension from apparent n to independent core k and substantially alter the solver-work curve.

v0.0.33 asks whether a small learned proposer can recover part of that oracle compression without holding execution authority.

The new corpus removes the obvious v0.0.32 role cues:

- generic observed variable names
- randomized variable order
- randomized equation order
- affine dependencies with offsets
- chained dependencies
- no fixed core/derived row blocks

Learned path:

    full permuted system
      -> fixed candidate enumerator
      -> tiny learned candidate scorer
      -> top-B proposals
      -> deterministic reduction checker
      -> safe retained subsystem
      -> exact solver
      -> reconstruction
      -> verify ORIGINAL full problem

Important scaffold:

    B = n - k

The model is told the oracle elimination cardinality. It predicts **which** reductions to attempt, not **how far** compression should continue.

First measured final result:

- final examples: **256**
- examples with compression opportunity: **224**
- tiny MLP parameters: **289**
- feature dimension: **16**
- hidden width: **16**
- verified retention: **100%**
- unsafe accepted reductions: **0**
- fail-closed rejected proposals: **1,209**
- mean elimination-count recovery: **72.02%**
- mean exact oracle-rule recovery: **71.98%**
- mean oracle solver-savings recovery: **84.93%**
- KEEP: **true**

At k=2,n=32:

    baseline solver ops ≈ 6121.4
    oracle solver ops   = 15
    learned solver ops  ≈ 1302.5
    oracle savings recovered ≈ 78.89%

At k=4,n=32:

    baseline solver ops ≈ 6464.6
    oracle solver ops   ≈ 95.8
    learned solver ops  ≈ 1586.0
    oracle savings recovered ≈ 76.20%

Learned elimination recovery declines with apparent dimension, reaching roughly **54%** at n=32. The learned discovery layer is therefore itself a scaling bottleneck.

The result is deliberately narrow.

It does **not** establish:
- learned discovery of k
- globally minimal structure
- domain-general compression
- natural-language compression
- total-compute superiority

Two post-result diagnostic controls were added before merge:

- deterministic random ranking: **24.40%** elimination recovery
- simple sparsity + target-incidence heuristic: **61.55%**
- learned MLP: **72.02%**

The learned scorer therefore exceeds this particular simple heuristic by about **10.46 percentage points**, while the heuristic itself remains strong. Because these controls were added after the primary result was observed, they are diagnostic rather than pre-registered evidence.

The final-head learned result reproduced exactly across two independent GitHub Actions executions. The next falsification target is a pre-registered stronger heuristic suite plus removal of the oracle-cardinality budget.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/experiments/v0.0.32.md`
- `docs/experiments/v0.0.33.md`

### Frozen enabling results

**v0.0.32**

- oracle Structural Compression benchmark
- full-solution equivalence: **1.0**
- baseline solver finite-range slope: about **2.03–2.14**
- fixed-k oracle-compressed solver slope: about **0**
- explicit certificate byte overhead retained as a negative result

**v0.0.31**

- matched Direct / Structural Tiny Transformers: **75,538 parameters each**
- Direct final verified coverage: **12.76%**
- Structural final verified coverage: **100%**

**v0.0.26–v0.0.30**

Established representation reuse, learned-proposal accounting, authority separation, and direct-vs-structure controlled comparisons.

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