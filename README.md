# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.18**

NEUMANN now has both an execution architecture and an explicit plugin trust model.

Implemented through v0.0.18:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract + conformance harness
- static plugin manifests and installed-package discovery
- fresh-venv cross-distribution interoperability
- digest-bound approval and use-time revocation
- durable hash-chained authorization ledger
- trusted-head rollback detection boundary
- **machine-readable Threat Model v1**
- **assurance labels tied to evidence identifiers**

## v0.0.18 focus

v0.0.18 deliberately does not add another security mechanism.

It freezes the attacker and trust-boundary model first.

Threat actors include:
- malicious plugin publisher
- installed-package tamperer
- local ledger tamperer
- host administrator capable of rollback
- compromised plugin after activation
- compromised NEUMANN process
- compromised checkpoint authority

Each threat scenario declares:
- protected asset
- trust boundary
- PREVENT assurance
- DETECT assurance
- CONTAIN assurance
- RECOVER assurance
- controls
- evidence identifiers
- residual risk

Strong assurance labels require explicit evidence.

### Main result

The existing system is strongest around:
- static discovery
- exact-manifest approval
- managed runtime revocation
- persisted-ledger integrity

The largest uncontained runtime gap is:

**approved plugin code executes inside the NEUMANN Python process.**

Therefore Threat Model v1 selects:

    out_of_process_plugin_isolation

as the next implementation priority.

### Why not signatures first?

Signatures establish identity/authenticity. They do not contain what signed code can do after import.

A perfectly signed malicious or compromised plugin would still run with ordinary Python process authority today.

See:
- `docs/THREAT_MODEL.md`
- `docs/experiments/v0.0.18.md`

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v018.py

## Security claim discipline

NEUMANN currently must **not** claim:
- publisher authenticity
- safe execution of approved plugin code
- sandboxing after import
- defense against a compromised NEUMANN process
- rollback-proof storage without an external trust anchor
- tamper-proof storage

## Next milestone

v0.0.19 should test an **out-of-process plugin execution boundary** with:
- bounded request/response schema
- timeout/crash fail-closed behavior
- revocation before dispatch
- no direct mutation of core in-memory authorization state

## Status

Research prototype. Not production-ready.