# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal / competence signal → deterministic family compiler → solver-ready IR → family registry → family-owned solver/verifier → answer + evidence + cost ledger

## Current engineering baseline

**v0.0.12**

Implemented:
- learned proposal + deterministic compiler acceptance
- complete controlled IR compilers for matching and square linear systems
- Family Adapter Contract v1
- Family Registry + conformance harness
- **open namespaced representation kinds for external families**
- backward compatibility for legacy core IRKind values
- family-owned solver/verifier execution
- fail-closed UNKNOWN path
- CI-backed tests and benchmark smoke

## v0.0.12 focus

v0.0.11 had a real ecosystem blocker: IRKind was a closed Python Enum.

v0.0.12 keeps that enum for backward compatibility, but opens the runtime kind namespace.

Core enum kinds are projected into reserved identifiers such as:

    core.bipartite_matching
    core.linear_system

External families may use namespaced string kinds such as:

    example.scalar_sum
    vendor.some_family

The core.* namespace is reserved.

The v0.0.12 benchmark defines an external scalar-sum family with its own compiler, solver, and verifier. It registers and executes without adding an IRKind enum member.

This proves a runtime extension point, not yet a complete plugin distribution ecosystem.

Still missing:
- package discovery
- signed manifests
- capability/permission declarations
- dependency isolation and sandboxing
- richer version negotiation
- public plugin registry/index
- supply-chain security

See `docs/experiments/v0.0.12.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v012.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Core compatibility should not close the extension namespace**
- **External kinds must be namespaced**
- **Family execution should be adapter-owned and conformant**
- **Do not call a runtime extension point a mature plugin ecosystem until discovery and supply-chain boundaries exist**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.
