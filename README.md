# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

Core path:

Problem → learned proposal → deterministic compiler → solver-ready IR → family registry → authorized solver/verifier → answer + evidence

## Current engineering baseline

**v0.0.17**

Implemented:
- learned proposal + deterministic compiler acceptance
- open namespaced external family kinds
- Family Adapter Contract v1 + conformance harness
- Plugin Manifest v1 + static installed-package discovery
- fresh-venv cross-distribution interoperability
- digest-bound plugin approval + use-time revocation
- **durable JSONL authorization ledger**
- **SHA-256 hash-chained authorization events**
- **trusted-head rollback/truncation detection**
- fail-closed UNKNOWN / authorization denial / ledger-integrity paths
- CI-backed tests and interoperability checks

## v0.0.17 focus

Authorization state can now survive process restarts.

Each persisted event contains:
- ledger version
- monotonic sequence
- APPROVE / REVOKE action
- plugin ID
- exact manifest digest
- reason
- previous event hash
- current event hash

On reload NEUMANN verifies the entire chain before reconstructing authority state.

Local hash-chain verification detects:
- event mutation
- record reordering
- broken predecessor links
- malformed or partial records

### Rollback boundary

A complete rollback to an older valid ledger prefix is still internally self-consistent.

Therefore v0.0.17 supports a **trusted expected head SHA-256** supplied from outside the ledger file.

With that checkpoint, an older/truncated valid prefix fails closed.

This distinction is deliberate:

    local hash chain
        !=
    rollback-proof storage

Correct claim:
**tamper-evident relative to the stated checkpoint trust boundary**.

CI verifies:
- persisted authorization state survives reload
- reloaded ledger drives ManagedPluginRegistry and RegistryEngine
- event mutation is detected
- event reordering is detected
- whole-event truncation can look valid without a checkpoint
- the same truncation is detected with a trusted expected head
- append-after-reload extends the verified chain
- existing fresh-venv plugin discovery/authorization/revocation remains green

### Important boundary

The persistent ledger is currently single-writer and file-backed.

It does not yet provide:
- multi-process locking
- authenticated operator identity
- signatures
- WORM/immutable storage
- secure remote checkpoint service
- distributed consensus
- rollback resistance if attacker controls both ledger and checkpoint

See docs/experiments/v0.0.17.md.

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v017.py

## Design principles

- **Correctness before compression**
- **UNKNOWN is a valid answer**
- **Learned prediction is proposal, not authority**
- **Discovery must not imply import**
- **Activation must not imply permanent authority**
- **Revocation is checked at use time**
- **Persisted authority must be verified before use**
- **Hash chains do not magically solve rollback without an external trust anchor**
- **Do not claim tamper-proof when the evidence only supports tamper-evident**

## Status

Research prototype. Not production-ready.