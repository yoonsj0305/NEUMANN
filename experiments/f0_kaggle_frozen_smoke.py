"""One opened-source runtime smoke; reuse FrozenAcceleratorCore, never train.

This is a bounded notebook adapter, not a five-arm F0 result or a model loader.
The parent notebook enforces the hard process deadline, including initialization.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

MODEL_ID = "google/gemma-4-E2B-it"
MODEL_REVISION = "3e22461f65e89153144f8adb70e3b8c2cc9845a7"
MIN_VRAM = 14 * 1024**3


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)


def check_bundle(root):
    manifest = json.loads((root / "bundle-manifest.json").read_text())
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("BUNDLE_IDENTITY_MISMATCH: " + name)
    return manifest


def preflight(torch_module=None):
    """No checkpoint download. BF16 execution and native support are distinct."""
    started = time.perf_counter()
    result = {"status": "BLOCKED_ENVIRONMENT", "stage": "LIBRARIES",
              "model_calls": 0, "checkpoint_download_attempted": False,
              "versions": {}, "bf16_native": None, "bf16_operations": None}
    try:
        if torch_module is None:
            for name in ("torch", "torchvision", "transformers", "huggingface_hub",
                         "numpy", "scipy", "sklearn", "z3"):
                result["dependency"] = name
                module = importlib.import_module(name)
                result["versions"][name] = getattr(module, "__version__", None)
            import transformers
            for name in ("AutoModelForMultimodalLM", "AutoProcessor", "Gemma4Processor"):
                result["dependency"] = "transformers." + name
                getattr(transformers, name)  # Actually import lazy classes.
            result["versions"]["z3"] = importlib.import_module("z3").get_version_string()
            torch_module = importlib.import_module("torch")
        t = torch_module
        result["stage"] = "CUDA"
        if not t.cuda.is_available() or t.cuda.device_count() < 1:
            raise RuntimeError("CUDA_UNAVAILABLE")
        p = t.cuda.get_device_properties(0)
        result.update(device_name=t.cuda.get_device_name(0),
                      cuda_runtime=t.version.cuda,
                      device_count=t.cuda.device_count(), selected_device=0,
                      compute_capability=list(t.cuda.get_device_capability(0)),
                      single_device_vram_bytes=int(p.total_memory))
        result["stage"] = "SINGLE_DEVICE_VRAM"
        if int(p.total_memory) < MIN_VRAM:
            raise RuntimeError("SINGLE_GPU_BELOW_14_GIB")
        result["stage"] = "BF16_OPERATIONS"
        try:
            result["bf16_native"] = bool(t.cuda.is_bf16_supported(including_emulation=False))
        except TypeError:
            result["bf16_native"] = None  # Old API cannot attest native support.
        # Do not reject emulated BF16 solely by compute capability; actually test
        # BF16 tensors/matmul/attention. No cast, quantization or loader override.
        with t.inference_mode():
            a = t.ones((32, 32), device="cuda:0", dtype=t.bfloat16)
            b = a @ a
            q = t.ones((1, 1, 8, 32), device="cuda:0", dtype=t.bfloat16)
            attention = t.nn.functional.scaled_dot_product_attention(q, q, q)
            t.cuda.synchronize(0)
            if (b.dtype != t.bfloat16 or attention.dtype != t.bfloat16
                    or not bool(t.isfinite(b).all())
                    or not bool(t.isfinite(attention).all())):
                raise RuntimeError("BF16_OPERATION_INVALID")
        result["bf16_operations"] = True
        del a, b, q, attention
        t.cuda.empty_cache()
        result["status"] = "READY_FOR_ONE_FROZEN_ATTEMPT"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        # No token, account data, authentication errors or local paths exported.
        result["reason"] = str(exc) if str(exc) in {
            "CUDA_UNAVAILABLE", "SINGLE_GPU_BELOW_14_GIB", "BF16_OPERATION_INVALID"
        } else "ENVIRONMENT_OPERATION_FAILED"
    result["preflight_ms"] = (time.perf_counter() - started) * 1000
    return result


def candidate_text(core, generation):
    text = core.processor.decode(generation["output_token_ids"], skip_special_tokens=True).strip()
    # One deterministic transport wrapper, no substring search or answer repair.
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[8:-4].strip()
    return text


def smoke(root, out):
    started = time.perf_counter()
    registration = json.loads((root / "registration.json").read_text())
    write_json(out / "attempt-started.json", {
        "registration_sha256": hashlib.sha256((root / "registration.json").read_bytes()).hexdigest(),
        "status": "STARTED", "model_calls": 0,
    })  # Refuse a second attempt, even if the first crashed.
    result = {"status": "NOT_VERIFIED", "verified": None, "stage": "BUNDLE",
              "model_calls": 0, "scientific_success": False,
              "scope": "OPENED_SINGLE_SOURCE_RUNTIME_SMOKE_NOT_FRONTIER_GAP",
              "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
              "paid_budget_krw": 0, "cost_usd": None, "energy_j": None, "flops": None,
              "subscription_investment": None, "peak_process_rss_bytes": None}
    core = None
    startup = None
    try:
        manifest = check_bundle(root)
        result["source_commit"] = manifest["source_commit"]
        result["stage"] = "PREFLIGHT"
        p = preflight()
        write_json(out / "runtime-preflight.json", p)
        if p["status"] != "READY_FOR_ONE_FROZEN_ATTEMPT":
            result["status"] = "BLOCKED_ENVIRONMENT"
            return result
        from neumann1.f0_opened_bridge import verify_original_answer, OriginalVerificationUnavailable
        from neumann1.hybrid_runtime_r0 import digest, source_problem_payload, validate_task
        from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
        source = (root / "original.sl").read_text(encoding="utf-8")
        if hashlib.sha256(source.encode()).hexdigest() != registration["source_sha256"]:
            raise ValueError("ORIGINAL_SOURCE_DRIFT")
        task = {"domain": "sygus.invariant", "source": source}
        result["original_problem_sha256"] = digest(source_problem_payload(task, validate_task(task)))
        result["original_source_sha256"] = registration["source_sha256"]
        messages = [{"role": "user", "content": registration["prompt_prefix"] + source}]
        write_json(out / "input.json", {"task": task, "messages": messages,
                                      "allowed_tools": [], "registration": registration})
        result["stage"] = "FROZEN_CORE_INITIALIZATION"
        write_json(out / "startup-started.json", {"status": "STARTED"})
        startup = time.perf_counter()
        core = FrozenAcceleratorCore()  # UNCHANGED existing loader and identities.
        result["startup_attempt_ms"] = (time.perf_counter() - startup) * 1000
        result["core_startup_ms"] = core.startup_ms
        if core.identity["model_revision"] != MODEL_REVISION:
            raise ValueError("MODEL_IDENTITY_DRIFT")
        if any(x.is_floating_point() and x.dtype != core.torch.bfloat16
               for x in core.model.parameters()):
            raise ValueError("PARAMETER_PRECISION_DRIFT")
        write_json(out / "model-identity.json", core.identity)
        result["startup_peak_allocated_bytes"] = int(core.torch.cuda.max_memory_allocated(core.device))
        result["startup_peak_reserved_bytes"] = int(core.torch.cuda.max_memory_reserved(core.device))
        result["stage"] = "GENERATION"
        write_json(out / "generation-started.json", {"status": "STARTED", "model_calls": 1})
        result["model_calls"] = 1
        stamp = time.perf_counter()
        generation = core.generate(messages, max_tokens=registration["output_tokens"],
                                   thinking=False, deadline_ms=registration["generation_deadline_ms"])
        result["request_ms"] = (time.perf_counter() - stamp) * 1000
        write_json(out / "generation.json", generation)
        result["generation_ms"] = generation["generation_ms"]
        result["generation_deadline_reached"] = generation["deadline_reached"]
        result["peak_accelerator_memory_bytes"] = generation["peak_accelerator_memory_bytes"]
        result["peak_process_rss_bytes"] = generation["peak_process_rss_bytes"]
        result["stage"] = "ORIGINAL_VERIFICATION"
        text = candidate_text(core, generation)
        stamp = time.perf_counter()
        try:
            answer = json.loads(text)
        except json.JSONDecodeError:
            result.update(verified=False, verification_reason="OUTPUT_CONTRACT_REJECTED")
        else:
            write_json(out / "answer.json", answer)
            try:
                result["verified"] = verify_original_answer(task, answer)
                result["verification_reason"] = "EXISTING_ORIGINAL_INIT_INDUCTION_SAFETY_CHECK"
            except OriginalVerificationUnavailable as exc:
                result["verification_unavailable"] = exc.proof
        result["verification_ms"] = (time.perf_counter() - stamp) * 1000
        result["stage"] = "FROZEN_CORE_AUDIT"
        stamp = time.perf_counter()
        audit = core.audit()
        write_json(out / "checkpoint-audit.json", audit)
        result["checkpoint_audit_ms"] = (time.perf_counter() - stamp) * 1000
        if audit["unchanged"] is not True:
            result.update(status="IDENTITY_REJECTED", verified=None)
        else:
            result["status"] = "MODEL_EXECUTED_ORIGINAL_VERIFIED" if result["verified"] is True else (
                "MODEL_EXECUTED_CANDIDATE_REJECTED" if result["verified"] is False else "MODEL_EXECUTED_NOT_VERIFIED")
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        if startup is not None and "startup_attempt_ms" not in result:
            result["startup_attempt_ms"] = (time.perf_counter() - startup) * 1000
        # Preserve exact failure text locally. The public summary is allowlisted.
        write_json(out / "failure.private.json", {"stage": result["stage"], "error_type": type(exc).__name__,
                                                   "detail": str(exc)})
    finally:
        result["complete_attempt_ms"] = (time.perf_counter() - started) * 1000
        t = sys.modules.get("torch")
        try:
            if t is not None and t.cuda.is_available():
                result["observed_peak_allocated_bytes"] = int(t.cuda.max_memory_allocated(0))
                result["observed_peak_reserved_bytes"] = int(t.cuda.max_memory_reserved(0))
        except Exception:
            pass  # A broken CUDA context has no usable memory measurement.
        write_json(out / "result.public.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.preflight_only:
        check_bundle(args.root)
        result = preflight()
        write_json(args.out / "preflight.public.json", result)
    else:
        result = smoke(args.root, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
