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

**v0.0.35 — Compression Utility / Value-of-Reduction Oracle**

v0.0.35 replaces generator-reference imitation as the primary optimization target with measured downstream solver-work utility:

    VoR(c | R)
        = solver_ops(R) - solver_ops(R ∪ {c})

It separates:

- validity,
- computational utility,
- stopping,

while keeping every learned or heuristic proposal advisory under the deterministic checker.

The experiment used a new split disjoint from every v0.0.33/v0.0.34 signature:

- calibration: **192 systems**
- final: **256 systems**
- verified retention: **100% for every method**
- unsafe accepted reductions: **0**
- `KEEP = true`

### First measured result

Full-system baseline:

- mean solver ops: **1960.09**

Dynamic greedy marginal-utility teacher:

- mean solver ops: **161.50**
- mean solver savings: **1798.60**
- mean accepted eliminations: **11.07**
- mean retained dimension: **3.93**
- mean trial materializations: **277.21**

Strongest cheap deterministic baseline, **target-leaf**:

- mean solver ops: **210.37**
- mean solver savings: **1749.73**
- dynamic-vs-target solver-savings delta: **+48.87**
- target-leaf recovered **97.28%** of dynamic greedy solver savings

Other key results:

- Markowitz: **244.03 mean solver ops**
- utility-calibrated frozen learned-reference MLP: **384.51**
- static isolated utility: **780.02**

Dynamic state-aware utility beat static isolated utility by:

- **+618.52 mean solver savings**

The interaction gap grew strongly with apparent dimension. At `n=32` it reached:

- `k=2`: **2094.75**
- `k=4`: **1821.13**

Therefore:

> **Value-of-Reduction is strongly state-dependent on this benchmark family.**

A candidate that looks useful in isolation is not an adequate substitute for evaluating its marginal value after earlier reductions.

### Teacher-search cost boundary

The dynamic oracle is intentionally **not** a deployable inference policy.

Its successful trial materializations alone consumed on average:

- **104,298.70 trial solver ops per example**

That is about **53.2×** the original full-system solver-work baseline, before counting partial work from failed materializations.

The full v0.0.35 benchmark took approximately **618.9 s** on the first GitHub Actions run.

Therefore the result supports a teacher/distillation role only, not end-to-end efficiency.

### Architecture consequence

The cheapest mechanism already captures most of the downstream value:

    target-leaf
        -> deterministic checker
        -> ~97.3% of dynamic teacher savings

The next research step should therefore not replace target-leaf wholesale with a larger learned policy.

The preferred sequence is:

    cheap deterministic compression
        ↓
    residual state-aware utility only where value remains
        ↓
    deterministic checker
        ↓
    exact execution + original-problem verification

This makes the next target **residual Value-of-Reduction**, with learned residual prediction considered only after the cheap-first residual contract is measured.

See:
- `docs/experiments/v0.0.34.md`
- `docs/experiments/v0.0.35.md`

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