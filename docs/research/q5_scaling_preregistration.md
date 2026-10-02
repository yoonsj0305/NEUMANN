# Q5 first slice — frozen EXPAND4 complete-cost scaling contract

## Current state

`CONTRACT_ONLY_NO_NEW_EVIDENCE` — no new LP has been generated, no model has
run, and no experimental timing has been performed for this contract. The
eight unit tests are synthetic analysis fixtures, not Q5 evidence. This change
does not revise v102 or increment its experimental version.

The latest result is v0.0.102, not the interrupted v0.0.94 candidate. Its
fresh constructed-LP Q34 result authorizes a Q5 test. End local Q3/Q4 polishing,
refitting, support-width search and threshold rescue on that family.

This first Q5 slice asks a narrower, falsifiable question: does the exact
frozen support system keep an end-to-end advantage as independently varied
constraint count and apparent width increase? It does not test cross-domain
transfer or close global Q5. Natural-family/task-transfer evaluation needs a
separate source and capability contract; no synthetic result can replace it.

## Immutable parent authority

Parent decision: `Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5`.

- Result execution head: `46af13c3d7d9b1a87f0a0db8511f5972511beb16`.
- Result gzip SHA256:
  `a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a`.
- Result decoded SHA256:
  `d748f70433360ed76ed226f0608a34418af19e0aa9ec3d6aabe9233751995195`.
- Seed100001 weight SHA256:
  `c19ad47a4fd310ba469308529ff87134c6ea5de3066ad5750c4af54d658457ea`.
- Seed100002 weight SHA256:
  `20d012c6536cdb4041f6620307b5dbb1c1f3ab56f9438cbff971123a657c3ab5`.

The metadata guard checks these pins. Before any future source generation or
measurement, CI must merge v102 after its first-result witness replay actually
executes, and the evaluator must independently load/replay its exact bytes.
Manifest metadata alone is not evidence verification. Preserve first CI #450's
all-skipped replay failure; the subsequent upstream change removes its
unnecessary solver-availability skip because replay never calls a solver.
Do not overwrite this concurrent correction or rerun the original study.

## Planned source matrix

| Dimension | Frozen values |
|---|---|
| Constraints m | 32, 64, 128, 256 |
| Apparent width n/m | 1, 16, 32 |
| Independent base replicates per cell | 4 |
| Conditioning | replicate 0/2: 1; replicate 1/3: 1000 |
| Equivalent views | base and signed-row/permutation + positive-column scaling |
| New base seeds | 103500..103547, canonical row/width/replicate order |
| Surface seed offset | 400000 |
| Total | 48 independent bases; 96 views; 24 cells of 4 |

Use the existing generator and normalization contract, with width set from
the matrix, not a new favorable family. Register the sources model-free,
route-free and timing-free, retaining full arrays and independently checked
oracle witnesses before opening evaluation. New seeds must also be checked
against any work published after this preregistration; a collision blocks
generation, rather than silently changing seeds after outcomes.

Square n=m is the real no-dimension-reduction control. n=16m preserves the
successful mechanism's width; n=32m tests apparent-width expansion. m=256
is the new constraint-count stress. Every view is retained, including failed
generation, verification and Direct capability. Paired surface views count
as one base cluster, not two independent experiments.

## Frozen inference and comparator rights

Carry both frozen quotient support models, one ranking per query, top min(n,2m)
restricted native execution, one top min(n,4m) retry only after original verifier
rejection, then charged Direct fallback. No new fitting, seed selection,
score calibration, support-factor adjustment, gate tuning, or reuse of v098
holdout inputs. No structural result cache; all queries are cache misses.

Four routes: native verified DIRECT, non-deployable free ORACLE (offline
headroom only), EXPAND4_s100001 and EXPAND4_s100002. Direct receives the same
native solver, original certificate checker and optimized execution authority.
This mechanism test does not separately prove that a learner beats every
possible equal-budget Direct learner or all classical support heuristics.

## Measurement and accounting requirements

Measurement implementation is deliberately **not enabled** by this commit.
It must first be published and pass contract-only CI, with the following rules:

