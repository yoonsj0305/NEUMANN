# AM1 Local Zero-Cost Execution

Status: **HISTORICAL LOCAL RUN INSTRUCTIONS, NOT CURRENT SCIENCE ACTION.**

> **2026-10-19 correction:** The first real frozen AM1 BF16/Tesla T4 study has **already run and FAILED** (36/36 terminal results, DIRECT/TOOL/NEUMANN 0/12, 72/72 non-final thought-channel generations). That immutable first AM1 cannot be reexecuted with altered prompts/parser and called a scientific first PASS. This document documents an archived launcher only. Follow [critical path](critical_path_v1062.md) and [new AM2 CP0 report](AM2_CP0_FIRST_TYPED_CONTROL_VERDICT_20261019.md) instead.


This path exists so Decision 2 can be executed on a suitable local NVIDIA GPU
without paid cloud compute. It does not change the frozen Architecture
Multiplier task set, model revision, precision, baseline rights, budgets or
PASS/FAIL thresholds.

## What is already prepared

Windows entrypoints at repository root:

- `AM1_LOCAL_SETUP.cmd`
- `AM1_LOCAL_RUN.cmd`

Supporting scripts:

- `scripts/am1_local_setup.ps1`
- `scripts/am1_local_run.ps1`
- `experiments/general_multiplier_local_preflight.py`
- `experiments/general_multiplier_evidence_replay.py`

The historical first-run launcher uses the authoritative
`experiments/general_multiplier_first.py` and the same frozen Decision-2
contract merged in PR #126.

## Hardware admission

The local path refuses to weaken the experiment merely to fit hardware.

Required by the current runner:

- NVIDIA CUDA device,
- at least 14 GiB total VRAM,
- BF16 reported as supported by PyTorch,
- no CPU fallback,
- no quantization.

A machine that fails those conditions does **not** create negative capability
evidence. It is simply inadmissible for this frozen runner.

## Setup

Double-click:

`AM1_LOCAL_SETUP.cmd`

The setup first performs a hardware-only check. If hardware is admissible it
creates an isolated `.venv-am1` and installs the AM1 runtime.

Default CUDA wheel channel is `cu126`. The setup script also accepts
`cu130` or `cu132` as an environment-repair choice when required by the
local driver/GPU. Changing that wheel channel does not change the scientific
model identity: the run still verifies the exact frozen model artifact SHA,
tokenizer SHA, model revision and BF16 precision before evidence is admitted.

The default pinned runtime mirrors the first actual E2B evidence where useful:

- PyTorch 2.14.0,
- torchvision 0.29.0,
- transformers 5.10.1.

## Model access

If the frozen Hugging Face model requires authenticated download, set
`HF_TOKEN` in the environment before the first run. The token is used only to
download the frozen artifact. The downloaded bytes are hash-checked before
inference and a mismatch fails closed.

## One-shot run

Double-click:

`AM1_LOCAL_RUN.cmd`

The launcher:

1. repeats CUDA/VRAM/BF16 preflight,
2. refuses tracked source modifications when Git metadata is available,
3. selects CUDA device 0,
4. runs the 36 frozen observations,
5. retains failures instead of replacing them,
6. performs a model-free evidence replay,
7. writes a ZIP under `_am1_local`.

An archive ZIP from a historical/diagnostic rerun must never replace the original first frozen AM1 scientific evidence.

## Windows portability boundary

The bounded Python checker previously depended on Unix `resource` and could
not run on native Windows. The local-prep patch keeps Unix kernel resource caps
where available. On Windows the same restricted AST/builtin policy and parent
subprocess deadline remain active; unavailable process-RSS telemetry is
recorded as UNKNOWN rather than fabricated.

## What remains blocked

The actual AM1 verdict is FAIL. Until a NEW separately frozen matched architecture PASS exists, do not start:

- sealed v107 evaluation,
- frontier reference execution,
- 4B/7B scaling,
- Edge optimization,
- new training,
- large benchmark expansion.

The only next scientific action is the first valid AM1 execution.
