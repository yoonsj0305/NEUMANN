"""AM2-CP1 native CUDA BF16/VRAM gate. Hardware-only, never a capability run.

A Tesla T4 can store BF16 tensors but DOES NOT offer native BF16 math:
torch.cuda.is_bf16_supported(including_emulation=False) must be True.
This check does not open source tasks, model weights or any provider.
Preregd GitHub Issue #247, BEFORE first CPU CI / first actual physical probe.
"""
from __future__ import annotations
import argparse
import json
import platform
import subprocess
from pathlib import Path

MIN_VRAM_BYTES = 14 * 1024**3

def blocked(reason,details=None):
    return {
        "schema":"neumann.am2-cp1.native-bf16-hardware.v1",
        "status":"BLOCKED_HARDWARE","reason":reason,
        "hardware_only":True,
        "model_loaded":False,"model_calls":0,"gpu_kernel_calls":0,
        "paid_compute_used":False,"am1_historical_verdict":"FAIL_UNCHANGED",
        "am2_frozen_model_multiplier":"NOT_EVALUATED",
        "global_Q1_Q7":"OPEN",
        "details":details or {},
    }

def probe_native_bf16(torch_module=None, *, require_nvidia_smi=True):
    """Only real device probing when require_nvidia_smi=True & no injected mock.
    A caller supplied mock is for LOGICAL SELF-TESTS ONLY and cannot certify hardware.
    """
    if require_nvidia_smi:
        try:
            device_probe=subprocess.run(
                ["nvidia-smi","--query-gpu=name","--format=csv,noheader"],
                capture_output=True,text=True,timeout=6)
        except (FileNotFoundError,PermissionError,subprocess.TimeoutExpired):
            return blocked("NO_NVIDIA_CUDA_ACCELERATOR_VISIBLE")
        if device_probe.returncode!=0 or not device_probe.stdout.strip():
            return blocked("NO_NVIDIA_CUDA_ACCELERATOR_VISIBLE")
    if torch_module is None:
        try:
            import torch as torch_module
        except Exception as e:
            return blocked("PYTORCH_ACCELERATOR_PACKAGE_NOT_AVAILABLE",
                {"error_class":type(e).__name__})
    simulation_only=bool(torch_module is not None and not require_nvidia_smi)
    t=torch_module
    try:
        if not t.cuda.is_available() or t.cuda.device_count()<1:
            return blocked("NO_CUDA_VISIBLE_TO_PYTORCH")
        p=t.cuda.get_device_properties(0)
        capacity=int(p.total_memory)
        major=int(p.major)
        minor=int(p.minor)
        name=str(p.name)
        details={"device_name":name,"compute_capability":[major,minor],
          "vram_bytes":capacity,"minimum_vram_bytes":MIN_VRAM_BYTES,
          "torch_version":str(t.__version__),
          "python_version":platform.python_version()}
        if major<8:
            return blocked("NATIVE_BF16_GPU_ARCHITECTURE_REQUIRED",details)
        if capacity<MIN_VRAM_BYTES:
            return blocked("ACCELERATOR_MEMORY_BELOW_14_GIB",details)
        try:
            native=t.cuda.is_bf16_supported(including_emulation=False)
        except (TypeError,AttributeError) as e:
            return blocked("CANNOT_QUERY_NONEMULATED_BF16",{
                **details,"error_class":type(e).__name__})
        if native is not True:
            return blocked("BF16_NATIVE_HARDWARE_NOT_SUPPORTED",details)
        details["native_bfloat16_reported"]=True
        return {
            "schema":"neumann.am2-cp1.native-bf16-hardware.v1",
            "status":("LOGIC_READY_SIMULATION_ONLY" if simulation_only
            else "READY_NATIVE_BF16_PHYSICAL_GATE_ONLY"),
            "hardware_only":True,"model_loaded":False,
            "model_calls":0,"gpu_kernel_calls":0,
            "paid_compute_used":False,
            "am1_historical_verdict":"FAIL_UNCHANGED",
            "am2_frozen_model_multiplier":"NOT_EVALUATED",
            "global_Q1_Q7":"OPEN",
            "details":details,
        }
    except Exception as e:
        return blocked("PHYSICAL_HARDWARE_PROBE_FAILED",
            {"error_class":type(e).__name__,"error_excerpt":str(e)[:130]})

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    receipt=probe_native_bf16()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("AM2_NATIVE_BF16_PHYSICAL_PREFLIGHT",json.dumps(receipt,sort_keys=True))
    print("AM2_NEURAL_CAPABILITY",receipt["am2_frozen_model_multiplier"])
if __name__=="__main__":
    main()
