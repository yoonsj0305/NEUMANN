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

**v0.0.34 — Structural Baseline Gauntlet + Confidence Stopping**

v0.0.34 removes the v0.0.33 oracle-cardinality scaffold.

Final inference receives neither (k) nor (n-k).

Each method uses one global threshold calibrated on a disjoint 192-example calibration set, then runs unchanged on 256 final examples.

The frozen learned scorer remains:

- 16 features
- 16 hidden units
- 289 fitted weight+bias scalars
- same v0.0.33 training corpus

Pre-registered deterministic controls include:

- random ranking
- target-leaf
- row-sparsity
- sparsity + incidence
- dependency contrast
- Markowitz-style local fill
- fixed structural combo

All proposals remain advisory:

    score
      -> threshold stopping
      -> deterministic checker
      -> exact retained solve
      -> reconstruction
      -> verify ORIGINAL full problem

### Reproducibility freeze

Cross-run numerical drift was detected before release and was not accepted.

The final CI pins the numerical stack, hash seed, BLAS thread count, and OpenBLAS CPU kernel.

Final learned scorer SHA-256:

`f9c1dccd0bda28619cb74c6fd6e8a457cde96944cbe5bfa65c9665859da3cc69`

Two independent final-head runners reproduced the same fingerprint, threshold, calibration metrics, and final aggregates.

### First measured result

- core pytest: **176 passed, 1 skipped**
- sequence lane: **PASS**
- final verified retention: **100% for every method**
- unsafe accepted reductions: **0 for every method**
- `KEEP = true`

Learned MLP:

- threshold: **0.40**
- final proposal precision: **91.04%**
- recall: **94.27%**
- F1: **92.63%**
- mean solver ops after certified compression: **442.23**
- mean solver savings vs full baseline: **1529.42**

Best deterministic proposal F1 among the pre-registered heuristics:

**Markowitz**

- proposal F1: **77.86%**
- mean solver ops: **387.31**
- retained-dimension MAE: **4.09**
- exact reference-retained-dimension match: **35.94%**

Highest downstream solver savings:

**Target-leaf heuristic**

- proposal F1: **74.00%**
- mean solver ops: **325.13**
- mean solver savings: **1646.52**

The full-system baseline averaged **1971.66 solver arithmetic operations**.

### Central negative result

The learned scorer is best at reproducing the generator's dependency-reference labels.

It is **not** best at the actual downstream objective of reducing verified solver work.

Therefore:

> **better oracle-rule classification does not imply better Structural Compression.**

This shifts NEUMANN's next target from candidate-label imitation to **Compression Utility / Value-of-Reduction**.

The next system should treat:

- validity,
- computational utility,
- stopping / minimality

as separate primitives.

Simple deterministic structural heuristics are now first-class baselines/components rather than merely controls.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/experiments/v0.0.32.md`
- `docs/experiments/v0.0.33.md`
- `docs/experiments/v0.0.34.md`

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