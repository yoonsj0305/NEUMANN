# NEUMANN 1: high-efficiency system research gates

Updated 2026-10-01 through v0.0.96. Goal: a system with substantially less **total** compute
at fixed independently verified capability, not victory in one solver subroutine.
"Model" means the complete inference system; a small learned component alone
does not constitute the desired model. No extrapolation from a synthetic
family to general reasoning capability is permitted.

Latest LP checkpoint: v082 admitted classical basis-discovery screening, not
training. In v083, observable column-norm rules passed the raw planted-family
gate (complete-cost/native geomean 0.0182276863; 11/12 expanded wins and
no-fallback cases), but failed after matched column normalization (1.1156167303;
0/12 wins and no-fallback cases). All 768 timed/warmup observations verified.
This is a generator-aware classical shortcut, not learned-model evidence.
Q3/Q4 remain OPEN. Require stronger norm-invariant classical comparators and
residual headroom before proposing a learned gate. See `../experiments/v0.0.83.md`
for the first retained archive and cross-BLAS source-reproduction limitation.

v084's scale-invariant least-squares/residual/primal/QR portfolio verified all
720 timed and 240 warmup paths, but every expanded case fell back to native.
Raw and normalized complete-cost geomean ratios are 1.3553861823 and
1.3559506383, with zero 20% wins. Decision:
`RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION`. Keep native default;
failed heuristics do not prove learning has value. Exact retained inputs and
primal/dual witnesses enable solver-free offline replay. Q3/Q4 remain OPEN.

v085 repairs LP's executable-Direct attribution boundary. For all 210 unique
case/basis pairs actually attempted in v084's first timed repeats, the same
supplied head interpreted as a NEUMANN basis or a closed Direct checked-basis
program produced identical stable outcomes, full witnesses and call ledgers
(36 accepted, 174 rejected per adapter). No training or timing was evaluated.
Decision: `LP_BASIS_ONLY_Q4_ATTRIBUTION_REJECTED`. Basis-only output relabeling
cannot establish Q4 against equal tool authority. This stops that attribution
route, not different learned architectures or the broader LP line. Q3/Q4 OPEN.

v086 implements the previously missing native HiGHS warm-start interface:
Direct can supply an advisory basis and pay native repair, original numerical
verification and any cold fallback. Correctness fixtures verify optimal,
nonoptimal and singular heads; negative controls deny acceptance on verifier
failure or deadline expiry. No timing audit, task admission or training was
performed. A future LP experiment must actually measure this comparator and
applicable learned-basis baselines; its mere existence does not admit learning.

v087 implements actual internal graph-state/edge removal in a runnable small
GNN. The sole declared corrective opened-development screen verified 864/864
calls and admitted bounded fitting: perfect-output complete-cost/classical
geomean 0.3118916013, 12/12 expanded >=20% wins, compact/full forward geomean
0.7374609639. Predictions were discarded and a certified oracle basis injected.
This is not learned discovery, a matched trained-model result or Q3/Q4 closure.
The first timing-confounded archive was lost in workspace replacement before
publication; the missing-evidence notice preserves that limitation. Only the
retained correction supports this candidate-specific gate. A separate fitting
and sealed final-evaluation preregistration is required; no paper reproduction
or general learned-LP superiority is established.

v088 completes the first actual compact/full/pointwise/wider-GNN learned study,
48 fresh training examples and two fixed seeds. All 768 final calls verified,
but compact seed87001 fails classical/learned-Direct savings and seed87002 is
not consistently <=.8 of strong learned Direct across IID and size/surface
groups. Only 0/6,0/6,1/6,0/6 cells solve its entire predicted basis without
native repair, below the >=4/6 requirement. First decision:
`FIRST_LEARNED_CANDIDATE_GATE_FAILED`. Native stays default; all eight weights,
train/final arrays, failures and full costs are retained. No favorable seed,
fit/timing rerun or holdout tuning. Q3/Q4 remain OPEN; this rejects the bounded
candidate, not every learned architecture or the broader research thesis.

