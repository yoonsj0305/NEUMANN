# NEUMANN 1 · Source-optimal discovery of hidden CA rules and price-aware stopping

**Completed 2026-10-23 KST.** All counts are from actual successful dedicated GitHub Actions, *not* a claim of global Q1–Q7 closure. The original test collection was created by another researcher: AutomataBench, `neelsomani/automata-bench` pinned Git SHA `7d86373fdb63fe1bd3592ddf71d923ceebc5acd9`. Public development/evaluation splits each comprise **300 different underlying original tasks**. The same two splits have previously been evaluated by NEUMANN in related work, and are not private first-blind leaderboard tests.

## What is not provided to the model

The authentic original task's 16-entry bijective 2×2 Margolus CA permutation, original initial-state reference `answer`, and hidden metadata are **all removed** from the inference job input. A separately isolated *data-construction process* knows the original rule only to produce supervised experimental whole-4×4-grid input→one-step-output demonstration pairs. Thus **the experimenter can choose and observe the controlled state change**; the model knows the CLASS of possible local rules but not its 16 numerical rule values. This is conditional supervised active system identification, not emergent new neural physical laws. The whole 2×2 reversible primitive itself is human-specified.

## Theorem: four whole-grid probes are necessary and sufficient for complete unknown-permutation identification

There are sixteen possible binary 2×2 block states. An unconstrained reversible local CA rule is an arbitrary permutation `p:{0,...,15}->{0,...,15}`. A single full 4×4 input→output one-step example comprises exactly four non-overlapping local 2×2 transitions. Three examples reveal at most twelve different input→output entries. Even with the permutation prior, **at least four input entries remain unobserved**, whose remaining output symbols may be permuted at least `4! = 24` ways without changing any of the three observations. Thus *no three such one-step full-grid probes can universally identify the entire unconstrained permutation*. Four probes are sufficient: choose their quadrants to expose input states 0–3, 4–7, 8–11, 12–15, independently of the unknown `p`. The four output states for each input block then directly reveal all sixteen true rule values. This is a COMPLETE mathematical bound for **full rule identification under this observation interface**, not necessarily a bound for a particular query initial state.

64 independently randomized bijective hidden rules confirmed the constructive algorithm: first three designed probes leave exactly 24 completions, fourth uniquely recovers the original all-16 permutation for all 64. The actual 300 original-rule problems per split additionally validated exact equality of all 16 inferred mapping values to the original hidden rule.

## Original-author grade: four designed probes versus 4, 6, 12 random probes

