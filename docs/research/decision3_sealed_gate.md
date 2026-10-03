# NEUMANN 1 — Decision 3 Sealed General Evaluation

Status: **PREREGISTERED / UNARMED / SEALED DATA UNOPENED.**

Decision 3 is prepared in advance so a positive Decision-2 result cannot trigger
post-hoc benchmark shopping, task cherry-picking, or a new answer-capable
architecture after seeing sealed data.

No gated task row, answer, rationale, frontier response, paid API call or new
training is opened by this preparation.

## Admission order

```
Decision 2 actual one-shot
        |
        v
model-free replay is valid?
        |
        v
Decision 2 verdict == PASS?
        |
        v
candidate architecture + winning baseline frozen
        |
        v
task-agnostic interface can accept >=1 new family
without adding post-D2 answer-capable semantics?
        |
        v
source registry / provider identity / budgets frozen
        |
        v
ONE sealed evaluation
```

Any failure before the final line keeps the sealed rows closed.

## Why the interface gate exists

The current AM1 NEUMANN path is deliberately narrow:

- math: `expression + bindings -> arithmetic`,
- planning: `domains + constraints -> CSP`,
- coding: `requirement -> solve(items)`.

That is suitable for Decision 2's opened architecture-multiplier falsification,
but it is not a general expert-QA interface. Adding an HLE-specific executor,
gold-derived parser or new answer-capable route after seeing a sealed benchmark
would invalidate the generalization test.

Therefore the current readiness marker is:

`BLOCKED_CURRENT_TASK_SPECIFIC_INTERFACE`.

A future interface change may be tested only on opened matched development data.
It cannot be silently inserted between a Decision-2 PASS and Decision 3.

## Frozen source registry

Metadata-only registry:

`docs/experiments/decision3_source_registry_v1.json`

Preparation opened **zero task rows**.

Primary candidate is HLE-Rolling under a strict future eligibility rule: only
stable ids absent from the frozen base-HLE id set, text-only automatically
verifiable rows, with selection based only on id and metadata. Raw selected rows
must stay local/private and must not be committed or publicly redistributed.

HLE-Diamond is retained as a contamination-control candidate, not automatic
proof of unseen data: its 2026 release is refined from the broader HLE question
collection.

GPQA is too old/public to be the primary unseen surface for the frozen Gemma-4
core.

ARC-AGI-2 has strong private tiers but requires a grid interface/remote path not
present in the Decision-2 architecture.

LiveCodeBench is attractive for date-tagged coding, but the official release
metadata inspected for this freeze did not provide post-2026-07-20 tasks through
the frozen official dataset path. It remains a future candidate, not an excuse
to use an unofficial convenient mirror.

## Metadata-only task selection

The selector is frozen in:

`experiments/decision3_selection.py`

Selection uses:

`sha256(seed_commitment || source_id || stable_task_id)`

with per-subject and per-category diversity caps.

Question, answer, rationale, choices, solution and model-response fields are
explicitly rejected as selection inputs.

## Sealed multiplier persistence

Decision 3 reuses the Decision-2 success logic instead of inventing a friendlier
gate after the opened result:

Capability path:

- NEUMANN >= baseline + 2 verified tasks,
- NEUMANN complete wall <= 1.25x baseline.

OR efficiency path:

- NEUMANN >= baseline verified capability,
- NEUMANN complete wall <= 0.50x baseline.

The baseline arm is whichever DIRECT/TOOL arm was frozen by Decision 2. It is
not reselected on sealed data.

## Frontier gap

For registered sealed task T:

`T in G iff frozen baseline fails T AND frozen frontier reference succeeds T`.

NEUMANN never determines membership.

Minimum evaluable gap:

- at least 6 verified gap tasks,
- at least 3 represented families.

Recovery gate:

- NEUMANN recovers at least 50% of G,
- any family containing >=2 gap tasks must have >=1 NEUMANN recovery.

No sufficient gap is NOT_EVALUATED, not a fabricated success or failure.

## Frontier resource signal

Every role reports four explicit axes:

- complete latency,
- monetary cost,
- energy,
- compute.

Each axis is `measured`, `estimated` or `unavailable`. UNKNOWN never becomes
zero.

For Decision-3 admission, at least one compatible measured N/frontier axis must
show >=2x improvement and no compatible measured axis may regress beyond 1.25x.

This is a bounded engineering-admission signal, not a global North-Star Pareto
claim.

## Decision

Possible terminal states include:

- `PASS_ADMIT_EDGE_CLOUD_ENGINEERING`
- `FAIL_SEALED_MULTIPLIER_DID_NOT_PERSIST`
- `FAIL_FRONTIER_GAP_RECOVERY`
- `NOT_EVALUATED_NO_SUFFICIENT_VERIFIED_FRONTIER_GAP`
- `NOT_EVALUATED_FRONTIER_RESOURCE_SIGNAL`
- infrastructure/provenance blockers.

Even PASS keeps global Q1-Q7 formally open. It authorizes the next engineering
surface; it does not turn one sealed case set into a universal claim.

## Zero-content readiness check

On Windows:

`D3_READINESS_CHECK.cmd`

This searches for a local AM1 `replay.json`, validates the Decision-2 verdict,
checks the source registry and interface marker, and writes
`.decision3_readiness.json`.

It does **not** import a dataset, download gated rows, call a model or call a
frontier provider.
