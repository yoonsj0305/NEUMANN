# v0.0.106.2 General Runtime-0.2 Compact Pointer Repair

Status: OPENED interface-repair candidate only. General capability is still
NOT_EVALUATED. Q1-Q7 remain OPEN. The v107 Fresh General Holdout remains sealed.

## Why Runtime-0.1 was insufficient

Runtime-0.1 removed long hidden-thinking loops, but the retained first run exposed
two new interface costs:

1. the pinned Transformers runtime rejected the attempted
   `parse_response(..., prefix=...)` integration, and
2. native function schemas expanded tool-enabled prompts to 447-757 input tokens.

All nine B2/B3/N observations then emitted only the first `<|tool_call>` token
before exceeding the 120 s complete-query wall gate.

The independent v1061 replay preserves the original bytes and corrects the
derived timeout count to 9/15. On those nine same-run one-token observations,
the local diagnostic fit is:

- slope: 0.358686 s / input token,
- R²: 0.999977,
- estimated 120 s one-token boundary: about 342 input tokens,
- estimated 90 s one-token boundary: about 259 input tokens.

This is a local measurement on the frozen Gemma 4 E2B GitHub CPU execution, not
a general scaling law.

## Requirements deleted in v1062

Runtime-0.2 removes both failed layers instead of tuning them:

- no native function/tool schema is rendered into the prompt,
- no processor response parser is called,
- no second narration call is required after a deterministic tool succeeds.

The model emits one small raw JSON action. The runtime parses that exact object,
executes a deterministic tool, and submits the resulting candidate directly to
the original checker.

`model -> compact action -> deterministic tool -> original checker`

This batch right is shared by B2, B3 and N in the repair diagnostic, so N does
not receive a hidden extra narration-cost advantage.

## Compact action protocol

Final:

`{"a":"f","v":...}`

Direct deterministic compute:

`{"a":"c","t":"m|c|p","s":"optional Python source"}`

Certified representation:

`{"a":"r","k":["public field names"],"x":"m|c|p","s":"optional Python source"}`

Executor codes:

- `m`: exact rational arithmetic,
- `c`: finite CSP,
- `p`: bounded Python `solve(items)`.

No prose extraction or fuzzy answer recovery is allowed. The already-observed
legacy final envelopes `{"answer":...}` and
`{"action":"final","answer":...}` are accepted only as explicit complete JSON
finals.

## Pointer semantics

A representation contains public-field *names*, not copied field values.

The model must select exactly:

- math: `expression`, `bindings`,
- planning: `domains`, `constraints`,
- coding: `requirement`.

Only after those names are selected may the deterministic certifier materialize
the exact original public values. It may perform only the previously registered
safe reductions, such as dropping arithmetic bindings not referenced by the
original expression.

This avoids two opposite errors:

- repeating every original field value wastes tokens,
- silently restoring omitted obligations would make the runtime, not the model,
  perform the structural decision.

The original checker remains authoritative and receives the original task.

## Physical admission gate

Runtime-0.2 keeps the 120 s complete-query wall gate but adds a measured prompt
admission gate:

- complete context cap: 4096 tokens,
- prompt admission cap: 240 tokens,
- per-call output cap: 64 tokens,
- complete-query output cap: 128 tokens,
- model-call cap: 2,
- tool-call cap: 6.

The 240-token cap is below the observed v1061 90 s one-token estimate
(~259 tokens), leaving a small execution margin for a compact JSON action.
This is an engineering admission rule derived from one measured environment, not
an Edge claim.

There is no silent prompt truncation. A prompt above 240 tokens is retained as
`PROMPT_ADMISSION_BLOCKED` and no model forward is attempted.

## Repair-arm behavior

- B0: direct final only.
- B1: bounded direct final only. Hidden thinking remains disabled in this repair
  candidate, so this is not yet the final reasoning-baseline capability contest.
- B2: exactly one compact compute action; runtime auto-submits its candidate.
- B3: at least one compact compute or representation action; runtime auto-checks.
- N: representation action first; certified representation and executor are
  auto-checked on the original task.

