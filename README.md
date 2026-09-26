# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal → deterministic compiler → solver-ready IR → family registry → family-owned solver/verifier → answer + evidence

## Current engineering baseline

**v0.0.15**

Implemented:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract v1 + conformance harness
- Plugin Manifest v1 + static Plugin Catalog
- static installed-package manifest discovery
- explicit Python plugin activation
- **fresh-venv cross-distribution interoperability proof**
- fail-closed UNKNOWN path
- CI-backed tests and interoperability checks

## v0.0.15 focus

v0.0.15 moves beyond fake distribution objects.

The repository contains a separate external Python distribution used only for interoperability testing:

    neumann-example-scalar-sum

CI builds two independent wheels:

    neumann1-0.0.15-*.whl
    neumann_example_scalar_sum-0.1.0-*.whl

Then it creates a fresh virtual environment, installs both wheels, and starts a new Python process.

The interoperability proof verifies:
- the external plugin module is not imported before discovery
- its static manifest is discovered from installed distribution metadata
- catalog creation does not import plugin code
- explicit activation imports the plugin
- the external FamilyAdapter registers without modifying core IRKind
- raw input executes through RegistryEngine
- result verification succeeds
- the same family conformance contract passes

### Important boundary

This is real cross-distribution interoperability, but the external package source still lives in the same Git repository because the current GitHub connector cannot create another repository.

It is therefore not yet evidence of:
- independently maintained repository interoperability
- independently published PyPI compatibility
- publisher authenticity
- sandboxing
- dependency isolation

See docs/experiments/v0.0.15.md.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v014.py

The fresh-venv cross-package proof is executed by GitHub Actions.

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Discovery must not imply import**
- **Activation must be explicit**
- **Cross-package claims require clean-environment evidence**
- **Installation is not trust**
- **Do not claim security properties that are not enforced**
- **Do not claim capability that the benchmark has not demonstrated**

## Status

Research prototype. Not production-ready.