v089 tests a new shared restricted-LP executor with all eight frozen v088
checkpoints, no new fitting and twelve new final inputs. All 960 calls certify
original answers, but compact/classical ratios are 2.6744/0.8924 (seed87001,
IID/shift) and 1.6897/1.2077 (seed87002). Compact/best learned Direct ratios
are 2.1758/0.9674 and 1.3747/1.3092. All four frozen conjunctions fail despite
no-full-rescue counts 3/6,6/6,5/6,5/6. Decision:
`FROZEN_CHECKPOINT_SHORTLIST_GATE_FAILED`. Preserve first bytes and the initial
post-measurement replay-schema failure; no solver/model/timing rerun or weakened
gate. Native stays default; Q3/Q4 OPEN. See `../experiments/v0.0.89.md`.

v090 deletes the compact model's late graph updates after the internal 2m
retained-set decision and permits the same coarse-head path to full Direct.
Only 16 already-opened v088 training inputs are screened; no new fitting or
final generation. All 1792 calls certify original LP answers and all 32 retained
sets agree. Ordered solver input differs on all 16/16 cases for both seeds;
the screen is an executor alternative, not an isolated FLOP attribution.
Complete-cost / best learned Direct ratios 1.8274 and 1.3203 both fail, as do
the frozen conjunctions. Decision `STOP_ONE_PASS_CANDIDATE`: no fresh final
budget is admitted, no global closure, no inference state-pruning claim against
the same early full Direct computation. Native default and Q3/Q4 OPEN remain.
See `../experiments/v0.0.90.md` for the first archive and paired-vs-pooled caveat.

v091 removes both least-squares feature fits and retrains all eight candidates
once with the original48 opened training inputs and equal budgets. The first
16 training inputs screen22 routes,1408/1408 certified answers. Both compact
seeds require full rescue on16/16 cases; compact/best learned Direct ratios
3.5577/3.6873 and all frozen conjunctions fail. Full16 with the same cheap
observables avoids rescue on11/10 cases, so the result does not establish that
cheap features are unlearnable. Stop this specific early-pruning/fit candidate,
admit no holdout, preserve all first weights and costs. This in-sample screen
does not establish generalization, Q3 or Q4. Native remains default. See
`../experiments/v0.0.91.md`.

v092 moves coarse selection after two full graph updates and retrains once,
protecting all eight previous cheap-feature checkpoints as concurrent controls.
All1920 original-LP answers certify, but compact avoids full rescue on only2/16
and0/16 cases. Complete-cost / best learned Direct ratios3.3394/4.0392 fail;
the full56.025541-second eight-model fit phase is charged at10000 queries and
does not rescue the decision. Stop this fixed late-pruning candidate without
admitting a holdout. This is not an isolated causal timing ablation or a claim
that all delayed selection methods fail. Q3/Q4 OPEN, native default unchanged.
See `../experiments/v0.0.92.md`.

## Q1 — Does learned structural discovery pay for itself?

**Decision on v0.0.33–0.0.36 exact affine-linear family: No.** v0.0.68
measures the entire existing frozen path; all 32/32 cases verify in each
method, but n=32 learned inference is ~95–104 ms versus ~3.2–3.4 ms for
exact direct, despite lower *final* solver arithmetic counts. The learned
scorer alone takes ~9 ms. Stop promoting this model on this family. This
does not establish impossibility on other tasks or larger dimensions.

## Q2 — Where is compression actually profitable?

**Open beyond the studied affine family.** v0.0.69 found no opportunity at
n≤32 after adding a fast numerical direct proposal with exact original
verification and exact fallback: n=32 direct took ~0.31–0.33 ms versus
~110–116 ms learned compression (4 new cases/cell, 5 repeats/case, all
verified). Define and measure a different family where direct verified computation is
costly enough that discovery, validation, reconstruction, and verification
can collectively fit beneath it. Select the family for principled structure
and genuine difficulty, not because one particular method won preliminary
timings. Require strongest cheap deterministic and optimized direct
baselines. Pre-register the minimum capability and costs before final data.

