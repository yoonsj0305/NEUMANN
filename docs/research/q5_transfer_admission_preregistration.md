# Q5 independent-construction admission — v104 first protocol

Status: implementation contract, UNARMED until final-head CI and merge. No new
registered source, measurement, model forward or fit has occurred at publication.
The v103 first Q5 result remains `Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED`.
This protocol does not replace that result and cannot close global Q5.

## 1. Question and first-principles boundary

Can even a free exact-support-and-dual ceiling save complete verified work on
two independently constructed LP classes against the strongest DECLARED Direct
envelope? If not, allocating frozen-checkpoint transfer or fitting to that class
has no demonstrated economic justification under this executor.

This is admission research, not a model evaluation, a tenfold-improvement promise
or an impossibility theorem. Two new construction classes share one LP backend
and original primal/dual verifier. They are NOT independent computational domains,
natural workloads, cache-invalidation evidence or a Q5 cross-domain pass.

## 2. Delete unnecessary assumptions before optimization

Delete the demand that an optimal primal support contain exactly m variables:
assignment optima have only k nonzeros while m=2k-1. No artificial square-basis
completion or repeated fitting is needed for this optimistic ceiling. Preserve
original-task verification, specialized baselines, failures and complete costs.
The Oracle receives BOTH exact primal support and an original optimal dual for
free. This is deliberately more privileged than v103's basis-only diagnostic;
its ratios are not interchangeable with v103 utility or model ratios.

## 3. Frozen inputs and interfaces

There are 32 sources: two families × k in {8,16,32,64} × four replicates. Seeds
104000..104031 are assigned in family/level/replicate order by the checked-in
`experiments/q5_transfer_contract.py`. Audit collision with latest repository
state before arming; a collision blocks this protocol rather than reseeding it.

| Class | Original standard-form task | Rows m | Columns n |
|---|---|---:|---:|
| assignment | Minimum-weight perfect bipartite matching; all k row sums and first k-1 column sums equal 1 | 2k-1 | k² |
| basis_pursuit | Minimize sum(x), [X,-X]x=b, x>=0 | 2k | 32k=16m |

Assignment costs are independent integer draws in [1,10007]. Basis-pursuit X has
independent normal entries and unit column norms; b=X beta, where beta has
max(2,m/8) randomly located normal nonzeros. The planted beta is discarded and
is never answer authority: the unrestricted original native optimum supplies
the offline exact-support/dual label. Both are author-constructed workloads.

Public query authority is original A,b,c only. Oracle alone receives the frozen
offline label. The specialized assignment route validates original grammar
before use. No model, learned ranker, fit, original-label shortcut in Direct,
cross-query array cache or hidden reference solution is permitted.

## 4. Equal verification and strong Direct envelope

Every answer must satisfy the same frozen v081 float64 original-LP primal
feasibility, dual feasibility and objective-equality certificate. Failed or late
answers remain failures regardless of a solver's success flag.

Direct routes are cold native HiGHS simplex with presolve and SciPy `highs-ipm`,
both one thread and 5 seconds. Assignment also includes optimized SciPy
`linear_sum_assignment` (modified Jonker–Volgenant), plus independently built
dual difference-constraint potentials and the same original LP certificate.
The route receives no offline label. Grammar checking, matching, dual creation
and original verification all count.

The reference for each source is the minimum complete-cost median of its
declared Direct routes. This per-case post-hoc envelope is NON-DEPLOYABLE and
optimistically strong: no uncharged selector is claimed. It prevents ignoring
an applicable specialized implementation, but does not establish dominance
over every existing solver or specialized L1 algorithm.

Oracle restricts to the frozen original native nonzero support, runs the same
native checked solver, lifts the primal back to the original columns and uses
the given original dual. Subproblem setup, solve, lift and original certificate
are charged. Free support AND dual and free Oracle cold startup intentionally
make this an optimistic headroom screen, not an executable NEUMANN system.

Primary implementation references:
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html
- https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html

## 5. Complete-cost and capability gates

Four fresh persistent route workers start only AFTER all source bytes are
frozen. External process startup to READY is retained per route. Every request
re-reads and verifies gzip source bytes and decodes original arrays. Complete
request time includes input I/O/decode, solver imports/setup/work, witness/dual
creation, original verification, JSON transport and receipt. No kernel-only
timing may substitute for it. Failures retain their elapsed work and witnesses.

All 112 route/source pairs have one warmup, then three timed repeats: 448
observations. Order is all shuffled warmups BEFORE shuffled timed observations,
with fixed order seed104991. Timing is serial in one dedicated worker job,
without concurrent fitting, replay or tests. Research source generation, native
labeling and source certificate preparation occur before the timing window and
are explicitly not deployable costs of this optimistic Oracle. Their records
and controller wall time remain retained. No model investment is invented.

