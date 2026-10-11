# Native BF16 admission: environment checks only

Current decision: **HOLD_INFERENCE / BLOCKED_SMALL_MODEL_RUNTIME_NATIVE_BF16**.
This is a hardware/authority boundary, not a model capability FAIL. Paid budget
is zero. No GitHub upload, GPU session, checkpoint download or model call was
performed in this continuation. No fresh F0 evidence was obtained.

## Contract interpretation

The frozen preregistration pins BF16, Gemma revision, artifact and tokenizer
hashes. The local execution contract forbids quantization and CPU fallback and
requires one GPU with at least 14 GiB. The existing preflight's BF16 API result
does not separately establish native hardware support. No explicit emulation
permission was found in the two contracts, `general_multiplier_contract.py`,
`architecture_multiplier_gate.md` or `am1_local_execution.md`.

That is **NOT_EXPLICITLY_AUTHORIZED**, not a claim that the historical contract
explicitly banned emulation. The owner's newer instruction admits CPU preparation
and GPU checks only and requires stopping without established emulation authority.
The stricter current adapter gate does not amend frozen contracts or prior results.

Unchanged: `FrozenAcceleratorCore`, BF16 weights, model
`google/gemma-4-E2B-it`, revision
`3e22461f65e89153144f8adb70e3b8c2cc9845a7`, expected artifact SHA
`bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66`
and tokenizer SHA
`8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207`.

## Actual changes and evidence

The existing `f0_kaggle_frozen_smoke.py` now selects CUDA device 0 and records:

- `is_bf16_supported(including_emulation=False)` as `bf16_native`.
- The separate `including_emulation=True` flag.
- Small BF16 matmul/SDPA dtype and finite-output checks. These are not a full
  Gemma compatibility test and do not attest a native kernel implementation.
- Single-device memory and CUDA details; aggregate multi-GPU memory is ineligible.
- `BLOCKED_BF16_CONTRACT` for native False even if operations succeed;
  `NOT_VERIFIED_NATIVE_BF16` for an API that cannot attest native support.
- Native True plus operation/library success yields
  `ENVIRONMENT_CHECK_PASS_INFERENCE_HOLD`. The existing smoke entrypoint also
  returns before importing/constructing the frozen loader under current authority.

No alternate loader, precision conversion, model framework or training was added.
Libraries are checked after the hardware gate so a Transformers import failure
cannot conceal native BF16 results. Blocked hardware does not establish model
library compatibility; the receipt explicitly records `model_libraries_checked`.

Local model-free tests: **45 passed, 58 subtests passed, zero failed/skipped**.
Native-absent but operations-success, old API UNKNOWN, unsupported kernels,
insufficient single-device VRAM, mutated bundle, first-receipt preservation and
native-supported-but-no-inference are covered, alongside existing frozen contract
and original-verifier regression tests. These synthetic tests are not T4 readings.

The environment-only notebook has two code cells and no inference cell. Static
compilation of both cells and 60 bundled Python sources passed. Existing R0
original preparation/imports passed without a model. All reused core/domain files
match `1201d45`; frozen contracts match preparation parent `6438835`.

## Free hardware investigation

| Route | Hardware assessment | Eligibility / current decision |
| --- | --- | --- |
| Kaggle general T4 x2 | T4 is CC 7.5; no native BF16. Two VRAM pools cannot satisfy a native requirement. | Owner's allowance confirmation remains valid; T4 inference is held regardless of remaining time. Actual assigned device/API/operation results are unmeasured. |
| Kaggle restricted L4 x4 | L4 is CC 8.9, BF16-capable; verify one actual device >=14 GiB. | Official Gemma competition restricts L4 use to its attached notebooks and disables Internet. This is not a general research entitlement; no restriction bypass or allocation attempted. |
| Hugging Face ZeroGPU | Current docs specify RTX PRO 6000 Blackwell, 48 GB for `large`; native BF16 hardware. | Official docs allow free accounts in good standing to host two Spaces. Account eligibility/remaining free allowance and original loader compatibility are UNKNOWN. Gradio/dynamic allocation needs an actual real-GPU check; simulated startup CUDA is not native evidence. No Space created or private data published. |
| Colab free | GPU type varies; no guarantee of a native-BF16 device with adequate VRAM. | Only consider an actual zero-charge qualifying allocation. No paid plan, premium selection or runtime started. |

Primary sources checked on 2026-10-10:
[NVIDIA GPU compute capabilities](https://developer.nvidia.com/cuda/gpus),
[NVIDIA feature table](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html),
[PyTorch API](https://docs.pytorch.org/docs/main/generated/torch.cuda.is_bf16_supported.html),
[Kaggle P100 retirement / T4 availability](https://www.kaggle.com/product-announcements/735239),
[Kaggle L4 restrictions](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview),
[ZeroGPU specifications and free hosting](https://huggingface.co/docs/hub/spaces-zerogpu),
[Colab FAQ](https://research.google.com/colaboratory/faq.html).

No currently authenticated, allocated, zero-charge native-BF16 >=14 GiB runtime
has been verified. Browser automation remains unavailable; the actual Kaggle
environment check is therefore **NOT_EXECUTED**, rather than inferred from docs.

## Active artifact and shortest next action

Use only `NEUMANN 1/Continuation/F0_BF16_ENVIRONMENT_CHECK_2026-10-10/`
`NEUMANN_Frozen_Gemma_Environment_Only.ipynb`. Run CPU preparation with GPU disabled,
then at most the 60-second GPU check on a confirmed free allocation. Download its
private receipts and stop the session after any outcome. Even PASS does not run
Gemma under this instruction. No account screen or personal usage data is bundled.

The original one-call notebook is preserved byte-for-byte with SHA
`5ef55d0d86020d74f15efb137c583683dcc5510e1110c49dc6b29626e53fccf1`;
its older READY rule is not current inference authority. The new copy is derived
from its source closure and CPU/check cells; inference cell removed. Historical
`registration.json` remains unchanged and is explicitly superseded for execution
by the new environment-only policy, not reclassified as a completed experiment.

Evidence: `research/development/f0-bf16-environment-check-2026-10-10/` contains the
active policy, source/bundle identities, static preparation receipt and test logs.
Original prepared source remains OPENED SyGuS 2019 From2018/ex1, SHA
`930b37d15f14baf615c7e7741ef5d607db717390bb8465ad8255a0d12764125c`;
it is not fresh F0 data. Protected local commits `1201d45` and `6438835`, historical
test receipts, first evidence and sealed boundaries are retained. Remote CI for
this local change has not run. Free runtime eligibility is the next obstacle;
no paid call or model-contract relaxation is proposed.
