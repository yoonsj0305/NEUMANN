# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal → deterministic compiler → solver-ready IR → family registry → authorized solver/verifier → answer + evidence

## Current engineering baseline

**v0.0.16**

Implemented:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract v1 + conformance harness
- Plugin Manifest v1 + static installed-package discovery
- fresh-venv cross-distribution interoperability
- **digest-bound plugin approval ledger**
- **use-time authorization checks**
- **runtime revocation and re-approval**
- fail-closed UNKNOWN / authorization denial paths
- CI-backed tests and interoperability checks

## v0.0.16 focus

Activation is no longer treated as permanent authority.

Approval is bound to the exact canonical manifest SHA-256:

    plugin_id + manifest_digest_sha256

A changed manifest requires a new approval.

The managed execution path is:

    static discovery
      → explicit approval
      → authorized activation
      → managed plugin registration
      → use-time authorization check
      → solver

ManagedPluginRegistry checks authorization every time RegistryEngine requests an external family.

This means revocation can stop the next solver action even when the Python module is already imported.

CI verifies:
- unapproved activation does not reach the resolver/import boundary
- exact approved digest can activate
- changed manifest digest is blocked
- approved external plugin executes
- revoke is recorded
- next execution fails closed
- solver call count increases by **0** after revocation
- re-approval restores execution

### Important boundary

The authorization ledger is currently in-memory and unauthenticated.

Revocation means NEUMANN managed-runtime execution authority is withdrawn. It does not unload already imported Python code or provide OS/process sandboxing.

Still missing:
- durable/tamper-evident ledger storage
- cryptographic publisher identity
- distributed policy consistency
- OS/process isolation
- dependency sandboxing
- revocation distribution across multiple hosts

See docs/experiments/v0.0.16.md.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v016.py

The fresh-venv external-plugin authorization proof is also executed by GitHub Actions.

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Discovery must not imply import**
- **Activation must not imply permanent authority**
- **Authorization is bound to exact manifest identity**
- **Revocation is checked at use time**
- **Post-revocation solver actions should be zero in the managed path**
- **Do not claim security properties that are not enforced**

## Status

Research prototype. Not production-ready.