v0.0.70 gives **bounded positive combinatorial mechanism evidence**, not a
full pass: classical false-twin quotient on constructed MIS graphs gave
2.53×, 13.83× and 57.50× lower complete verified cost in three expanded
cells against native-presolve/symmetry-enabled HiGHS. Two m=1 controls were
near equal. The fourth expanded cell's direct MIP failed the 5s optimality
budget, so frozen overall verdict remains `CAPABILITY_UNREACHED` and no
speed factor exists there. Exact DP independently checked every completed
optimum. A stronger specialized graph/DP comparator and natural incidence
are required before promoting this known mechanism as a NEUMANN contribution.

v0.0.71–72 delete the redundant MIP in this artificial false-twin family.
Fresh v0.0.72 seeds with a separately implemented Bellman proof checker
certified all 162 timed paths. In the k=32,m=4 and m=8 cells, complete
quotient-DP cost was 7.52/11.35 ms versus direct proof-DP 180.85/1085.50 ms
and quotient MIP 46.54/40.90 ms. This clears the frozen constructed cost
gates, including the m=1 controls. It establishes a classical exact
subroutine opportunity, **not** superiority over modern graph reductions
or a NEUMANN learned/system-level advantage. The direct proof checker is
independent code but not an optimized production-grade graph solver.

v0.0.73's first four non-planted classic network checks all certified exact
optima across 60 timed calls, but the frozen small-graph routing gate
**failed**: 7.1%, 8.4%, and 12.3% routed cost reductions on the three
graphs with some false twins, versus a 10.3% cost increase on the no-twin
graph. No graph reached the 20% gain condition. These examples are not a
representative sample. Stop promoting exact-twin discovery as a broad
NEUMANN advantage on this evidence. The huge synthetic wins remain a
conditional classical mechanism, not product-level efficiency.

Literature boundary: LearnAndReduce (Großmann, Langedal and Schulz,
ACDA 2025) already combines GNN screening with exact MIS reductions.
Before allocating any graph-specific learned-discovery budget, compare
against this line of work and native exact KaMIS reductions; a simple
"learn the reduction location" claim is already occupied. See
`prior_art_positioning.md` for primary sources and license boundary.

## Q3 — Is learned discovery needed beyond cheap tests?

**Open.** Construct a matched-observable case where cheap deterministic
features are insufficient and a model predicts a useful compressible
structure from admissible input; no hidden oracle labels at inference.
Compare to a strong deterministic search and equal-budget direct learner.
If learned discovery costs more than it saves, disable it.

v0.0.74 screens an exact counting planner before spending training budget:
27 fresh synthetic graphs, 243 timed calls, all independently certified and
agreeing. Best-of-eight stochastic min-fill costs 1.7568× the per-graph
faster measured min-fill/min-degree reference in geometric mean, with zero
20% cost wins. Its non-deployable zero-planning diagnostic is 0.8824×, only
2/27 graphs with 20% wins, versus the frozen <=0.8× and >=9/27 thresholds.
Do **not** train to reproduce these selected orders on this n=16–32 input
distribution. This rules out neither better orders outside these eight
candidates nor larger/other tasks. It is an unlearned headroom rejection,
not a negative test of every possible learned planner. Learned tree
decomposition/ordering already has direct prior art; see the positioning map.


v0.0.75 is a maintenance gate, not progress on learned discovery. It removes
per-call recursive-closure cycles from both exact graph-DP paths while
preserving exact answers, memoized state counts and proof records. The first
frozen timing audit failed its strict every-cell <=1.20 no-regression rule
because one independent/direct cell measured 1.2094×; a later identical-tree
replication passed all caps. Preserve the first decision and the replication.
Keep the code change only as deterministic lifetime hygiene; make no efficiency
claim from it. The result does not change Q3 or Q4 status.


## Q4 — Does NEUMANN itself beat a matched direct model?

**Open.** v0.0.31's 2×2 neural demonstration is a capability feasibility
result, not evidence of lower total compute. Hold fixed problem distribution,
training data budget, quality target, hardware, warm-up convention, and
verification contract. Report model inference, deterministic tooling, retries,
memory, and training amortization separately. At matched verified quality,
compare capability-versus-total-compute frontiers, not parameter counts.

