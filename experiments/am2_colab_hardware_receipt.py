"""Colab metadata receipt around the unchanged CP1 gate. NEVER loads a model.

Run only inside a user-confirmed free Colab runtime. This is not an AM2 runner.
No pip, model download, tensor arithmetic, training, or historical audit replay.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter


def write_once(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def load_cp1():
    path = Path(__file__).with_name("am2_cp1_native_bf16_preflight.py")
    spec = importlib.util.spec_from_file_location("unchanged_cp1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initial_receipt():
    return {
        "schema": "neumann.am2.colab-hardware-only.v1",
        "status": "BLOCKED_FREE_ENTITLEMENT_UNCONFIRMED",
        "free_runtime_evidence": "UNKNOWN",
        "measured_at_utc": None,
        "cp1": None,
        "telemetry": {"torch_version": None, "cuda_runtime_version": None,
                      "driver_version": None, "free_device_memory_bytes": None,
                      "total_device_memory_bytes": None, "native_bf16": None},
        "model_loaded": False, "model_calls": 0, "model_forward_calls": 0,
        "model_downloads": 0, "training_runs": 0,
        "gpu_tensor_compute_calls": 0, "paid_resource_requests": 0,
        "actual_monetary_charge": None,
        "am1_first_verdict": "FAIL_UNCHANGED",
        "am2_comparison": "NOT_EVALUATED", "global_Q1_Q7": "OPEN",
        "sealed_data_opened": False,
        "inference_authorized_by_this_receipt": False,
    }


def measure_hardware(free_runtime_confirmed):
    receipt = initial_receipt()
    if free_runtime_confirmed is not True:
        return receipt
    receipt["free_runtime_evidence"] = "OPERATOR_CONFIRMED_FREE_COLAB_UI_NOT_API_AUDITED"
    receipt["measured_at_utc"] = datetime.now(timezone.utc).isoformat()
    # Bind the same selected device before CP1 asks the current-device BF16 API.
    try:
        import torch
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            torch.cuda.set_device(0)
    except Exception:
        pass  # The unchanged checker owns the primary unavailable-runtime verdict.
    receipt["cp1"] = load_cp1().probe_native_bf16()
    receipt["status"] = receipt["cp1"]["status"]
    try:
        import torch
        telemetry = receipt["telemetry"]
        telemetry["torch_version"] = str(torch.__version__)
        telemetry["cuda_runtime_version"] = torch.version.cuda
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            # CP1 tests the current device's BF16 API; bind its selected GPU 0.
            torch.cuda.set_device(0)
            free, total = torch.cuda.mem_get_info(0)
            telemetry["free_device_memory_bytes"] = int(free)
            telemetry["total_device_memory_bytes"] = int(total)
            try:
                telemetry["native_bf16"] = bool(
                    torch.cuda.is_bf16_supported(including_emulation=False))
            except (AttributeError, TypeError):
                pass  # Old API cannot establish native support; never emulate.
        driver = subprocess.run(
            ["nvidia-smi", "--id=0", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=6, check=True)
        telemetry["driver_version"] = driver.stdout.strip().splitlines()[0]
    except Exception as exc:
        # Preserve the actual CP1 failure; do not expose environment secrets.
        receipt["telemetry_error_class"] = type(exc).__name__
    if receipt["status"] == "READY_NATIVE_BF16_PHYSICAL_GATE_ONLY":
        t = receipt["telemetry"]
        if any(value is None for value in t.values()) or t["native_bf16"] is not True:
            receipt["status"] = "BLOCKED_INCOMPLETE_TELEMETRY"
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="NEW receipt directory; existing directory is refused")
    parser.add_argument("--confirm-free-colab-runtime", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    receipt = measure_hardware(args.confirm_free_colab_runtime)
    receipt["hardware_probe_wall_seconds"] = perf_counter() - started
    receipt["source_sha256"] = {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("am2_colab_hardware_receipt.py", "am2_cp1_native_bf16_preflight.py")}
    write_once(args.out / "GPU_QUALIFICATION.json", receipt)
    write_once(args.out / "SHA256.json", {
        "GPU_QUALIFICATION.json": hashlib.sha256(
            (args.out / "GPU_QUALIFICATION.json").read_bytes()).hexdigest()})
    print(json.dumps({"status": receipt["status"], "out": str(args.out),
                      "model_calls": 0, "am2_comparison": "NOT_EVALUATED"}))
    return 0 if receipt["status"] == "READY_NATIVE_BF16_PHYSICAL_GATE_ONLY" else 2


if __name__ == "__main__":
    sys.exit(main())
