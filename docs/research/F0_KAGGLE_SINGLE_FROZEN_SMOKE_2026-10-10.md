# One frozen Gemma Kaggle runtime smoke

Status: **READY_FOR_USER_EXECUTION / GPU_AND_MODEL_NOT_YET_EXECUTED**.
The owner confirmed positive free GPU allowance. This resolves the previous
allowance UNKNOWN, but does not establish device allocation, BF16 compatibility
or model execution. No account screen, identifier or personal quota is included.
New paid budget remains zero; nothing was uploaded to GitHub.

## Execute the prepared local notebook

Artifact: `NEUMANN 1/Continuation/F0_KAGGLE_SMOKE_2026-10-10/NEUMANN_Frozen_Gemma_One_Call.ipynb`.
Import it into a **private** Kaggle notebook with Internet enabled.

1. Keep Accelerator **None** for cell 1. It reconstructs hash-bound existing
   code, fetches one pinned public original and prepares historical
   `transformers==5.16.1` / `z3-solver==4.13.4.0`. It does not download weights.
   Kaggle CUDA torch/torchvision are retained; their actual versions are logged.
2. Select the approved free **GPU T4 x2**, then run cell 2 once. Its process
   limit is 60 seconds. It checks actual CUDA, **single-device** memory >=14 GiB,
   lazy Gemma library imports, BF16 matmul and attention. Two GPU memories are
   never combined. A native BF16 flag alone neither proves nor disproves full
   PyTorch BF16 execution. No FP16 conversion, quantization or loader override.
3. Only after `READY_FOR_ONE_FROZEN_ATTEMPT`, run cell 3 once. If switching
   accelerators removed `/kaggle/working` preparation, stop and report that
   environment reset; do not treat the missing files as a model failure.
4. Download the receipts ZIP after success **or** failure, then stop the Kaggle
   session immediately. Ending Python releases its CUDA context but does not
   guarantee that the Kaggle GPU allocation stops consuming quota.

The complete model process is capped at **480 seconds** including download,
checkpoint/tokenizer hashing, initialization, generation, original verification
and final checkpoint audit. Generation uses **one** call, <=256 tokens and the
unchanged core's 30-second stopping criterion. The hard process timer is the
backstop when a kernel/initialization stalls. No automatic retries. A timeout
retains partial phase markers; missing output remains NOT VERIFIED.

## Frozen identities and scope

- Reused source baseline: local `1201d45a87a07504c060e4e2243b293371b8cd91`.
- Model: `google/gemma-4-E2B-it` at
  `3e22461f65e89153144f8adb70e3b8c2cc9845a7`.
- Expected weight/config artifact SHA-256:
  `bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66`.
- Expected tokenizer SHA-256:
  `8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207`.
- `FrozenAcceleratorCore` and its contract are reused byte-for-byte. No loader
  change, new model, training, Decision 2 rerun or sealed evaluation.
- One already OPENED original:
  [SyGuS 2019 From2018/ex1.sl](https://github.com/SyGuS-Org/benchmarks/blob/13c8deb68a873635879c9a69bc78caebd340f646/comp/2019/Inv_Track/From2018/ex1.sl),
  SHA-256 `930b37d15f14baf615c7e7741ef5d607db717390bb8465ad8255a0d12764125c`.
  It was already used by R0's clean-release engineering gate. Selection uses
  provenance and existing verifier compatibility, not any small/frontier outcome.
  Upstream license is UNKNOWN; this artifact fetches it for private evaluation
  rather than publishing new copies of upstream sources.
- Tools available to this single model request: **none**. The independent
  original checker is outside the model. This is not an armed five-role F0.

## Retained output

The worker preserves input and prompt, source/model identities, exact raw output
and token IDs, generation/request latency, startup attempt cost, startup and
generation allocated/reserved VRAM, process RSS when available, original answer
verification, final checkpoint audit, complete process time and failures.
Failure details/process logs are private; public summaries omit them. Energy,
FLOPs, monetary billing and research investment stay UNKNOWN when unmeasured.
First receipts are exclusive files; rerunning cannot replace an earlier attempt.

The startup/attempt markers also distinguish a failed model initialization from
an actual generation. Independent verifier UNKNOWN/error is not candidate FAIL.
Even a valid model answer on this opened original establishes no Frontier Gap,
new learned structure, generalization or compute advantage. Codex is not called
by this notebook; its previously captured subscription probe remains separate.

## Local validation

New adapter denial/integrity tests, existing frozen contract tests and existing
F0 original-verifier tests: **42 passed, 58 subtests passed, 0 skipped**, 6.52 s.
All three notebook code cells and 60 bundled Python sources compile. Model-free
imports/source preparation pass. All reused bundled code is identical to
`1201d45`. Notebook/registration hashes and retained logs are in
`research/development/f0-kaggle-smoke-preparation-2026-10-10/`.

These are local engineering checks. Actual Kaggle GPU allocation, CUDA/BF16
results, Gemma initialization/generation, original model-answer verification and
latest-HEAD remote CI are **not yet measured**.

References for the BF16 distinction:
[PyTorch includes an emulation option](https://docs.pytorch.org/docs/main/generated/torch.cuda.is_bf16_supported.html);
[NVIDIA lists hardware capabilities separately](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/compute-capabilities.html).

Next action: execute the preflight; if READY, obtain the one fixed-model output.
Review the first receipts before choosing any further inference/cohort contract.
