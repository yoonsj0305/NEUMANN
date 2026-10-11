# Colab T4 result and bounded free-runtime follow-up

**COLAB_T4_NATIVE_BF16_UNSUPPORTED / BLOCKED_SMALL_MODEL_RUNTIME.**
The owner supplied actual Colab hardware measurements: Tesla T4, single-device
VRAM 15637086208 bytes, native BF16 false, BF16 operations true, ready false.
VRAM passes the unchanged 14 GiB minimum; native BF16 does not. The raw runtime
JSON, measurement timestamp and Torch version were not received and are UNKNOWN.
The separate human-hardware-result.json records this provenance; no agent GPU
execution is claimed. Gemma inference is 0 and Frontier Gap remains unmeasured.

Preserve the earlier UNKNOWN readiness receipt and all notebooks as historical
preparation. The existing preflight already distinguishes native support from
working BF16 operations and blocks emulation without explicit authority. No
runtime patch, new loader, FP16, quantization or contract amendment is needed.
The frozen Gemma revision remains 3e22461f65e89153144f8adb70e3b8c2cc9845a7.
FrozenAcceleratorCore and expected checkpoint/tokenizer hashes are unchanged;
an expected hash is not a newly measured downloaded-checkpoint identity.

The connected HF authentication lookup returned an authenticated read context
but no verified email, account age, ZeroGPU entitlement or remaining allowance.
It did not establish Space write authority. Account identifiers and subscription
details were not copied into this record. The documentation connector was
unavailable; the official web documentation was checked instead.

[Official ZeroGPU documentation](https://huggingface.co/docs/hub/spaces-zerogpu)
lists default half RTX Pro 6000 Blackwell hardware with 48GB VRAM and conditional
free personal hosting. This is a hardware candidate, not an actual allocation
or free entitlement. Only Gradio is supported; outside GPU-decorated functions
CUDA is emulated. Admission must run the existing preflight inside a real GPU
allocation, before constructing the unchanged core. Included allowance and paid
credit fallback must be checked first. No Space, job or new adapter was created.
Repeated Colab/Kaggle allocations stop; no paid service was used.

F0 preparation reuses the already opened SyGuS 2019 From2018/ex1 source, R0 cvc5
and the independent Z3 init/induction/safety verifier. The existing source and
notebook identities are checked, without rerunning historical performance
experiments. The Codex marker is authentication evidence only; no original task
answer, backend revision or paired frontier comparison is inferred from it.
The LP-only three-route capture must not duplicate one SyGuS answer as three
distinct discovery paths. The prior 8ffcd32 regression results remain historical.

Actual local verification: 3 existing regression tests passed, 0 failed/skipped
(1.600 seconds in the XML report): native BF16 rejection despite working BF16
operations, an old API leaving native evidence UNKNOWN, and a successful
preflight never entering the loader while the inference gate is closed. These
use synthetic hardware and do not reproduce the Colab measurement. All three
notebook hashes and five core/contract/adapter source identities were preserved.
The existing opened source passed CPU parsing; no native performance experiment
or model execution was repeated. No remote CI was run for these local changes.

Current follow-up evidence and local verification receipts are in
research/development/f0-colab-t4-result-2026-10-10/. The sole next admission step
is confirmation of free ZeroGPU eligibility and remaining included allowance.
Without it, HOLD_NEW_LEARNING and FRONTIER_GAP_UNARMED continue. A T4 emulation
study would need separate explicit authority and a distinct contract; none was
created or executed. Changes are local only, with no GitHub upload.
