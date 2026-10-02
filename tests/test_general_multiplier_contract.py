"""Pure Architecture Multiplier contracts. No model weights or inference."""
from dataclasses import asdict

import pytest

from experiments.general_multiplier_tasks import TASK_SHA256, MODEL_VIEW_SHA256, manifest, model_view, multiplier_tasks
from neumann1.general_multiplier_contract import (
    FROZEN_ARTIFACT_SHA256,
    FROZEN_MODEL_ID,
    FROZEN_MODEL_REVISION,
    FROZEN_TOKENIZER_SHA256,
    MultiplierBudget,
    evaluate_multiplier,
    select_strongest_baseline,
    validate_environment,
)
from neumann1.general_runtime_v106 import sha


def environment(device_type="cuda"):
    return {
        "device_type": device_type,
        "device_name": "fixture accelerator",
        "accelerator_memory_bytes": 24 * 1024**3,
        "precision": "bfloat16",
        "model_id": FROZEN_MODEL_ID,
        "model_revision": FROZEN_MODEL_REVISION,
        "artifact_sha256": FROZEN_ARTIFACT_SHA256,
        "tokenizer_sha256": FROZEN_TOKENIZER_SHA256,
        "deterministic": True,
        "do_sample": False,
        "framework": "torch-fixture",
        "driver": "driver-fixture",
    }


def result(arm, successes, complete_ms, *, core="core", tasks=TASK_SHA256, budget=None):
    if budget is None:
        budget = sha(asdict(MultiplierBudget()))
    return {
        "arm": arm,
        "core_sha256": core,
        "task_sha256": tasks,
        "budget_sha256": budget,
        "observations": 12,
        "terminal_receipts": 12,
        "successes": successes,
        "complete_ms": complete_ms,
        "model_calls": 12,
        "tool_calls": 0 if arm == "DIRECT" else 12,
        "input_tokens": 1200,
        "output_tokens": 600,
        "peak_accelerator_memory_bytes": 12 * 1024**3,
        "token_accounting_complete": True,
        "resource_accounting_complete": True,
    }


def test_cpu_is_not_an_admissible_capability_environment():
    with pytest.raises(ValueError):
        validate_environment(environment("cpu"))
    assert validate_environment(environment("cuda"))["device_type"] == "cuda"


def test_opened_task_set_is_small_balanced_and_hides_runtime_family_labels():
    m = manifest()
    assert m["count"] == 12
    assert m["families"] == {"math_logic": 4, "coding": 4, "constraint_planning": 4}
    assert m["sealed"] is False and m["training_allowed"] is False
    assert len(TASK_SHA256) == 64 and len(MODEL_VIEW_SHA256) == 64
    for task, _private in multiplier_tasks():
        view = model_view(task)
        assert "id" not in view and "family" not in view
        assert set(view) == {"instruction", "public"}


def test_strongest_baseline_is_capability_first_then_latency():
    rows = {
        "DIRECT": result("DIRECT", 7, 700.0),
        "TOOL": result("TOOL", 8, 1200.0),
        "NEUMANN": result("NEUMANN", 9, 1100.0),
    }
    assert select_strongest_baseline(rows)["arm"] == "TOOL"
    rows["DIRECT"] = result("DIRECT", 8, 900.0)
    assert select_strongest_baseline(rows)["arm"] == "DIRECT"


def test_capability_path_passes_only_with_two_task_gain_and_bounded_latency():
    rows = {
        "DIRECT": result("DIRECT", 6, 900.0),
        "TOOL": result("TOOL", 7, 1000.0),
        "NEUMANN": result("NEUMANN", 9, 1200.0),
    }
    verdict = evaluate_multiplier(rows)
    assert verdict["verdict"] == "PASS"
    assert verdict["strongest_baseline"] == "TOOL"
    assert verdict["capability_path"] is True
    assert verdict["sealed_general_evaluation_admitted"] is True


def test_efficiency_path_requires_no_capability_loss_and_two_x_speed():
    rows = {
        "DIRECT": result("DIRECT", 7, 800.0),
        "TOOL": result("TOOL", 8, 1000.0),
        "NEUMANN": result("NEUMANN", 8, 500.0),
    }
    verdict = evaluate_multiplier(rows)
    assert verdict["verdict"] == "PASS"
    assert verdict["efficiency_path"] is True


def test_small_one_task_gain_does_not_create_a_positive_signal():
    rows = {
        "DIRECT": result("DIRECT", 7, 900.0),
        "TOOL": result("TOOL", 8, 1000.0),
        "NEUMANN": result("NEUMANN", 9, 1000.0),
    }
    verdict = evaluate_multiplier(rows)
    assert verdict["verdict"] == "FAIL"
    assert verdict["architecture_pivot_required"] is True
    assert verdict["sealed_general_evaluation_admitted"] is False


def test_core_task_or_budget_mismatch_is_not_evidence():
    rows = {
        "DIRECT": result("DIRECT", 7, 900.0),
        "TOOL": result("TOOL", 8, 1000.0),
        "NEUMANN": result("NEUMANN", 10, 1000.0, core="different"),
    }
    verdict = evaluate_multiplier(rows)
    assert verdict == {
        "verdict": "NOT_EVALUATED",
        "reason": "core_sha256_MISMATCH",
        "global_questions_closed": [],
    }


def test_incomplete_receipts_or_accounting_cannot_enter_gate():
    bad = result("DIRECT", 7, 900.0)
    bad["terminal_receipts"] = 11
    with pytest.raises(ValueError):
        evaluate_multiplier({
            "DIRECT": bad,
            "TOOL": result("TOOL", 8, 1000.0),
            "NEUMANN": result("NEUMANN", 10, 1000.0),
        })

    bad = result("NEUMANN", 10, 1000.0)
    bad["resource_accounting_complete"] = False
    with pytest.raises(ValueError):
        evaluate_multiplier({
            "DIRECT": result("DIRECT", 7, 900.0),
            "TOOL": result("TOOL", 8, 1000.0),
            "NEUMANN": bad,
        })
