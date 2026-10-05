# P1.11 first actual — retained NOT_EVALUATED first result

Date: 2026-10-05

This note retains the immutable first P1.11 actual result exactly as reported by
the original Kaggle session. It does not rerun, rescue, replace, or reinterpret
the historical result.

## Immutable first-result identity

- archive: `NEUMANN_P111_FIRST_EVIDENCE.zip`
- bytes: `23,620`
- SHA-256: `d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0`
- frozen source head: `8094b4ea90fc48f4d3c0d8142ff378dbe73afc59`
- bootstrap SHA-256: `07d3f606ba9fe5beb9c79f4181e1525731a2699e9b77b361042158794ca120de`
- model artifact manifest SHA-256: `f961e60f6f7352d756e7addf8d7887be199c81facd2ae93950bc03d1e52d7292`
- setup status: `FINISHED_NONPASS`
- runner exit: `2`
- model-free replay exit: `0`
- development verdict: **NOT_EVALUATED**
- development_only: true
- no_replacement: true

The model-free replay succeeding means the retained receipts and historical
decision are internally replayable. It does **not** explain why the evaluator
returned NOT_EVALUATED.

## Historical interpretation boundary

P1.11 is not PASS and is not semantic-capability FAIL on the information above.
The frozen evaluator can return NOT_EVALUATED only before the normal cost and
capability gates, e.g. for incomplete/coverage drift or reference/core identity
drift. The exact frozen reason must be read from the retained `report.json`
before any diagnosis or next architecture decision.

No favorable rerun or replacement is permitted. The first archive remains the
historical first result.

Fresh validation remains unregistered. P2 registration=false. P2=false.
Decision3=false. Q1-Q7 globally OPEN. The North Star claim of overwhelming
iso-capability advantage/category change is not affected or established by this
result.


## Exact diagnosis from retained report

Read-only inspection of the retained first result established:

- report status: `INCOMPLETE`
- observations: `0`
- model calls: `0`
- neural forward calls: `0`
- core receipt: absent
- no task start marker exists
- evaluator reason: `INCOMPLETE_OR_COVERAGE_DRIFT`
- runner error: `ValueError: P1.11 frozen model parameter-count drift`

The failure occurred during `FrozenMiniLMSemanticEncoder` construction, before
any semantic task or forward pass. The contract had conflated the model's
22,713,216 parameters with 22,713,728 total artifact/state elements, the latter
including 512 non-parameter I64 state elements.

Historical P1.11 therefore remains **NOT_EVALUATED**, not semantic FAIL.

A separately named P1.11.1 identity-only repair is allowed because no task score
or task-dependent model signal was observed. It does not replace or mutate this
archive.
