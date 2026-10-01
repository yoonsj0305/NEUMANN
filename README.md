# NEUMANN 1

**NEUMANN 1** is a research-engineering project for **Structural Compression: reducing computational degrees of freedom before solving**.

> Discover the minimal sufficient computational structure, execute only what remains, and verify the original problem.

## Research thesis freeze

After v0.0.31, NEUMANN is no longer positioned primarily as "LLM + symbolic solver", "structure-first reasoning", or "IR + solver + verifier".

Those mechanisms are treated as enabling components with substantial prior art.

The central research hypothesis is now:

> **Can an AI reduce reasoning cost by discovering a minimal sufficient computational structure before solving?**

The stronger scaling question is:

> **Does Structural Compression change how verified reasoning compute grows with problem complexity?**

Canonical target architecture:

    Raw Problem
        ↓
    Semantic Parse
        ↓
    Structural Discovery
        ↓
    Structural Compression
        ↓
    Minimal Structural IR
        ↓
    Algorithm / Solver Router
        ↓
    Specialized Execution
        ↓
    Independent Verification
        ↓
    Result
        ↓
    Canonical Structure Memory

The critical distinction is:

    Structure discovery ≠ Structural Compression

NEUMANN must not merely re-encode all variables and constraints into an IR. It should attempt to remove safely reconstructible variables, redundant constraints, equivalent states, symmetry-related distinctions, and other computational degrees of freedom before execution.

Every learned reduction remains advisory. A compression certificate and independent checks retain execution authority.

See:
- `docs/research/structural_compression_thesis.md`
- `docs/research/prior_art_positioning.md`
- `docs/research/core_question_gates.md`
- `docs/experiments/v0.0.32.md`

## Current engineering baseline

**v0.0.91 — Cheap features learn in full models, but early pruning fails**

Retrain all eight compact/full/pointwise candidates once with observable
features that omit both least-squares input fits. The preregistered in-sample
screen certifies all 1408 original-LP answers, but both compact seeds require
full rescue on all 16 cases and cost 3.5577/3.6873 times best learned Direct.
Full16 avoids rescue on 11/10 cases with the same inputs. Stop this specific
candidate without a new holdout; Q3/Q4 remain OPEN and native remains default.
The first data, weights, fit costs and negative verdict are preserved in
`docs/experiments/v0.0.91.md` and its byte-exact archive.

**v0.0.90 — Delete late graph work, but stop the one-pass candidate**

A preregistered opened-training screen gave all Direct models the same early
coarse-head access. All 1792 original-LP checks and 32 retained-set parity checks
passed, yet compact/best learned Direct complete-cost ratios were 1.8274 and
1.3203. Both seeds fail the frozen gate. No new fit or final evaluation; Q3/Q4
remain OPEN. Retained sets agree, but solver column orders differ. The same
one-pass graph computation is available to full Direct, so it is not an
inference-compaction attribution result. Keep native default; see
`docs/experiments/v0.0.90.md` and the preserved first archive.

**v0.0.89 — Shared shortlist fails with frozen learned checkpoints**

All eight frozen v088 models received the same restricted native executor and
paid full original-LP checking/rescue on twelve new constructed inputs. All
960 observations certified original answers, but every seed/group failed the
unchanged complete-cost gate. Compact/best learned Direct ratios were
2.1758/0.9674 and 1.3747/1.3092; Q3/Q4 remain OPEN. The first byte-exact archive,
failed replay-schema notice and solver/model-free replay are retained. No new
fitting or timing rerun. Keep native default. See `docs/experiments/v0.0.89.md`.

**v0.0.88 — First actual learned model comparison fails the frozen gate**

Four runnable models x two seeds trained on 48 fresh cases. All 768 final
calls certified original LP answers, with equal answer/basis/native-repair
authority and paid failures. Compact seed87002 reduced some costs, but
seed87001 lacked classical/learned-Direct superiority, and native repair was
needed on 12/12 and 11/12 cases. No stable matched-model pass: decision
`FIRST_LEARNED_CANDIDATE_GATE_FAILED`; Q3/Q4 remain OPEN. All exact train/final
inputs, eight weights, losses and failed/accepted witnesses are retained in
the first archive with solver/model-free replay. Keep native default. See
`docs/experiments/v0.0.88.md` for all four comparison rows and amortization.

**v0.0.87 — Real model-state compaction clears bounded fitting admission**

