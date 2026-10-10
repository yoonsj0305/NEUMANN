# ZeroGPU eligibility and unchanged-core suitability

Decision: **BLOCKED_SMALL_MODEL_RUNTIME**. This continuation is read-only
eligibility inspection and static analysis, not model inference or a new F0 run.

| Admission item | Result |
| --- | --- |
| Free personal Space creation | NOT_ELIGIBLE under the documented account-age rule; backend grant itself UNKNOWN |
| Existing Space inventory | Public listing inspected; private inventory UNKNOWN. Account-specific counts retained outside Git |
| Remaining included GPU-seconds | UNKNOWN; authenticated quota could not be read |
| Unchanged executor compatibility | NOT_VERIFIED; not a confirmed technical impossibility |
| Expected cold GPU occupancy | UNKNOWN; initialization/restore/audit have no measurement on this hardware |
| Next GPU execution | NO; this instruction authorizes no GPU call, Space creation or model download |

## Read-only access evidence

The connected HF account is authenticated. Public account creation metadata was
read and its timestamp was checked against current UTC: the account-age condition
for free personal hosting is not satisfied. Email verification, good standing
and backend entitlement were not returned. No account name, creation timestamp,
identifier, token, plan snapshot or numeric personal quota is copied into Git.
This policy result is specific to creating an own free ZeroGPU Space. It does
not establish inability to use someone else's existing Space.

`hf` was absent from PATH and the research venv had no huggingface_hub. Official
SDK 2.2.0 was installed only into a separate local read-only utility directory;
the research venv and frozen loader dependencies were not changed. Its
`HfApi.get_zero_gpu_quota(token=True)` was invoked once. It stopped locally with
LocalTokenNotFoundError: neither an HF_TOKEN environment value nor a standard
SDK login was available. No authenticated quota HTTP request was issued. The
connected app's credential has no read-billing scope and exposes no quota tool;
its OAuth credential was not extracted or transferred to the SDK.

The CLI command and SDK method are real documented interfaces. Quota reading
requires OAuth read-billing or a fine-grained token with Billing read-usage and
payment-method-status permission. A quota response would not by itself establish
hosting entitlement. Listing public Spaces used metadata GETs only, never an
app/Gradio endpoint; private occupancy is not inferable from the public list.

## Static core boundary

Analysis used the unchanged experiments/general_multiplier_accelerator_core.py
and experiments/f0_kaggle_frozen_smoke.py, plus existing registration and notebook.
Frozen revision is 3e22461f65e89153144f8adb70e3b8c2cc9845a7; core, contract,
checkpoint expectations and original verifier authority are unchanged.

The core constructor checks CUDA/device memory and seeds CUDA before calling
snapshot_download. It then hashes the checkpoint, creates the processor and
BF16 model, moves to cuda:0, records parameter version counters, synchronizes
CUDA and captures environment identity. These operations are inseparable in
the current constructor. generate() and audit() use that device and version
identity; output is already converted to CPU tokens/plain Python values.

ZeroGPU's normal eager-loading path uses patched CUDA at module scope and a
real worker only inside the decorated Gradio handler. Consequently a root-scope
core identity cannot be accepted as actual GPU/BF16 admission. Fixed device
indexing, synchronization, version-counter checks and identity captured across
the packing/fork boundary are unverified. The existing notebook's subprocess
worker is not automatically an allocation-bound ZeroGPU handler. Copying the
notebook or decorating an inner helper is not a demonstrated working adapter.

Minimal future adapter proposal ONLY: import spaces before CUDA-touching imports;
bind the decorated function directly to Gradio; reuse the existing preflight
inside the actual GPU worker. Only after admission and later inference authority,
construct the unchanged core in that same worker, call its existing generate
and audit, return plain receipts, and run the existing original verifier on CPU.
Do not fake properties, rewrite a loader, return CUDA objects or keep the core
in gr.State. Worker-local cold loading is outside the recommended eager pattern
and must be evaluated before approval; compatibility remains NOT_VERIFIED.
No adapter or Space was implemented/deployed in this continuation.

## Placement and five-minute feasibility

CPU-only preparation can check code/source hashes, parse the opened original
and prepare the prompt. After eligibility and separate download authority, the
same pinned snapshot could be cached on CPU so the unchanged constructor's
snapshot call hits cache. Cache preparation and hashes must still be charged
as startup/investment; they are not free execution evidence.

Inside an actual GPU worker, native admission, cold core creation/load/transfer,
generation and core audit consume allocation time, including CPU hashing there.
The independent original Z3 verification can run after returning CPU receipts.
Scheduler cold restore/queue time and any retries must be tracked separately.
The official free tier's five minutes is a policy allowance, not the account's
measured remaining time or a measured runtime estimate. The existing preparation
has a 60-second preflight limit, 30-second generation deadline and a 480-second
complete-attempt ceiling. That ceiling does not prove a <=300-second fit.
No empirical bound for cold initialization/audit exists on ZeroGPU. A future
registration must fit requested GPU durations inside actually read remaining
allowance with no paid fallback; do not silently substitute a new time contract.

## F0 continuation and stop decision

Stop free-GPU allocation hunting here. Reuse the already opened SyGuS 2019
From2018/ex1 source, R0 cvc5 and independent Z3 original init/induction/safety
checker. Confirm source/native identities and missing-response/UNKNOWN behavior
without repeating Native performance cohorts or substituting model responses.
Actual local regression execution: 6 tests passed, 0 failed/skipped (1.70 seconds
as pytest reports): four existing Z3 init/induction/safety cases, missing model
receipt handling and UNKNOWN preventing a false Frontier Gap. These are existing
engineering fixtures and injected outcomes, not provider responses or fresh
scientific samples. No Native synthesis/performance cohort was rerun.
The prior Codex marker remains authentication evidence only. Paired original
responses and Gemma inference remain zero; HOLD_NEW_LEARNING continues.

Evidence: research/development/f0-zerogpu-suitability-2026-10-10/ contains an
allowlisted public decision and local verification receipt. Private eligibility
details, account counts and the SDK utility remain only under Continuation.
No GitHub upload or remote CI is performed. No credentials need to be sent in chat.

Primary sources checked on 2026-10-10:
[ZeroGPU hosting/runtime](https://huggingface.co/docs/hub/spaces-zerogpu),
[quota API and permission](https://huggingface.co/docs/huggingface_hub/v2.1.1/package_reference/hf_api#get_zero_gpu_quota),
[CLI quota command](https://huggingface.co/docs/huggingface_hub/v2.1.0/guides/cli),
[HF ZeroGPU lifecycle reference](https://github.com/huggingface/skills/blob/main/skills/huggingface-spaces/references/zerogpu.md).