Complete cost is median of three timed external observations plus Direct cold
startup/10000. Oracle cold is free for the ceiling, but actually recorded.
Q=1 costs also include full Direct startup and are descriptive, not an extra
positive gate. Peak RSS is descriptive, not a cost proxy. The exact runtime is
Python3.12, NumPy2.3.5, SciPy1.17.0, sklearn1.9.1, threadpoolctl3.7.0,
highspy1.15.1, torch2.14.0+cpu, Ubuntu24.04, one thread, OpenBLAS HASWELL.
Torch exists only for parent-authority checks and forbidden-forward guards.

Every warmup and repeat of EVERY declared route must be capable within the
complete 5-second budget. A failed case has NO speed ratio. No failed route,
source or size may be removed because another route succeeds.

For each family, all four cells must pass:
- k8 control: sum Oracle / sum best declared Direct <=1.20.
- k16,32,64 individually: that ratio <=0.80 AND at least 3/4 source ratios <=0.80.

The four replicates are a bounded admission screen, not a statistically powered
generalization claim. There is no fitted slope or confidence-bound claim here.
All cells and source ratios will be published; favorable pooling is forbidden.

## 6. First-run integrity and Degraded Mode

Reserve the exclusive `v104_transfer_admission_first` evidence directory BEFORE
scientific imports or generation. Record head, runtime, immutable source hashes,
native labels and original witnesses in a chained ledger. Each generated source
is stored BEFORE rejecting a failed label. A failure stops registration and
retains partial first evidence; it does not admit a replacement source.

Only the first workflow attempt may run. No dispatch, retry button, replacement
seed, budget extension, post-result gate adjustment or model tuning is allowed.
Publish partial evidence even if the workflow fails. A completed result is
independently replayed from all retained source and observation bytes with
generation, Highs.run, linprog, assignment optimizer and model forwards forbidden.
After opening, external first-head/raw-file/terminal hashes must pin that archive.

Degraded Mode remains original checked native (or the declared specialized
assignment Direct where its grammar is known). Headroom failure disables any
new transfer/fitting budget for that family under this protocol.

## 7. Decisions and Q5 closure ledger

| Observation | Frozen decision | Next authority |
|---|---|---|
| Any declared route capability failure | CAPABILITY_UNREACHED_NO_TRANSFER_BUDGET | Retain failure; no replacement or transfer |
| Capable, any frozen cost cell fails | STOP_FAMILY_NO_ORACLE_HEADROOM | Stop family under this executor; no new fit |
| All family cells pass | ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING | Separately preregister first transfer with both existing frozen checkpoints |

A positive ceiling does NOT establish learned discovery, matched-Direct model
advantage, transfer, or new-training admission. Neither family can close Q5:

| Global requirement | Current evidence boundary |
|---|---|
| Larger-size complete iso-capability scaling | v103 first gate failed; unchanged |
| Actual frozen-model structural/task transfer | Not tested by this zero-model audit |
| Independent computational domains/natural relevance | Both classes share LP; absent |
| Unseen randomized surface/held-out class behavior | Not supplied by these source classes |
| Cache misses, invalidation, cold/warm traffic | Cold/warm measured; caching/invalidation absent |
| Log-compute uncertainty and preserved failures | v103 restricted slope evidence; cannot rescue failure |

`global_q5_closed=false` and `cross_domain_pass=false` are invariant in the
executable protocol, including wholly favorable synthetic test fixtures.

## 8. Investment accounting, risks and buffers

The manufacturing Idiot Index (finished price/raw-material cost) is undefined
for this code experiment: no material-price inputs exist. Do not fabricate an
economic index. Report measured complete-cost ratios and descriptive resource
use. Existing model fitting is irrelevant to this zero-model ceiling and must
be charged under a future actual-model transfer contract if admitted.

Risks include unattainably privileged Oracle labels, native support numerical
degeneracy, specialized alternatives not declared here, four-replicate sampling
uncertainty and shared-backend dependence. A positive result is only sufficient
to spend on a separately frozen test, not sufficient for deployment or Q5.

Work breakdown: implementation/math fixtures → final-head CI/merge → first
exclusive registration/admission → retained-byte independent replay → result
publication/CI/merge. Allow one CI cycle as engineering buffer and the frozen
5-second per-route deadline as capability limit; buffers NEVER permit another
scientific attempt. There is no fixed calendar completion promise.

## 9. Single iteration and restart boundary

This iteration tests ONE hypothesis: this exact optimistic Oracle has complete
cost headroom on the two fixed new construction classes. Do not turn the result
into multiple local sweeps. If both fail, document the stopped budgets and choose
a genuinely different task/representation through a new future preregistration.
If a family passes, the next iteration must specify frozen-checkpoint transfer,
fresh unobserved inputs, strong matched Direct and all failures BEFORE opening.

At implementation publication: source/measurement trigger absent, registered
inputs unopened, v103 first archives unchanged, repository release remains103.
The scientific v104 result document is created only after retained first evidence
exists. Keep canonical research-journal checkpoints linked to the exact head.
