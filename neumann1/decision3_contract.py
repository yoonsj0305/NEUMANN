"""Decision-3 sealed evaluation contract.

Pure evaluator only: no model calls, no dataset access, no provider calls.
Decision 3 is allowed to run only after a valid Decision-2 PASS and a frozen
task-agnostic interface that can accept at least one genuinely new family
without adding answer-capable privileges after seeing sealed data.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math

ARMS = ("BASELINE", "NEUMANN", "FRONTIER")
RESOURCE_AXES = (
    "complete_latency_ms",
    "monetary_cost_usd",
    "energy_j",
    "compute_units",
)

SCHEMA = "neumann.decision3-contract.v1"


@dataclass(frozen=True)
class Decision3Policy:
    min_tasks: int = 18
    min_families: int = 3
    min_new_families: int = 1
    capability_gain_tasks: int = 2
    capability_path_max_wall_ratio: float = 1.25
    efficiency_path_max_wall_ratio: float = 0.50
    min_frontier_gap_tasks: int = 6
    min_frontier_gap_families: int = 3
    min_gap_recovery_fraction: float = 0.50
    max_resource_regression_ratio: float = 1.25
    required_resource_improvement_ratio: float = 0.50


def policy_manifest(policy=Decision3Policy()):
    return {"schema": SCHEMA, "policy": asdict(policy)}


def _validate_rows(rows):
    if type(rows) is not list or not rows:
        raise ValueError("sealed task receipts required")
    ids = set()
    for row in rows:
        if type(row) is not dict:
            raise ValueError("receipt row object required")
        task_id = row.get("task_id")
        family = row.get("family")
        if type(task_id) is not str or not task_id:
            raise ValueError("stable task id required")
        if task_id in ids:
            raise ValueError("duplicate task id")
        ids.add(task_id)
        if type(family) is not str or not family:
            raise ValueError("family required")
        roles = row.get("roles")
        if type(roles) is not dict or set(roles) != set(ARMS):
            raise ValueError("exact BASELINE/NEUMANN/FRONTIER coverage required")
        for arm in ARMS:
            rec = roles[arm]
            if type(rec) is not dict:
                raise ValueError("role receipt required")
            if type(rec.get("verified_success")) is not bool:
                raise ValueError("independent verified_success boolean required")
            if type(rec.get("complete_ms")) not in (int, float) or rec["complete_ms"] <= 0:
                raise ValueError("positive complete wall receipt required")
            resources = rec.get("resources")
            if type(resources) is not dict:
                raise ValueError("resource receipt map required")
            for axis in RESOURCE_AXES:
                item = resources.get(axis)
                if type(item) is not dict:
                    raise ValueError("explicit resource item required for every axis")
                if item.get("status") not in ("measured", "estimated", "unavailable"):
                    raise ValueError("resource status required")
                if item["status"] == "measured":
                    if type(item.get("value")) not in (int, float) or item["value"] < 0:
                        raise ValueError("measured resource value required")
                    if type(item.get("unit")) is not str or not item["unit"]:
                        raise ValueError("resource unit required")
                elif item.get("value") is not None:
                    raise ValueError("non-measured resource must not masquerade as a value")


def _sealed_multiplier(rows, policy):
    b_success = sum(row["roles"]["BASELINE"]["verified_success"] for row in rows)
    n_success = sum(row["roles"]["NEUMANN"]["verified_success"] for row in rows)
    b_wall = sum(float(row["roles"]["BASELINE"]["complete_ms"]) for row in rows)
    n_wall = sum(float(row["roles"]["NEUMANN"]["complete_ms"]) for row in rows)
    wall_ratio = n_wall / b_wall
    capability_path = (
        n_success >= b_success + policy.capability_gain_tasks
        and wall_ratio <= policy.capability_path_max_wall_ratio
    )
    efficiency_path = (
        n_success >= b_success
        and wall_ratio <= policy.efficiency_path_max_wall_ratio
    )
    return {
        "baseline_successes": b_success,
        "neumann_successes": n_success,
        "baseline_complete_ms": b_wall,
        "neumann_complete_ms": n_wall,
        "wall_ratio_N_over_B": wall_ratio,
        "capability_path": capability_path,
        "efficiency_path": efficiency_path,
        "persists": capability_path or efficiency_path,
    }


def _frontier_gap(rows, policy):
    gap = [
        row for row in rows
        if not row["roles"]["BASELINE"]["verified_success"]
        and row["roles"]["FRONTIER"]["verified_success"]
    ]
    families = sorted({row["family"] for row in gap})
    recovered = [row for row in gap if row["roles"]["NEUMANN"]["verified_success"]]
    required_recovered = math.ceil(policy.min_gap_recovery_fraction * len(gap))
    family_counts = {}
    family_recovered = {}
    for family in families:
        family_counts[family] = sum(row["family"] == family for row in gap)
        family_recovered[family] = sum(
            row["family"] == family and row["roles"]["NEUMANN"]["verified_success"]
            for row in gap
        )
    no_family_zero = all(
        family_counts[family] < 2 or family_recovered[family] >= 1
        for family in families
    )
    return {
        "task_count": len(gap),
        "families": families,
        "family_count": len(families),
        "recovered_count": len(recovered),
        "required_recovered_count": required_recovered,
        "recovery_fraction": (len(recovered) / len(gap)) if gap else None,
        "family_counts": family_counts,
        "family_recovered": family_recovered,
        "no_represented_family_with_2plus_gap_tasks_has_zero_recovery": no_family_zero,
        "sufficient_gap": (
            len(gap) >= policy.min_frontier_gap_tasks
            and len(families) >= policy.min_frontier_gap_families
        ),
        "recovery_pass": (
            len(gap) >= policy.min_frontier_gap_tasks
            and len(families) >= policy.min_frontier_gap_families
            and len(recovered) >= required_recovered
            and no_family_zero
        ),
    }


def _frontier_resource_signal(rows, policy):
    """Compare N and frontier on tasks both independently verify as successful."""
    paired = [
        row for row in rows
        if row["roles"]["NEUMANN"]["verified_success"]
        and row["roles"]["FRONTIER"]["verified_success"]
    ]
    ratios = {}
    compatible = []
    for axis in RESOURCE_AXES:
        n_values = []
        f_values = []
        units = set()
        for row in paired:
            n = row["roles"]["NEUMANN"]["resources"][axis]
            f = row["roles"]["FRONTIER"]["resources"][axis]
            if n["status"] != "measured" or f["status"] != "measured":
                continue
            units.update((n["unit"], f["unit"]))
            if n["unit"] != f["unit"]:
                continue
            n_values.append(float(n["value"]))
            f_values.append(float(f["value"]))
        if n_values and sum(f_values) > 0:
            ratio = sum(n_values) / sum(f_values)
            ratios[axis] = ratio
            compatible.append(axis)

    improvement_axes = [
        axis for axis, ratio in ratios.items()
        if ratio <= policy.required_resource_improvement_ratio
    ]
    regression_axes = [
        axis for axis, ratio in ratios.items()
        if ratio > policy.max_resource_regression_ratio
    ]
    return {
        "paired_success_tasks": len(paired),
        "compatible_measured_axes": compatible,
        "ratios_N_over_frontier": ratios,
        "improvement_axes_2x_or_better": improvement_axes,
        "regression_axes_over_1_25x": regression_axes,
        "pass": bool(improvement_axes) and not regression_axes,
    }


def evaluate_decision3(
    rows,
    *,
    decision2_valid_pass,
    architecture_frozen,
    task_agnostic_interface,
    baseline_arm_frozen,
    source_registry_frozen,
    sealed_before_admission,
    policy=Decision3Policy(),
):
    """Return a decision-changing verdict without opening or executing anything."""
    if decision2_valid_pass is not True:
        return {"verdict": "BLOCKED_DECISION2_NOT_PASS", "global_questions_closed": []}
    if architecture_frozen is not True or baseline_arm_frozen not in ("DIRECT", "TOOL"):
        return {"verdict": "BLOCKED_ARCHITECTURE_NOT_FROZEN", "global_questions_closed": []}
    if source_registry_frozen is not True or sealed_before_admission is not True:
        return {"verdict": "BLOCKED_SEALING_OR_SOURCE_PROVENANCE", "global_questions_closed": []}
    if task_agnostic_interface is not True:
        return {
            "verdict": "BLOCKED_TASK_SPECIFIC_INTERFACE",
            "reason": "new-family sealed evaluation would require a post-D2 architecture change",
            "global_questions_closed": [],
        }

    try:
        _validate_rows(rows)
    except Exception as exc:
        return {
            "verdict": "NOT_EVALUATED_INCOMPLETE_RECEIPTS",
            "reason": type(exc).__name__ + ": " + str(exc),
            "global_questions_closed": [],
        }

    families = sorted({row["family"] for row in rows})
    new_families = sorted({row["family"] for row in rows if row.get("new_family") is True})
    if (
        len(rows) < policy.min_tasks
        or len(families) < policy.min_families
        or len(new_families) < policy.min_new_families
    ):
        return {
            "verdict": "NOT_EVALUATED_INSUFFICIENT_SEALED_COVERAGE",
            "task_count": len(rows),
            "families": families,
            "new_families": new_families,
            "global_questions_closed": [],
        }

    multiplier = _sealed_multiplier(rows, policy)
    gap = _frontier_gap(rows, policy)
    resource = _frontier_resource_signal(rows, policy)

    if not multiplier["persists"]:
        verdict = "FAIL_SEALED_MULTIPLIER_DID_NOT_PERSIST"
    elif not gap["sufficient_gap"]:
        verdict = "NOT_EVALUATED_NO_SUFFICIENT_VERIFIED_FRONTIER_GAP"
    elif not gap["recovery_pass"]:
        verdict = "FAIL_FRONTIER_GAP_RECOVERY"
    elif not resource["pass"]:
        verdict = "NOT_EVALUATED_FRONTIER_RESOURCE_SIGNAL"
    else:
        verdict = "PASS_ADMIT_EDGE_CLOUD_ENGINEERING"

    return {
        "verdict": verdict,
        "task_count": len(rows),
        "families": families,
        "new_families": new_families,
        "baseline_arm_frozen": baseline_arm_frozen,
        "sealed_multiplier": multiplier,
        "frontier_gap": gap,
        "frontier_resource_signal": resource,
        "global_questions_closed": [],
        "scope_note": (
            "A PASS is an admission signal for Edge/Cloud engineering at this sealed "
            "scope; it does not globally close Q1-Q7."
        ),
    }
