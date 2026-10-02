# NEUMANN 1 — Accelerated Opened Architecture Multiplier Gate

Status: CONTRACT-ONLY / UNARMED.

This is Decision 2 in the three-decision critical path. Runtime-0.2 already
resolved Decision 1 as a single-thread CPU harness failure, not a capability
verdict. Do not return to Runtime-0.x CPU micro-tuning.

## Question

Does the same frozen Gemma 4 E2B core become materially better per complete
resource when run through NEUMANN than through the strongest matched use of that
same core?

The gate is intentionally small. It is not a paper-sized benchmark.

## Frozen core

All arms must use exactly:

- model: `google/gemma-4-E2B-it`,
- revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`,
- artifact SHA256:
  `bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66`,
- tokenizer SHA256:
  `8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207`,
- precision: bfloat16,
- deterministic greedy generation,
- no new fitting or training.

A CPU receipt is inadmissible. The execution device must identify itself as a
real accelerator and report device name, driver/framework version and accelerator
memory capacity.

## Opened development set

Exactly 12 author-constructed opened tasks:

- 4 exact math,
- 4 bounded coding,
- 4 finite constraint planning.

The task source is frozen in `experiments/general_multiplier_tasks.py`.

The model sees only:

`instruction + public problem`

It does **not** receive runtime-only `id` or `family` labels.

This set is opened development. It cannot establish unseen generalization and
cannot close Q6/Q7.

## Three arms only

### DIRECT

Same frozen core, no external tools. It may reason inside the shared token
budget and must return a final candidate.

### TOOL

Same frozen core and budget. It may use the deterministic arithmetic/CSP/Python
tool pool, but it receives no certified NEUMANN representation step.

### NEUMANN

Same frozen core, budget and tool pool. Its distinguishing right is the
representation-first structural path, followed by deterministic execution and
the same original-task checker.

There is no B2/middle arm. The strongest matched baseline is selected from
DIRECT and TOOL **after execution only by the frozen rule**:

1. more original-checker successes wins,
2. exact success ties are broken by lower complete wall time.

This is baseline selection, not post-hoc architecture tuning.

## Shared budget

Per observation, every arm is bounded by:

- context: 4096 tokens,
- complete generated output: 512 tokens,
- per call: 256 tokens,
- model calls: 4,
- tool calls: 4,
- query wall: 120 s,
- individual deterministic tool wall: 2 s.

The implementation may use fewer calls. Unused budget is not charged as if used.

The original checker remains authority. Hidden checker feedback is not exposed
as an iterative tool.

## Primary measurements

For each arm retain all 12 terminal receipts and measure:

- original-checker successes,
- complete wall time,
- model calls,
- tool calls,
- input/output tokens,
- peak accelerator memory,
- retries/failures in the raw observation receipts.

Unavailable energy/FLOPs/money telemetry stays UNKNOWN. It is never filled with
zero or inferred from token count.

Let `Q` be original-checker success rate and `L` complete arm wall time.

Descriptive architecture multiplier:

`M_A = Q_N / Q_B`

when `Q_B > 0`.

Primary efficiency multiplier:

`M_E = (Q_N/L_N) / (Q_B/L_B)`

when both capability terms are nonzero.

## Frozen PASS rule

A positive Architecture Multiplier signal exists only if either path passes.

### Capability path

- NEUMANN succeeds on at least **2 more of 12 tasks** than the strongest baseline,
  and
- NEUMANN complete wall time is at most **1.25×** the strongest baseline.

This is an absolute capability gain of at least 16.7 percentage points.

### Efficiency path

- NEUMANN succeeds on at least as many tasks as the strongest baseline, and
- NEUMANN complete wall time is at most **0.50×** the strongest baseline.

Anything else is FAIL, not “promising”.

Any core/task/budget identity mismatch or incomplete registered accounting makes
the experiment NOT_EVALUATED.

## Decision

PASS:

`Opened Architecture Multiplier PASS -> admit exactly one sealed general evaluation.`

FAIL:

`Opened Architecture Multiplier FAIL -> architecture pivot.`

NOT_EVALUATED:

repair only the measurement/environment defect. Do not change the model,
task set or gate based on partial outcomes.

No result from this opened gate closes Q1-Q7 globally.

## Explicitly blocked

Until this gate passes:

- no sealed v107 general evaluation,
- no frontier API/reference execution,
- no 4B/7B scaling,
- no Edge optimization,
- no new training,
- no large benchmark expansion,
- no return to constructed-LP polishing.

## Execution authority

This branch does not provision or purchase accelerator compute and does not start
model inference. Actual execution remains UNARMED until a concrete non-CPU
runner is available and its environment receipt satisfies the frozen contract.

When such a runner exists, the next implementation step is the smallest possible
runner adapter plus one first opened execution. No additional architecture
search is admitted beforehand.
