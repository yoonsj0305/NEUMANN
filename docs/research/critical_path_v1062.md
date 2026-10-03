# NEUMANN 1 — Critical Path Contract after Runtime-0.1

Status: ACTIVE execution policy. Q1-Q7 remain fixed research questions, but they
are no longer seven independent development programs.

## North-star decision

The project now optimizes for:

```
maximum decision-changing information per experiment
```

An experiment is not on the mainline unless its outcome can change whether the
project continues, pivots, or advances to the next gate.

The immediate question is:

> Does NEUMANN make the same small billion-scale core materially stronger per
> complete resource than the strongest matched use of that core?

## Decision 1 — Compact Runtime readiness

**RESOLVED: FAIL on first actual v0.0.106.2 single-thread CPU run.**

Candidate: v0.0.106.2 Runtime-0.2 Compact Pointer Actions.

This gate evaluates interface/runtime readiness only. It is not a capability
comparison and cannot close Q1-Q7.

PASS requires all three primary conditions:

1. 15/15 opened observations complete under the registered query wall gate.
2. Every B2/B3/N observation actually exercises a deterministic tool path.
3. Every one of the 15 observations reaches the original-task checker.

The retained implementation also requires complete token accounting, no prompt
admission block, and no actual model deadline.

The first actual v1062 attempt failed this readiness gate: 5/15 actual timeouts,
only 1/9 tool-enabled observations with a tool call, and only 7/15 observations
reaching the original checker, despite all 15 prompts passing the 240-token
admission gate. Therefore CPU runtime micro-optimization is STOPPED on the
mainline. Do not create Runtime-0.3 merely to tune prompts, token caps, parser
behavior, compact grammar, or single-thread CPU latency. Move the same frozen
core and matched runtime contract to an accelerator-class execution environment
for the capability study.

Edge efficiency is a later Reality Gate. Single-thread CPU inference is not the
scientific target of the General Capability study.

## Decision 2 — Architecture Multiplier

**RESOLVED: FAIL on the first valid accelerator execution.**

The frozen Gemma 4 E2B / BF16 Architecture Multiplier completed 36/36 terminal
observations on a Tesla T4. The model-free replay is valid and the frozen-core
audit is unchanged. DIRECT, TOOL and NEUMANN each scored 0/12, so the
architecture multiplier is undefined and the preregistered evaluator returned
FAIL with next action ARCHITECTURE_PIVOT.

The retained receipts show a shared control-plane failure before any structural
executor comparison occurred:

- 72/72 model calls used the full 256-token per-call output allowance;
- 72/72 began in the thought channel;
- 0/72 reached the final channel;
- all 72 action parses failed with JSONDecodeError;
- TOOL and NEUMANN executed zero tool calls;
- no model receipt hit the wall-clock generation deadline.

The frozen verdict remains FAIL. Do not relabel it NOT_EVALUATED and do not
rerun the same contract with favorable prompt/parser/token-budget changes.

The tested architecture

```
free-form reasoning -> final JSON control action -> executor
```

is stopped. The active mainline is now an architecture pivot that separates
low-entropy control selection from free-form generation. Any replacement must
return to opened matched validation before Decision 3.

## Decision 3 — One sealed general evaluation

If Decision 2 passes, run one separately frozen unseen evaluation designed to
produce the evidence needed for generalization/scaling/frontier-gap questions
together.

The same sealed experiment should measure, where applicable:

- unseen/open-set persistence,
- complete discovery+execution+verification economics,
- scaling behavior inside the admitted range,
- frontier-gap recovery using actually executed references.

Q5, Q6 and Q7 remain distinct questions in the scientific record. They are not
three separate engineering projects.

Decision-3 contracts, metadata-only source census and a no-unseal readiness
checker are preregistered in advance. They do NOT authorize execution before
Decision 2 passes. The current AM1 representation/executor grammar is
task-specific; the Decision-3 readiness marker therefore records
`BLOCKED_CURRENT_TASK_SPECIFIC_INTERFACE`. A genuinely new family may not be
made runnable by adding answer-capable semantics after seeing sealed data. Any
such interface change must return to opened matched validation first.

Only a positive sealed result admits Edge/Cloud engineering.

## Explicit STOP list until admitted

Do not spend mainline work on:

- further constructed-LP architecture polishing,
- new solver-family exploration,
- 4B/7B model scaling,
- frontier API integration,
- Edge optimization,
- new model training or fitting,
- large new benchmark construction,
- revival of native function schemas,
- single-thread CPU latency optimization beyond Decision 1,
- another basis-pursuit transfer rescue.

Historical LP and transfer evidence remains immutable and useful as mechanism
evidence. It is no longer the active optimization surface.

## Branch / evidence policy

- PR #123 is the authoritative Runtime-0.1 scientific record.
- PR #122 is historical/superseded and must not become a parallel development
  line.
- v1062 first actual bytes are one-shot evidence. Preserve failures; do not
  replace them with a favorable rerun.
- Decision 2 first actual accelerator evidence is authoritative and immutable.
  Its frozen verdict is FAIL.
- No favorable rerun of the failed AM1 contract is allowed.
- Decision 3, v107 sealed work and frontier work remain blocked until a new
  architecture passes a separately frozen opened matched validation gate.

## Mainline

```
v1062 Compact Runtime
        |
        v
Decision 1: interface ready? = NO
        |
        v
LEAVE CPU HARNESS
        |
        v
Accelerated Opened Architecture Multiplier
        |
        v
Decision 2: matched advantage? = NO
        |
        v
ARCHITECTURE PIVOT
        |
        v
opened matched validation of new control architecture
   NO -> pivot again / stop candidate
   YES
        |
        v
ONE sealed general evaluation
        |
        v
Decision 3: unseen + economics + frontier-gap signal?
   NO -> generalization architecture pivot
   YES -> Edge / Cloud engineering
```
