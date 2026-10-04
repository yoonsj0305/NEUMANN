# P1.4 — Bounded Semantic Interpretation Before Verified Execution

## Why this gate exists

P1.3 established that already-typed public interfaces should not spend model
compute rediscovering their executor. Its first CPU contract diagnostic passed
with zero neural forwards and no weights loaded. It did **not** test the hard
case that remains: an original obligation arrives only as natural language, or
several valid typed interfaces coexist and the runtime must determine which
obligation is actually requested.

P1.4 isolates those two cases without opening P2.

## First-principles rule

The model is not execution authority.

For raw input:

```
raw original query
    ↓
P1.3 deterministic admission
    ↓
NEEDS_SEMANTIC_INTERPRETATION
    ↓
one bounded frozen-model semantic proposal
    ↓
strict parse
    ↓
P1.3 admissibility again
    ↓
exactly one specialist contract
    ↓
one specialist execution
    ↓
original-task Boolean verifier
```

The proposal may be wrong. A syntactically valid proposal is not accepted as
truth. Only an answer that passes the original independent checker counts.

For an already mixed valid interface:

```
mixed typed original
    ↓
P1.3 admissibility
    ↓
unchanged masked full-S4 fallback
    ↓
selected route must stay inside admissible routes
    ↓
specialist execution
    ↓
original verifier
```

## Frozen development scope

Twelve newly authored opened items are registered before any P1.4 model score:

- 4 raw arithmetic natural-language obligations
- 4 raw finite-CSP natural-language obligations
- 2 mixed arithmetic+CSP items whose requested obligation is arithmetic
- 2 mixed arithmetic+CSP items whose requested obligation is CSP

Coding-source semantic synthesis is deliberately excluded. It adds a second
generation problem and would confound this gate.

The eight raw items expose only `instruction` plus `public.query` to the
semantic compiler. Private exact values, hidden CSP checker structures,
construction witnesses and expected routes stay outside controller/model
inputs.

## Semantic compiler contract

Exactly one greedy call to the same frozen Gemma is allowed for each raw item.

- thinking disabled
- output cap: 192 tokens
- no retry after verifier failure
- exact output schemas only:
  - ARITHMETIC: expression + integer bindings
  - CSP: finite integer domains + supported constraints
  - ABSTAIN
- unsupported fields or malformed output fail closed
- a non-abstaining proposal must re-enter P1.3 as exactly one specialist
  contract before execution

This deliberately tests whether a small amount of neural computation can create
a useful representation. It does not assume the representation is correct.

## Opened development gate

PASS requires all complete accounting/identity checks plus:

```
raw accepted             >= 6 / 8
raw arithmetic accepted  >= 3 / 4
raw CSP accepted         >= 3 / 4
mixed fallback accepted  >= 3 / 4
raw model calls          == 8
mixed fallback calls     == 4
semantic retries         == 0
```

The original checker decides accepted answers.

Even PASS means only:

```
OPENED_SEMANTIC_PATH_DIAGNOSTIC_ONLY
```

It does not admit P2, Decision 3, Q5, Q6 or Q7.

## What would count as a useful result

The important evidence is not merely that Gemma emits valid JSON. The path must
show:

1. raw natural language can be compressed into a valid typed representation;
2. the deterministic contract layer prevents invalid execution;
3. the specialist can solve the proposed representation;
4. the answer still satisfies the original obligation;
5. mixed typed inputs can invoke the expensive neural fallback only where the
   deterministic contract layer cannot decide.

If this works, the architecture becomes hierarchical:

```
cheap public contract
    ↓
typed? ── yes → zero-neural specialist dispatch
    ↓ no
semantic representation only when necessary
    ↓
ambiguous typed? ── yes → semantic fallback
    ↓
executor
    ↓
original verifier
```

That is closer to the NEUMANN objective than making every query pay for a
general neural router.

## Boundaries

P1.2 fresh validation remains FAIL and is not rescued.
P1.3 CPU PASS remains a contract diagnostic only.
P1.4 uses opened authored development tasks.
A P1.4 PASS must be followed by architecture freeze and a newly registered
fresh semantic validation before any P2 registration discussion.

P2 registration = false.
P2 actual admission = false.
Decision 3 = false.
Q1–Q7 remain globally open.
