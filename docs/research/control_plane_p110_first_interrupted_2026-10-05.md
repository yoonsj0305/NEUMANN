# P1.10 first actual — interrupted first-result retention

Date: 2026-10-05

This note retains the first P1.10 actual attempt exactly as observed. It does not rerun, rescue, replace, or complete the interrupted study.

## Immutable first-attempt identity

- archive: `NEUMANN_P110_FIRST_EVIDENCE.zip`
- bytes: `49,983`
- SHA-256: `26639aaa19074efc564bbd01d7ac106e586491a8e43fc7524fde0d9cc95535b9`
- frozen source head: `0c9b04954ffffe83051fcc2fcb675101717021ad`
- bootstrap SHA-256: `8dffa777f716604365ac0c8d95da5d0bc437addda8edd46203f56a502c46c572`
- setup status: `FAILED_OR_INTERRUPTED`
- setup error: `KeyboardInterrupt`
- first minimal-pairwise semantic development stage: `FAILED_OR_INTERRUPTED`
- active child after interruption: none
- archive already packaged: yes
- replacement/rerun: forbidden

This is **INCOMPLETE evidence**, not a PASS or FAIL verdict. No report or terminal receipt exists.

## Retained study coverage

Files observed in the first archive/session:

- `study_started.json`
- `manifest.json`
- `core.json`
- complete item receipts `task_00.json` through `task_05.json`
- start marker `task_06_started.json`
- no `task_06.json`
- no `task_07_started.json`
- no `task_07.json`
- no `report.json`
- no `terminal.json`

Therefore six task outcomes are available as partial first-result evidence, task 6 was entered but not completed, and task 7 was never started.

## Epistemic boundary

The preregistered P1.10 gate requires exactly 8 observations and a model-free replay of the terminal decision. This first attempt cannot be evaluated against that gate.

Partial task receipts may be used for **read-only diagnostic analysis only**. They cannot be promoted to a P1.10 PASS/FAIL verdict, cannot admit fresh validation/P2/Decision3, and cannot close Q1-Q7.

The original first attempt must not be deleted or overwritten. Any future execution, if scientifically justified, must be explicitly registered as a new attempt/version with the interrupted first result retained and clearly separated. It must never be described as a replacement or favorable rerun.

## Current next step

Read the six retained task receipts and the partial start marker without model inference or evidence mutation. Determine whether the minimal semantic contrast + symmetric pairwise mechanism showed useful partial signal before interruption. Any architectural change must be based on that retained partial evidence and prospective reasoning, not on selectively rerunning the same first attempt.


## Read-only partial diagnostic from the six completed receipts

The already-retained receipts were analyzed without model inference or evidence mutation.

Aggregate completed partial evidence:

- completed tasks: 6/8
- neural forwards: 12
- evaluated tokens: 10,536
- accepted: 2
- raw Condorcet evaluable: 5
- raw Condorcet correct: 2/5
- batch-order numerical drift: 0 on every completed selector receipt

Per-task diagnostic:

| task | expected | raw Condorcet | confident? | historical partial outcome |
|---|---:|---:|---|---|
| p110d_b01 | 1 | 0 | yes, 2.875 nats | verifier rejection |
| p110d_b02 | 2 | none | no | semantic abstain |
| p110d_b03 | 2 | 2 | yes, min 0.9375 | accepted |
| p110d_b04 | 1 | 0 | yes, 1.125 | verifier rejection |
| p110d_b05 | 0 | 0 | yes, min 3.5859 | accepted |
| p110d_b06 | 3 | 0 | no; raw min 0.40625 | semantic abstain |

The completed subset therefore does **not** show a useful semantic-capability recovery signal. Two tasks are confidently wrong, two are correctly accepted, one has no Condorcet winner, and one has the wrong raw winner below the confidence floor.

This diagnostic does not convert the interrupted study into a FAIL verdict. The historical first P1.10 attempt remains INCOMPLETE because the preregistered 8-observation terminal gate was never reached.

## Architectural consequence

P1.10 succeeded at aggressive control-cost reduction but did not rescue the semantic bottleneck in the retained partial evidence. The evidence now argues against further tuning of:

- absolute A/B semantic code thresholds,
- left/right pairwise symmetrization,
- Condorcet thresholds,
- additional Gemma batch/order diagnostics,
- prompt variants over the same next-token control formulation.

The next prospective architecture should question the use of a 5.1B generative LM as the primitive semantic resolver for a tiny residual relation-selection problem.

A NEUMANN-consistent next hypothesis is a **semantic micro-executor**:

```
deterministic source binding extraction
-> derive target semantic relation / candidate role descriptions
-> cheapest frozen semantic specialist that can resolve the relation
-> confidence / abstain
-> exact compiler + specialist executor + independent original verifier
-> escalate to larger learned compute only when the micro-executor cannot certify a choice
```

The purpose is not merely to replace Gemma with another model. It is to test the stronger system claim that irreducible semantic uncertainty can often be routed to a much smaller specialized representation/matcher, reserving large generative models for genuinely hard residual cases.

No P1.11 model or specialist is selected or scored by this note. Any such experiment requires prospective model identity, complete resource accounting, fresh tasks, strong shared baselines, and an escalation policy fixed before results.