v0.0.76 implements the missing direct **atomic tool-program** comparator
for the v0.0.31 route. Its output labels can be renamed to a trusted solver
call or abstention with the same checkpoint/training. All 39,852 paired
post-head checks (486 already-opened texts x 82 possible head outputs) match
in status, answer and separate counters; 243 positive head-0 calls match
generated known solutions, and 243 near-negatives reject. No model inference,
training or timing was run. The v0.0.31 structural route contains no variable
compression and is downstream-equivalent to this bounded direct program
interpretation. Its answer-only learning gap cannot establish a compression
advantage. This is comparator repair, not a Q4 capability/cost result.

v0.0.77 integrates PR #82's frozen task-admission evidence alongside the
v0.0.76 program-parity witness. The zero-learned-parameter path retained
243/243 verified hidden-solution-equivalent positives and 243/243 rejected
near-negatives, so `REJECT_EXISTING_LINEAR_TASK_FOR_Q4` is preserved. The
canonical first CI summary remains unchanged; no new timing gate is opened.
This closes the old controlled grammar as a central Q4 candidate, not Q4.

v0.0.78 tests a new natural-language-source candidate's **reference-program
execution**, not learned semantic discovery: all 1,000 opened SVAMP expressions
had at most two arithmetic operations, with zero >=20% common-subexpression
sharing wins and local median complete expression work 0.040462 ms. One
equation/answer disagreement was retained (999/1,000 exact matches). This
rejects that bounded numeric-execution-compression target before training.
It does not settle model-side planning/compression or natural-language semantic
verification. The entire corpus is opened development data, not a final set.
Neither a supplied reference equation nor a gold answer may become inference
authority. Direct must have the same optimized program runtime.

v0.0.79 implements the shared-authority full-path measurement interface,
including complete five-route coverage, failed attempt/fallback costs,
verification scopes and investment accounting. Fault-injection fixtures
test these contracts; no new learner or independent final data is evaluated.
Caller-declared scopes/refs require separate audit and summaries remain
descriptive. This is measurement infrastructure, not a Q3/Q4 pass.

v0.0.80 screens a constructed integer relational planning task using native
DuckDB, a deterministic bag-multiplicity rewrite, four forced connected join
orders, and SQLite original-query verification. All 216 timed calls verified,
but the zero-model-cost post-hoc plan choice was only 3.3575% cheaper than
the strongest fixed Direct path; only 3/12 cases reached 20% savings. Do not
train on this bounded rejected target. The observed dominant cost was the
independent original-query replay, not a learned planning step. A next task
needs a cheaper independently checkable witness and the same verification
access for all comparators; waive neither capability nor original semantics.

v0.0.81 implements that missing verification boundary for one candidate
class: standard-form LPs with primal/dual certificates. The original LP can
be checked through primal feasibility, dual feasibility and objective equality
without calling an optimizer; complementary slackness is retained as a
diagnostic rather than a duplicate gate. Fixed float64 componentwise
backward-error tolerances and negative controls are tested. This is an enabling
interface, not evidence that certificate checking
is cheap enough in practice, that a basis predictor has headroom, or that
learning is needed. v0.0.82 must screen non-deployable basis/support oracle
headroom against a strong HiGHS Direct path while both pay the same verifier.

v0.0.82 first retained matched-control audit **passes only the mechanism
headroom admission screen**. All frozen routes/cases verified. On the 12
expanded cases, the geometric mean exact-basis-oracle / per-case fastest
verified Direct ratio is 0.0087784284; 12/12 expanded cases clear the 20%
reduction condition, and 12/12 matched n=m -> 16m pairs clear the >=2x
scaling-amplification condition. Decision:
`ADMIT_BASIS_DISCOVERY_SEARCH_NOT_MODEL_TRAINING`.

