# NEUMANN 1: high-efficiency system research gates

Updated 2026-09-30 through v0.0.74. Goal: a system with substantially less **total** compute
at fixed independently verified capability, not victory in one solver subroutine.
"Model" means the complete inference system; a small learned component alone
does not constitute the desired model. No extrapolation from a synthetic
family to general reasoning capability is permitted.

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

## Q4 — Does NEUMANN itself beat a matched direct model?

**Open.** v0.0.31's 2×2 neural demonstration is a capability feasibility
result, not evidence of lower total compute. Hold fixed problem distribution,
training data budget, quality target, hardware, warm-up convention, and
verification contract. Report model inference, deterministic tooling, retries,
memory, and training amortization separately. At matched verified quality,
compare capability-versus-total-compute frontiers, not parameter counts.

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

Immediate priority: Q4's matched **model-level** comparison, not more MIS
subroutine wins. Direct answer-only classification is insufficient: include
a same-budget executable-program/IR predictor with identical access to the
executor and original-task verifier, as well as strongest cheap deterministic
input processing. Freeze training data, architecture/size budget, generated
surface holdouts, verified quality target, failure costs, inference and
training-amortization accounting before training. Reject a task up front if
a cheap deterministic parser/executor already saturates it. Graph-family
scaling and mature KaMIS integration remain optional mechanism follow-ups,
not the project's central next milestone. Do not call a trained component
or an oracle cost proxy a Q4 pass.
The v0.0.68 score-only lower bound rules out a checker-only rescue for the
existing n≤32 learned path.
