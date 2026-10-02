# v0.0.106.1 Runtime-0.1 opened protocol repair

Date: 2026-10-02

## Why this candidate exists

The preserved Boot2 first run on PR #121 is immutable negative interface
evidence: all five arms were 0/3, nine B2/B3/N queries timed out while
restarting unfinished thought, B1 exhausted its per-call reasoning allowance,
Direct produced two framing failures and one checked arithmetic error, and no
tool was invoked.  The General Capability Gate therefore remained
`NOT_EVALUATED`.

This candidate does not replace those bytes and is not v0.0.107.

## Frozen parent

- parent Boot2 archive:
  `c57fd111b249d442e63113ae223801b2987e7b82`
- parent evidence merged to main:
  `f43242ae09fb5343257e8f83eacf01dfaa4548d8`
- same model/revision/weights/precision
- same three already-opened Boot2 controls
- same five arms
- same 4096 context, 512 complete-query output, 192 per-call output,
  six model calls, six tool calls, 120 s query wall cap and 2 s Python cap
- no training, frontier call, paid API, fresh holdout, new task family or
  checker change

## Exactly four candidate changes

1. Supply the explicit generation prefix to the Transformers response parser.
2. Force hidden thinking off for this readiness candidate.
3. Append a charged prompt suffix requiring an immediate JSON action.  A
   no-tool deliberative response may place at most 24 words of visible rationale
   in the same object.
4. Normalize only an unambiguous structured object that omitted `action`:
   `answer -> final`, `tool+args -> call`, or `ir -> represent`.

The adapter never converts arbitrary plain text, ambiguous objects or malformed
JSON into an answer.  It retains raw model bytes and the processor's original
parsed content before any action-key insertion.

## Opened repair admission test

The candidate is interface-ready only if all fifteen observations complete and:

- every query leaves a candidate answer;
- no query reaches or exceeds the 120 s wall deadline;
- every query reaches the original checker;
- B2, B3 and N each exercise at least one actual tool path;
- charged latency and token accounting are complete.

Accuracy is recorded but is not an interface-readiness condition.  A READY
result still does not close Q1-Q7 and does not evaluate general capability.

If this candidate is not READY, retain the complete negative trace and repair
only the measured failure.  Do not open v0.0.107.

If READY, inspect accuracy and cost separately before deciding whether the
protocol is strong enough to freeze for a fresh General holdout.  A weak
baseline or an artificially constrained B1 must not be used to claim a
NEUMANN advantage.
