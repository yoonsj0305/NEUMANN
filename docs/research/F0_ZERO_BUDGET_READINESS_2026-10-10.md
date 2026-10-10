# F0 zero-budget readiness — 2026-10-10

New paid F0 budget: **0 KRW**. No paid API/GPU/service execution, credit purchase,
paid fallback or GitHub upload without a later explicit human instruction.
[Current authority](../../research/development/f0-zero-budget-2026-10-10/execution-policy.json)
records this instruction; it does not modify historical contracts or impose a
provider-side invoice cap. No model inference or GPU session was started.

| Route | Identity and revision | Actual authentication / allowance | Decision |
|---|---|---|---|
| Google Gemma via HF download and local/Kaggle inference | `google/gemma-4-E2B-it`, `3e22461f65e89153144f8adb70e3b8c2cc9845a7` | Historical constants/manifest agree; public exact-revision endpoint returned matching SHA and ungated/public/enabled status. Standard local cache and torch/transformers/HF runtime absent. | Reuse exact pin; not run. |
| Existing Kaggle | T4 x2 option; original 2026-10-03 environment | Browser authenticated; accelerator None and session off. Numerical remaining free quota not obtained; browser lookup timed out. | Hold execution until free quota is verified. No old cells run/changed. |
| Hugging Face Inference Providers | No frontier model selected | Authenticated non-Pro OAuth has jobs/profile/read scopes, no inference scope; no inference callable exposed. Current official default Free allowance is none. Account-specific balance is unknown. | No verified free inference route. |
| OpenAI Codex subscription | CLI 0.160.1; catalog includes `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | Actual account/read reports ChatGPT Plus; actual model/list returns seven IDs. Point-in-time ordinary quota allowed, 33% five-hour and 92% weekly used, purchased balance 0. Immutable backend revision not returned. | Real subscription route candidate; no F0 capture, frontier selection or inference probe yet. |
| External OpenAI/Anthropic/Google API | No model selected; immutable revision unknown | No corresponding API key in the process environment and no verified free grant. Subscription login is not API authority. | `BLOCKED_PROVIDER_EVIDENCE`; do not call. |
| Existing Native / Classical R0 | HiGHS/SciPy, independent Z3, official cvc5 1.4.2 | Local CPU, no external service charge. cvc5 CLI installed from official release with archive digest checked. | Existing SyGuS synthesis → original Z3 certificate path now executable. Engineering only. |

The [sanitized observations](../../research/development/f0-zero-budget-2026-10-10/provider-observations.json)
retain actual metadata. A model catalog is not an inference response; public
Gemma weights are not a verified runnable GPU environment. No small FAIL or
frontier PASS was inferred from missing calls. No independent F0 paired original
was evaluated. `BLOCKED_PROVIDER_EVIDENCE` therefore remains the scientific gate,
despite discovery of the Codex subscription candidate.

## Work continued without provider calls

Reused `hybrid_sygus_r0`, `hybrid_runtime_r0`, `f0_opened_bridge`,
`f0_capture_local`, existing source fixtures and original Z3 init/inductive/safety
checks. Downloaded the official Windows cvc5 1.4.2 static executable to the shared
local `NEUMANN 1/tools` directory, outside tracked code. No solver or model was
reimplemented; global PATH and auth configuration were not changed.

Archive SHA256: `9055de9b724724890ba5a19cfdc98f68a8c0653284afa843096dec432a0f88c3`.
Executable SHA256: `868a0d7a5e3acba7d7e71b95c7a7f89fdc7b82d1ab8d2ea4a84ff067274bdf5a`.
Version: `cvc5 1.4.2 [git 282d5e0 on branch HEAD]`.
Only a process-local PATH makes the CLI visible during the existing tests.
This addresses the prior missing-native-executable skip; it does not replace
historical first evidence, rerun an old scientific cohort or establish headroom.

Actual focused result: **80 passed, 17 subtests passed, zero skipped**, 12.20 s.
This includes the previously skipped live cvc5 synthesis and independent three
original proofs. See the [execution receipt](../../research/development/f0-zero-budget-2026-10-10/receipt.json)
and [pytest log](../../research/development/f0-zero-budget-2026-10-10/pytest.log).
CPU latency in tests is an engineering duration. Energy, complete compute,
subscription investment and peak provider memory remain UNKNOWN. Zero new
provider charges must not be reported as zero total computation cost.

Gemma's existing CUDA implementation was also found:
`experiments/general_multiplier_accelerator_core.py:FrozenAcceleratorCore`.
It imports the same frozen revision, requires at least 14 GiB CUDA memory, keeps
historical BF16 precision, and verifies artifact
`bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66`
and tokenizer
`8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207`.
Reuse that implementation for a compatible free GPU environment instead of
building another model loader. T4 compatibility/dependencies must be measured;
the adapter's existence is not an environment PASS. No historical AM1 cohort
was rerun, and no weight/precision requirement was silently changed.

## Remaining minimum authority and next action

Prefer the existing Codex subscription route over purchasing API access. Before
using it for F0, bind the actual selected provider model and returned identity,
record any unavailable revision as UNKNOWN, enforce identical permitted tools,
and retain actual response/usage/timeout traces without paid-credit fallback.
The current conversation cannot stand in for a controlled frontier receipt.
The pinned Gemma arm additionally needs a verified remaining free Kaggle quota
and compatible inference environment. Do not launch old G0/P1 notebook cells.

Single next high-value task: resolve those runtime preflight facts for the
existing model pair and source-bound F0 capture; then freeze the smallest
opened cohort **before** any model outcome. No new benchmark, neural training,
G1/G2 or sealed Decision3 is admitted while that gate remains blocked.

If a paid external API is later chosen, minimum authority is a separately
authorized API credential plus a positive explicit spend limit; neither is
granted here. Illustrative current Standard `gpt-6-astra` pricing gives
`2,000 × $10/1M + 2,000 × $50/1M = $0.12` per attempt, counting reasoning in the
output allowance. This is an estimate, not a selected model, invoice, quote for
a whole cohort or permission to execute. Retries/tools can add cost. With the
current 0 KRW limit it cannot run.

Official sources: [HF billing](https://huggingface.co/docs/inference-providers/pricing),
[Codex authentication](https://learn.chatgpt.com/docs/auth),
[Codex model/account protocol](https://learn.chatgpt.com/docs/app-server),
[OpenAI API pricing](https://developers.openai.com/api/docs/pricing),
[cvc5 release](https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.2).

GitHub: no push/PR/Notion publication. Existing local verifier patch remains
`49fe3bbd6103c620f58cc72c262b45a40ba237c0`, based on PR #179's
`a5c4097c418231b416c8ece482df5eac4ae6d9bc`; the remote CI applies only to the
remote head. No old result or model pin changed. Q1–Q7 open; HOLD_NEW_LEARNING.
