# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal / competence signal → deterministic family compiler → solver-ready IR → deterministic or neural solver → verification → answer + evidence + cost ledger

NEUMANN separates what learned models are good at from what traditional algorithms and formal solvers already do faster and more reliably.

## Current engineering baseline

**v0.0.10**

Implemented:
- typed problem / representation / result objects
- bipartite-matching, shortest-path, and linear-system solvers
- deterministic answer verification
- benchmark-side semantic contracts
- learned open-set structure-family recognizer
- structurally-near OOD evaluation and selective-risk curves
- complete controlled IR compilers for matching and square linear systems
- multi-family deterministic routing
- **learned family proposal + deterministic compiler acceptance**
- fail-closed UNKNOWN path
- cost ledger and execution trace

## v0.0.10 focus

The learned model is **not allowed to authorize solver execution by itself**.

It may propose a family, but the corresponding deterministic compiler must independently accept the raw input and emit the same IR family. Otherwise NEUMANN returns UNKNOWN.

    raw problem
        ↓
    learned proposal
        ↓
    authorized family compiler
        ↓
    accept complete IR OR UNKNOWN
        ↓
    solver

This tests a possible scalable pattern for NEUMANN:

**learned proposal + deterministic acceptance**

See `docs/experiments/v0.0.10.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v010.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is a proposal, not authority**
- **Traditional algorithms are first-class execution backends**
- **Answer correctness and representation fidelity are separate checks**
- **Silent partial parsing is a correctness failure**
- **Expand capability one structural family at a time**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.