Runnable compact/full GNNs differ in actual retained states and edges, not
the name of a shared basis head. The sole declared corrective opened-data
screen verified 864/864 paths. Paying real untrained forward/features while
injecting a perfect basis gave complete-cost/classical geomean 0.3118916013,
12/12 expanded >=20% wins, and compact/full forward geomean 0.7374609639.
This is a nondeployable perfect-output diagnostic: it admits bounded fitting,
NOT learned accuracy or Q3/Q4 closure. The first run was timing-confounded;
its uncommitted archive was lost during workspace replacement. That retention
failure is explicitly disclosed, not replaced with reconstructed evidence.
The correction and missing-evidence notice are retained in the v087 manifest.
See `docs/experiments/v0.0.87.md`. Native remains the deployed default.

**v0.0.86 — Native warm-start comparator interface (performance untested)**

Direct can now supply the same advisory basis to native HiGHS simplex and
let it repair nonoptimal/singular proposals. Full original-LP certificates
retain authority; invalid proposals, failed verification and shared-deadline
exhaustion fail closed with charged cold fallback. Setup, failed attempts,
verification and native call counts are retained. Eleven focused tests cover
real native repair and negative controls. This completes a comparator
interface, not a learned experiment or speed gate. Native stays the default
on the normalized family; Q3/Q4 remain OPEN. See `docs/experiments/v0.0.86.md`.

**v0.0.85 — LP basis-only attribution rejected under executable-Direct parity**

A closed Direct program can execute the same supplied basis head with the
same LU/reconstruction, original-LP certificate and charged native fallback.
On 210 unique case/basis pairs from v084's already-opened retained inputs,
both adapters agreed exactly in stable outcomes, full primal/dual witnesses
and call ledgers: 36 accepted and 174 rejected on each side. The diagnostic
disabled native fallback; fresh-process fixtures separately cover paid
fallback, singular bases, invalid heads and abstention. No learner, new
holdout or speed ratio was tested. Decision:
`LP_BASIS_ONLY_Q4_ATTRIBUTION_REJECTED`. Stop treating a basis-only head versus
a cold full solver as a central Q4 comparison; this does not reject all LP
learning or different architectures. Q3/Q4 remain OPEN. The first runtime
preflight failure is retained alongside the first completed untimed comparison.
See `docs/experiments/v0.0.85.md` and the results manifest.

**v0.0.84 — Scale-invariant classical portfolio fails the cost gate**

An observable-only portfolio now normalizes received columns, then proposes
bases using least-squares dual residual trimming, minimum-norm primal scores
and pivoted QR. Its complete cost includes all proposal work, failed attempts,
original-LP checking and native fallback. The explicit first-audit runner
retains exact inputs and primal/dual witnesses for solver-free offline replay.
The first audit verified all 720 timed and 240 warmup observations, and offline
witness replay passed without solving or regenerating inputs. Expanded
portfolio/native geomean complete-cost ratios are 1.3553861823 raw and
1.3559506383 normalized, with 0/12 >=20% wins and 0/12 no-fallback cases in
both forms. Decision: `RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION`.
Keep native as default on the normalized family. No learned training or Q3/Q4
pass follows from failed heuristics. See `docs/experiments/v0.0.84.md` for
the frozen gate, first split archive and portability limits.

**v0.0.83 — Classical norm shortcut consumes raw-family headroom**

The first retained observable-only audit verified all 576 timed and 192 warmup
records. On 12 expanded raw cases, discovery plus checking and any fallback
had geometric mean complete-cost ratio `0.0182276863` versus best native;
11/12 cleared the 20% reduction threshold and avoided fallback. On matched
column-normalized cases the ratio was `1.1156167303`, with 0/12 wins and
0/12 avoiding fallback. Decision: `CHEAP_DISCOVERY_CONSUMES_RAW_FAMILY_HEADROOM`.
This is a classical, generator-aware shortcut on a constructed family, not a
learned NEUMANN speedup. Q3/Q4 remain OPEN; normalization failure does not
authorize model training. Next: stronger norm-invariant classical comparisons
before a new residual-headroom gate. See `docs/experiments/v0.0.83.md` for the
preserved first archive, timing scope and cross-BLAS reproducibility limit.

**v0.0.82 — Oracle-basis headroom admitted for discovery screening**

The first retained matched-control audit reached verified capability on every
frozen route and case. Across the 12 expanded `n=16m` cases, the geometric
mean oracle/best-Direct complete-cost ratio was `0.0087784284`; all 12/12
expanded cases cleared the >=20% reduction condition, and all 12/12 matched
`n=m` -> `16m` pairs cleared the >=2x scaling-amplification condition.
The decision is `ADMIT_BASIS_DISCOVERY_SEARCH_NOT_MODEL_TRAINING`.
This is a constructed, non-deployable exact-basis oracle diagnostic, not a
NEUMANN model speedup: basis discovery cost is zero by design. Q3/Q4 remain
OPEN. Next step is deterministic/classical observable-only basis discovery
screening before any learned predictor. See `docs/experiments/v0.0.82.md` and
the preserved `v082_first_audit.json`.