This does not close Q3. The oracle is given the exact optimal basis for free on
an author-generated constructed family. Before any learning, cheap
observable-only deterministic/classical discovery and solver-native warm-start
information must be tested under equal authority. It also does not close Q4:
no learned NEUMANN route, matched executable Direct learner, no-compression
ablation, training amortization, or fresh natural/held-out workload has been
evaluated.

## Q5 — Are scaling and cross-domain reuse real?

**Open.** Only after Q2–Q4 pass: test larger apparent sizes and independent
domains, randomized surface forms with held-out structural classes, cache
misses and invalidation, and separately report cold and warm traffic.
Estimate uncertainty in the log-compute slope; do not infer improved slope
from the reduced solver dimension alone.

## Stop / advance rules

Advance only on exact, independently checked success and end-to-end
iso-capability total compute. A result that improves a proxy but worsens
complete time is a failed compute gate, not a partial speed win. Retain
negative results and costs for all failed proposals. If a cheap deterministic
component saturates a family, do not train a model merely to have one.

Immediate priority is now the **Q34 joint architecture gate**, not serial Q3
then Q4 tuning. Q3 and Q4 remain analytical labels, but a system advances only
when it recovers enough available structural utility and discovery costs fit
inside the saved compute under equal original-task verification. The internal
engineering floor is utility recovery >=0.80 and discovery cost <=20% of
pre-discovery savings, with complete cost below Direct. See
`q34_joint_gate.md`.

Before any new training, screen the representation ceiling. Then compare
materially different deterministic-first, minimal learned, full-information,
and adaptive support architectures under one evaluator. Delete Pareto-dominated
families immediately. Three materially different adequate-ceiling families
failing the same Q34 gate ends local tuning and triggers representation /
objective / task redesign. One fresh Q34 pass advances directly to Q5 with
fallback. The v0.0.68 score-only lower bound still rules out a checker-only
rescue for the existing n<=32 learned path.


## v093–94 selector and input-compaction boundary

v093 rejects CG3 point parity and more fitting: strongest cheap classical
shortlist32/48, point coverage46→44/45. v094 preregisters fixedCG5 and a
point selector before all graph messages. Both seeds preserve46/48 required
columns and graph terms fall to1/8 of full16; this admits only a paid screen.
The first31-route cost screen certifies1984/1984 answers but fails both
frozen conjunctions. A focused pytest process overlapped timing; all first
bytes and a no-positive-cost-claim notice are retained. No clean quantitative
performance estimate or speed claim follows. No new fit/holdout is admitted.
Point-only chooses exactly the same2m retained set as the routed graph, so
additional graph work must earn its cost through useful finer proposals;
state-work reduction alone does not establish Q4. Native default, Q3/Q4 OPEN.

v095 closes that attribution loophole by construction. The compact route sets
`keep=top2m(point)` and then asks the graph to rank exactly those2m columns;
its2m shortlist must therefore be the same support as point-only, up to a
permutation. The restricted LP has identical variable support. The graph can
only alter the exact-m basis proposal/order under this contract. Decision:
`STOP_SAME_SUPPORT_GRAPH_REFINEMENT_NO_NEW_FIT`. Do not fit another variant
with this same support authority. This is candidate-specific, not a global Q3
or Q4 closure; a successor must change verified structural authority or target
a different task/family.

v096 performs the first representation-ceiling screen before any new training.
The frozen point-selected2m support contains the complete hidden reference basis
on46/48 cases for both seeds (95.83%) and mean basis recall is0.999349. Early
compression OFF exposes all columns, but the frozen full graph still produces
0/48 original-LP-certified exact-m proposals on both seeds; compact produces
0/48 and1/48. Full-information certificate gains are0 and-1, far below the
frozen +4 rescue threshold. Decision:
`DISCOVERER_BOTTLENECK_DOMINATES_EARLY_SUPPORT_LOSS`.

This does not pass Q34 or close Q3/Q4. It stops further pruning-point tuning on
this candidate and changes the next target from exact-m basis generation to
verified support discovery plus restricted execution and charged fallback.
The next tournament is specified in `q34_architecture_tournament.md`.
