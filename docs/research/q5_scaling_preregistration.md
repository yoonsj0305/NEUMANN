# Q5 first slice — frozen EXPAND4 complete-cost scaling contract

## Current state

`EXECUTOR_IMPLEMENTED_NO_NEW_EVIDENCE` — the per-case registrar, serial
whole-path executor, retained replay and exact-runtime authority preflight are
implemented. No new Q5 LP has been generated, no model forward has run, and no
Q5 experimental timing has been performed. The thirty unit tests are synthetic
analysis/fault-injection fixtures, not Q5 evidence. The metadata protocol's
original contract-only status remains frozen as provenance. This change
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

The CLI implementation is now available; source generation and measurement are
**not armed in any workflow**. Publish this executor head and pass its fixtures
and exact-runtime preflight before adding a one-shot registration workflow.
The following frozen rules still apply:

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

## Contract CI correction history

The first dedicated contract workflow, run36952164612, failed before fixtures:
the test imported the package's legacy eager `__init__`, which requires
scientific/model dependencies even though this new module uses only the
standard library. Local checking used a partial source snapshot and therefore
did not expose that package initialization dependency. Preserve this failure.

Only the fixture import was corrected to load the exact standalone module by
file path. No package exports or scientific runtime were changed. This keeps
the dedicated contract job genuinely model/solver/dependency-free. The Q5
metadata, costs, gates, bootstrap and absence of experimental evidence are
unchanged. The corrected fixtures must actually execute before merge.

## Safe next execution point

The registrar and executor are implemented, with these concrete boundaries:

- `experiments.q5_register`: atomically reserves an attempt directory before
  scientific imports or sources. Pins the operator's latest seed-collision
  audit to the execution head. The new generator entry point shares v082's
  exact formula but accepts only the Q5 grid; v082's old grid is unchanged.
  Retains one bounded gzip per view, including rejected labels before stopping.
  Hashes, canonical metadata, original oracle certificates and the exact
  paired surface transform are replayed. No model restore/forward in registration.
- `experiments.q5_evaluate`: requires the committed manifest's SHA256, restores
  only the two frozen models, serializes one warmup + three retained repeats in
  the frozen 1536-observation schedule. Each route's first process launch through
  READY is measured externally. Full parent authority replay is also charged
  to every deployable cold startup (not hidden in research overhead). Workers
  remain idle except the current query. Startup is one-time service loading;
  it includes model restoration but cannot be claimed as zero by preloading.
- Every query charges source read/decompression/digest/array decoding. Candidate
  discovery charges those operations plus features, tensor conversion, forward,
  permutation validation and ranking. All native/restricted attempts, lifted
  certificates, failure witnesses and fallback ledgers survive. External
  request/response and retained-ledger serialization are charged conservatively
  in post cost, with separate descriptive transport cost. The unchanged 5s
  capability deadline also applies to that external receipt.
- Files are exclusive-create only. Hash-chained fsynced events bracket the
  isolated timing window, every query start, every completed compressed
  observation and terminal completion/failure. A partial attempt cannot be
  resumed or replaced. One gzip per observation avoids a >100MiB monolithic Git
  blob. Post-window replay verifies sources, native execution ledgers, support
  authority, primal reconstruction, original witnesses and complete budgets;
  it performs no forwards, new solves or timing. Report identity is pinned by
  the terminal receipt. Published first-run manifest/receipt hashes must be
  recorded as the external authority before ordinary CI admits retained replay.
- Analysis uses each case's median **complete** charge, not a favorable sum of
  independently selected stage medians. Warmup failures remain capability
  failures. Q=1 includes full original training/setup plus cold startup; Q=10000
  amortizes both. Native-stage costs must be contained by full attempt/path
  clocks. Missing observations or accounting invalidate evidence, never reduce
  the sample. RSS is descriptive Linux KiB; no energy claim.

Exact envelope: CPython3.12, NumPy2.3.5, SciPy1.17.0, scikit-learn1.9.1,
PyTorch2.14.0+cpu, highspy1.15.1, threadpoolctl3.7.0; Linux x86_64
Ubuntu24.04 runners, HASWELL BLAS dispatch, one numerical/Torch thread.
Actual CPU/kernel/affinity/BLAS metadata are retained and must match across
routes on the single measurement runner. This envelope does not assert that
separately scheduled source-registration and timing runners have identical CPUs.
CI's authority job only replays old bytes and restores old weights. It never
generates Q5 inputs, executes inference or provides a cold/timing sample.

Fixture-discovered correction before any Q5 evidence: equal analytic exponents
produced a tiny negative OLS difference from floating-point roundoff. Differences
within 1e-12 are now exactly zero before the frozen bootstrap decision; such
noise cannot count as a strictly improved slope. Size/width/seed selection,
cost/utility/burden thresholds and bootstrap design are unchanged.

Next: after final-head CI/preflight passes, audit latest seed use, publish a
single registration trigger, commit all first registered bytes/receipts, pin
the resulting manifest, then publish a single isolated evaluation trigger.
Upload AND retain receipts on failure; never rerun a favorable replacement.
Only a retained real result may use the scientific decision labels. Global Q5
remains OPEN, and cross-domain testing still needs a separate task contract.
