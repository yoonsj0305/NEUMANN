# F0 OPENED v102 Original LP CPU Cold: first authentic local evidence (2026-10-10 KST)

**Verdict:** `COLD_FROZEN_Q34_NO_HEADROOM_IN_TWO_OPENED_ORIGINALS / ORIGINAL_CERTIFICATION_6_OF_6 / F0_FRONTIER_UNARMED / Q1_Q7_OPEN`.

This is a genuine executed CPU subprocess experiment reusing already registered historical v102 source originals and model. It is **not** a fresh, held-out or frontier evaluation, nor evidence about new model training or unseen families.

## Immutable run and source

- **Original run:** [Actions #38012360839, f0-original-controls](https://github.com/yoonsj0305/NEUMANN/actions/runs/38012360839) at code head `e1ee52f708d987e4b230f6fe0b438f2c16b63a1b`.
- **Raw artifact:** [neumann-f0-opened-v102-frozen-cold-first, artifact #11653732636](https://github.com/yoonsj0305/NEUMANN/actions/runs/38012360839/artifacts/11653732636). Retains `manifest.json`, `local_controls.jsonl`, `frozen_existing_cold.jsonl`, `summary.json`.
- **Existing source archive:** `docs/experiments/results/v102_fresh_sources.manifest.json` with registered gzip sha256 `9420b10a44ca3101374a79d638cc209f1301d2b867cec8de3ebecb0f270c4202`, loaded by original `load_registered` and original `lp_portfolio_v084.decode_array`. Fixed first two *base* m64 independent originals: `fresh102_00_base`, `fresh102_01_base`, one view per pair. Already opened development, not fresh F1.
- **Frozen seed:** 100001. No training or retuning, and old first historical Q34 results were not altered.
- **Environment/scope:** one GitHub Actions Linux CPU runner; Python 3.12; three routes each launched in their **own new Python interpreter process** so checkpoint cold restore is charged. Each route includes original solver, internal independent original LP certificate, and extra independent parent verifier. Financial, energy, GPU and training total `UNKNOWN`. No calls to small or frontier models.
- **Focused Python tests:** 15 passed in first actual local capture; subsequently one extra model-free counter regression test added. The immutable historic frozen-first job completed all 6 original LP paths independently VERIFIED.

## Actual observed operational milliseconds from SAME-JOB frozen comparison

| Already opened original | Strong Native cold | Deterministic residual4m cold | Frozen Q34 learned cold |
| --- | ---: | ---: | ---: |
| fresh102_00_base | 940.399164 | 875.363558 | 3077.804039 |
| fresh102_01_base | 913.728656 | 920.588581 | 3044.446328 |

| Source | frozen/native wall ratio | frozen/classical wall ratio |
| --- | ---: | ---: |
| fresh102_00_base | 3.272869816 | 3.516029438 |
| fresh102_01_base | 3.331893235 | 3.307065057 |

All 6 original mathematical routes VERIFY. Frozen is approximately 3.27–3.33× **slower than Native** under the measured cold request surface, not faster. Do not advertise a 10× NEUMANN saving on this surface. A persistent shared model service differs from cold; earlier warm Q34 observations are not silently mixed with these cold results.

Previous separate classical-only first job [Actions #38012224956](https://github.com/yoonsj0305/NEUMANN/actions/runs/38012224956) had 4/4 original verified with Native / classical cold geomean 1.0466068875× (source times: 825.093628/814.020161 and 884.482133/818.445866 ms). Keep that first run independent, don't replace it with the later same-job frozen results.

## First artifact accounting discrepancy and corrective ledger

The **raw frozen-first artifact summary has contradictory execution counts**: the generic classical-only keys state `learned_model_executions:0` and `actual_local_executions:4` while the same stored summary correctly says `actual_existing_learned_model_executions:2`, `all_frozen_originals_verified:true`, and retains exactly **two** frozen first-run rows in `frozen_existing_cold.jsonl`. This is a **summary metadata bug**, NOT permission to rewrite the original data or replace the first run.

**Correct interpretation:** four local Native/classical routes plus two genuinely executed frozen learned routes = **six original-verifier-complete paths, including two learned model inference executions**. The stored original ZIP and original receipts are preserved unchanged. In later code commit `2f0e3955b0ed3bc8b24ad4c6fc118bc1fedf69fc`, the summary counters are fixed and a model-free regression test asserts six total/two learned. CI no longer automatically replays a costly frozen checkpoint run on each commit; one-time first archive #11653732636 remains authoritative.

## Prior G0 first experiments already constrain the next direction

The Oct 8 master decision ledger, already preserved in PR #176 ancestry, reports more than just the LP result:

- **G0-B certified Boolean counting:** first 17 OPENED public CNF originals, 12 completed and 5 certificate-generation timeouts, hence **INCOMPLETE**, not PASS. In the completed subset, the reported Native/free ratio geomean was **0.4393×**, best **4.0204×**, with **zero 10× positives out of 12**. That is not a measured general negative for every Boolean circuit but does block naive rerun/training of that same cold pipeline.
- **G0-A probabilistic goal structure:** 125 first native jobs, 361 exact PASS / 14 NOT_VERIFIED, 9 process errors / 15 timeouts, all-family conclusion **INCOMPLETE**. Registered 2-bin optimistic mean BRP 4.364× and Crowds 9.67849×, neither reaches 10× family gate; higher positive singleton free-floor values are not viable learned or strong-analytic-matched conclusions.
- **Previous Guarded Perspective:** same optimized strong Native operational cold1 0.96735×, cold64 1.02222×, warm 0.98839× free representation diagnostic, no meaningful 10× headroom.

**Updated decision:** Do NOT route from failed Q34 cold to repeating the same incomplete G0-A or G0-B first setup. The defensible next move is first identifying a genuinely open natural-language-to-goal-sufficient-representation capability gap with real small/frontier/system inputs and a stronger classical comparator, then only conducting one narrow pre-registered economic diagnostic if strong-native paid-proof headroom exists. Until actual hosted reference responses and auditable spending authority exist, provider/model outcomes remain UNKNOWN. This requirement cannot be replaced by model-free contracts or additional engineering wrappers.
## Research implication and STOP/PIVOT

- R0 classical wheel remains a sound engineering asset in previously certified scopes.
- For these two **old constructed LP** originals, learned frozen selection does not pay its cold overhead. No further P1.x / LP Q34 cold reruns, task-adjacent tuning, re-labeling or new fitting is admitted on the basis of this result.
- Prior Q34 learned warm benefit on other opened tasks remains a narrower observation and does not magically become false; use a **single explicitly budgeted warm/high-volume service evaluation** only if real edge/cloud customer workload assumptions justify amortization.
- Continue to search for **real frontier-verified hard problem gaps** and goal-preserving representations that *strongest native + classical hybrid cannot cheaply produce*. Historical G0-B certified Boolean counting-circuit headroom (against real D4/CPOG/Ganak family) has priority conditional on actual native availability. If even a free valid representation cannot show headroom, no learned model training in that family.
- R1/R2 and global Q1–Q7 remain OPEN; Decision 3 SEALED; F0 actual small/frontier externally attested responses **NOT OBTAINED**.

**Do not interpret a more detailed benchmarking harness as a new model or a demonstrated category-changing capability.**
