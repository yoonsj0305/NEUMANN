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

v0.0.34 removes the v0.0.33 oracle-cardinality scaffold from final inference.

No final method receives:

    k
    n - k
    a fixed proposal count

Instead, each scorer receives one global confidence threshold selected on a disjoint labeled calibration set and proposes every candidate above that threshold.

The deterministic checker retains authority over every reduction.

### Data / reproducibility

- calibration examples: **192**
- final examples: **256**
- all v0.0.34 signatures disjoint from v0.0.33
- calibration/final mutually disjoint
- frozen v0.0.33 checkpoint: **289 fitted MLP weight+bias scalars**
- immutable checkpoint SHA-256:
  `f9c1dccd0bda28619cb74c6fd6e8a457cde96944cbe5bfa65c9665859da3cc69`
- two independent final CI executions reproduced the same learned threshold and aggregate exactly
- core pytest: **176 passed, 1 skipped**
- all benchmark, wheel, sequence, and fresh-venv checks: **PASS**
- KEEP: **true**

### Learned no-cardinality stopping result

Calibration selected:

    learned threshold = 0.40

Final:

- raw proposal precision: **91.04%**
- raw proposal recall: **94.27%**
- raw proposal F1: **92.63%**
- mean accepted eliminations: **7.492**
- retained-dimension MAE vs generator k: **4.508**
- exact generator-k match: **31.25%**
- mean post-compression solver ops: **442.23**
- mean solver savings vs baseline: **1,529.42**
- mean generator-reference solver-savings recovery: **83.01%**
- verified retention: **100%**
- unsafe accepted reductions: **0**

This establishes that the frozen learned scorer can stop without receiving oracle cardinality at final inference in the controlled family.

### Main falsification result

The learned scorer is the best **reference-rule classifier**, but it is not the best **computational compression policy**.

| Method | Raw proposal F1 | Retained-dim MAE | Mean solver ops | Mean solver savings |
|---|---:|---:|---:|---:|
| Learned MLP | **92.63%** | 4.508 | 442.23 | 1,529.42 |
| Markowitz-style | 77.86% | **4.086** | 387.31 | 1,584.34 |
| Target-leaf | 74.00% | 4.324 | **325.13** | **1,646.52** |
| Sparsity + incidence | 67.73% | 5.305 | 418.91 | 1,552.75 |
| Deterministic random | 59.64% | 5.902 | 601.53 | 1,370.13 |

All listed methods retain **100% verified original-problem correctness** with **0 unsafe accepted reductions**.

Markowitz beats learned scoring on mean solver savings by **54.92 arithmetic ops** despite having much lower reference-rule F1.

Target-leaf is an even stronger computational counterexample: it has only **74.00%** raw reference F1 but the lowest mean solver work and largest mean solver savings in the gauntlet.

At n=32:

    k=2
      learned      1192.19 solver ops
      Markowitz    1083.91
      target-leaf   667.00

    k=4
      learned      1530.16 solver ops
      Markowitz    1203.53
      target-leaf   801.34

### Research consequence

v0.0.34 changes the optimization target.

The project should no longer treat:

    "match the generator dependency certificate"

as the primary objective.

The emerging objective is:

    valid reduction
        ↓
    verified equivalence
        ↓
    marginal computational utility

Reference-certificate recovery remains a diagnostic, not the final target.

This also reinforces that the generator dependency DAG is a reference certificate rather than a unique global optimum: a small number of non-reference reductions were deterministically verified as valid.

### Important boundaries

v0.0.34 still does not establish:

- globally minimal structure,
- total end-to-end compute superiority,
- domain-general Structural Compression,
- natural-language compression,
- asymptotic complexity improvement.

Thresholds are still calibrated using labeled generator-reference data.

Solver work, learned scoring work, checker work, reconstruction, and verification remain separate cost categories.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/experiments/v0.0.32.md`
- `docs/experiments/v0.0.33.md`
- `docs/experiments/v0.0.34.md`

### Next research gate

**v0.0.35 candidate: Utility-Directed Structural Compression**

Rather than training primarily against reference-rule identity:

- freeze Markowitz and target-leaf as first-class baselines,
- measure marginal verified solver-work reduction per candidate,
- compare deterministic, learned, and hybrid utility-directed policies,
- include checker / reconstruction / verification costs explicitly,
- preserve fail-closed deterministic reduction authority.

NEUMANN should absorb the cheapest mechanism that works rather than defend a learned component for its own sake.

### Frozen enabling results

**v0.0.33**

- oracle-cardinality learned proposal experiment
- final verified retention: **100%**
- elimination recovery: **72.02%**
- oracle solver-savings recovery: **84.93%**
- later falsified as insufficient evidence that learned ranking is the best compression policy

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