**v0.0.81 — Certificate-first LP verifier contract**

Standard-form LP candidates can now carry a primal/dual witness checked against
the original coefficients without calling an optimizer or replaying the solve.
The verifier checks primal feasibility, non-negativity, dual feasibility and
primal/dual objective agreement under fixed float64 componentwise backward-error
tolerances; complementary slackness is retained as a diagnostic. Fault-injection
tests and a bounded HiGHS integration smoke exercise the contract.
This is enabling infrastructure only: no timing gate, learned basis predictor,
or Q3/Q4 result is claimed. The next gate is a zero-model basis/support
headroom screen in which every path pays this same original-LP verification.
See `docs/experiments/v0.0.81.md`.

**v0.0.80 — Constructed relational planner target rejected before training**

All 216 timed calls and 72 warmups matched a separate SQLite original-query
execution exactly. Even a non-deployable zero-model choice among six measured
policies reduced complete cost by only 3.3575% against the strongest fixed
Direct policy; >=20% savings occurred in 3/12 cases, below the frozen gate.
The exact deterministic multiplicity rewrite was also available to Direct.
Original-query recomputation dominated observed verification cost. No model
is trained on this bounded constructed target and Q3/Q4 remain open.
See `docs/experiments/v0.0.80.md`; the preserved final audit is not rerun by CI.

**v0.0.79 — Shared-authority full-path measurement interface**

The next model experiment can measure all five required comparator routes
with shared execution/verification callbacks, observable-only proposer
arguments, retained failed attempts and deterministic fallback costs.
Label matches and expression checks do not count as original-task verification.
Complete paired records are required for descriptive ratios. This is
instrumentation with fault-injection fixtures, not new training, task admission
or a model efficiency win. Q3/Q4 remain open. See `docs/experiments/v0.0.79.md`.

**v0.0.78 — Natural arithmetic execution target rejected before training**

An opened-development audit of all 1,000 official SVAMP reference equations
found only 0–2 arithmetic operations per program and zero >=20% wins from
shared common-subexpression execution. Median complete expression parse,
exact execution and independent expression check was 0.040462 ms locally.
999 equation results matched source answers exactly; one equation/answer
disagreement remains archived rather than silently fixed or dropped.
No raw word problem was solved and no model was trained. This rejects only
this numeric-execution-compression target; semantic model/planning costs
were not measured. Q3/Q4 remain open. See `docs/experiments/v0.0.78.md`.

**v0.0.77 — Integrate the interrupted Q4 admission audit**

The formerly conflicting PR #82 audit is integrated without replacing
v0.0.76's atomic-program comparator. Its unchanged first CI result rejects
the old controlled linear-text task for Q4: a zero-learned-parameter path
verified all 243 positives against hidden solutions and rejected all 243
paired unsupported forms. The first summary and its missing per-row timing
archive limitation are preserved. Observation summaries now reject duplicate,
missing and inconsistent evidence. No new timing gate or model training is
claimed; Q3/Q4 stay open. See `docs/experiments/v0.0.77.md`.

**v0.0.76 — Direct tool-program comparator parity (not a Q4 pass)**

The v0.0.31 structural classifier can also be interpreted as a direct
atomic tool-program predictor using the same checkpoint and labels.
On 486 already-opened positive/near-negative texts and all 82 possible
head outputs, 39,852 paired downstream checks had zero mismatches in
status, answer and individual bookkeeping counters. This is a post-head
contract witness, **not** 39,852 model inferences, new training, or a latency
advantage. The old answer-only comparison cannot isolate compression from
tool access. Q3/Q4 remain open. See `docs/experiments/v0.0.76.md`.

**v0.0.75 — DP lifetime hygiene (correctness fix; first timing gate failed)**

Both exact graph-DP paths now avoid per-call self-referential recursive
closures, so memo state is released without waiting for cyclic GC on normal
and budget-exceeded exits. Exact answers, memoized state counts and full
proof records match the embedded legacy implementations. The first frozen
25-case audit retained the preregistered negative verdict
`LIFETIME_FIX_CORRECT_BUT_PERF_REGRESSION`: all aggregate geometric means
were near 1.0, but one independent/direct cell measured 1.2094× versus the
1.20 no-regression cap. An identical-tree clean replication later passed all
caps; it is recorded as timing-variance evidence and does not replace the
first result. Keep the lifetime fix as runtime hygiene, with **no speedup or
NEUMANN-efficiency claim**. See `docs/experiments/v0.0.75.md`.


**v0.0.74 — Elimination-order learning headroom screen (negative)**

