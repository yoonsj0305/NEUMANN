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

v0.0.37 asked whether a learned residual policy is still justified after the
cheap-first Structural Compression path discovered in v0.0.36.

Frozen first stage:

    target-leaf @ 0.10
        ↓
    deterministic checker

The experiment then compared:

- Ridge residual regression,
- an 8-hidden-unit state-aware MLP,
- cheap residual structural heuristics,
- an exact one-step greedy marginal-utility teacher.

Data:

- train: **96 systems**
- validation: **64 systems**
- final: **192 systems**
- all splits disjoint from v0.0.33–v0.0.36 and from one another
- final verified retention: **100% for every deployable method**
- unsafe accepted reductions: **0**
- `KEEP = true`

### Learned result

Validation selected the tiny MLP:

- state features: **22**
- hidden units: **8**
- fitted weight+bias scalars: **193**
- threshold: **0.10**

On untouched final data:

- frozen target-leaf solver ops: **209.41**
- exact one-step greedy teacher solver ops: **53.21**
- tiny MLP solver ops: **59.93**
- tiny MLP residual-value recovery: **95.70%**

The learned model was therefore genuinely effective.

### But the learned component was deleted

Validation selected a deterministic **Markowitz residual policy @ 0.05** under
the pre-registered tie-break.

On untouched final data:

- Markowitz solver ops: **46.22**
- Markowitz residual-value recovery vs greedy teacher: **104.47%**
- mean attempted proposals: **8.56**
- verified retention: **100%**
- unsafe accepted reductions: **0**

Pre-registered decision:

    KEEP_DETERMINISTIC_RESIDUAL

The MLP passed the >=70% recovery gate but failed the requirement to beat the
best deterministic residual policy by at least 10% of teacher residual value.

Its measured learned advantage fraction was:

    -8.77%

Therefore the neural residual branch is not part of the current deployable
architecture for this family.

### Greedy teacher correction

The exact marginal-utility teacher is now explicitly treated as a
**one-step greedy teacher**, not an upper bound.

Several deterministic orderings reached lower final solver work than the greedy
trajectory. This is further evidence that Structural Compression is strongly
path-dependent.

Final data did **not** change the frozen primary choice. Markowitz remains the
primary deterministic residual policy because it was selected on validation
before the final set was opened.

### Current affine-family architecture

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
    original-problem verification

### Research consequence

Do not increase neural capacity on this affine-linear benchmark family.

The family is now too friendly to local sparse-elimination heuristics for more
learned optimization to be justified.

The next Structural Compression experiment should move to a harder family with
nonlocal interactions, symmetry/equivalent-state compression, long-range
redundancy, or mixed-family routing, while preserving cheap structural methods
as first-class baselines.

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