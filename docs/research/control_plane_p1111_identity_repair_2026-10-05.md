# P1.11.1 identity repair — zero-inference technical correction

Date: 2026-10-05

P1.11 historical first actual remains immutable:

- archive: `NEUMANN_P111_FIRST_EVIDENCE.zip`
- SHA-256: `d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0`
- verdict: `NOT_EVALUATED`
- reason: `INCOMPLETE_OR_COVERAGE_DRIFT`
- observations: 0
- model calls: 0
- neural forwards: 0
- task starts: 0
- error: `P1.11 frozen model parameter-count drift`

No semantic task score, selector output, candidate ranking, or verifier result was observed.

## Root cause

The P1.11 contract used `22,713,728` as the value compared against:

```python
sum(p.numel() for p in AutoModel.parameters())
```

Those are different accounting quantities.

For the frozen `all-MiniLM-L6-v2` AutoModel:

- floating-point model parameters: **22,713,216**
- additional non-parameter I64 state elements in artifact metadata: **512**
- total state elements reported by the broader artifact metadata: **22,713,728**

Therefore:

```
22,713,216 parameters
+      512 non-parameter state elements
=22,713,728 total state elements
```

The historical guard correctly rejected the mismatched contract before the model
could score any task.

P1.11.1 corrects the parameter identity to `22,713,216` and retains
`22,713,728` and `512` as separate state-accounting metadata so the two
quantities cannot be conflated again.

## Scientific admissibility of the repair attempt

The 12-task opened-development set, private expected positions, capability gate,
cosine threshold, margin threshold, model revision, pooling rule, precision,
device, feasibility front end, compiler, executor and verifier are unchanged.

Reusing the frozen task set for P1.11.1 is admissible as a technical repair
because the historical first attempt exposed **zero task-dependent model
information**:

- no task began,
- no neural forward occurred,
- no similarity was produced,
- no candidate was selected,
- no expected label was compared to a model output.

The correction was determined from model-identity accounting, not task outcomes.

P1.11.1 is not a replacement for the historical first archive. It is a new,
explicitly named first-evaluable attempt after a zero-inference identity repair.

## New evidence namespace

P1.11.1 uses separate first-attempt paths, including:

- `neumann_p1111_first_setup.json`
- `neumann_p1111_first/`
- `NEUMANN_P1111_FROZEN/`
- `NEUMANN_P1111_MINILM_FROZEN/`
- `NEUMANN_P1111_FIRST_EVIDENCE.zip`

The setup and archive manifest retain the historical first archive SHA and
zero-inference provenance. They declare:

- `identity_repair_revision = P1.11.1`
- `repair_scope = MODEL_PARAMETER_IDENTITY_ONLY`
- `task_scores_seen_before_repair = false`
- `replacement_of_historical_first = false`
- `favorable_rerun = false`

## Unchanged gate

The development gate remains unchanged:

- 12 observations
- accepted >= 9/12
- 12 model calls
- 12 neural forwards
- 0 generation
- 35 feasibility calls
- 12/12 selector receipts complete
- lexical-overlap unique selections = 0
- selector <= 10 s/item
- complete item <= 15 s
- whole study <= 240 s
- exact frozen model/artifact identity
- model-free replay

A PASS remains opened-development diagnostic evidence only. It does not register
fresh validation, admit P2 or Decision3, close Q1-Q7, or establish the project's
overwhelming-advantage/category-change North Star.