All 243 timed calls on 27 frozen synthetic exact-counting graphs verified
and agreed. Best-of-eight stochastic min-fill cost 1.76× the faster measured
min-fill/min-degree baseline (geometric mean). Even a **non-deployable**
zero-planning diagnostic ratio of 0.882 failed the predeclared 20% aggregate
gain and 9/27 gain-incidence conditions. Do not train on this bounded
candidate-order/distribution screen; no learned or model-level advantage
was measured. Raw concurrent-test-contaminated timings were preserved and
replaced by a sequential audit with unchanged inputs and thresholds.
See `docs/experiments/v0.0.74.md`.

**v0.0.73 — Small non-planted graph routing gate (negative)**

Four provenance-backed classic networks and 60 timed exact-proof calls
showed no 20% complete-cost win for exact twin routing: reductions were
7–12% on three graphs with some twins, while one no-twin graph incurred
~10% overhead. The preregistered gate failed. This prevents extrapolating
v0.0.72's planted large wins to general networks. See
`docs/experiments/v0.0.73.md` and archived raw measurements.

**v0.0.72 — Proof-carrying DP and exact quotient (constructed mechanism)**

After removing the redundant MIP executor and using a separate Bellman
proof checker, all 162 timed paths on a fresh constructed MIS holdout
certified the same optima. At base k=32 and twin multiplicities 4/8,
quotient DP cost 7.52/11.35 ms end-to-end versus direct proof-DP
180.85/1085.50 ms; quotient MIP cost 46.54/40.90 ms. Frozen complete-cost
gates passed on this artificial family. This is a known classical reduction
and specialized DP, **not** a learned or state-of-the-art graph advantage.
See `docs/experiments/v0.0.72.md` and its archived raw audit.

**v0.0.70 — Constructed combinatorial compression (bounded positive mechanism)**

Classical false-twin quotient reduced full verified MIS cost by 2.53×,
13.83× and 57.50× in three constructed expanded cells versus HiGHS with
native presolve and symmetry enabled. Every completed optimum was checked
by separate exact integer DP and original-edge feasibility. Two m=1
controls were near equal, but direct execution failed the 5s optimality
budget in the fourth expanded cell; overall gate is **CAPABILITY_UNREACHED**,
not PASS. A summary ratio for that censored cell was corrected to null,
with original raw trials preserved. No learned or graph-SOTA advantage is
claimed; see `docs/experiments/v0.0.70.md`.

**v0.0.69 — Verified fast direct baseline (negative opportunity gate)**

With a dense numerical proposal, exact integer-equation verification on
the original problem, and fail-closed exact fallback, direct inference on
the new n=32 affine-linear cases took ~0.31–0.33 ms median. Learned
compression took ~110–116 ms; all answers were exactly verified, with zero
fallbacks in the 160 timed fast-direct calls. This studied family has no
structural-compression opportunity at these dimensions against a stronger
direct method. Look elsewhere rather than tuning the learned scorer here.
See `docs/experiments/v0.0.69.md`.

**v0.0.68 — Full-path learned compression gate (negative)**

At identical exact verified capability on a frozen affine-linear family,
the 289-parameter learned candidate scorer plus its checker took about
95–104 ms at apparent dimension 32 versus 3.2–3.4 ms for the full exact
direct solve. Its score computation alone took ~9 ms. Earlier reduced-solver
operation counts omitted repeated tentative solves and thus do not imply a
complete-system efficiency advantage. Stop deploying learned compression
on this family; seek a genuinely compute-limited regime and compare to
strong direct baselines before claiming model-level efficiency. See
`docs/experiments/v0.0.68.md`.

**v0.0.67 — Strong batched grid comparator (negative routing gate)**

The known PTDF-style multiple-RHS path was compared with per-outage
rank-one reuse and a frozen query-size router under identical full-angle
output and original-equation verification. On the separately selected
300-bus standard network, the router's four-workload median sum was
20.872 ms versus 20.369 ms for fixed batching; the predeclared 10%
advantage failed. Use batching for this measured workload and delete the
extra router. These are local DC approximation diagnostics, not a NEUMANN
algorithm novelty or AC power-system safety result. See
`docs/experiments/v0.0.67.md`.

**v0.0.66 — Verified DC power-grid outage reuse (positive mechanism, limited)**

For the externally sourced 118-bus test network, one factorization reused
across 177 connected single-branch outages took 20.779 ms median versus
94.409 ms for repeating generic sparse factorization, including topology
screening and every original-outage residual check. Nine islanding outages
are outside the defined connected-outage capability. This is a known
rank-one/LODF-style method; a mature specialized baseline and untouched
networks are still required before any NEUMANN architecture claim. See
`docs/experiments/v0.0.66.md`.

**v0.0.65 — Persistent recourse LP diagnostic on SEMI3 (negative)**

