# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

The core idea is simple:

```text
Problem
  → Representation / Structure Formation
  → Choose the cheapest correct execution path
  → Deterministic or neural solver
  → Verification
  → Answer + evidence + cost ledger
```

NEUMANN is not trying to make an LLM perform every calculation itself. It aims to separate what learned models are good at from what traditional algorithms and formal solvers already do faster and more reliably.

## Current engineering baseline

**v0.0.5**

Implemented:

- typed problem / representation / result objects
- bipartite-matching solver
- shortest-path solver
- linear-system solver
- deterministic answer verification
- benchmark-only semantic contract verification
- learned structure-family classifier
- two-stage open-set / UNKNOWN gate
- cost ledger and execution trace
- held-out / hard-negative tests

Current test status:

```text
14 PASS
0 FAIL
```

## Important boundary

v0.0.5 does **not** yet understand arbitrary natural-language problems.

The learned model currently predicts only a coarse structure family:

- `bipartite_matching`
- `shortest_path`
- `linear_system`
- `unknown`

Complete solver-ready IR generation, semantic equivalence from raw language, and general LLM-backed structure formation are future work.

## Research ↔ Engineering loop

NEUMANN is developed through a continuous loop:

```text
research hypothesis
    ↓
minimal implementation
    ↓
measured gain or failure
    ↓
interpretation
    ↓
KEEP / MODIFY / KILL
    ↓
next experiment
```

Research results are tracked separately in the project research log; this repository is the source of truth for executable code, tests, benchmarks, and versioned engineering evidence.

## Run

Requires Python 3.10+.

```bash
pip install -e .
pytest -q
python benchmark_v005.py
```

## Current research questions

1. When does representation-first hybrid execution actually beat direct solving after representation, routing, solving, verification, and recovery costs are all counted?
2. Can the system recognize when a problem is outside its supported structural competence?
3. Can a learned Structure Former eventually produce complete, semantically faithful IRs from natural language?
4. How often do directly reusable reasoning structures occur in naturally occurring heterogeneous task streams?

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Traditional algorithms are first-class execution backends**
- **A faster solver is useless if representation and verification overhead erase the gain**
- **Answer correctness and representation fidelity are separate checks**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.

