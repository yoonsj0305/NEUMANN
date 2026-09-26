# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.23**

v0.0.22 made persistent-worker state resettable and auditable.

v0.0.23 makes lifecycle selection **declaration-aware**.

Plugins may optionally declare a digest-bound `state_class` in their manifest.

## State classes

### `stateless_semantics`
- semantic correctness may not depend on hidden worker state
- persistent worker allowed

### `cache_only`
- retained state is performance cache only
- persistent worker allowed
- a finite `max_requests_per_worker` is mandatory
- missing recycle bound is rejected

### `explicit_stateful`
- semantics intentionally depend on state across requests
- **rejected in v0.0.23** because NEUMANN does not yet have a session-scoped explicit-state protocol

### `non_persistent_only`
- worker reuse explicitly forbidden
- fresh process per operation

### no declaration
- declaration-aware runtime fails safe to fresh-process execution
- legacy manifest canonical shape remains unchanged

## Authority identity

`state_class`, when present, is part of the manifest canonical representation and SHA-256 digest.

Therefore changing:

    stateless_semantics → cache_only

or any other lifecycle declaration requires a **new approval**.

## Declaration-aware runtime

`resolve_plugin_lifecycle()` maps the declaration to:
- persistent
- fresh_process
- reject

`build_declared_lifecycle_adapter()` then enforces that decision.

The external scalar-sum interoperability plugin now declares:

    state_class = stateless_semantics

and is automatically routed to the persistent-worker path.

## Critical boundary

A state declaration is a plugin contract claim, **not proof**.

A malicious or buggy implementation can falsely claim `stateless_semantics`. Lifecycle enforcement and declaration conformance testing are separate concerns.

State classes also do not provide filesystem/network isolation or side-effect rollback.

See `docs/experiments/v0.0.23.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v023.py

## Status

Research prototype. Not production-ready.