Retaining the LP basis removed most recourse-model rebuilds: 103 LP runs used
five constructions in a 19.722-second complete-path diagnostic. Yet no
original-feasible candidate appeared in 24 master iterations. Native HiGHS
returned an independently verified feasible solution within the same nominal
20-second budget. The SEMI instances share a core, so this is not a new
independent holdout or an iso-capability speed comparison. Stop tuning this
core and seek a verifiable structural reduction on a new family. See
`docs/experiments/v0.0.65.md`.

**v0.0.64 — SEMI2 recourse decomposition exploration (negative opportunity)**

An exploratory classical dual-cut master removed the two 9,802-variable
recourse blocks from its integer master but generated no complete feasible
answer within 20 seconds. Native HiGHS returned an independently verified
feasible MIP incumbent in 19.089 seconds (objective 1711.347, gap 0.204).
No iso-capability timing ratio or learned discovery claim follows. The
candidate stays out of runtime. See `docs/experiments/v0.0.64.md`.

**v0.0.63 — SEMI two-stage input and original-model verifier (enabling)**

Hash-pinned SIPLIB semiconductor tool-planning SMPS data are expanded into
2/3/4-scenario MIPs with the published dimensions. An independent verifier
checks original scenario rows, first-stage integrality and expected
objective; a short sanity run and two rejection controls pass. No new
reduction or iso-capability speed comparison has been run. See
`docs/experiments/v0.0.63.md`.

**v0.0.62 — Residual motif screen after native MIP presolve (descriptive)**

Three previously inspected MIPLIB instances were screened for equality
leaves, exact duplicate columns and disconnected components after native
HiGHS presolve. The new fixed-cost flow example `beasleyC3` has none of
these simple residual motifs; `n5-3` has five tiny separate components
totaling 11 of 2,139 presolved variables. No new reducer or speed claim
follows. See `docs/experiments/v0.0.62.md`.

**v0.0.61 — Original-MIP affine reduction, corrective capability gate (negative)**

The v0.0.60 frozen objective/gap conjunction was unattained by either arm;
its timing ratio was not an iso-capability result. In a separately frozen,
explicitly post-result-calibrated v0.0.61 rerun, all six trials met the
corrected objective/gap gate and passed original-MIP verification. The
763-variable affine reduction was 1.313× slower than native HiGHS on median
complete-path time (9.871 vs 7.520 s). It remains out of the runtime.
This is a nonblind, single-instance negative gate, not an independent
holdout or scaling result. See `docs/experiments/v0.0.60.md` and
`docs/experiments/v0.0.61.md`.

**v0.0.59 — Bounded affine elimination against native LP presolve (negative)**

On one nonblind MIPLIB instance's continuous LP relaxation, a verified
substitution removed 763 variables but rewrote 763 bound rows. The full
candidate path was 10.18× slower than the original LP with native HiGHS
presolve (161.74 vs 15.89 ms median). This is a local negative gate, not
a MIP or general impossibility result. See `docs/experiments/v0.0.59.md`.

**v0.0.58 — Existing-presolve workload triage (descriptive)**

Across 240 official MIPLIB benchmark instances, trivial presolve already
removes at least half the variables in 20. A stronger native HiGHS presolve
on one hash-pinned aggregation-rich example removes 796/2,500 variables,
where the raw trivial presolve removes only 29. This is an opportunity-screen
correction, not a NEUMANN speedup or solve result. See
`docs/experiments/v0.0.58.md`.

**v0.0.57 — Verified-compute floor and leaf opportunity (descriptive)**

On the 13 previously inspected original matrices, iterative degree-at-most-one
graph peeling reaches at most 3.39% of variables; none meets the 10% screening
heuristic. This nonblind structural count is not a numeric compression or
runtime result. Full original-equation verification and explicit output also
impose a linear input/output floor on the total path. See
`docs/experiments/v0.0.57.md`.

**v0.0.56 — Corrective natural-matrix reuse audit (negative gate)**

The v0.0.55 first audit aborted on a frozen forward-error threshold, while
the original-equation backward error remained small. The corrective protocol
retains every source and comparator and declares its updated numerical
criterion before the next complete audit. Across all 13 unmodified originals,
three had repeated components but none delivered the required end-to-end
advantage; seven of ten no-repeat cases had >10% scanning overhead. The
generic component scan is stopped. See `docs/experiments/v0.0.56.md`.

**v0.0.55 — Unmodified matrix reuse incidence (invalid numerical gate)**

All 13 original NIST BCSSTRUC1 stiffness matrices test how often exact
identical components actually occur, with a scan-and-abstain path charged
against native full solves. The protocol is in `docs/experiments/v0.0.55.md`.
The first audit aborted on the frozen forward-error tolerance for `bcsstk13`;
no reuse-incidence conclusion follows from this run.

**v0.0.54 — Component splitting versus reuse (positive controlled ablation)**

