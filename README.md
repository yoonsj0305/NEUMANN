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

**v0.0.42 — Nonunit parser and residual-incidence peeling**

This experiment tested two deterministic repairs to the v0.0.41 failure
modes on fresh generated exact systems. E1 removes the unit-only 2x2 target
restriction. E2 also peels validated low-incidence blocks from the remaining
row set. Neither method trains a learned block model. The pre-registered
protocol is `docs/experiments/v0.0.42.md`; the fresh 224-system audit passed
and E2 recovered 100% of oracle solver savings on all three active arms.
Run `python benchmark_v042.py` for the audit or `python benchmark_v042_smoke.py`
for a bounded correctness check. E2 examined 1,305.5 row pairs per active
system on average; solver arithmetic savings exclude discovery and checking.

**v0.0.41 — Anti-shortcut causal audit**

The v0.0.40 deterministic result was challenged on three separate
synthetic arms: generic nonunit invertible 2x2 coefficients, cross-block
overlap, and both together. Candidate visibility is measured separately from
verified downstream compression. The audit is pre-registered in
`docs/experiments/v0.0.41.md`; no learned block scorer was trained. The
224-system audit passed its integrity and verification gates. Nonunit block
coefficients exposed a candidate-visibility limit; cross-block overlap
exposed a conflict/selection bottleneck. Run
`python benchmark_v041.py` for the frozen 224-system audit, or
`python benchmark_v041_smoke.py` for a bounded correctness check.

**v0.0.40 — Coupled-Block Discovery / Routing Gauntlet**

v0.0.40 moved from family design to actual structure discovery on a fresh
256-system audit set.

No learned block model was trained.

The validated v0.0.38.1 mixed family was held fixed:

- easy local one-row leaves,
- coupled exact 2x2 blocks,
- generic variable names,
- row/column permutation,
- exact original-problem verification.

The frozen local pipeline remained:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker

v0.0.40 then compared deterministic routing/discovery variants.

### Result

The selected method under the pre-registered tie-break was:

    D4 = incidence router + row/target component graph

It achieved:

- solver-savings recovery: **100%**
- elimination recovery: **100%**
- block precision: **100%**
- block recall: **100%**
- block F1: **100%**
- verified retention: **100%**
- unsafe reductions: **0**

Decision:

    KEEP_DETERMINISTIC_DISCOVERY

Therefore a learned block scorer is **not justified** on this family.

### Performance-equivalent deterministic winners

D2, D3, and D4 all recovered the full measured verified compression value.

D2:

    incidence router
        +
    exact candidate-overlap block discovery

D3:

    incidence router
        +
    sparse shared-unit block discovery

D4:

    incidence router
        +
    2-row / 2-target component graph

All three reached:

    100% solver-savings recovery
    100% elimination recovery
    100% block recall
    100% verified retention

D4 is the formal winner only because the frozen tie-break counted fewer
row-pair examinations.

That does not prove D4 has lower total discovery cost, because D4 instead
examines graph edges and unlike cost units are intentionally kept separate.

### Most important finding: routing before discovery

D1 used the old local-first pipeline before exact block discovery.

It still achieved:

- solver-savings recovery: **98.20%**
- elimination recovery: **95.02%**

but block recall dropped to:

    86.46%

because the local stage consumed coupled targets before block discovery.

Average coupled targets consumed locally:

    D1 = 0.7109
    D2 = 0

After adding a trivial incidence router:

    target incidence == 1
        -> local path

    target incidence > 1
        -> reserve for multi-row path

block recall became:

    100%

with easy-leaf routing precision/recall also:

    100% / 100%

So the current structural lesson is not "use a better block scorer."

It is:

    route structural degrees of freedom correctly
        before
    consuming them with local reductions.

### Current validated architecture on this family

    raw exact system
        ↓
    incidence-aware structural router
        ├── local one-row path
        └── multi-row reserved path
        ↓
    deterministic block discovery
        ↓
    exact independent algebra checker
        ↓
    exact retained solve
        ↓
    reconstruction
        ↓
    original full-system verification

### Saturation boundary

This mixed 2x2 family is now saturated by cheap deterministic structure.

Do not train a block-discovery neural model on it.

The next research family must remove at least one shortcut:

- fixed +/-1 coupled coefficients,
- clean two-row/two-target connected components,
- absence of distractor overlaps,
- absence of cross-block dependencies,
- single block size,
- incidence-perfect routing.

Only if deterministic methods leave pre-registered verified downstream
headroom should learned structural discovery be reconsidered.

See:

- `docs/experiments/v0.0.38.1.md`
- `docs/experiments/v0.0.40.md`

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
