# F0 original-verification UNKNOWN correction — 2026-10-10

Decision: **ENGINEERING PASS / BLOCKED_PROVIDER_EVIDENCE / HOLD_NEW_LEARNING**.
All changes and results remain local under the latest user instruction. No GitHub push, PR modification, CI dispatch, Notion write, provider call or model training occurred.

## Actual change

The existing F0 SyGuS intake converted the independent checker's `accepted:false` into a model rejection even when an original proof obligation was `unknown` or `parser_error`. That could manufacture a small-model failure and an apparent frontier gap. The fault was reproduced before changing production code.

`neumann1/f0_opened_bridge.py` now distinguishes:

- Complete independent `init`, `inductive`, `safe` proofs (`unsat` for all three): accepted.
- An independently checked original counterexample (`sat`), or a deterministic output-contract rejection: rejected.
- Incomplete proof, UNKNOWN, checker parsing error or unavailable dependency: unavailable original verification. A supplied `accepted:true` alone has no authority.

Unavailable results preserve the proof, task/role/repeat and original resource receipt. The result is `verified:null`; an unavailable repeat cannot be averaged into an accuracy score. Any incomplete arm disables the cohort's resource-ratio claims and sets `INCOMPLETE_ORIGINAL_VERIFICATION`. Checked small/frontier pairs may remain visible as partial diagnostics, never a complete cohort PASS. Unavailable Native/Classical-Hybrid rates also remain null.

Reused without modification: `hybrid_sygus_r0.independent_check` (original Z3 obligations), `hybrid_runtime_r0` source/goal binding, `lp_certificate_v081`, exact rational verification, `f0_capture_local`, and the existing `frontier_gap_contract` integrity tests. No new solver, mathematical certificate or model was implemented.

## Actual tests and evidence

Before the production fix, targeted fault injection reported **8 failed, 3 passed, 10 deselected** in 7.27 seconds. Seven failing unittest subtests were proof-status cases; the remaining failure reproduced a manufactured gap. The original tool output is identified by `cd659a`; a raw pre-fix file was not captured. This is engineering fault evidence, not model capability evidence.

After the first fix, the five related suites reported **78 passed, 1 skipped, 7 subtests passed** in 8.57 seconds (`dd0b3c`). Additional checks then covered unavailable verification in every arm and either of two repetitions; Native/Classical-Hybrid gap rates were corrected to propagate null.

The final recorded run reported **79 passed, 1 skipped, 17 subtests passed** in **6.82 seconds**, exit 0 (`df9399`):

```text
python -X utf8 -m pytest -q tests/test_f0_opened_bridge.py tests/test_f0_capture_local.py tests/test_hybrid_runtime_r0.py tests/test_hybrid_sygus_r0.py tests/test_frontier_gap_contract.py --tb=short --junitxml=research/development/f0-verification-unknown-2026-10-10/pytest-final.xml
```

The skipped test is `test_live_native_synthesis_three_original_proofs`: cvc5 CLI is unavailable. Independent Z3 positive/negative checks did run. Tests use existing small engineering fixtures and injected checker faults; they are neither fresh evaluation originals nor authentic provider responses. Synthetic resource values in fixtures are not measured NEUMANN costs. Test duration is not an inference-performance comparison.

Raw final log, JUnit result, hashes/runtime receipt and protected-file checks: [local engineering artifacts](../../research/development/f0-verification-unknown-2026-10-10/). JUnit counts include subtests; the console summary above separates them. `git diff --check` passed. The full repository benchmark/CI workflow was not rerun locally.

Existing declared optional dependency `highspy==1.15.1` was installed locally to run the current Native LP capture tests. Python 3.12.14, NumPy 2.4.6, SciPy 1.17.1 and Z3 4.15.4.0 were used. No torch/model forward was available or invoked.

## Baseline and preservation

- main: `55178a211962caf5ce677deb37edd30bfb4fdccc`.
- Work starts at PR #179 HEAD `a5c4097c418231b416c8ece482df5eac4ae6d9bc`, after the current pivot/handoff documentation updates.
- Latest read-only lookup confirms #174 open, #175–#179 draft/open. The ancestry #174 → #175 → #176 → #177 → #178 → #179 was independently checked with Git; all five ancestor checks passed.
- Remote #179 baseline [CI 38014206653](https://github.com/yoonsj0305/NEUMANN/actions/runs/38014206653) and [frozen contract checks 38014206664](https://github.com/yoonsj0305/NEUMANN/actions/runs/38014206664) succeeded for **a5c4097**, not this local change. No GitHub CI exists for the unpushed local commit.
- Work is isolated on local `research/f0-local-pivot-20261010` in `NEUMANN-F0-LOCAL`. The previous `NEUMANN` checkout retains its dirty `AGENTS.md` and untracked `research/v3/` unchanged.
- All 64 previously inventoried protected OPENED files still match their baseline Git blobs. No sealed contents were opened. Frozen contracts, checkpoint identities, historical first results and scientific verdicts were not changed.

## Remaining real-comparison blockers and single next action

The existing independent answer interfaces and local capture code are available. LP/exact controls ran in engineering tests. SyGuS original verification is available, but executing its strong native synthesis control locally also requires the missing cvc5 CLI. The already-opened official SyGuS source and historical LP provenance are indexed by the existing runbook and R0 release records; their historical exposure cannot be relabeled fresh. No new evaluation cohort was registered or measured here.

The primary blocker remains an authenticated provider capture with a fixed small/frontier pair, exact model revisions, equal actual tool authority, finite authorized budget, first-call traces and usage/cost receipts. None of those missing provider facts was fabricated. The current conversation is not a controlled frontier run. A placeholder model ID or supplied invoice is not provider attestation.

**Next single high-value action:** freeze and capture one authorized paired F0 opened-original cohort using the existing intake and independently verified strong classical controls. Before any calls, finalize source identities/exposure, model pair/revisions, equal tools, deadlines and finite authorized budget. If those inputs remain unavailable, keep `BLOCKED_PROVIDER_EVIDENCE`; do not substitute training or additional synthetic experiments.

New scientific capability observations: **0**. Frontier parity, new learned perspective generation, structural generalization and 10× complete-cost advantage remain **NOT ESTABLISHED**. Historical bounded Q34 success, scaling/transfer failures, incomplete G0 cohorts and sealed Decision 3 remain unchanged.

## Latest user steering applied

The next candidate is verified program/constraint semantic structure discovery, with **F0 → G0 → R1 → independent F1** admission. LP Q34 remains a historical asset/comparator; repeated LP tuning, P1 model swaps and the same G0 A/B reruns receive no new investment. No learned-discovery implementation is justified by this engineering fix. The present SyGuS certificate proves the supplied original formal conditions, not that those conditions faithfully encode an unstated human intention; any natural-language-to-specification claim needs a separate semantic evaluation.

Primary prior work was checked: [COINS](https://arxiv.org/abs/2608.13077) separates specification quality from ambiguous proof failure; [AutoSpec+](https://aclanthology.org/2026.acl-demo.66/) already combines learned candidate specifications with a symbolic checking/repair loop. This correction addresses proof-outcome handling in the existing intake; it makes no novelty or comparative-performance claim against those systems.

A future moving-baseline analysis must compare the cheapest **verified, iso-capability eligible** system on each measured resource axis. Monetary 2×/5×/10× price-reduction scenarios are hypothetical sensitivity checks, not forecasts or compute reductions. Apply reductions only to identified price-sensitive components; keep measured fixed/native/verification/investment components explicit. Without authenticated measurements, all scenario outcomes remain UNKNOWN. No additional scenario harness or training was created to stand in for real F0 observations.
