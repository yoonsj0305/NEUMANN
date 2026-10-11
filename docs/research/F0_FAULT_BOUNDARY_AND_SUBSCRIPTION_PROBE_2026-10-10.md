# F0 checker-fault boundary and subscription response — 2026-10-10

Base: published Draft PR #179, `a8ad955db4c0f07b797420a245893b1c4a9c5876`.
This follow-up is local only. Earlier remote CI success applies to that base,
not to these changes. No merge, upload, paid call, GPU start, training, old
scientific cohort rerun, or sealed Decision 3 access occurred.

## Checker fault boundary

Hypothesis: exceptions from a trusted original checker must not manufacture a
small-model failure or an apparent Frontier Gap. Invalid candidate syntax and
original-task counterexamples must still be rejected.

`f0_opened_bridge.verify_original_answer` no longer maps broad ValueError,
TypeError, KeyError or overflow to False. Candidate rational/vector checks are
explicit. LP, exact arithmetic, original-source handling, and SyGuS checker
faults raise the existing `OriginalVerificationUnavailable`, with a stage and
error type. Private exception text is not copied into a public receipt. Invalid
or nonfinite LP proof results also remain UNKNOWN.

The existing SyGuS parser now raises `SyGuSParseError`, a ValueError subclass,
for its deterministic syntax/size rejection. Only that typed rejection of a
candidate is a model failure; a source error or unexpected checker exception
remains unavailable verification. Original init/inductive/safety proof
obligations, LP primal/dual tolerances, and executors are unchanged.

Acceptance: no injected checker fault may become False or generate a gap or
resource ratio; actual invalid candidates and checked counterexamples remain
False. Focused result: **86 tests passed, 58 subtests passed, zero failures and
zero skips**, 6.89 s. The five existing test files include the live cvc5 fixture,
original Z3 proof checks, capture/runtime regression, and F0/F1 contracts.
New tests inject eight exception classes into three checker paths and retain
the existing all-role/repeat UNKNOWN checks. No model response is a test fixture.

## Actual subscription authentication probe

Read-only Codex CLI 0.160.1 preflight confirmed managed ChatGPT authentication,
backend permission for ordinary included usage, absence of paid-credit fallback,
and no API-key environment override. Account payloads stayed in process memory.
Only execution-eligibility booleans and catalog/protocol facts were exported.

Before inference, a separate registration fixed one authentication-only call,
zero retries, a 30-second wall budget, zero paid budget, no tools, and a fixed
marker prompt. The actual catalog default `gpt-6.1-sol` was used; this was not a
selection of the future scientific frontier reference. The request was made
through the existing CLI app-server's managed authentication; no token was
extracted and no external API credential was fabricated.

Actual result: one completed turn, response `NEUMANN_AUTH_PROBE_OK`, returned
model `gpt-6.1-sol` and provider `openai`, zero tool calls, no observed model
reroute, approximately 4,992 ms. Reported usage: 10,614 input tokens, including
4,992 cached input tokens; 11 output tokens, zero reported reasoning-output
tokens. CLI system/tool context contributes to these totals; the marker prompt
alone does not represent the inference cost. New paid spend is zero; total
compute, energy, peak provider memory and subscription investment are UNKNOWN.

This establishes that a real included-usage response is obtainable through the
local Codex protocol at that time. It supplies neither an immutable backend
revision nor a signed provider trace/raw backend request identifier. Protocol
thread/turn identities were hashed. The evidence does not claim stronger
attestation than the local capture actually provides.

**No original problem was submitted, no Gemma call occurred, and paired F0
original count remains zero.** A successful marker is not evidence of frontier
task capability, a capability gap, structural discovery, or resource advantage.
No further probe or model attempt is authorized by this one-call registration.

Official context: [managed authentication](https://learn.chatgpt.com/docs/auth),
[app-server model/turn/usage protocol](https://learn.chatgpt.com/docs/app-server),
and [included usage versus paid credits/API billing](https://learn.chatgpt.com/docs/pricing).
Account-specific access and the actual response above were observed locally;
the documentation alone was not used as entitlement evidence.

## Privacy and remaining gate

New public artifacts omit account IDs, email, plan names, precise quota
percentages, balances, and credentials. The current readiness summary now omits
those personal details. Its already published historical provider JSON and
first receipt remain byte-identical: they are still present remotely. No
GitHub deletion or history rewrite was performed. New evidence is stored
separately, rather than altering the old receipt's hashes or zero-call result.

Kaggle browser discovery timed out; no remaining free GPU quota was obtained
and no session was started. Reuse the exact Gemma revision
`3e22461f65e89153144f8adb70e3b8c2cc9845a7` and existing accelerator adapter,
with its original artifact/tokenizer hashes and BF16 contract. Its existence
does not establish that the available T4 environment can execute that contract.

Decision: **ENGINEERING PASS; subscription response route observed;
BLOCKED_PROVIDER_EVIDENCE for the paired F0; HOLD_NEW_LEARNING.** Global Q1–Q7
remain open. The next single high-value action is to verify an available free
environment for the pinned Gemma arm, without running old notebook cells or
changing revision/precision. Freeze the actual opened comparison contract and
resolve model identity/attestation limitations before submitting original tasks.

Evidence: [new local receipt](../../research/development/f0-verifier-fault-boundary-2026-10-10/receipt.json),
[registration](../../research/development/f0-verifier-fault-boundary-2026-10-10/authentication-probe.registration.json),
[actual response](../../research/development/f0-verifier-fault-boundary-2026-10-10/authentication-probe.result.public.json),
and [test log](../../research/development/f0-verifier-fault-boundary-2026-10-10/pytest.log).
