"""AM2 CP1 first audit: synthetic safety logic + real CPU physical no-GPU block.
Synthetic ready is expressly NOT actual hardware evidence.
No model/weights loaded, no new model capability study. Prereg Issue #247.
"""
import argparse
import json
import types
from pathlib import Path
from experiments.am2_cp1_native_bf16_preflight import probe_native_bf16,MIN_VRAM_BYTES

def fake_gpu(major,minor,gb,native,available=True,signature=True):
    def bf16(*,including_emulation=True):
        if not signature:
            raise TypeError("including_emulation unsupported")
        return native if not including_emulation else True
    p=types.SimpleNamespace(
        major=major,minor=minor,total_memory=gb*(1024**3),
        name=("Synthetic Tesla T4" if major==7 else "Synthetic Ampere"))
    cuda=types.SimpleNamespace(is_available=lambda:available,
        device_count=lambda:1 if available else 0,
        get_device_properties=lambda _:p,
        is_bf16_supported=bf16)
    return types.SimpleNamespace(cuda=cuda,__version__="SYNTHETIC_ONLY")

def first_run():
    tests={}
    configurations={
      "T4_emulation_is_not_native":(fake_gpu(7,5,15,False),
                                    "NATIVE_BF16_GPU_ARCHITECTURE_REQUIRED"),
      "native_ampere_16GiB_logic_only":(fake_gpu(8,0,16,True),
                                    "LOGIC_READY_SIMULATION_ONLY"),
      "ampere_12GiB_below_14GiB":(fake_gpu(8,6,12,True),
                                    "ACCELERATOR_MEMORY_BELOW_14_GIB"),
      "inaccessible_CUDA":(fake_gpu(8,0,16,True,available=False),
                                    "NO_CUDA_VISIBLE_TO_PYTORCH"),
      "no_nonemulated_bf16_query":(fake_gpu(8,0,16,True,signature=False),
                                    "CANNOT_QUERY_NONEMULATED_BF16"),
    }
    for name,(fake,expected) in configurations.items():
        result=probe_native_bf16(fake,require_nvidia_smi=False)
        assert result["status"]==expected, (name, result)
        assert result["model_loaded"] is False
        assert result["model_calls"]==0 and result["gpu_kernel_calls"]==0
        assert result["paid_compute_used"] is False
        assert result["am1_historical_verdict"]=="FAIL_UNCHANGED"
        assert result["am2_frozen_model_multiplier"]=="NOT_EVALUATED"
        tests[name]={"observed":result["status"],"expected":expected,"PASS":True}
    actual=probe_native_bf16()
    if actual["status"]!="BLOCKED_HARDWARE":
        raise RuntimeError("FIRST_FREE_GITHUB_CPU_NO_GPU_EXPECTED_BLOCKED")
    if actual["model_loaded"] is not False or actual["model_calls"]!=0:
        raise RuntimeError("UNAUTHORIZED_ACTUAL_MODEL_RUN")
    # Note: this is a PHYSICAL CPU runner, never a GPU test.
    return {"study":"AM2_CP1_ZERO_COST_NATIVE_BF16_ELIGIBILITY_FIRST",
      "preregistered_issue":247,
      "real_free_CPU_runner_status":actual["status"],
      "real_free_CPU_runner_reason":actual["reason"],
      "synthetic_logic_controls":tests,
      "synthetic_logic_controls_pass":len(tests),
      "synthetic_positive_is_not_real_hardware":True,
      "minimum_vram_bytes":MIN_VRAM_BYTES,
      "actual_gpu_compute_calls":0,"actual_model_calls":0,
      "actual_frozen_core_loaded":False,
      "provider_charged":False,
      "am1_scientific_FAIL":"PRESERVED",
      "am2_model_capability":"NOT_EVALUATED",
      "global_Q1_Q7":"OPEN",
      "first_gate_pass":len(tests)==5
        and actual["status"]=="BLOCKED_HARDWARE"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    report=first_run()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("AM2_CP1_FIRST_PHYSICAL_GATE",report["real_free_CPU_runner_status"],
          report["real_free_CPU_runner_reason"])
    print("AM2_CP1_FIRST_SYNTHETIC_CONTROLS",report["synthetic_logic_controls_pass"])
    print("AM2_CP1_REAL_MODEL_CAPABILITY",report["am2_model_capability"])
    print("AM2_CP1_FIRST_AUDIT_GATE",report["first_gate_pass"])
if __name__=="__main__":main()
