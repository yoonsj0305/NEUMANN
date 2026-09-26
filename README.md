# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

The core idea:

Problem → Representation / Structure Formation → Selective execution policy → Deterministic or neural solver → Verification → Answer + evidence + cost ledger

NEUMANN is not trying to make an LLM perform every calculation itself. It aims to separate what learned models are good at from what traditional algorithms and formal solvers already do faster and more reliably.

## Current engineering baseline

**v0.0.6**

Implemented:
- typed problem / representation / result objects
- bipartite-matching, shortest-path, and linear-system solvers
- deterministic answer verification
- benchmark-only semantic contract verification
- learned structure-family classifier
- two-stage open-set / UNKNOWN gate
- prototype-distance rejection baseline
- structurally-near OOD benchmark
- selective-risk curves
- cost ledger and execution trace

Local test status:

**17 PASS / 0 FAIL**

## v0.0.6 result

On a tiny frozen synthetic fixture:
- two-stage gate: 80% known auto-route coverage, 13.33% near-unknown false-route
- prototype-distance gate: 33.33% known auto-route coverage, 0% near-unknown false-route

This is not a production guarantee. It demonstrates the safety-versus-coverage trade-off that a NEUMANN router must explicitly manage.

See `docs/experiments/v0.0.6.md`.

## Important boundary

v0.0.6 does **not** yet generate complete solver-ready IRs from arbitrary natural language.

The learned path currently recognizes only coarse structure families:
- `bipartite_matching`
- `shortest_path`
- `linear_system`
- `unknown`

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v006.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Traditional algorithms are first-class execution backends**
- **A faster solver is useless if representation and verification overhead erase the gain**
- **Answer correctness and representation fidelity are separate checks**
- **Routing coverage must be chosen against an explicit false-route risk budget**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.