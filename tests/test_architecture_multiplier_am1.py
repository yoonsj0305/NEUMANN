"""AM1 contract tests. No model weights, network, or accelerator inference."""
from experiments.architecture_multiplier_am1 import (
    TASK_COUNT,
    opened_tasks,
    summarize,
)


FAMILIES = ("math_logic", "coding", "constraint_planning")
ARMS = ("B0", "B1", "B2", "B3", "N")


def fake_record(arm, family, accepted, complete_ms, model_tokens, peak=1000, error=None):
    input_tokens = model_tokens - 10
    return {
        "arm": arm,
        "family": family,
        "accepted": accepted,
        "error": error,
        "complete_ms": float(complete_ms),
        "input_tokens": input_tokens,
        "output_tokens": 10,
        "model_calls": 1,
        "tool_calls": 1 if arm in ("B2", "B3", "N") else 0,
        "token_accounting_complete": True,
        "events": [
            {
                "kind": "model_result",
                "receipt": {
                    "generation_ms": float(complete_ms) * 0.8,
                    "gpu_peak_allocated_bytes": peak,
                },
                "ms": float(complete_ms) * 0.8,
            },
            {"kind": "tool_result", "ms": float(complete_ms) * 0.1},
        ],
    }


def build_records(counts, ms_by_arm=None, tokens_by_arm=None, peak_by_arm=None):
    ms_by_arm = ms_by_arm or {}
    tokens_by_arm = tokens_by_arm or {}
    peak_by_arm = peak_by_arm or {}
    records = []
    tasks = opened_tasks()
    remaining = {arm: counts[arm] for arm in ARMS}
    for task, _ in tasks:
        family = task["family"]
        for arm in ARMS:
            accepted = remaining[arm] > 0
            if accepted:
                remaining[arm] -= 1
            records.append(
                fake_record(
                    arm,
                    family,
                    accepted,
                    ms_by_arm.get(arm, 60),
                    tokens_by_arm.get(arm, 100),
                    peak_by_arm.get(arm, 1000),
                )
            )
    return records


def test_opened_task_contract_is_small_balanced_and_unique():
    tasks = opened_tasks()
    assert len(tasks) == TASK_COUNT == 12
    assert len({task["id"] for task, _ in tasks}) == 12
    assert {task["family"] for task, _ in tasks} == set(FAMILIES)
    assert {
        family: sum(task["family"] == family for task, _ in tasks)
        for family in FAMILIES
    } == {family: 4 for family in FAMILIES}


def test_positive_multiplier_passes_only_with_capability_and_efficiency():
    # Accepted tasks are consumed in task order. This gives B3 3/2/2 by family
    # and N 4/4/2, so N is not worse anywhere and better in two families.
    records = build_records(
        {"B0": 4, "B1": 6, "B2": 5, "B3": 7, "N": 10},
        ms_by_arm={"B0":70, "B1":65, "B2":64, "B3":60, "N":50},
        tokens_by_arm={"B0":110, "B1":108, "B2":105, "B3":100, "N":95},
        peak_by_arm={"B3":1000, "N":1040},
    )
    result = summarize(records)
    assert result["strongest_matched_baseline"] == "B3"
    assert result["architecture_multiplier"]["absolute_verified_task_gain"] == 3
    assert result["pass_conditions"]["neumann_at_least_8_of_12"]
    assert result["pass_conditions"]["absolute_gain_at_least_2"]
    assert result["pass_conditions"]["latency_capability_efficiency_at_least_1_05"]
    assert result["pass_conditions"]["peak_gpu_memory_ratio_at_most_1_10"]
    assert result["decision_2"] == "PASS_ADMIT_ONE_SEALED_GENERAL_EVALUATION"


def test_capability_gain_without_efficiency_fails_to_pivot():
    records = build_records(
        {"B0":4, "B1":6, "B2":5, "B3":7, "N":10},
        ms_by_arm={"B3":50, "N":120},
        peak_by_arm={"B3":1000, "N":1000},
    )
    result = summarize(records)
    assert result["architecture_multiplier"]["absolute_verified_task_gain"] == 3
    assert not result["pass_conditions"]["latency_capability_efficiency_at_least_1_05"]
    assert result["decision_2"] == "FAIL_ARCHITECTURE_PIVOT"


def test_same_capability_never_passes_architecture_multiplier():
    records = build_records(
        {"B0":4, "B1":6, "B2":5, "B3":8, "N":8},
        ms_by_arm={"B3":80, "N":20},
        peak_by_arm={"B3":1000, "N":900},
    )
    result = summarize(records)
    assert result["strongest_matched_baseline"] == "B3"
    assert result["architecture_multiplier"]["absolute_verified_task_gain"] == 0
    assert not result["pass_conditions"]["absolute_gain_at_least_2"]
    assert result["decision_2"] == "FAIL_ARCHITECTURE_PIVOT"


def test_infrastructure_error_forces_not_evaluated():
    records = build_records(
        {"B0":4, "B1":6, "B2":5, "B3":7, "N":10},
        ms_by_arm={"B3":60, "N":50},
        peak_by_arm={"B3":1000, "N":1000},
    )
    # A CUDA failure is infrastructure, not negative capability evidence.
    records[-1]["error"] = "RuntimeError: CUDA out of memory"
    result = summarize(records)
    assert not result["pass_conditions"]["infrastructure_valid"]
    assert result["decision_2"] == "NOT_EVALUATED_INFRASTRUCTURE"


def test_strongest_baseline_selection_is_predeclared_not_named():
    records = build_records(
        {"B0":4, "B1":8, "B2":6, "B3":7, "N":10},
        ms_by_arm={"B1":70, "B3":40, "N":40},
        tokens_by_arm={"B1":90, "B3":70, "N":80},
        peak_by_arm={"B1":1000, "N":1000},
    )
    result = summarize(records)
    assert result["strongest_matched_baseline"] == "B1"
