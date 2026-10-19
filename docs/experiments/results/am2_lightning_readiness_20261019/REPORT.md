# Lightning AI readiness — 2026-10-19

**BLOCKED_SERVICE_UNAVAILABLE. GPU physical gate NOT_MEASURED.**

Reviewed remote main `55178a211962caf5ce677deb37edd30bfb4fdccc`, open Draft PR #248 head `193a1bf269cfe667defcb9af57c0ebeb7ec3dec6`, open Draft PR #254 head `0c4ba37d18dd6a2a9363f5d2bb326edfe484beea`, Issue #253 and its protocol corrections. Existing source and scientific verdicts are unchanged.

## Direct observation

Opening the official [Lightning site](https://lightning.ai/) displayed an October 2026 security-incident notice. It reports an incident identified October 15 23:00 UTC, revocation of all platform user access October 16 01:00 UTC, and current Studio platform unavailability during investigation. Separate public web retrieval of the main and Studio sites returned HTTP 503. The notice is a provider statement, not evidence that this particular user's credentials were affected. No account security changes were attempted.

The public notice screenshot and accessibility text are retained in the separate local `Continuation/AM2_LIGHTNING_READINESS_20261019/` directory. Their SHA-256 values are in the JSON. Full notice text/screenshots are not republished in this Git branch. No credentials or account identifiers were collected.

## Actual readiness

| Requirement | Observation |
|---|---|
| Account eligibility / verification | UNKNOWN: account workspace unavailable |
| Actual free credits, expiry, overage controls | UNKNOWN; no promotional amount assumed |
| Free CPU Studio preparation | NOT_EXECUTED: service inaccessible |
| Account-specific L4 availability | UNKNOWN; no machine requested |
| Native BF16 / CC / VRAM / CUDA / PyTorch | NOT_MEASURED |
| GPU shutdown | NOT_APPLICABLE: no instance started |

Public pricing or old promotional documentation cannot substitute for the actual account balance or prove zero-cost entitlement. No paid resource, alternate cluster-rental route, account signup, terms acceptance, identity verification, credential connection or runtime was started. No package installation, CPU science trial, model download, inference, training, frontier call or sealed access occurred.

## Exact reusable checker, once access is restored

The unchanged CP1 file is pinned at commit `193a1bf269cfe667defcb9af57c0ebeb7ec3dec6`, SHA-256 `e515443496fd7799c961edeef0eb748ad429b90c5bca57a588260dcfce28dc13`. No new executor/framework was made.

Only AFTER the user completes any service-required signup/identity/terms steps, actual remaining free credits and no-overage conditions are verified, and a bounded L4 session is safely available:

```sh
git clone --depth 1 --branch research/am2-cp1-native-bf16-preflight-20261019 https://github.com/yoonsj0305/NEUMANN.git
cd NEUMANN
test "$(git rev-parse HEAD)" = 193a1bf269cfe667defcb9af57c0ebeb7ec3dec6
printf '%s  %s\n' e515443496fd7799c961edeef0eb748ad429b90c5bca57a588260dcfce28dc13 experiments/am2_cp1_native_bf16_preflight.py | sha256sum -c -
python -m experiments.am2_cp1_native_bf16_preflight --out ../neumann_am2_lightning_gpu_gate0.json
```

These commands were NOT run on Lightning. Prepare on free CPU first; do not allocate the GPU until the account cost gate passes and immediate shutdown control is available. Save the actual first receipt and turn the GPU off immediately after the metadata-only check. Its READY_NATIVE_BF16_PHYSICAL_GATE_ONLY result requires real accessible CUDA, CC>=8, VRAM>=14GiB and strict non-emulated BF16; it does not authorize any model experiment.

The previously committed Colab-only wrapper must not be used to attest Lightning billing eligibility. No static/mock GPU result was created or substituted for physical evidence. AM2 original checkers/cohort/matched-arm limitations remain as recorded in PR #255.

## Preserved conclusions and next single action

AM1 first FAIL unchanged; global Q1-Q7 OPEN; EX1 NOT_EVALUATED; EX2 NOT_AUTHORIZED; R0/F0/L0/NC unchanged. This is an operational block, not a model or cognitive-capability failure. CI is intentionally skipped to avoid unrelated inherited neural benchmarks.

**Next single action:** once official Studio access is restored, verify the actual account's free-credit balance and overage protection before requesting an L4. No automatic polling or repeated acquisition attempts were set up.
