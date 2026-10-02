# v0.0.106.1 General Runtime-0.1 Repair Candidate

Status: OPENED interface-repair candidate only. It does not replace, edit, or
reinterpret the first Runtime-0 evidence retained by PR #121.

## Why this candidate exists

The first actual Gemma 4 E2B Runtime-0 run reached the frozen model but did not
reach a valid capability contest. The retained evidence showed three distinct
interface failures:

1. valid-looking answer content could be rejected by the custom action envelope,
2. thinking-enabled calls could spend the 192-token call budget without reaching
   an action boundary,
3. retrying an invalid/truncated turn could restart the same long reasoning path
   and consume the 120 s query wall budget.

The repair therefore changes the interface, not the frozen weights or task set.

## Deleted complexity

Runtime-0.1 removes the extra hand-written JSON action layer for tool selection.
Gemma 4's revision-pinned native tool-call template is used directly. The
processor response is parsed with the original prompt prefix, and the runtime
accepts only one native tool call per model turn.

For final responses, exactly two pre-registered envelopes are accepted:

- `{"answer": ...}`
- `{"action":"final","answer": ...}`

Markdown JSON fences may be stripped, but the runtime never infers, repairs, or
extracts an answer from prose.

## Bounded reasoning policy

The total query budgets remain 4096 context tokens, 512 generated tokens,
6 tool calls and 120 s wall time. The action step is reduced from 192 to
96 generated tokens and at most 4 model calls.

For this repair candidate `enable_thinking=False` on every model action.
Reasoning is externalized into certified deterministic operations:

`TASK -> ACTION -> TOOL/REPRESENT -> RESULT -> FINAL/CHECK`

This is deliberate. The candidate tests whether the small model can reliably
route and finish bounded actions before reintroducing any expensive hidden
reasoning policy.

## Native actions

B0/B1 receive no tools. B2 may call at most one deterministic tool. B3 receives
the shared arithmetic/CSP/Python pool plus `represent`. N must call
`represent` first.

A NEUMANN representation is not allowed to omit fields and let the runtime fill
them from the answer key. The model must submit:

- math: exact original expression plus required original bindings,
- planning: exact original domains and constraints,
- coding: exact original requirement.

Only after those fields are independently certified may the runtime execute the
chosen arithmetic/CSP/Python path and check the candidate against the original
task.

## Opened repair diagnostic

The first repair run reuses the same three Boot2 OPENED controls and five arms,
for 15 observations. Reuse is intentional because this is an interface repair,
not a generalization claim. The sealed v107 Fresh General Holdout remains
unopened.

The interface-readiness contract requires all of the following:

- 15/15 observations retained,
- no query timeout/deadline failure,
- complete model token accounting,
- a non-null candidate answer on every observation,
- original checker execution on every observation,
- every B2/B3/N observation performs at least one actual deterministic tool
  invocation.

This readiness predicate contains no accuracy threshold. Accuracy is retained in
the report, but General Gate remains `NOT_EVALUATED` regardless of the repair
result.

## Immutable boundaries

- no new training or fitting,
- no frontier calls,
- no paid API,
- no v107 holdout opening,
- frozen Gemma 4 E2B model revision unchanged,
- original Runtime-0/Boot2 evidence unchanged,
- Q1-Q7 remain OPEN.

A successful Runtime-0.1 repair only permits the next opened general capability
development step. It does not permit v107 or v108 by itself.

Official interface references checked 2026-10-02:

- https://huggingface.co/docs/transformers/chat_response_parsing
- https://huggingface.co/google/gemma-4-E2B-it
- https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
