# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.21**

v0.0.20 measured the fresh-process execution path and found ~99.98% of the trivial-family dispatch interval outside measured child plugin service.

v0.0.21 tests the resulting performance hypothesis:

> Keep the process boundary, but reuse the worker process.

## Persistent worker path

Fresh-process path:

    compile child → exit → solve child → exit → verify child → exit

Persistent path:

    start child once
      → import / activate once
      → compile
      → solve
      → verify
      → reuse for later requests

Protocol:

    neumann.plugin.persistent-rpc.v1

Properties:
- line-delimited JSON RPC
- monotonically increasing request IDs
- one serialized request at a time per worker
- authorization checked before worker start and every request
- revoke terminates the worker without sending another plugin RPC
- timeout/crash discards worker
- next approved request may start a clean replacement worker
- plugin module remains outside the core Python process

## Pre-registered keep gate

Keep this direction only if CI shows:

1. warm persistent pipeline median <= 25% of fresh-process median
2. revoked execution is not verified
3. post-revocation plugin requests = 0
4. worker is terminated on revocation

## Important semantic boundary

Persistent workers retain child-process state across requests.

That may include plugin globals, caches, allocator state, and accidental mutable state.

This is useful for performance, but creates a new lifecycle question:

    What plugin state is allowed to persist, and when must a worker be recycled?

## Security boundary

Persistent reuse is **not** a sandbox improvement.

Threat Model v2 still sets the next security priority to:

    os_level_capability_sandbox

See `docs/experiments/v0.0.21.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v021.py

## Status

Research prototype. Not production-ready.