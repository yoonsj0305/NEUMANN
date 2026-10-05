# P1.11 P0 — Semantic Micro-Executor

Date: 2026-10-05

P1.10 first actual remains **INCOMPLETE / KeyboardInterrupt**. Its six retained
completed receipts are diagnostic-only. They show 2 accepted, 2 confidently
wrong selections, one non-Condorcet abstention and one wrong raw winner below
the confidence floor. This does not satisfy the P1.10 gate and does not justify
rerunning or threshold-tuning the same 5.1B next-token controller.

## Category-change hypothesis

The residual task after deterministic source extraction and feasibility is tiny:
match a target semantic role to 2–4 source-bound candidate role descriptions.

A 5.1B generative language model is therefore not the default primitive.

P1.11 tests a different compute category:

```
raw obligation
-> deterministic source/candidate extraction
-> deterministic feasibility
-> if one candidate: zero neural
-> if multiple candidates:
     Semantic Role IR
       target role
       candidate source entity -> role description
     -> frozen semantic micro-executor
     -> confidence / abstain
-> exact compiler
-> specialist executor
-> independent original verifier
```

The first P0 specialist is frozen
`sentence-transformers/all-MiniLM-L6-v2` at revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.

Frozen parameter count: 22,713,728.

The previously frozen Gemma control core has 5,104,297,504 parameters, so the
parameter-count ratio is about 224.7x. This ratio is design context only.
It is **not** a compute, energy, latency or economic advantage claim.

## Minimal neural input

The micro-executor never receives:

- CSP numbers
- domains
- constraints
- candidate assignment atoms
- solver witnesses
- full raw query

It receives only:

```
target semantic role
candidate role description 1
candidate role description 2
...
```

Candidate entity identity stays outside the embedding text and is reattached
deterministically after scoring.

## Frozen embedding semantics

Use the model-card Transformers formulation:

1. tokenize target + all candidate role descriptions as one batch,
2. one frozen encoder forward,
3. attention-mask mean pooling,
4. L2-normalize sentence embeddings,
5. cosine(target, candidate),
6. select a unique top candidate only if:
   - top cosine >= 0.0
   - top-vs-second cosine margin > 0.05.

Otherwise abstain.

No generation, retry, hidden label, private reference or new training is allowed.

## Why this is not merely another model

The system-level hypothesis is **specialization and routing**:

> use the cheapest representation and executor that can resolve the irreducible
> uncertainty, and reserve large generative compute for cases where smaller
> semantic machinery cannot certify a choice.

P1.11 therefore isolates the semantic micro-executor without Gemma fallback.
A later stage may add prospective escalation only after micro-executor capability
and complete cost are measured.

## Evidence boundary

P1.11 P0 is synthetic-contract work only.

- no P1.11 model score has run
- no P1.10 task may be rescored as P1.11 evidence
- actual P1.11 requires newly authored preregistered tasks
- parameter count is not FLOPs, energy, memory or latency
- model load, tokenization, pooling, similarity, abstention, execution and
  verification must all be charged in complete cost
- fresh validation, P2 and Decision3 remain blocked
- Q1–Q7 globally remain OPEN

The project North Star remains **overwhelming iso-capability resource advantage
plus category change**, not a local benchmark win.
