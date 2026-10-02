"""Pure contracts for the opened accelerator Architecture Multiplier gate.

No model loading, task execution, fitting, frontier calls, or sealed data access.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from neumann1.general_runtime_v106 import MODEL_ID, MODEL_REVISION

ARMS = ("DIRECT", "TOOL", "NEUMANN")
BASELINE_ARMS = ("DIRECT", "TOOL")
CANDIDATE_ARM = "NEUMANN"
TASK_COUNT = 12

FROZEN_MODEL_ID = MODEL_ID
FROZEN_MODEL_REVISION = MODEL_REVISION
FROZEN_ARTIFACT_SHA256 = "bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66"
FROZEN_TOKENIZER_SHA256 = "8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207"

ACCELERATOR_TYPES = ("cuda", "rocm", "xpu", "npu", "mps")

CAPABILITY_GAIN_TASKS = 2          # >= 2/12 = 16.7 percentage-point gain.
MAX_LATENCY_RATIO_GAIN = 1.25     # Capability path may cost at most +25% wall time.
MAX_LATENCY_RATIO_EFFICIENCY = 0.50  # Equal-or-better capability at >=2x speed.


@dataclass(frozen=True)
class MultiplierBudget:
    context_tokens: int = 4096
    output_tokens: int = 512
    per_call_tokens: int = 256
    model_calls: int = 4
    tool_calls: int = 4
    wall_ms: float = 120000.0
    tool_ms: float = 2000.0

    def __post_init__(self):
        for key in ("context_tokens", "output_tokens", "per_call_tokens", "model_calls", "tool_calls"):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError("positive integer budget required: " + key)
        for key in ("wall_ms", "tool_ms"):
            value = getattr(self, key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError("positive finite time budget required")
        if self.per_call_tokens > self.output_tokens:
            raise ValueError("per-call output exceeds complete output budget")


def validate_environment(receipt):
    """Admit only an actual non-CPU frozen-core accelerator environment."""
    required = {
        "device_type", "device_name", "accelerator_memory_bytes", "precision",
        "model_id", "model_revision", "artifact_sha256", "tokenizer_sha256",
        "deterministic", "do_sample", "framework", "driver",
    }
    if type(receipt) is not dict or set(receipt) != required:
        raise ValueError("complete accelerator receipt required")
    if receipt["device_type"] not in ACCELERATOR_TYPES:
        raise ValueError("accelerator required; CPU is not admissible")
    if type(receipt["device_name"]) is not str or not receipt["device_name"].strip():
        raise ValueError("device identity required")
    if type(receipt["accelerator_memory_bytes"]) is not int or receipt["accelerator_memory_bytes"] <= 0:
        raise ValueError("measured accelerator memory capacity required")
    if receipt["precision"] != "bfloat16":
        raise ValueError("frozen multiplier precision is bfloat16")
    if receipt["model_id"] != FROZEN_MODEL_ID or receipt["model_revision"] != FROZEN_MODEL_REVISION:
        raise ValueError("frozen model identity drift")
    if receipt["artifact_sha256"] != FROZEN_ARTIFACT_SHA256:
        raise ValueError("frozen weight/config artifact drift")
    if receipt["tokenizer_sha256"] != FROZEN_TOKENIZER_SHA256:
        raise ValueError("frozen tokenizer drift")
    if receipt["deterministic"] is not True or receipt["do_sample"] is not False:
        raise ValueError("deterministic greedy execution required")
    for key in ("framework", "driver"):
        if type(receipt[key]) is not str or not receipt[key].strip():
            raise ValueError(key + " receipt required")
    return dict(receipt)


def validate_arm_result(result):
    required = {
        "arm", "core_sha256", "task_sha256", "budget_sha256", "observations",
        "terminal_receipts", "successes", "complete_ms", "model_calls",
        "tool_calls", "input_tokens", "output_tokens", "peak_accelerator_memory_bytes",
        "token_accounting_complete", "resource_accounting_complete",
    }
    if type(result) is not dict or set(result) != required:
        raise ValueError("complete arm result required")
    if result["arm"] not in ARMS:
        raise ValueError("registered arm required")
    for key in ("core_sha256", "task_sha256", "budget_sha256"):
        if type(result[key]) is not str or not result[key]:
            raise ValueError("identity hash required: " + key)
    for key in (
        "observations", "terminal_receipts", "successes", "model_calls",
        "tool_calls", "input_tokens", "output_tokens", "peak_accelerator_memory_bytes",
    ):
        value = result[key]
        if type(value) is not int or value < 0:
            raise ValueError("nonnegative integer result required: " + key)
    if result["observations"] != TASK_COUNT or result["terminal_receipts"] != TASK_COUNT:
        raise ValueError("all opened observations must retain terminal receipts")
    if result["successes"] > TASK_COUNT:
        raise ValueError("success count exceeds task count")
    if type(result["complete_ms"]) not in (int, float) or not math.isfinite(result["complete_ms"]) or result["complete_ms"] <= 0:
        raise ValueError("positive finite complete latency required")
    if result["peak_accelerator_memory_bytes"] <= 0:
        raise ValueError("peak accelerator memory measurement required")
    if result["token_accounting_complete"] is not True:
        raise ValueError("complete token accounting required")
    if result["resource_accounting_complete"] is not True:
        raise ValueError("complete registered resource accounting required")
    return dict(result)


def select_strongest_baseline(results):
    """Highest verified successes; latency breaks exact capability ties."""
    valid = [validate_arm_result(results[arm]) for arm in BASELINE_ARMS]
    valid.sort(key=lambda row: (-row["successes"], row["complete_ms"], row["arm"]))
    return valid[0]


def evaluate_multiplier(results):
    """Return the pre-registered Decision-2 verdict from complete arm receipts."""
    if type(results) is not dict or set(results) != set(ARMS):
        raise ValueError("DIRECT, TOOL and NEUMANN results required")
    rows = {arm: validate_arm_result(results[arm]) for arm in ARMS}

    identity_fields = ("core_sha256", "task_sha256", "budget_sha256")
    for key in identity_fields:
        if len({rows[arm][key] for arm in ARMS}) != 1:
            return {
                "verdict": "NOT_EVALUATED",
                "reason": key + "_MISMATCH",
                "global_questions_closed": [],
            }

    baseline = select_strongest_baseline(rows)
    candidate = rows[CANDIDATE_ARM]

    q_b = baseline["successes"] / TASK_COUNT
    q_n = candidate["successes"] / TASK_COUNT
    latency_ratio = candidate["complete_ms"] / baseline["complete_ms"]

    m_a = None if q_b == 0 else q_n / q_b
    m_e = None
    if q_b > 0 and q_n > 0:
        m_e = (q_n / candidate["complete_ms"]) / (q_b / baseline["complete_ms"])

    capability_path = (
        candidate["successes"] >= baseline["successes"] + CAPABILITY_GAIN_TASKS
        and latency_ratio <= MAX_LATENCY_RATIO_GAIN
    )
    efficiency_path = (
        candidate["successes"] >= baseline["successes"]
        and latency_ratio <= MAX_LATENCY_RATIO_EFFICIENCY
    )
    passed = capability_path or efficiency_path

    return {
        "verdict": "PASS" if passed else "FAIL",
        "strongest_baseline": baseline["arm"],
        "baseline_successes": baseline["successes"],
        "neumann_successes": candidate["successes"],
        "task_count": TASK_COUNT,
        "capability_absolute_gain": q_n - q_b,
        "architecture_multiplier": m_a,
        "latency_ratio": latency_ratio,
        "capability_per_latency_multiplier": m_e,
        "capability_path": capability_path,
        "efficiency_path": efficiency_path,
        "sealed_general_evaluation_admitted": passed,
        "architecture_pivot_required": not passed,
        "general_capability_gate": "OPENED_ARCHITECTURE_MULTIPLIER_PASS" if passed else "OPENED_ARCHITECTURE_MULTIPLIER_FAIL",
        "global_questions_closed": [],
    }


def contract_manifest(task_sha256, budget_sha256):
    return {
        "schema": "neumann.architecture-multiplier-contract.v1",
        "model_id": FROZEN_MODEL_ID,
        "model_revision": FROZEN_MODEL_REVISION,
        "artifact_sha256": FROZEN_ARTIFACT_SHA256,
        "tokenizer_sha256": FROZEN_TOKENIZER_SHA256,
        "precision": "bfloat16",
        "arms": list(ARMS),
        "strongest_baseline_pool": list(BASELINE_ARMS),
        "candidate_arm": CANDIDATE_ARM,
        "task_count": TASK_COUNT,
        "task_sha256": task_sha256,
        "budget": asdict(MultiplierBudget()),
        "budget_sha256": budget_sha256,
        "capability_gain_tasks": CAPABILITY_GAIN_TASKS,
        "max_latency_ratio_gain": MAX_LATENCY_RATIO_GAIN,
        "max_latency_ratio_efficiency": MAX_LATENCY_RATIO_EFFICIENCY,
        "sealed": False,
        "training_allowed": False,
        "frontier_calls": 0,
        "edge_claim_allowed": False,
    }
