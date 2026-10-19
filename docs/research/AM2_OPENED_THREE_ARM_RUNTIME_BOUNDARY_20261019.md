# AM2 opened three-arm real-core execution boundary | 2026-10-19

## Scope and honesty

**ENGINEERING COMPONENT only.** This PR extends [generic public QA ABI PR #254](https://github.com/yoonsj0305/NEUMANN/pull/254), without modifying the frozen historical AM1 artifact, failed original Decision 2, previous bounded Q3 work, or the sealed Decision-3 eligibility marker. Lightning Studio is blocked by the reported platform-wide service interruption beginning 2026-10-16; Colab UI only offered ineligible T4; no native BF16 GPU was acquired. No model, training, weights, providers, frontier models or gated task rows were opened during this code work.

This is **NOT** an original-task capability comparison. It does not solve the **source-cohort / original-checker / strongest TOOL+ / actually learned semantic proposer / real native-BF16 access** blockers identified in [Issue #253](https://github.com/yoonsj0305/NEUMANN/issues/253) and [Colab PR #255](https://github.com/yoonsj0305/NEUMANN/pull/255). It is not a successor implementation of AM1 under the old failed prompt or a favorable rerun.

## What was actually implemented

- **Executable same-core three-arm boundary**, `neumann1/am2_opened_three_arm_runtime.py`. `run_one_opened` has directly runnable code for calling `core.generate(messages,max_tokens,thinking=False,deadline_ms)`, validating frozen model identity when `production=True`, checking strict answer-only final output through the parent ABI, and calling a **separate original checker**. `run_matched_opened` invokes DIRECT, TOOL+, NEUMANN on **one shared core object**, checks identity stability, rejects any non-identical TOOL+/NEUMANN shared tool output. No model constructor is called by this module.
- A **strongest registered TOOL+ is NOT supplied** by the wrapper. Instead both TOOL+ and N REQUIRE an external actual `shared_tool(public_view)` callable returning `{context,tool_id,internal_calls}`. No TOOL+ result may be called strongest in scientific records without independent source-level confirmation.
- NEUMANN REQUIREs an additional `proposer(public_view)` and `certifier(public_view,proposal)`. Unbound or certificate-rejected structures ABSTAIN **before** inference. The certifier operates on the public source only and must return true plus a 64-byte hex proof identifier. The wrapper does NOT itself prove the truth of a returned `valid=True`; an independent trusted source-specific certifier remains mandatory, and a source proof is not automatically newly learned.
- Model/core identity, public input, tool output and structure proposal hashes; charged provider/proposal wall time, per-arm model input/output tokens, memory and checker time, strict final-only answer; original checker calls; cold startup separately `core.startup_ms` where actually present. **Missing forward count, energy, dollars, amortization and actual strong-tool eligibility remain null/UNKNOWN**, never zero. Per-arm `complete_cost_measurement=INCOMPLETE_UNTIL_REGISTERED_BUDGET_AND_HARDWARE`. Existing model-call receipt cannot establish actual neural forward count.
- Hardware/model **production** mode refuses a mock core, rejects non-frozen or incorrect Gemma-4 E2B revision and changed identities. Even production execution is engineering observation until the ≥24 authenticated hard originals, ≥3 independent sources, identical tools, real semantic learning and complete costs have been admitted by a separately frozen EX1.
- The local **test-only fake core** has `evidence_kind=SYNTHETIC_TEST_ONLY`, `production=False` and `actual_model_generate_calls=0`. It tests protocol correctness only; fake right answers are not benchmark evidence.

## Fixed execution boundary

1. The input is PR #254's **public-only** QA schema; hidden private, gold or checker fields are refused.
2. DIRECT uses the same frozen core without external tools by protocol definition.
3. TOOL+ receives output of the registered shared tool that has received only the public view; all provider execution wall is charged.
4. NEUMANN receives the **same** registered tool output and separately charged independently certified source-conditioned structural proposal; it cannot borrow hidden gold from the original checker callback.
5. Every arm's final answer is checked by the **same externally supplied original checker**. Malformed/AM1 thought-only outputs, model deadline, incorrect answer, identity drift and mismatched shared tools fail closed.
6. All printed model capability verdicts and global Q1–Q7 remain OPEN until original authentic model runs; sealed Decision-3 must remain closed.

## First software-contract tests

Dedicated workflow `.github/workflows/am2-opened-three-arm-boundary.yml` runs only 12 Python stdlib tests using a synthetic test-core. These test the full three-arm call chain, one identity, original checker authority, missing TOOL+ and structure/certifier rejection, hidden content refusal, thought-only failure, changed tool context rejection, false production model identity, core mutation, unknown costs and incorrect answer.

**These are not 12 scientific source tasks and must never be confused with AM1's saturated 12!** Tests are program safety boundaries. CI source and first failures are preserved in an Actions artifact.

## STOP gate

Next genuine research action: **curate the missing opened, registered, nonsaturated, original-checked set** from real independent sources, bind the strongest eligible TOOL+ and an actually source-verified NEUMANN semantic proposer, freeze model/energy/cold/tool/forward budgets, then obtain an eligible cost-authorized real GPU. Only THEN run Experiment 1 once. If a common resource or original checker cannot be validated, stop rather than simulate neural evidence. Experiment 2 sealed gap remains forbidden until Experiment 1 passes. Historic D2 FAIL stays immutable.

`AM2_RUNTIME_SOFTWARE_BOUNDARY=IMPLEMENTED`; `EX1_ACTUAL_MODEL=NOT_EVALUATED`; `D3=BLOCKED`; `GLOBAL_Q1_Q7=OPEN`.
