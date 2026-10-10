"""Model-free BF16 admission and inference-HOLD tests, not F0 outcomes."""
import hashlib
import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from experiments.f0_kaggle_frozen_smoke import (
    MIN_VRAM, candidate_text, check_bundle, preflight, smoke, write_json,
)


def fake_torch(vram=MIN_VRAM, *, cuda=True, native=False, matmul_error=False):
    tensor = MagicMock()
    tensor.dtype = "bfloat16"
    tensor.__matmul__.return_value = tensor
    if matmul_error:
        tensor.__matmul__.side_effect = RuntimeError("unsupported kernel")
    module = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: cuda, device_count=lambda: 2,
             get_device_properties=lambda _: SimpleNamespace(total_memory=vram),
             get_device_name=lambda _: "synthetic test GPU",
             get_device_capability=lambda _: (8, 0) if native else (7, 5),
             is_bf16_supported=MagicMock(side_effect=lambda **kw:
                 True if kw["including_emulation"] else native),
             set_device=MagicMock(), synchronize=lambda _: None,
             empty_cache=lambda: None),
        version=SimpleNamespace(cuda="synthetic"), bfloat16="bfloat16",
        inference_mode=nullcontext, ones=lambda *a, **k: tensor,
        isfinite=lambda _: SimpleNamespace(all=lambda: True),
        nn=SimpleNamespace(functional=SimpleNamespace(
            scaled_dot_product_attention=lambda *a: tensor)),
    )
    return module


def test_cuda_absence_stops_before_weights():
    r = preflight(fake_torch(cuda=False))
    assert r["status"] == "BLOCKED_ENVIRONMENT"
    assert r["reason"] == "CUDA_UNAVAILABLE"
    assert r["checkpoint_download_attempted"] is False and r["model_calls"] == 0


@pytest.mark.parametrize("vram", [4*1024**3, 8*1024**3, MIN_VRAM-1])
def test_two_gpu_aggregate_is_not_single_device_capacity(vram):
    r = preflight(fake_torch(vram))
    assert r["device_count"] == 2
    assert r["status"] == "BLOCKED_ENVIRONMENT"
    assert r["reason"] == "SINGLE_GPU_BELOW_14_GIB"
    assert r["bf16_operations"] is None


def test_native_bf16_absence_is_distinct_from_operation_failure():
    t = fake_torch(native=False)
    r = preflight(t)
    assert r["status"] == "BLOCKED_BF16_CONTRACT"
    assert r["bf16_native"] is False and r["bf16_operations"] is True
    assert r["bf16_with_emulation"] is True
    assert r["reason"] == "NATIVE_BF16_UNAVAILABLE_EMULATION_NOT_AUTHORIZED"
    assert r["model_calls"] == 0 and r["inference_authorized"] is False
    t.cuda.is_bf16_supported.assert_any_call(including_emulation=False)
    t.cuda.is_bf16_supported.assert_any_call(including_emulation=True)
    t.cuda.set_device.assert_called_once_with(0)


def test_native_supported_gpu_still_holds_inference():
    r = preflight(fake_torch(native=True))
    assert r["status"] == "ENVIRONMENT_CHECK_PASS_INFERENCE_HOLD"
    assert r["bf16_native"] is True and r["bf16_operations"] is True
    assert r["inference_authorized"] is False and r["model_calls"] == 0


def test_old_bf16_api_does_not_supply_native_evidence():
    t = fake_torch(native=True)
    t.cuda.is_bf16_supported = MagicMock(side_effect=TypeError("old API"))
    r = preflight(t)
    assert r["status"] == "NOT_VERIFIED_NATIVE_BF16"
    assert r["bf16_native"] is None and r["bf16_operations"] is True
    assert r["bf16_with_emulation"] is None and r["model_calls"] == 0


def test_unsupported_bf16_kernel_stops_before_download():
    r = preflight(fake_torch(matmul_error=True))
    assert r["status"] == "BLOCKED_ENVIRONMENT" and r["stage"] == "BF16_OPERATIONS"
    assert r["bf16_operations"] is False
    assert r["checkpoint_download_attempted"] is False
    assert "unsupported kernel" not in str(r)


