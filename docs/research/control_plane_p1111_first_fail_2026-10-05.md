# P1.11.1 first evaluable actual — retained FAIL

Date: 2026-10-05

This note retains the immutable first-evaluable P1.11.1 actual result exactly as
reported by the original Kaggle session. It does not rerun, rescue, replace, or
reinterpret the result.

## Immutable evidence identity

- archive: `NEUMANN_P1111_FIRST_EVIDENCE.zip`
- bytes: `54,180`
- SHA-256: `ba2538830d60403294b7bc8230c7d8769bfb4ea66f59c2c7c26f5079beefcb81`
- identity repair revision: `P1.11.1`
- frozen repair source: `9dcb96a2c1e303c2178776ba9ab8b66eee53913b`
- repair bootstrap SHA-256: `fb81110e363662a47fe6489599a945d2adb3441a89d8d40fdee4ce5c62acfd7d`
- model artifact manifest SHA-256: `f961e60f6f7352d756e7addf8d7887be199c81facd2ae93950bc03d1e52d7292`
- setup status: `FINISHED_NONPASS`
- runner exit: `2`
- model-free replay exit: `0`
- development verdict: **FAIL**
- development_only: true
- no_replacement: true

Historical P1.11 remains separately immutable as NOT_EVALUATED with archive
SHA-256 `d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0`.
P1.11.1 does not replace that record.

## Interpretation boundary

The successful model-free replay establishes that the retained P1.11.1 receipt
set and terminal decision are replayable. The top-level output alone does not
identify which frozen FAIL reason fired.

Do not yet classify this as semantic-capability failure, cost failure, timing
failure, accounting failure, or control-path drift until the retained
`report.json` and task receipts are read.

No favorable rerun or replacement is permitted.

Fresh validation remains unregistered. P2 registration=false. P2=false.
Decision3=false. Q1-Q7 globally OPEN. The North Star claim of overwhelming
iso-capability advantage plus category change is not established by this result.


## Exact retained diagnosis

Read-only inspection of the immutable P1.11.1 receipts establishes that this was
a complete, replayable **semantic-capability failure**, not a cost, timing,
accounting, control-path, reference, or core-identity failure.

Frozen report:

- status: `COMPLETE`
- observations: `12`
- accounting_complete: `true`
- whole study: `9,137.403 ms`
- selector startup: `5,461.325 ms`
- model calls: `12`
- neural forwards: `12`
- generated calls: `0`
- feasibility calls: `35`
- selector complete: `12/12`
- lexical unique selections: `0`
- accepted: `3/12`
- selected: `8/12`
- verifier rejected: `5`
- semantic abstained: `4`
- raw top correct: `6/12`
- exact frozen reason: `P111_SEMANTIC_CAPABILITY_FAILURE`

The model/artifact audit was unchanged, and peak accelerator allocated memory was
about 101 MB.

### Why threshold tuning is rejected

The six correct raw tops and six incorrect raw tops are already fixed before the
0.05 cosine-margin gate.

If the margin threshold were reduced all the way to zero, all 12 tasks would be
selected, but only the same 6/12 raw winners would be correct. Therefore no
global threshold change can reach the preregistered 9/12 capability floor.

The observed margin is also badly calibrated:

- b01: wrong raw winner, margin about 0.2174
- b02: correct, margin about 0.1140
- b03: wrong, margin about 0.0860
- b04: correct, margin about 0.0781
- b05: correct raw winner, margin about 0.0357 -> abstained
- b06: wrong, margin about 0.0613
- b07: correct raw winner, margin about 0.0144 -> abstained
- b08: correct, margin about 0.0504
- b09: correct raw winner, margin about 0.0083 -> abstained
- b10: wrong, margin about 0.1018
- b11: wrong, margin about 0.1119
- b12: wrong raw winner, margin about 0.0181 -> abstained

Higher confidence is therefore not monotonically associated with correctness on
this opened development set.

### Candidate-count diagnostic

Raw-top correctness by candidate count:

- 2 candidates: 2/4
- 3 candidates: 4/5
- 4 candidates: 0/3

This is diagnostic only and is confounded by task semantics, but the complete
failure on all three four-candidate tasks is consistent with the larger point:
independent sentence embeddings plus cosine similarity are not reliably
resolving the functional/relational distinctions that remain after deterministic
CSP pruning.

### Cost-side signal

P1.11.1 did achieve the intended cheap control regime:

- 12 learned calls / 12 forwards total
- 266 input tokens
- zero generation
- one batched encoder forward per ambiguous task
- after initial warmup, most forward times are approximately 5-6 ms
- peak accelerator allocated memory about 101 MB

This is strong local cost evidence but **not** an iso-capability efficiency win,
because capability failed badly.

## Prospective consequence

Do not continue tuning:

- the cosine margin,
- absolute cosine floors,
- pooling,
- batch order,
- the same independent-embedding formulation,
- or the same opened tasks.

The next architecture should preserve the one-batch micro-executor regime while
changing the semantic primitive from **independent bi-encoder similarity** to
**joint target-candidate interaction**.

A clean P1.12 hypothesis is a frozen, small **cross-encoder semantic judge**:
construct one pair for each candidate, batch all pairs into one forward, score
candidate relevance jointly with the target role, choose top-1, execute, and let
the independent original verifier accept/reject. Confidence calibration should
be separated from ranking capability instead of being used to mask raw ranking
errors.

P1.12 must use newly authored preregistered tasks. P1.11/P1.11.1 task scores may
be used only for retrospective diagnosis and must never become P1.12 evaluation
evidence.
