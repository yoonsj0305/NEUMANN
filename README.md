# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.23**

v0.0.22 made persistent-worker state visible through generation IDs and recycle evidence.

v0.0.23 replaces one global reuse policy with an explicit plugin lifecycle declaration that the runtime enforces.

## Worker state classes

### `STATELESS`
Semantic correctness requires no retained worker state.

Persistent reuse: **allowed**.

### `CACHE_ONLY`
Retained state may accelerate computation, but clearing it must not change semantic results.

Persistent reuse: **allowed**.

### `STATEFUL_EXPLICIT`
State is part of semantics and therefore requires an explicit state-transfer/checkpoint protocol.

v0.0.23 does not implement that protocol.

Current execution: **fail closed**.

### `NON_PERSISTENT`
The family must not be reused through a persistent worker.

Fresh-process execution: **allowed**.

Persistent reuse: **rejected before plugin launch**.

## Legacy manifests

Older manifests without `worker_state_class` remain valid on the fresh-process path.

They cannot silently gain persistent-reuse privileges:

    undeclared + fresh       → allowed
    undeclared + persistent  → rejected

## Manifest identity

When present, `worker_state_class` is part of the canonical manifest SHA-256.

Changing lifecycle class therefore changes approval identity and requires a new exact-manifest authorization.

## Runtime enforcement

Current compatibility matrix:

| Declaration | Fresh process | Persistent worker |
|---|---:|---:|
| undeclared legacy | allow | reject |
| STATELESS | allow | allow |
| CACHE_ONLY | allow | allow |
| NON_PERSISTENT | allow | reject |
| STATEFUL_EXPLICIT | reject | reject |

`STATEFUL_EXPLICIT` remains blocked until NEUMANN has a real explicit-state protocol rather than hidden worker memory.

## Important boundary

A declaration is a policy input, not behavioral proof.

A malicious or buggy plugin may claim `CACHE_ONLY` while actually depending on hidden state.

Therefore declaration enforcement must remain paired with behavioral evidence such as:
- v0.0.22 cross-generation correctness
- poison-state reset tests
- conformance suites

See `docs/experiments/v0.0.23.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v023.py

## Parallel security track

Lifecycle classes do not sandbox host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.