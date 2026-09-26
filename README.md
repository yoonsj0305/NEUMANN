# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.19**

NEUMANN now has an explicit plugin trust model and a first out-of-process execution boundary.

Implemented through v0.0.19:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract + conformance harness
- static manifests and installed-package discovery
- digest-bound approval + use-time revocation
- durable hash-chained authorization ledger
- machine-readable Threat Model v1
- **out-of-process plugin compiler/solver/verifier execution**
- **JSON RPC request/response boundary**
- **timeout/crash fail-closed behavior**
- **fresh-venv external wheel isolation proof**

## v0.0.19 focus

Threat Model v1 identified the largest uncontained runtime gap:

    approved plugin code executed inside the NEUMANN core Python process

v0.0.19 moves external family execution behind a child-process boundary.

Core process owns:
- manifest discovery
- authorization ledger
- ManagedPluginRegistry
- RegistryEngine
- RPC proxy

Child process owns:
- plugin import
- adapter factory
- compiler operation
- solver operation
- verifier operation

Each operation currently runs in a fresh child Python process.

### Protocol

    neumann.plugin.rpc.v1

Current bounds:
- request: 64 KiB
- response: 256 KiB
- configurable operation timeout
- JSON-serializable payloads only

Authorization is checked **immediately before every child launch**.

CI tests prove:
- adapter creation does not import the plugin in the core process
- compiler / solver / verifier run in child PIDs
- plugin module remains absent from parent `sys.modules`
- child `os.environ` mutation does not mutate parent environment
- compiler timeout fails closed
- compiler crash fails closed
- solver timeout fails closed
- verifier crash fails closed
- revoke before the next request causes **0 new child launches**
- external plugin wheel in a fresh venv follows the same out-of-process path

### Critical boundary

**This is process separation, not an OS sandbox.**

The child still runs as the same OS user and may retain normal filesystem, process, and network permissions.

v0.0.19 therefore supports claims about:
- Python runtime / address-space separation
- killable timeout/crash boundary
- no direct plugin import into core process
- revocation before dispatch

It does **not** support claims about:
- hostile-code-safe sandboxing
- filesystem isolation
- network isolation
- child-process descendant containment
- publisher authenticity
- defense against a compromised host or core process

See:
- `docs/THREAT_MODEL.md` for the pre-v0.0.19 threat baseline
- `docs/experiments/v0.0.19.md` for the isolation experiment

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v019.py

## Next trust-plane question

If v0.0.19 evidence holds, the next threat-model revision should distinguish:

    process separation
        from
    OS-level sandboxing

and decide whether the next control is host capability restriction, publisher identity, or both.

## Status

Research prototype. Not production-ready.