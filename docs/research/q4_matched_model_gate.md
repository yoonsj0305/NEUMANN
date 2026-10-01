# Q4 next milestone — matched model, not a solver-only demonstration

Updated 2026-10-01 through v0.0.85 executable-Direct parity. This is a **design gate**,
not a registered trained-model evaluation or a completed implementation.

## Exact question

At the same independently verified capability, can NEUMANN's complete path
cost less than strong same-budget learned **and** deterministic direct paths?
Q3 asks whether a learned decision is actually useful; Q4 additionally asks
whether the system beats the best applicable direct comparison. Neither is
answered by v0.0.74, parameter count, or a solver-only speed ratio.

## Task admission before training

1. Raw observable inputs, distribution generator, output semantics, and
   original-task verifier must be fixed. No model sees hidden structure or
   answers at inference. No unknown real data licence is presumed.
2. A cheap deterministic input-processing/execution baseline must be tested.
   If it saturates capability at negligible cost, reject the task as learned
   headroom evidence. This excludes the studied tiny explicit affine grammar.
3. An expensive structure/algorithm proposer may provide an upper-bound
   diagnostic. Charge it as a real comparator; its free-output version is
   non-deployable and cannot be a NEUMANN result. A failing bounded diagnostic
   is grounds to stop that candidate, not proof that every model must fail.
4. Identify the residual decision and nearest primary prior art. Learning
   graph reduction locations, tree decomposition, or variable order is not
   by itself new. Reuse strong existing algorithmic components.

## Required comparator matrix

| Path | Learned output | Execution access | Original verifier |
| --- | --- | --- | --- |
| Direct deterministic | none | best applicable algorithm | identical contract |
| Direct answer learner | final answer | no hidden oracle | identical contract |
| Direct executable learner | program or uncompressed typed IR | same permitted runtime/solver | identical contract |
| NEUMANN | structure plus certified reduction/planning proposal | same permitted runtime/solver | identical contract |
| NEUMANN without compression | same parsing/representation | same permitted runtime/solver | identical contract |

The executable direct learner prevents attributing ordinary computation
offloading to NEUMANN's compression. The ablation prevents attributing a
better parser, dataset or runtime to compression. Include a larger learner
only within an explicit additional training/hardware budget; do not silently
change the matched comparison. The frozen protocol must name actual runnable
models, not generic labels from this matrix.

## Matching and accounting

LP-specific boundary (v085): a Direct executable predictor may emit
`solve_basis_checked` with the same basis, reconstruction, original certificate
and fallback as NEUMANN. All 210 retained supplied-head checks agreed exactly;
this is not learned accuracy or cost evidence. Comparing a basis predictor
only against a cold full solver withholds execution authority. A new learned
experiment must compare actual architectures/training or paid discovery
behavior, not just rename one checkpoint's output. Same backend authority
does not make different trained architectures equally efficient. Do not infer
a universal impossibility result from this bounded adapter equivalence.


Fix text/graph-level disjoint training, development and sealed final sets;
hold out structural classes as well as surface forms if claiming generality.
Freeze budgets, model choices, epochs, seeds and stopping rules before final
evaluation. Use the same total training-example budget and record target
generation/teacher costs; do not equate example count with equal training
compute. Intermediate supervision is an allowed baseline, not a withheld
advantage for NEUMANN.

Primary measured inference latency:

`input processing + features + model + validation + execution + original
verification + failed attempts + fallback`.

Report cold model loading separately and warm latency explicitly. Measure
peak process memory independently; table entries or parameter bytes are not
that quantity. Record tokens/FLOPs proxies/solver operations separately; do
not add incompatible units into an invented total. Joules/dollars require
actual instrumentation/rates. An engineering "Idiot Index" based on material
cost has no literal measurable denominator here and should not be fabricated.

For training time `T` and positive per-query saving `d` on comparable
hardware, report amortization break-even `T/d` queries. If `d <= 0`, no
positive break-even exists. Include rejected teacher labels and failed
training attempts in research-cost reporting.

## Quality, failure and acceptance

The actual next experiment must freeze numerical quality and improvement
targets **before training**. The design default is exact independent
verification of all admitted final cases and >=20% complete inference-cost
reduction versus the strongest applicable reference; this default is a
design choice, not an observed result or statistical-power calculation.
Report paired uncertainty and repeated-seed variability. Reject timeout
speed ratios and comparisons at unequal attained quality.

Invalid reductions, invalid programs, ambiguity or budget exhaustion must
fail closed. If direct fallback rescues a case, count **both** failed work
and fallback cost and tag that route. A verifier timeout is not success.
At fixed verified capability, compression must beat the no-compression
ablation too. Otherwise the result belongs to parsing/offloading, not the
central structural-compression hypothesis.

## Routes to investigate, not promises of 10x

- A genuinely expensive hidden structural decision with an amortizable cheap
  learner, only after an admissible full-cost headroom screen.
- Reuse of certified canonical structures across independent queries,
  charging lookup, equivalence validation, invalidation and cold misses.
- Adaptive local/cloud compute placement on a real workload, charging every
  escalation and using fixed capability rather than model-size comparisons.

No 10x multiplier is assumed for these options. Stop after a frozen negative
gate rather than shrinking the comparator until a win appears.

## Restart checkpoint