The mechanism ablation compares exact factor reuse against an equally
decomposed baseline that independently factors each component. Both verify
the original assembled equations. Reuse lowered full-path time by >=20% on
4/4 large cases, separating reuse from decomposition in this repeated-copy
workload. See `docs/experiments/v0.0.54.md`.

**v0.0.53 — Exact real-matrix component reuse (positive controlled gate)**

A controlled workload interleaves repeated copies of two pinned NIST matrices.
It tests whether full-path exact factorization reuse, including component
detection and original-equation verification, beats a fixed strong native
SuperLU baseline. All 4/4 large cases beat fixed NATURAL by >=20%; the
`bcsstk09` 16-copy case was 11.0× faster. This mixes decomposition and reuse;
the next ablation must separate them. See `docs/experiments/v0.0.53.md`.

**v0.0.52 — Real numerical matrix ordering audit (negative gate)**

Four pinned NIST BCSSTRUC1 sparse matrices test a cheap external RCM order
against SuperLU's native ordering policies, charging full-path work and
checking the original equations. The data are fetched separately. The
predeclared >=20% threshold was met on 0/4 matrices; native NATURAL was
fastest on all four. No learned orderer was trained. The complete first
audit and limitations are in `docs/experiments/v0.0.52.md`.

**v0.0.51 — PACE external ordering opportunity gate (no model trained)**

On all 28 PACE 2017 public minimum-fill graphs with at most 128 vertices,
16 bounded min-fill restarts left no >=10% arithmetic-proxy headroom over
the stronger of min-degree/min-fill in the 11 sparse cases. This is an
external graph-only negative gate, not an exact optimum or verified numeric
solve. See `docs/experiments/v0.0.51.md`.

**v0.0.50 — Sparse ordering opportunity gate (no model trained)**

On 48 fresh 12-node SPD graph Laplacian systems, min-degree/min-fill left
no >=10% sparse scalar-operation headroom versus globally optimal
symbolic order. The optimum search was far costlier than an exact solve.
This family is saturated for learned ordering claims; see
`docs/experiments/v0.0.50.md`.

**v0.0.49 — Matched topology cost audit (no model trained)**

96 exact counterfactual pairs matched dimension, nonzero count and original
column-incidence histogram. Every pair changed F3's retained dimension
by two, but none showed a robust F3-to-F1 cost reversal: caching remained
beneficial on the retained-support side. This is a negative gate result,
not learned structural intelligence. See `docs/experiments/v0.0.49.md`.

**v0.0.48 — Cost-gate opportunity audit (no model trained)**

On 128 fresh exact n=16 systems, a one-feature original-incidence gate
separated all high-degree cases from dense and control cases. Only five
robust cost winners conflicted with it (pre-registered minimum: 16), so
the audit did not justify training a learned gate. All exact answers
verified; local timing is diagnostic, not a deployment claim. See
`docs/experiments/v0.0.48.md` and `python benchmark_v048_smoke.py`.

**v0.0.47 — Row-overlap boundary (contract only)**

F3's exact two-row support-pair candidates cannot overlap one row in a
nonsingular square residual: four target columns would occupy only three
rows. The [contract and audit](docs/experiments/v0.0.47.md) checks singular
overlap, full-rank repair, and disjoint controls on 384 fresh integer
matrices. This is not a new learned model or a performance improvement.
Run `python benchmark_v047_smoke.py` for a small contract check.

**v0.0.46 — Cached exact candidates and dense abstention (research)**

An incremental candidate cache preserves v0.0.45's exact high-incidence
reductions on a fresh 96-case arm while cutting derivation/checker calls
from 56 to 9.5 per system. Paired local full-path time was 0.764× frozen
F1 on that arm. On 96 dense systems F3 abstained and exactly matched F1,
but still ran 1.017× as long; controls were also slightly slower. Thus the
result is conditional and synthetic, not a general performance claim or a
trained model. The pre-registered 224-system audit is documented in
`docs/experiments/v0.0.46.md`; run `python benchmark_v046_smoke.py` or
`python benchmark_v046.py`.

**v0.0.45 — Exact Schur cost audit (research only)**

On 224 fresh exact systems, an experimental deterministic F2 repaired both
v0.0.44 structural gaps: all 96 high-incidence systems matched the full
oracle, and all 96 dense systems admitted an exact two-variable Schur
elimination. Yet measured full-path execution was slower than frozen F1:
paired median ratios 1.060 and 1.487. F2 is kept as a research baseline,
not promoted as a performance upgrade. See `docs/experiments/v0.0.45.md`
and run `python benchmark_v045_smoke.py` or `python benchmark_v045.py`.

**v0.0.44 — Adversarial structural boundary audit**