A successful repair does not itself establish comparative capability because the
B1 reasoning baseline is intentionally degraded while the interface is repaired.

## First opened diagnostic

Reuse the same three Boot2 OPENED controls and five arms = 15 observations.
No new tasks are opened and no v107 holdout is touched.

Interface readiness requires:

- 15/15 observations retained,
- zero actual deadline/timeouts,
- complete token accounting,
- zero prompt-admission blocks,
- a candidate answer on every observation,
- original checker execution on every observation,
- at least one deterministic tool invocation on every B2/B3/N observation.

Accuracy is retained but is not an interface-readiness threshold. General Gate
remains NOT_EVALUATED regardless of the result.

## First actual result

Source run: `37013632396`.

Source trigger head: `7a47dba21934675e7f6a1c44c67ee9326bd30db3`.

Retained evidence commit: `0185661132822e7b62c37dc8a24d64ca45af1d75`.

The one-shot first actual Runtime-0.2 run completed all 15 retained observations
and preserved the frozen-core audit, but **Decision 1 FAILED**.

Measured replay:

- 15/15 prompts passed the 240-token admission gate,
- observed prompt range: 159-229 tokens,
- 15/15 model-token accounting complete,
- 5/15 actual query timeouts,
- only 1/9 B2/B3/N observations executed any deterministic tool,
- only 7/15 observations reached the original checker,
- 7/15 observations produced a retained candidate answer,
- 2/15 observations were accepted by the checker.

By arm:

- B0: 0 timeouts, 3/3 checker reached, 1/3 accepted,
- B1: 0 timeouts, 3/3 checker reached, 0/3 accepted,
- B2: 0 timeouts, 0/3 tool calls, 0/3 checker reached,
- B3: 2/3 timeouts, 1/3 tool path, 1/3 checker reached, 1/3 accepted,
- N: 3/3 timeouts, 0/3 tool calls, 0/3 checker reached.

The compact prompt successfully removed native-schema inflation. That means this
failure must not be reclassified as another prompt-length problem. Instead, the
frozen E2B core frequently failed to obey the compact control grammar on the
first attempt, while a second model call was physically too expensive inside the
120 s single-thread CPU query budget. First calls already consumed roughly
70-109 s on the opened controls.

This is still **NOT** a General Capability verdict. The run does not establish
that NEUMANN helps or hurts the same core on a matched capability task. It shows
that the current single-thread CPU harness is no longer an efficient scientific
surface for obtaining that answer.

## Decision after first actual v1062

Per the frozen critical-path contract:

```
Decision 1 = FAIL
CPU runtime mainline = STOP_MICROTUNING_MOVE_ACCELERATOR
General Capability Gate = NOT_EVALUATED
Q1-Q7 = OPEN
```

Do **not** create Runtime-0.3 to tune prompt wording, compact grammar, parser
heuristics, token caps or single-thread CPU latency.

The next execution environment must preserve:

- the same frozen Gemma 4 E2B revision,
- matched baseline vs NEUMANN rights,
- original-checker authority,
- complete resource accounting,
- bounded tool and model calls,

while moving the capability experiment to accelerator-class execution. Edge
efficiency remains a later Reality Gate and must not be inferred from that
accelerated capability run.

The byte-identical first-run files are retained under
`docs/experiments/results/v1062_general_compact_first/`. The independent
`replay.json` is recomputed in CI without loading model weights or re-running
tools.

## Immutable boundaries

- frozen Gemma 4 E2B revision unchanged,
- no new training or fitting,
- no frontier calls,
- no paid API,
- no holdout access,
- Runtime-0 and Runtime-0.1 evidence unchanged,
- no performance claim from synthetic contracts,
- no Edge Reality claim.

If Runtime-0.2 becomes interface-ready, the next step is an opened matched
general-capability candidate with a restored bounded reasoning baseline before
any v107 Fresh General Holdout.
