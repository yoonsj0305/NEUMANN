# P1.8 first actual opened-development result — retained FAIL

Date: 2026-10-05

This is a post-result retention note. It does not modify or reinterpret the frozen P1.8 source, registration, tasks, gates, model, runtime, or first-attempt evidence.

## Immutable first-result identity reported by the original Kaggle session

- archive: `NEUMANN_P18_FIRST_EVIDENCE.zip`
- bytes: `87,402`
- SHA-256: `a1545091f858d8b573183ea1b52157a8e52a677a2d5d85c51e41fe919e8239c8`
- frozen source head: `4e48320c2c67f15f8a41b0b4721caabd0c9b6df3`
- frozen bootstrap SHA-256: `19de12d24316b7122720404f0c4252f1b2c1fa3f179958e28e597ac75c18a49c`
- runner exit: `2`
- model-free replay exit: `0`
- study: `COMPLETE`, 8 observations, report error = null
- frozen verdict: **FAIL / CONTROL_WORK_ACCOUNTING_FAILURE**
- no favorable rerun or replacement

The archive bytes have not been independently ingested into this repository. The identity above is the original-session reported identity. The copied receipt bundle reports terminal complete=true, no_replacement=true, and model-free replay `integrity_valid=true`, `cost_replayed=true`.

## Frozen-core identity

The actual run used the registered frozen model/runtime:

- `google/gemma-4-E2B-it`
- revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16
- Tesla T4
- torch `2.11.0+cu128`
- transformers `5.16.1`
- weights unchanged=true

Peak receipts:
- accelerator allocated: 11,012,405,248 bytes
- accelerator reserved: 12,624,855,040 bytes
- process RSS: 12,271,366,144 bytes

Energy, FLOPs and monetary cost remain UNKNOWN.

## Stratum A — decisive positive localization

All four feasibility-reducible ambiguity tasks passed end to end:

| task | candidate count | selected | model calls | neural forwards | complete ms | result |
|---|---:|---:|---:|---:|---:|---|
| p18d_a01 | 2 | 1 | 0 | 0 | 7.896266 | ACCEPTED |
| p18d_a02 | 3 | 1 | 0 | 0 | 11.805042 | ACCEPTED |
| p18d_a03 | 4 | 2 | 0 | 0 | 20.871893 | ACCEPTED |
| p18d_a04 | 3 | 2 | 0 | 0 | 12.181506 | ACCEPTED |

Aggregate A item time: 52.754707 ms. Every item used deterministic source-bound extraction, bounded feasibility, exact compilation, cached feasibility witness, specialist execution and independent original verification. A had exactly 0 model calls, 0 neural forwards and 0 generation.

Within this bounded opened-development mechanism, public deterministic feasibility successfully removed ambiguity before neural control whenever exactly one candidate remained satisfiable.

This is mechanism evidence only. It is not a general NLP, open-set, iso-capability or economic claim.

## Stratum B — residual semantic path failure

All four B tasks retained multiple feasible candidates and invoked the frozen non-generative full-S4 selector.

### p18d_b01

- eligible: [0,1]
- selector completed all 36 forwards
- 38,808 evaluated/padded tokens
- selector receipt complete in 99,623.019907 ms
- selected candidate 0
- specialist executed from the cached feasibility witness
- independent original verifier rejected the answer
- accounting complete=true

This is the one clean completed semantic-choice observation in the first P1.8 result. Under the frozen selector, the chosen binding was wrong for the authored public lexical-semantic cue.

### p18d_b02

- eligible: [0,1,2]
- selector completed all 36 forwards
- 69,480 evaluated/padded tokens
- selector receipt complete in 182,669.810339 ms
- frozen selector wall = 180,000 ms
- no candidate admitted to execution
- error: `semantic selector wall cap`
- accounting complete=false

The full scoring receipt completed, but after the frozen wall. This is timing/cost failure, not an admissible semantic outcome.

### p18d_b03

- eligible: [0,1,2,3]
- 30 of the required 36 forwards completed
- 78,960 evaluated/padded tokens charged
- selector receipt FAILED
- inner error: `CodedFailure: TimeoutError: completed forward deadline`
- no specialist/verifier execution
- accounting complete=false

No semantic winner/loser conclusion is admissible.

### p18d_b04