The frozen indexed method was challenged with two fresh generated families.
All 224 final answers verified against the original systems. It missed a
valid high-incidence block in every one of 96 cases; it also missed both
independently valid exact Schur witnesses in all 96 dense alternative cases.
The 32 controls remained uncompressed. The production materializer cannot
currently substitute eliminated targets into retained equations, so the
dense witnesses are references rather than available actions. See
`docs/experiments/v0.0.44.md`; run `python benchmark_v044_smoke.py` or
`python benchmark_v044.py`. No learned model was trained in this audit.

**v0.0.43 — Incremental indexed peeling**

This freezes v0.0.42 E2 and indexes residual low-incidence row pairs. On a
fresh 224-system audit, the same verified reductions and solutions were
selected on all 192 active cases; indexed pair examinations fell to 4.44%
in the coefficient arm and 0.73% in each overlap arm. The 32 controls stayed
uncompressed without rejected whole-system proposals. Paired local timing
ratios ranged from 0.855 to 0.893, but this does not measure energy or
general-purpose performance. See `docs/experiments/v0.0.43.md` and run
`python benchmark_v043_smoke.py` or `python benchmark_v043.py`.

**v0.0.42 — Nonunit parser and residual-incidence peeling**

This experiment tested two deterministic repairs to the v0.0.41 failure
modes on fresh generated exact systems. E1 removes the unit-only 2x2 target
restriction. E2 also peels validated low-incidence blocks from the remaining
row set. Neither method trains a learned block model. The pre-registered
protocol is `docs/experiments/v0.0.42.md`; the fresh 224-system audit passed
and E2 recovered 100% of oracle solver savings on all three active arms.
Run `python benchmark_v042.py` for the audit or `python benchmark_v042_smoke.py`
for a bounded correctness check. E2 examined 1,305.5 row pairs per active
system on average; solver arithmetic savings exclude discovery and checking.

**v0.0.41 — Anti-shortcut causal audit**

The v0.0.40 deterministic result was challenged on three separate
synthetic arms: generic nonunit invertible 2x2 coefficients, cross-block
overlap, and both together. Candidate visibility is measured separately from
verified downstream compression. The audit is pre-registered in
`docs/experiments/v0.0.41.md`; no learned block scorer was trained. The
224-system audit passed its integrity and verification gates. Nonunit block
coefficients exposed a candidate-visibility limit; cross-block overlap
exposed a conflict/selection bottleneck. Run
`python benchmark_v041.py` for the frozen 224-system audit, or
`python benchmark_v041_smoke.py` for a bounded correctness check.

**v0.0.40 — Coupled-Block Discovery / Routing Gauntlet**

v0.0.40 moved from family design to actual structure discovery on a fresh
256-system audit set.

No learned block model was trained.

The validated v0.0.38.1 mixed family was held fixed:

- easy local one-row leaves,
- coupled exact 2x2 blocks,
- generic variable names,
- row/column permutation,
- exact original-problem verification.

The frozen local pipeline remained:

    target-leaf @ 0.10
        ↓
    deterministic checker
        ↓
    Markowitz residual @ 0.05
        ↓
    deterministic checker

v0.0.40 then compared deterministic routing/discovery variants.

### Result

The selected method under the pre-registered tie-break was:

    D4 = incidence router + row/target component graph

It achieved:

- solver-savings recovery: **100%**
- elimination recovery: **100%**
- block precision: **100%**
- block recall: **100%**
- block F1: **100%**
- verified retention: **100%**
- unsafe reductions: **0**

Decision:

    KEEP_DETERMINISTIC_DISCOVERY

Therefore a learned block scorer is **not justified** on this family.

### Performance-equivalent deterministic winners

D2, D3, and D4 all recovered the full measured verified compression value.

D2:

    incidence router
        +
    exact candidate-overlap block discovery

D3:

    incidence router
        +
    sparse shared-unit block discovery

D4:

    incidence router
        +
    2-row / 2-target component graph

All three reached:

    100% solver-savings recovery
    100% elimination recovery
    100% block recall
    100% verified retention

D4 is the formal winner only because the frozen tie-break counted fewer
row-pair examinations.

That does not prove D4 has lower total discovery cost, because D4 instead
examines graph edges and unlike cost units are intentionally kept separate.

### Most important finding: routing before discovery

D1 used the old local-first pipeline before exact block discovery.

It still achieved:

- solver-savings recovery: **98.20%**
- elimination recovery: **95.02%**

but block recall dropped to:

    86.46%

because the local stage consumed coupled targets before block discovery.

Average coupled targets consumed locally:

    D1 = 0.7109
    D2 = 0

After adding a trivial incidence router:

    target incidence == 1
        -> local path

    target incidence > 1
        -> reserve for multi-row path

block recall became:

    100%

