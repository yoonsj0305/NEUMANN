"""Zero-cost local hardware/runtime preflight for AM1.

This performs no model download or inference. It reports whether the current
machine can enter the already-frozen CUDA/BF16 Architecture Multiplier runner.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MIN_VRAM_MIB = 14 * 1024
SCHEMA = "neumann.am1-local-preflight.v1"


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=10, check=True).stdout.strip()


def parse_nvidia_smi(text):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            raise ValueError("unexpected nvidia-smi CSV shape")
        index, name, memory_mib, driver = parts
        rows.append({
            "index": int(index),
            "name": name,
            "memory_total_mib": int(memory_mib),
            "driver": driver,
        })
    return rows


def classify(gpus, torch_info):
    if not gpus:
        return "NO_NVIDIA_GPU"
    if max(gpu["memory_total_mib"] for gpu in gpus) < MIN_VRAM_MIB:
        return "INSUFFICIENT_VRAM_FOR_FROZEN_BF16_AM1"
    if torch_info.get("installed") is not True:
        return "HARDWARE_OK_RUNTIME_NOT_INSTALLED"
    if torch_info.get("cuda_available") is not True:
        return "HARDWARE_OK_TORCH_CUDA_UNAVAILABLE"
    if torch_info.get("bf16_supported") is not True:
        return "BF16_NOT_SUPPORTED"
    if int(torch_info.get("selected_device_memory_mib", 0)) < MIN_VRAM_MIB:
        return "TORCH_SELECTED_DEVICE_INSUFFICIENT_VRAM"
    return "READY"


def collect():
    smi_path = shutil.which("nvidia-smi")
    gpus = []
    smi_error = None
    if smi_path:
        try:
            raw = _run([
                smi_path,
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ])
            gpus = parse_nvidia_smi(raw)
        except Exception as exc:
            smi_error = type(exc).__name__ + ": " + str(exc)

    torch_info = {"installed": False}
    try:
        import torch
        torch_info = {
            "installed": True,
            "version": str(torch.__version__),
            "cuda_runtime": str(torch.version.cuda),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            torch_info.update({
                "selected_device": torch.cuda.get_device_name(0),
                "selected_device_memory_mib": int(props.total_memory // (1024 * 1024)),
                "compute_capability": list(torch.cuda.get_device_capability(0)),
                "bf16_supported": bool(torch.cuda.is_bf16_supported()),
            })
        else:
            torch_info["bf16_supported"] = False
    except Exception as exc:
        torch_info = {
            "installed": False,
            "error": type(exc).__name__ + ": " + str(exc),
        }

    packages = {}
    for name in ("transformers", "torchvision", "huggingface_hub"):
        try:
            module = __import__(name)
            packages[name] = str(getattr(module, "__version__", "unknown"))
        except Exception:
            packages[name] = None

    status = classify(gpus, torch_info)
    return {
        "schema": SCHEMA,
        "status": status,
        "hardware_admissible": bool(gpus and max(g["memory_total_mib"] for g in gpus) >= MIN_VRAM_MIB),
        "runtime_ready": status == "READY",
        "minimum_vram_mib": MIN_VRAM_MIB,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "nvidia_smi": smi_path,
        "nvidia_smi_error": smi_error,
        "gpus": gpus,
        "torch": torch_info,
        "packages": packages,
        "frozen_requirements": {
            "accelerator": "CUDA",
            "precision": "bfloat16",
            "cpu_fallback": False,
            "quantization_allowed": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--allow-runtime-missing", action="store_true")
    args = parser.parse_args()

    report = collect()
    payload = json.dumps(report, sort_keys=True, indent=2)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")

    ok = report["runtime_ready"] or (
        args.allow_runtime_missing and report["hardware_admissible"]
    )
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
