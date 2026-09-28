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

**v0.0.37 — Smallest Adequate State-Aware Residual Predictor**

v0.0.37 tested whether a learned residual policy is justified after the
v0.0.36 cheap-first architecture.

The first stage remained frozen:

    target-leaf @ 0.10
        ↓
    deterministic checker

The residual stage compared:

- Ridge regression, 23 fitted weight+bias scalars
- tiny MLP, 8 hidden units / 193 fitted weight+bias scalars
- target-leaf residual
- Markowitz residual
- dependency-contrast residual
- structural-combo residual
- exact state-aware marginal-utility teacher

The learned target was exact downstream marginal solver-work gain, not
generator dependency identity.

Data:

- train: **96 systems**
- validation: **64 systems**
- untouched final: **192 systems**
- all splits disjoint from v0.0.33-v0.0.36 and from one another
- core pytest: **196 passed, 1 skipped**
- verified retention: **100% for every deployable method**
- unsafe accepted reductions: **0**
- `KEEP = true`

### Validation-only selection

Selected learned residual:

    tiny MLP @ threshold 0.10
    validation teacher-value recovery = 101.02%

Selected deterministic residual:

    Markowitz @ threshold 0.05
    validation teacher-value recovery = 103.91%

No final result participated in model or threshold selection.

### Untouched final result

Frozen first-stage target-leaf:

- mean solver ops: **209.41**

Exact residual teacher:

- mean final solver ops: **53.21**
- mean residual additional savings: **156.20**

Selected tiny MLP:

- mean final solver ops: **59.93**
- mean residual additional savings: **149.48**
- teacher-value recovery: **95.70%**

Selected Markowitz residual:

- mean final solver ops: **46.22**
- mean residual additional savings: **163.18**
- teacher-value recovery: **104.47%**

The learned policy passed the pre-registered 70% recovery gate, but failed the
required value-add gate over the selected deterministic residual:

    learned advantage fraction
        = -8.77% of teacher residual value

Decision:

    KEEP_DETERMINISTIC_RESIDUAL

The learned residual branch is therefore rejected for this family.

### Architecture consequence

The currently justified path is:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker
        ↓
    exact retained solve
        ↓
    reconstruction
        ↓
    verify ORIGINAL problem

This result is important because the tiny MLP did learn the residual objective
well. It recovered about **95.7%** of the exact greedy teacher's final residual
value.

It is still unnecessary.

A cheaper deterministic structural rule performed better on the
pre-registered primary comparison.

### Benchmark saturation warning

On the untouched final set, dependency-contrast descriptively reached
**44.81 mean solver ops**, slightly below the validation-selected Markowitz
policy. It is not promoted to the primary winner because it was not selected by
the validation protocol.

Together with the repeated strength of target-leaf, Markowitz, and related
heuristics, this indicates that the current affine-linear generator is becoming
saturated by local structural rules.

The next step is therefore **not** a larger neural residual model.

The preferred v0.0.38 direction is a **Harder Structural Family Gate** with
non-local compression motifs such as coupled multi-row dependencies,
relation-level redundancy, equivalence/symmetry structure, and adversarial
local-incidence decoys.

A learned component may return only if it creates pre-registered downstream
value beyond deterministic structural algorithms on an untouched harder
family.

See:
- `docs/experiments/v0.0.35.md`
- `docs/experiments/v0.0.36.md`
- `docs/experiments/v0.0.37.md`

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