[PR #522](https://github.com/yoonsj0305/NEUMANN/pull/522) [Actions #39881937232](https://github.com/yoonsj0305/NEUMANN/actions/runs/39881937232), public_dev300: **all three isolated jobs PASS**, source model unchanged from previous frozen PR520/521.

[PR #523](https://github.com/yoonsj0305/NEUMANN/pull/523) [Actions #39882226031](https://github.com/yoonsj0305/NEUMANN/actions/runs/39882226031), different original public_eval300: **all three isolated jobs PASS** with ALL FOUR model/data-source/grade/native simulator Git BLOB hashes checked *before reading this split*, **no new inference/model changes**.

| Demonstrations per task | Original 300 public_dev: full 16-entry rule / exact query | Original 300 public_eval: full rule / exact query | Two-split total: full rule / exact query |
| --- | --- | --- | --- |
| Random 4 | 0/300 ; 63/300 | 0/300 ; 67/300 | 0/600 ; 130/600 |
| Random 6 | 2/300 ; 203/300 | 2/300 ; 207/300 | 4/600 ; 410/600 |
| Random 12 | 137/300 ; 295/300 | 137/300 ; 296/300 | 274/600 ; 591/600 |
| **Designed 4** | **300/300 ; 300/300** | **300/300 ; 300/300** | **600/600 ; 600/600** |

All submitted query initial-state predictions from all methods were **correct on these actual original tasks**, with zero incorrect submissions; missing tasks were abstained. The 1,200 rows per split are augmented *same-original* source calibrations, NOT 1,200 independently authored benchmark problems.

Proof audit receipts: public_dev source pregrade SHA256 `7e6ca97ab0f3d678ed51ec766fee7959f193571040f50e5251f827b309cb93d6`; original author grade SHA256 `a3d65b46bc5196ea18e61e0a74bf652e2b53f1d630813afe3bf06bc631daa475`. Public_eval source pregrade SHA256 `acbf9a49bc561f5a86203e615cd9378326a10707b086e7d5766b5c22defd2c3b`; author original grade SHA256 `e34a2f7e17458583d507943bd9917e7a0a0568292b5c1f575a5bd69ec4a2bbc2`.

## Q4 actual source solver CPU, not mere 3x sample-count rhetoric

[PR #524](https://github.com/yoonsj0305/NEUMANN/pull/524) [Actions #39882653079](https://github.com/yoonsj0305/NEUMANN/actions/runs/39882653079): independently reread and SHA-verified the four UNCHANGED original actual pregrade+grade receipts from #522 and #523; no inference reruns or model refits.

| 600 original problems | Random 4 | Random 6 | Random 12 | Designed 4 |
| --- | --- | --- | --- | --- |
| Exact original problem solutions | 130 | 410 | 591 | **600** |
| Full unknown permutations identified | 0 | 4 | 274 | **600** |
| Sum of measured model-only CPU seconds | 15.829856 | 14.746900 | 1.365159 | **1.074050** |
| Exact original answers per CPU second | 8.21 | 27.80 | 432.92 | **558.63** |

Design4 has about **13.73× less actual source model inference CPU** than random6 on the identical 600 original tasks while solving 600 versus 410 and using only 4 instead of 6 full-grid interventions. Compared with random12, it uses 3× FEWER interventions but only **1.271× less measured source solver CPU**, so *observation count is NOT actual complete compute cost*. Data collection, physical oracle time, program development, model training, external original benchmark generation and I/O are **NOT** in these CPU timings. Audited report SHA256 `807ef1c34b1fb8d22df277ee028894300806f232bd90d428a675c7ba297d14b1`.

## Important exception: solve a particular query before full rule identification

[PR #525](https://github.com/yoonsj0305/NEUMANN/pull/525) [Actions #39883173748](https://github.com/yoonsj0305/NEUMANN/actions/runs/39883173748): stage1 physically REDACTS the fourth designed calibration response before inference. For each of the original 600 true source problems, three designed probes reveal twelve rule entries and leave **exactly 24** possible complete hidden permutations. The **same old** `discover(policy='joint')` independently checks all 24 and their exact source-compatible initial-state solutions, emitting only if every viable model yields the same unique initial state. Author original verifier scores predictions AFTER sealed inference.

**Results:** public_dev157/300 early exact, eval163/300 early exact; **320/600 early exact, 0 wrong** without full rule determination. Remaining 280/600 do not admit early proof, but previous verified full 4-probe complete source receipts guarantee correct answer for each after fourth observation. Counterfactual 3-then-4 adaptive source strategy needs **2080 instead of 2400 whole-grid interventions** (13.33% lower), but **10.954452s** total model CPU versus only **1.074050s** for always-four. That is **~10.20× more** model CPU spent to reduce observation acquisitions, not an efficiency win automatically. This is an *offline counterfactual adaptive stop plan* using already independently verified four-probe results, not an actually deployed closed-loop physical lab setup. Early3 source prediction SHA256 `75d91e9b79bc1fdd87add10404301011b25e45080a463120147a1e32c96deaba`, independent author grade/counterfactual audit SHA256 `8daaa27f92314a399b91be8e453aa5bcb2356b06f1bb4d22e5761786524c7c5a`.

## Q4 decide the cheapest SAFE observation/computation plan depending on observation price

Let `lambda` be an explicitly HYPOTHETICAL CPU-second equivalent price for conducting and receiving one whole-grid experimental transition. The two ALREADY certified correct paths have costs:

- **Always4:** `C_4=CPU_4 + 4*n*lambda`.
- **Early3, then 4 when unproved:** `C_3=CPU_3 + CPU_4_fallback + (4*n - n_early_proven)*lambda`.

Break-even `lambda_star=(CPU_3+CPU_4_fallback-CPU_4)/n_early_proven`. Infer it from ONLY public_dev300 without seeing public_eval300 timings or target costs. [PR #527](https://github.com/yoonsj0305/NEUMANN/pull/527) [Actions #39883679789](https://github.com/yoonsj0305/NEUMANN/actions/runs/39883679789) original two frozen source receipts exact SHA verification PASS. **Dev threshold 31.183878ms/probe; eval realized threshold 30.579956ms/probe.** Cheap simulated oracle at 10ms: choose ALWAYS4, eval total cost **12.7174s** vs early3 **16.0720s**, correct cheaper. Expensive simulated oracle at 50ms: choose early3, eval **57.5520s** vs ALWAYS4 **60.7174s**, correct cheaper. BUT at 31ms dev point-estimate selects ALWAYS4 while eval actual cheaper strategy is early3 by 0.068s; **retain actual failure counterexample** and a broad explicitly UNKNOWN_NEAR_TRADEOFF interval [30ms,32ms], avoiding post-hoc false generality. The price is NOT actual measured instrumentation latency. Policy is exact optimal only between these two candidate source strategies at stable cost estimates well outside uncertainty, NOT universal optimization of arbitrary tasks or NEUMANN full cost.

Postgrade cost-controller original SHA verified output: `c9035c4d0216f3030ead999e24c19e36796d6475884637d67ee75d7c4e7380ce`.

## Global scientific status and next decisive work

- **Q3 SCOPED PASS:** mathematically optimal source intervention count for full 16-state unknown reversible block rule identification under the explicitly specified full-grid experimental observation interface; actual 600 original independent-author tasks show 600/600 full correct latent rule and correct exact original initial-state reconstruction. The task-input pattern EXPERIMENTS are human-designed and their output labels are obtained from an external rule oracle.
- **Q3 SCOPED PASS:** some individual target answers provably invariant across 24 compatible unknown rule completions after 3 probes (320/600 original correct, 0 incorrect). This is inference of task-conditioned mathematical invariants, not unconstrained learner invention.
- **Q4 SCOPED PASS:** designed4 original inference CPU 13.73× lower than random6 (same 600 original tasks and exact strong joint solver), AND cost-aware chooser's dev-calibrated threshold test succeeds at two separated hypothetical probe prices on eval. Loss case at 31ms must remain visible.
- **Q3 GLOBAL OPEN:** neural learned original rule FAMILY/operator outside human-defined Margolus primitive, generic generalization to unrelated independent environments with no supervised intervention oracle. No neural forwards used to invent 2×2 CA block formalism.
- **Q4 GLOBAL OPEN:** whole NEUMANN 1 task generation+learning+inference+controller+experiment+verification physical cost/energy 10×, no accurate real measured oracle cost yet.
- **Frontier parity OPEN:** no new official ARC-AGI benchmark performance proven by this study.
- Every claim is bounded by the original authenticated independent-author open benchmark and actual historical GitHub Action receipts. Research PRs remain not release-admitted pending whole repo CI, architecture integration and no-hypothesis-leak retest.
