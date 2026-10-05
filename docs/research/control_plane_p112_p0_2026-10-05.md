# P1.12 P0 — Joint Cross-Encoder Semantic Judge

Date: 2026-10-05

P1.11.1 is an immutable complete **FAIL / P111_SEMANTIC_CAPABILITY_FAILURE**.
The failure was not caused by timing, accounting, control-path drift, model
identity, or incomplete work.

Retained P1.11.1 evidence:

- 12/12 tasks complete
- 12 model calls / 12 neural forwards
- 0 generation
- 266 input tokens
- whole study about 9.14 s
- peak accelerator allocation about 101 MB
- raw-top correct 6/12
- accepted 3/12
- verifier rejected 5
- semantic abstained 4

Lowering the cosine-margin threshold cannot rescue the mechanism because the raw
winner itself is wrong on 6/12 tasks. Margin is also miscalibrated: some
confident wrong items have larger margins than several correct raw winners.

## Hypothesis

The residual semantic problem requires **relational interaction** between a
target function and each candidate role.

P1.11 encoded target and candidates independently and compared them with cosine
similarity. P1.12 changes only the semantic primitive:

```
target role + candidate role
        ↓ joint token interaction
small frozen cross-encoder
        ↓ scalar relevance logit
rank all candidates
        ↓
top-1 candidate
        ↓
exact compiler / cached specialist / original verifier
```

The first P0 model is:

- `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision `ce0834f22110de6d9222af7a7a03628121708969`
- `BertForSequenceClassification`
- expected parameters: 22,713,601
- six layers, hidden size 384
- one scalar relevance logit per pair

This keeps the model in essentially the same 22.7M parameter class as P1.11.1,
so the main changed variable is **joint cross-attention / relevance scoring**,
not a large increase in model scale.

## One-forward regime

For an ambiguous item with k candidates, create k pairs:

```
("Target function: <target>", "Candidate role: <candidate 1>")
...
("Target function: <target>", "Candidate role: <candidate k>")
```

Tokenize all pairs as one batch and perform exactly one model forward.

No CSP numbers, domains, constraints, assignment atoms, solver witnesses,
expected labels, or private references enter the learned input.

## Ranking and calibration separation

P1.12 P0 deliberately removes the cosine-style confidence threshold.

The development question is:

> Does joint cross-encoder ranking recover the correct raw top candidate?

Use a unique top logit; exact ties abstain. Execute the top candidate and let the
independent original verifier accept or reject it.

Confidence calibration and escalation are deferred until ranking capability is
shown. This prevents a poorly calibrated margin from masking the underlying
ranking signal as happened in P1.11.1.

## Evidence boundary

P1.12 P0 is synthetic-contract work only.

- no P1.12 model score has run
- no P1.11/P1.11.1 task may be reused as P1.12 evaluation evidence
- P1.12 actual requires newly authored preregistered tasks
- no new training
- no generation
- no fallback
- fresh validation, P2 and Decision3 remain blocked
- Q1-Q7 globally remain OPEN

The project North Star remains overwhelming iso-capability resource advantage
plus category change. P1.12 is an attempt to recover capability without giving
back the cheap one-batch micro-executor regime.
