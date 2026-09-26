# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → Representation / Structure Formation → Selective execution policy → Deterministic or neural solver → Verification → Answer + evidence + cost ledger

NEUMANN separates what learned models are good at from what traditional algorithms and formal solvers already do faster and more reliably.

## Current engineering baseline

**v0.0.9**

Implemented:
- typed problem / representation / result objects
- bipartite-matching, shortest-path, and linear-system solvers
- deterministic answer verification
- benchmark-only semantic contract verification
- learned structure-family classifier
- two-stage open-set / UNKNOWN gate
- prototype-distance rejection baseline
- structurally-near OOD benchmark and selective-risk curves
- controlled natural-language matching compiler → complete solver-ready IR
- independent matching semantic-contract check
- **fail-closed matching parser diagnostics**
- **edge-level IR precision / recall / F1 measurement**
- cost ledger and execution trace

## v0.0.9 focus

v0.0.9 adds a second complete IR family and tests family-neutral routing.

The matching compiler now fails closed when:
- any nonempty statement is unparsed
- the same left entity is repeated with conflicting rights
- negation / exception / capacity / cost semantics appear
- right-side tokens are outside the controlled identifier grammar

Identical repeated statements are accepted but surfaced in diagnostics.

The goal is intentionally **not** broader language coverage. It is to make silent semantic loss harder.

See `docs/experiments/v0.0.8.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v009.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Traditional algorithms are first-class execution backends**
- **Answer correctness and representation fidelity are separate checks**
- **Routing coverage must be chosen against an explicit false-route risk budget**
- **Silent partial parsing is a correctness failure**
- **Expand capability one structural family at a time, with explicit semantic checks**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.


### v0.0.9 additions
- controlled linear-system compiler → complete A, b, variable-order IR
- composite Structure Former across matching + linear systems
- fail closed if zero or multiple families recognize the same input
- raw-text routing to matching or Gaussian elimination without oracle solver payload

See `docs/experiments/v0.0.9.md`.