1. Freeze the exact dependency/BLAS/thread/hardware envelope before sources.
   Use the successful v102 runtime, one numerical/Torch thread and HASWELL BLAS
   dispatch. Serial route execution, fixed shuffled order seed103991, one
   warmup plus three retained repeats, unchanged five-second per-query budget.
2. Isolate timing from pytest, archive replay, source generation and concurrent
   compute on the same runner. Preserve an execution ledger. An overlap makes
   the timing evidence ineligible; do not promote a favorable replacement run.
3. Proposal charges all input-dependent quotient features, tensor conversion,
   model forward, ranking and selection. Post charges all restricted attempts,
   original-problem certificates, reconstruction, discarded work and fallback.
   A rejected result is never reported as a cheap successful answer.
4. Report separately the single whole-process cold startup/import/loading/
   authority-preflight cost and warm per-query cost for each deployable route.
   Measure cold startup externally, including process launch, and retain its
   first observation. Oracle archive/source-generation research costs are not
   deployable inference costs; disclose them separately. Neither route can
   hide input preprocessing or loading by running it before its cost timer.
5. Complete steady-traffic cost is warm proposal + post + original fit/feature
   setup /10000 + route cold startup /10000. Report Q=1 cold cost separately;
   no warm-cache or energy/RSS claim is inferred. Process peak RSS and failure
   counts must be retained by the future executor as descriptive metrics.
6. Aggregate case medians over each frozen cell before computing Q34 ratios.
   Every accepted witness is checked against its original input; preserve
   rejected witnesses, attempt ledgers, deadline failures and raw times too.
7. Direct or candidate capability failure means `CAPABILITY_OR_ACCOUNTING_UNREACHED`
   and no speed ratio for that cell. Never drop slow/censored cases from a
   scaling fit, weaken the budget, or extrapolate a speedup from solver size.

`charged_cost`, `cell_gate` and `summarize_scaling` implement the analysis boundary. They
cannot validate caller-supplied verification flags; actual witness and attempt
ledger validation is a prerequisite in the future evaluator.

## Decisions frozen before evidence

Wide cells (n/m=16,32), for both seeds, both views and all m, must retain verified
capability, positive oracle/candidate savings, utility recovery >=0.80,
discovery burden <=0.20, and amortized complete/Direct <1. Square cells require
verified capability and complete/Direct <=1.20; they cannot rescue a failed
wide cell. At m=256 each wide cell must additionally be <=0.80 of Direct.

Analyze scaling separately for each of two seeds x two wide factors x two
surface statuses. Regress log complete cost on log m at all four sizes. Use
medians of four base costs per size. A 2000-draw paired condition-stratified
bootstrap with seed103992 resamples base replicate IDs independently within
each size, preserving Direct/candidate pairing. Do not pool surface views,
seeds or widths. Use a one-sided upper bound with familywise alpha0.05 across
eight comparisons (Bonferroni tail0.00625 each).

- Any capability/accounting failure: no complete scaling verdict.
- Any frozen cost-cell failure: `Q5_SCALING_COST_GATE_FAIL`; stop this scaling
  candidate without refitting or widening support to rescue it.
- Every cost gate passes, but any slope-difference upper bound >=0:
  `Q5_SCALING_COST_PASS_SLOPE_UNRESOLVED`; lower cost is not improved scaling.
- Every cost gate and every slope test passes:
  `Q5_CONSTRUCTED_LP_SCALING_PASS_NOT_CROSS_DOMAIN`.

These labels are reserved for a separately retained first evaluation, not this
contract. Four sizes and four bases per cell provide limited empirical slope
evidence, not an asymptotic law. Q5 stays globally OPEN in every outcome here.

## Safe next execution point

Implement and test a model-free multipart/per-case source registration archive,
then a separate complete-cost evaluator, failed-attempt retention, externally
measured cold startup and byte-exact no-execution replay. Publish the exact
runtime/executor contract and commit head before generating any source. Run
source registration once, commit its bytes, then admit one isolated evaluation.
Ordinary CI must run fixtures/replay only, never the Q5 benchmark.
