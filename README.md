# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal → deterministic compiler → solver-ready IR → family registry → family-owned solver/verifier → answer + evidence

## Current engineering baseline

**v0.0.13**

Implemented:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract v1 + conformance harness
- **Plugin Manifest v1**
- **static Plugin Catalog**
- **explicit activation boundary**
- pre-import metadata policy for declared capabilities
- fail-closed UNKNOWN path
- CI-backed tests and benchmark smoke

## v0.0.13 focus

The central rule is:

**Discovery != Trust != Execution**

A plugin can now be described by a static manifest:

    neumann.plugin.manifest.v1

The manifest declares:
- plugin ID and version
- family ID
- namespaced representation kind
- family contract version
- entry point
- capabilities

Catalog registration validates metadata and conflict rules **without resolving or importing plugin code**.

Activation is a separate explicit operation:

    manifest
      → policy check
      → resolve entry point
      → factory
      → FamilyAdapter identity check

The default metadata policy blocks plugins declaring network, filesystem.write, or subprocess before resolver code is called.

This is **not a sandbox**. Once imported, code is ordinary Python. Manifest SHA-256 is an audit identity, not a publisher signature.

Still missing:
- installed-package discovery
- cryptographic signatures / publisher identity
- dependency isolation and sandboxing
- capability enforcement after import
- revocation
- public package/index workflow
- multi-version compatibility negotiation

See `docs/experiments/v0.0.13.md`.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v013.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Discovery must not imply code execution**
- **Declared capability policy is not a sandbox**
- **External families must be namespaced and conformant**
- **Do not claim security properties that are not enforced**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.
