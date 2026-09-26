# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → Representation / Structure Formation → Selective execution policy → Deterministic or neural solver → Verification → Answer + evidence + cost ledger

NEUMANN separates what learned models are good at from what traditional algorithms and formal solvers already do faster and more reliably.

## Current engineering baseline

**v0.0.7**

Implemented:
- typed problem / representation / result objects
- bipartite-matching, shortest-path, and linear-system solvers
- deterministic answer verification
- benchmark-only semantic contract verification
- learned structure-family classifier
- two-stage open-set / UNKNOWN gate
- prototype-distance rejection baseline
- structurally-near OOD benchmark and selective-risk curves
- **controlled natural-language matching compiler → complete solver-ready IR**
- independent matching semantic-contract check
- cost ledger and execution trace

Local test status:

**21 PASS / 0 FAIL**

## v0.0.7 result

For one deliberately narrow family, controlled matching statements now run end-to-end:

raw text → matching IR → deterministic matching solver → answer verification

Three surface forms compiled to faithful solver-ready IRs in the frozen toy benchmark, and an unsupported minimum-spanning-tree prompt failed closed.

Important: this is a **controlled grammar compiler**, not general natural-language understanding.

See `docs/experiments/v0.0.7.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v007.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Traditional algorithms are first-class execution backends**
- **Answer correctness and representation fidelity are separate checks**
- **Routing coverage must be chosen against an explicit false-route risk budget**
- **Expand capability one structural family at a time, with explicit semantic checks**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.