# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal / competence signal → deterministic family compiler → solver-ready IR → family registry → family-owned solver/verifier → answer + evidence + cost ledger

## Current engineering baseline

**v0.0.11**

Implemented:
- typed problem / representation / result objects
- learned proposal + deterministic compiler acceptance
- complete controlled IR compilers for matching and square linear systems
- **Family Adapter Contract v1**
- **Family Registry**
- **family-owned solver + answer verifier execution**
- **conformance harness for valid/reject fixtures**
- fail-closed UNKNOWN path
- CI-backed tests and benchmark smoke

## v0.0.11 focus

NEUMANN is moving from a monolithic prototype toward an extensible runtime.

A family adapter bundles:

- `family_id`
- IR kind
- compiler
- solver
- answer verifier
- contract version

Contract version:

`neumann.family.v1`

The registry enforces uniqueness and runtime shape checks, while the conformance harness measures:

- valid compile rate
- valid solved+verified rate
- reject fail-closed rate

### Known blocker

The current `IRKind` is still a closed Python Enum.

That means a truly external plugin cannot introduce a new representation kind without modifying NEUMANN core.

So v0.0.11 is **not yet a fully open plugin system**.

The next compatibility problem is to migrate toward an open namespaced kind identifier without breaking safety.

See `docs/experiments/v0.0.11.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v011.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Family execution should be adapter-owned and independently conformant**
- **Traditional algorithms are first-class execution backends**
- **Do not hide ecosystem blockers behind a plugin-shaped API**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.