- eligible: [0,1,2]
- selector completed all 36 forwards
- 69,840 evaluated/padded tokens
- selector receipt complete in 182,919.904332 ms
- frozen selector wall = 180,000 ms
- no candidate admitted to execution
- error: `semantic selector wall cap`
- accounting complete=false

Again, the first result establishes a timing/cost failure, not an admissible semantic outcome.

## Aggregate first-result accounting

- model calls: 4
- neural forwards: 138
- generation: 0
- evaluated tokens: 257,088
- padded tokens: 257,088
- feasibility calls: 24
- feasibility nodes: 213
- feasibility constraint checks: 469
- tool calls: 5
- original-verifier calls: 5
- witness cache hits: 5
- selector startup: 154,144.665133 ms
- whole study: 856,605.532426 ms

The preregistered path required 144 B forwards and 8 tool/verifier calls. Because B02/B03/B04 did not reach admitted execution, aggregate control-work accounting was incomplete and the frozen evaluator correctly returned **CONTROL_WORK_ACCOUNTING_FAILURE** before the later capability gate.

## Research interpretation

P1.8 separates two claims that must remain distinct.

**Supported in this opened bounded mechanism:** deterministic feasibility can eliminate residual candidate ambiguity at zero neural cost when all but one source-bound candidate are proven impossible.

**Not supported:** the inherited 36-forward full-S4 residual semantic selector is a viable NEUMANN control mechanism. It is both expensive and, on the one clean completed semantic observation, wrong.

The important architecture lesson is therefore not to relax the wall again. P1.7 used 120 s and P1.8 prospectively used 180 s; two P1.8 receipts still completed just beyond 180 s and one did not finish. Increasing the cap again would preserve a diagnostic but move away from the NEUMANN objective.

The next development mechanism should instead reduce the residual semantic decision itself: fewer forward passes, fewer coded permutations, or a different bounded representation that removes arbitrary code-label effects without paying full-S4 cost. Any new mechanism must preserve source-bound evidence, feasibility pruning, no free numeric/entity regeneration, no hidden reference access, no generation retry, independent original verification, complete partial-work accounting, and first-result discipline.

P1.8 is not rerun or rescued. Fresh validation remains unregistered. P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 globally OPEN.


## Read-only post-hoc latent-selector diagnosis

After the immutable first result, the already-retained complete selector matrices were read without model inference, evidence mutation, execution or verification. These diagnostics are **POST_HOC_NON_ADMISSIBLE** and cannot change the historical P1.8 verdict.

- **B01**: expected candidate 1; frozen full-S4 latent choice 0. Eligible margin = 1.013020835 nats. All three execution modes were numerically identical and leave-one-orbit-out winners were stable. This is a clean, stable semantic miss.
- **B02**: expected candidate 1; raw eligible winner was candidate 1, but margin = 0.228515626 nats, below the frozen 0.5-nat admissibility floor. Therefore the historical selector would still abstain/fail even absent the 180 s wall. This is weak correct-direction evidence, not an admissible success.
- **B03**: only 30/36 forwards completed. No latent choice is reconstructed.
- **B04**: expected candidate 1; frozen full-S4 latent choice 0. Eligible margin = 5.178629555 nats with stable leave-one-orbit-out winners. This is a second clean, stable semantic miss.

The post-hoc evidence therefore rejects the narrow hypothesis that P1.8 B failed only because the selector wall was too small. Of the three B items with complete matrices, two strongly and stably prefer the wrong semantic candidate; the third points to the correct candidate but fails the prospectively frozen confidence margin.

### Architecture consequence

Do **not** extend the full-S4 wall again and do not treat the 36-forward mechanism as a production candidate. P1.9 should replace arbitrary multi-class A/B/C/D candidate-slot coding with a candidate-local semantic proposition test using shared fixed response semantics. A prospective design target is to score each remaining candidate as a proposition such as `FAITHFUL` vs `NOT_FAITHFUL`, so candidate identity lives in the prompt while output-token semantics remain constant across candidates.

For B candidate counts 2/3/4/3, a design using one primary batched pass plus one independently ordered confirmation pass would require approximately 4/6/8/6 scored candidate rows and about 8 total forward calls if batched by item, rather than the frozen P1.8 study's 144 forwards. Exact P1.9 budgets and stability criteria must be frozen before any new Gemma score.

This is an architecture proposal only. No P1.9 model score has been run.