def test_bad_operation_dtype_fails_closed():
    t = fake_torch()
    t.ones = lambda *a, **k: SimpleNamespace(dtype="float16")
    r = preflight(t)
    assert r["status"] == "BLOCKED_ENVIRONMENT"


def bundle(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "adapter.py").write_bytes(b"original core bytes")
    (root / "registration.json").write_text('{}')
    (root / "bundle-manifest.json").write_text(json.dumps({
        "source_commit": "synthetic-test-only",
        "files": {"adapter.py": hashlib.sha256(b"original core bytes").hexdigest()}}))
    return root


def test_bundle_bytes_are_checked_before_any_runtime(tmp_path):
    root = bundle(tmp_path)
    assert check_bundle(root)["source_commit"] == "synthetic-test-only"
    (root / "adapter.py").write_bytes(b"mutated core bytes")
    with pytest.raises(ValueError, match="BUNDLE_IDENTITY_MISMATCH"):
        check_bundle(root)


def test_environment_failure_preserves_first_attempt_and_forbids_retry(tmp_path, monkeypatch):
    root = bundle(tmp_path)
    out = tmp_path / "result"
    out.mkdir()
    monkeypatch.setattr("experiments.f0_kaggle_frozen_smoke.preflight", lambda: {
        "status": "BLOCKED_ENVIRONMENT", "model_calls": 0})
    r = smoke(root, out)
    assert r["status"] == "BLOCKED_ENVIRONMENT" and r["verified"] is None
    assert r["model_calls"] == 0 and r["scientific_success"] is False
    assert (out / "attempt-started.json").is_file()
    assert json.loads((out / "result.public.json").read_text())["verified"] is None
    with pytest.raises(FileExistsError):
        smoke(root, out)


def test_mutated_bundle_never_enters_preflight(tmp_path, monkeypatch):
    root = bundle(tmp_path)
    (root / "adapter.py").write_bytes(b"bad")
    out = tmp_path / "out"
    out.mkdir()
    called = []
    monkeypatch.setattr("experiments.f0_kaggle_frozen_smoke.preflight", lambda: called.append(True))
    r = smoke(root, out)
    assert r["verified"] is None and r["model_calls"] == 0
    assert called == []
    assert r["error_type"] == "ValueError"


def test_native_pass_never_constructs_core_or_downloads_weights(tmp_path, monkeypatch):
    root = bundle(tmp_path)
    out = tmp_path / "held"
    out.mkdir()
    monkeypatch.setattr("experiments.f0_kaggle_frozen_smoke.preflight", lambda: {
        "status": "ENVIRONMENT_CHECK_PASS_INFERENCE_HOLD", "model_calls": 0})
    # Guarded code returns before importing or initializing the frozen loader.
    import experiments.general_multiplier_accelerator_core as core
    constructor = MagicMock(side_effect=AssertionError("NO MODEL AUTHORITY"))
    monkeypatch.setattr(core, "FrozenAcceleratorCore", constructor)
    r = smoke(root, out)
    assert r["status"] == "INFERENCE_HELD_BY_CURRENT_DIRECTIVE"
    assert r["verified"] is None and r["model_calls"] == 0
    constructor.assert_not_called()
    assert not (out / "startup-started.json").exists()
    assert not (out / "input.json").exists()


def test_receipts_are_exclusive(tmp_path):
    p = tmp_path / "receipt.json"
    write_json(p, {"first": True})
    with pytest.raises(FileExistsError):
        write_json(p, {"first": False})
    assert json.loads(p.read_text()) == {"first": True}


def test_output_transport_does_not_search_for_embedded_answer():
    core = SimpleNamespace(processor=SimpleNamespace(decode=lambda *a, **k: 'text {"invariant":"x"}'))
    assert candidate_text(core, {"output_token_ids": []}).startswith("text ")


def test_only_explicit_json_fence_is_removed():
    core = SimpleNamespace(processor=SimpleNamespace(decode=lambda *a, **k: '```json\n{"invariant":"x"}\n```'))
    assert json.loads(candidate_text(core, {"output_token_ids": []})) == {"invariant": "x"}
