# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal → deterministic compiler → solver-ready IR → family registry → family-owned solver/verifier → answer + evidence

## Current engineering baseline

**v0.0.14**

Implemented:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract v1 + conformance harness
- Plugin Manifest v1 + static Plugin Catalog
- explicit activation boundary
- **static installed-package manifest discovery**
- fail-closed UNKNOWN path
- CI-backed tests and benchmark smoke

## v0.0.14 focus

Installed Python distributions can now advertise NEUMANN manifests by shipping JSON files under a path segment named:

    neumann_plugins/

Discovery uses importlib.metadata distribution file listings and reads those static JSON files directly.

It does **not** resolve or import the plugin entry point.

Rules:
- only JSON under a neumann_plugins path segment is considered
- manifest size is capped at 64 KiB by default
- malformed or oversized manifests become DiscoveryIssue records
- one bad distribution does not abort every other discovery
- duplicate plugin/family/kind conflicts are not silently resolved
- distribution name/version/path and manifest digest are retained as provenance

This is package discovery, not package trust. A malicious package that is already installed is still installed code.

Still missing:
- interoperability test with an independently published package
- signatures / publisher identity
- isolated installation and dependency resolution
- post-import sandboxing
- revocation / trust store
- public registry/index

See `docs/experiments/v0.0.14.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v014.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Discovery must not imply import**
- **Installation is not trust**
- **Static metadata errors should be auditable, not silently ignored**
- **Do not claim security properties that are not enforced**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.