Current v0.0.85 checkpoint: `v085_diagnostic.manifest.json` retains a failed
runtime preflight (zero paired executions) and the first completed untimed
comparison. Q3/Q4 remain OPEN. v084's classical portfolio also failed the cost
gate; this is not learning admission. Do not train solely to repackage the same
basis head. First next action: choose an actual matched model experiment with
distinct learned computation/inductive bias and frozen equal-authority
comparators, or reject its full-cost headroom before fitting. If revisiting LP,
include native warm starts and published learned-basis baselines. Preserve
the v074 rejected order target and all first timing evidence unchanged.

Restart update: latest code v0.0.76, based on exact upstream v0.0.75 tree
`2cf1c01bb292f1f05f733c59594617de2d10f2a3` (`ddfffc55...`). v0.0.75 retained
only a lifetime hygiene fix and preserved its first negative timing gate.
v0.0.76 now supplies a direct atomic tool-program interpretation of the
v0.0.31 structural route: 39,852 possible-head/text pairs have identical
downstream behavior. It is not new learned inference or a matched full-cost
comparison. Raw contract evidence is `docs/experiments/results/v076_program_parity.json`.
No further training on this cheap controlled grammar is justified; the next
new task must admit real reduction and include this direct tool-access baseline.


Current restart update: v0.0.77 preserves both formerly conflicting branches.
The first PR #82 admission verdict is now integrated and the v0.0.76 atomic
program comparator remains unchanged. Do not repeat a final audit to choose
better timings or train another model on the saturated controlled grammar.
The next substantive milestone is a new task admission with a residual
structural decision, an executable Direct comparison, a no-compression
ablation, shared verification authority, and full-path cost accounting.

v0.0.78 restart: the SVAMP **numeric execution compression** candidate is
rejected, not the natural-language problem-solving task as a whole. Supplied
reference equations take 0–2 arithmetic operations and have no measured CSE
redundancy. The source has one retained equation/answer disagreement. No model
is trained on this rejected target; model inference/planning remains unmeasured.
Next admission must identify a costly residual *learned discovery/planning*
decision and an actual runnable matched Direct learner. Shared compiler CSE
cannot be reserved for NEUMANN. Gold-answer checking is offline dataset-label
agreement, never production semantic verification of a raw NL problem.

v0.0.79 adds `matched_cost_v079.measure/summarize` for the next admitted
model experiment. It retains attempted/fallback work and distinguishes
original-task verification from labels and expression checks, but trusts
callback bodies and their declarations. No new task, actual model roster,
sealed dataset or performance claim is supplied by this instrumentation.
Freeze and audit these before using it; fixture ratios do not close Q3/Q4.
See `../experiments/v0.0.79.md`.

v0.0.80 restart: the bounded three-relation constructed planner workload is
rejected before training. The finite six-policy zero-model oracle improved
verified total cost by only 3.3575% over the strongest fixed Direct policy.
Independent SQLite replay dominated measured costs. Preserve the first
216-call archive and do not fit a learner or loosen the gate to rescue it.
The next candidate must pair a costly residual decision with a cheaper
independently checkable certificate, identical authority for Direct, and
actual runnable models frozen before fitting. Original-query recomputation
is one verification implementation, not the definition of verification;
any replacement needs its own original-semantics contract and falsification
controls before timing. No broader rejection of SQL learning follows.


v0.0.81 restart: standard-form LP is admitted only as a **verification
interface candidate**, not yet as a model task. A primal/dual witness can be
checked against the original coefficients without re-running the optimizer.
The verifier is solver-free and fail-closed under fixed float64 componentwise
backward-error tolerances; malformed, primal, dual and objective faults are
negative controls. Complementarity remains diagnostic rather than a duplicate
acceptance condition.
No timing threshold or learned active-set/basis predictor is present.

Next action is v0.0.82: freeze fresh LP instances and a strong HiGHS Direct
path, then give a non-deployable diagnostic oracle the optimal basis/support
for free. Both Direct and oracle-compressed paths must reconstruct a full
primal/dual witness and pay the identical original-LP certificate check.
If that zero-model oracle cannot clear the predeclared complete-cost gate, do
not train a basis/active-set model. A positive screen would still leave Q3/Q4
open until cheap deterministic basis tests, a matched runnable Direct learner,
a no-compression ablation, training budgets and final holdouts are frozen.

v0.0.82 restart: the matched-control exact-basis oracle passes the frozen
**mechanism headroom** gate, not Q3 or Q4. All cases verify under the same
v0.0.81 original-LP certificate. Expanded-case oracle/best-Direct geometric
mean ratio is 0.0087784284, 12/12 expanded cases clear the >=20% condition,
and 12/12 matched control/expanded pairs clear >=2x scaling amplification.
The exact basis is free oracle metadata, so the result is non-deployable and
cannot be called a model speedup.

Next action is deliberately **not neural training**. First freeze and run a
deterministic/classical basis-discovery shortcut screen using only admissible
A,b,c-derived observables and equal-authority solver-native information. If
cheap discovery consumes the residual headroom, Q3 learning is unnecessary.
Only if meaningful verified headroom remains should a learned basis/active-set
route be compared with published learned-basis baselines, a same-budget
executable Direct learner, and the NEUMANN no-compression ablation. Q4 stays
OPEN.