with easy-leaf routing precision/recall also:

    100% / 100%

So the current structural lesson is not "use a better block scorer."

It is:

    route structural degrees of freedom correctly
        before
    consuming them with local reductions.

### Current validated architecture on this family

    raw exact system
        ↓
    incidence-aware structural router
        ├── local one-row path
        └── multi-row reserved path
        ↓
    deterministic block discovery
        ↓
    exact independent algebra checker
        ↓
    exact retained solve
        ↓
    reconstruction
        ↓
    original full-system verification

### Saturation boundary

This mixed 2x2 family is now saturated by cheap deterministic structure.

Do not train a block-discovery neural model on it.

The next research family must remove at least one shortcut:

- fixed +/-1 coupled coefficients,
- clean two-row/two-target connected components,
- absence of distractor overlaps,
- absence of cross-block dependencies,
- single block size,
- incidence-perfect routing.

Only if deterministic methods leave pre-registered verified downstream
headroom should learned structural discovery be reconsidered.

See:

- `docs/experiments/v0.0.38.1.md`
- `docs/experiments/v0.0.40.md`

### Frozen enabling results

**v0.0.33**

- oracle-cardinality scaffold (B=n-k)
- learned elimination recovery: **72.02%**
- learned oracle solver-savings recovery: **84.93%**
- verified retention: **100%**
- unsafe accepted reductions: **0**

**v0.0.32**

- oracle Structural Compression benchmark
- full-solution equivalence: **1.0**
- fixed-k oracle-compressed solver slope: approximately **0**
- explicit certificate byte overhead retained as a negative result

**v0.0.31**

- matched Direct / Structural Tiny Transformers: **75,538 parameters each**
- Direct final verified coverage: **12.76%**
- Structural final verified coverage: **100%**

## Persistent privilege

Public persistent execution requires:

    exact manifest authorization
      + lifecycle-compatible declaration
      + exact-manifest PASS lifecycle attestation

Only then can the public persistent builder create a reusable worker.

## Lifecycle conformance attestation

Attestation currently supports persistent-compatible classes:
- `STATELESS`
- `CACHE_ONLY`

Minimum prototype PASS gate:
- at least 3 explicit conformance cases
- at least 2 warm repetitions per case
- warm persistent mode: 100% pass
- recycled mode: 100% pass
- compile/solve/verify cross-generation mode: 100% pass
- expected semantic subset equivalence: 1.0

Execution modes:

### Warm
Repeated cases reuse the same worker.

### Recycled
Worker is recycled at case boundaries.

### Cross-generation
`max_requests_per_worker=1` forces compile, solve, and verify through separate worker generations.

## Exact-artifact binding

Attestation records are bound to:
- plugin ID
- exact manifest SHA-256
- declared worker state class
- explicit conformance corpus SHA-256

The attestation itself also has a canonical SHA-256 digest.

Therefore:

    changed manifest + old attestation → reject

even when the logical plugin ID is unchanged.

## Runtime enforcement

Public persistent builder behavior:

| Evidence | Result |
|---|---:|
| no attestation registry | reject |
| no attestation for exact manifest | reject |
| stale attestation for another digest | reject |
| FAIL attestation | reject |
| exact PASS attestation | allow |

## Bootstrap boundary

Attestation must test a candidate before persistent privilege exists.

NEUMANN therefore has an internal conformance-only persistent builder that bypasses only the attestation requirement while still enforcing:
- manifest validation
- exact-manifest authorization
- activation policy
- lifecycle compatibility
- out-of-process execution

It is intentionally **not exported as a public NEUMANN API**.

## Important boundary

A PASS attestation is deterministic evidence over a finite declared corpus.

It is **not**:
- formal verification
- proof for all possible inputs
- proof against adaptive malicious behavior
- publisher identity
- OS sandboxing

v0.0.25 adds a durable append-only attestation ledger with:
- exact manifest / corpus / attestation digest binding
- ISSUE / REVOKE evidence history
- hash-chain integrity verification on reload
- optional trusted-head rollback detection
- use-time evidence checks before every persistent dispatch

A local hash chain still cannot detect rollback to an older valid prefix without a trusted external head.

See `docs/experiments/v0.0.25.md`.

## Run

    pip install -e .
    pytest -q
    python benchmark_v024.py
    python benchmark_v025.py
    python benchmark_v026.py
    python benchmark_v027.py
    python benchmark_v028.py
    python benchmark_v029.py
    python benchmark_v030.py
    # v0.0.31 requires optional CPU PyTorch in its separate CI job
    python benchmark_v031.py

## Parallel security track

Lifecycle attestation governs reuse semantics, not host capabilities.

Threat Model v2 still points to:

    os_level_capability_sandbox

## Status

Research prototype. Not production-ready.
