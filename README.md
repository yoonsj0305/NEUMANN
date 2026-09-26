# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **representation-first, compute-efficient problem solving**.

> Make the cheapest correct reasoning path easy to use.

## Current engineering baseline

**v0.0.22**

v0.0.21 proved that a persistent isolated worker can remove most fresh-process lifecycle overhead for lightweight families.

v0.0.22 addresses the semantic cost of that optimization:

> **What state is allowed to survive between requests, and how do we prevent hidden worker memory from becoming semantic authority?**

## Worker generations

Every persistent worker lifecycle now has an explicit `generation_id`.

All persistent RPC responses are checked against the active generation. A generation mismatch is a protocol failure and the worker is discarded.

`WorkerStatePolicy` currently supports:

    max_requests_per_worker

When the operation limit is reached, the next compile/solve/verify request starts a fresh worker generation.

Manual recycling is also available:

    dispatcher.recycle("reason")

and records the previous generation ID, PID, request count, and recycle reason.

## Semantic state rule

NEUMANN's runtime contract is now:

> Retained worker state may accelerate computation, but request correctness must not depend on hidden state that is absent from the explicit RPC payload and approved plugin artifact.

A strong CI probe sets:

    max_requests_per_worker = 1

which forces one problem's compile, solve, and verify operations into **three different worker generations**. The family must still return the correct verified answer.

## Poisoned-state experiment

The test plugin contains an intentional hidden global poison flag.

CI verifies:
- poison is visible inside the same generation
- manual recycle clears the poison
- request-limit recycle clears the poison
- generation ID changes after recycle
- normal results remain semantically equivalent across recycle
- parent process still does not import plugin code

## Boundary

Process recycling resets Python in-memory state for the worker process. It does **not** roll back external effects such as:
- filesystem writes
- network / remote service state
- databases
- escaped descendants
- host-level resources

That remains outside state hygiene and belongs to the OS-level sandbox / side-effect-control track.

See `docs/experiments/v0.0.22.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v022.py

## Status

Research prototype. Not production-ready.