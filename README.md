# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.20**

Implemented through v0.0.20:
- representation-first family routing
- static plugin discovery + exact-manifest authorization
- durable hash-chained authorization ledger
- use-time revocation
- out-of-process plugin compiler/solver/verifier execution
- crash/timeout fail-closed behavior
- fresh-venv external-wheel interoperability
- Threat Model v1 and **Threat Model v2**
- **dispatch-vs-child-service runtime cost instrumentation**

## v0.0.20 focus

v0.0.19 solved one trust problem by moving external plugin code out of the NEUMANN core Python process.

That created a new engineering question:

    Is the fresh-process boundary too expensive for repeated reasoning?

Every isolated dispatch now records:
- parent-observed dispatch time
- child-observed plugin service time
- outside-service time = dispatch - service

`outside-service` is a lower-bound proxy for process startup, imports, scheduling, IPC, and response handling.

### Prototype performance gate

Frozen before the CI measurement:

    outside_service_fraction >= 0.50

means this trivial-family microbenchmark is classified:

    fresh_process_lifecycle_dominated

and the next performance experiment becomes:

    persistent_worker_lifecycle

This is an engineering heuristic, not a universal threshold.

## Threat Model v2

v2 separates two threats that v1 grouped together:

### Direct core Python-runtime mutation

The isolated path now has evidence for process separation:
- plugin module absent from parent `sys.modules`
- compiler/solver/verifier worker PIDs differ from parent
- JSON RPC boundary between core and plugin

### Host capability abuse

Still not contained:
- filesystem access
- network access
- subprocess creation
- same-user OS capabilities

Therefore the next **security** control priority is:

    os_level_capability_sandbox

Performance and security priorities are intentionally allowed to diverge.

See:
- `docs/THREAT_MODEL_V2.md`
- `docs/experiments/v0.0.20.md`

## Run

Requires Python 3.10+.

    pip install -e .
    pytest -q
    python benchmark_v020.py

## Claim boundary

NEUMANN currently has process separation, not hostile-code-safe sandboxing.

A future persistent worker may improve latency but does not, by itself, strengthen the security boundary.

## Status

Research prototype. Not production-ready.