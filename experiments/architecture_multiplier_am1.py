"""Opened Architecture Multiplier AM1 contracts.

This is the first Decision-2 capability experiment after Runtime-0.2 ended the
single-thread CPU harness. It reuses the frozen General Runtime-0 strategy
contract on an accelerator-class device. No fitting, frontier calls, or sealed
holdout access occur here.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
import json
import math
from pathlib import Path
import random
import resource
import traceback
from time import perf_counter_ns

from neumann1.general_runtime_v106 import (
    ARMS, Limits, MODEL_ID, MODEL_REVISION, canonical, milliseconds, run, sha,
)

SCHEMA = "neumann.architecture-multiplier.am1.v1"
TASK_COUNT = 12
PASS_MIN_NEUMANN = 8
PASS_MIN_ABSOLUTE_GAIN = 2
PASS_MIN_LATENCY_EFFICIENCY = 1.05
PASS_MAX_PEAK_MEMORY_RATIO = 1.10


def opened_tasks():
    """Small preregistered development set. These are OPENED, never a holdout."""
    return [
        (
            {
                "id": "am1_math_01",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(p*q-r)/(s+t)",
                    "bindings": {"p":29,"q":11,"r":7,"s":3,"t":9,"unused":123},
                    "background": "The receipt is printed on green paper.",
                },
            },
            {"exact": "26"},
        ),
        (
            {
                "id": "am1_math_02",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "a*b+c/d",
                    "bindings": {"a":17,"b":6,"c":9,"d":3,"noise":44},
                    "background": "A blue triangle is painted on the box.",
                },
            },
            {"exact": "105"},
        ),
        (
            {
                "id": "am1_math_03",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(x-y)*(u+v)/w",
                    "bindings": {"x":23,"y":5,"u":7,"v":2,"w":6,"irrelevant":-8},
                    "background": "The laboratory clock is five minutes fast.",
                },
            },
            {"exact": "27"},
        ),
        (
            {
                "id": "am1_math_04",
                "family": "math_logic",
                "instruction": "Return the exact rational value.",
                "public": {
                    "expression": "(m*n+p)/(q-r)",
                    "bindings": {"m":8,"n":11,"p":2,"q":9,"r":4,"spare":999},
                    "background": "The envelope weighs twelve grams.",
                },
            },
            {"exact": "18"},
        ),
        (
            {
                "id": "am1_code_01",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the number of distinct negative integers in items, a list of integers.",
                    "background": "The caller likes music.",
                },
            },
            {"tests":[
                {"input":[],"output":0},
                {"input":[-2,-2,0,3,-5],"output":2},
                {"input":[0,1,3],"output":0},
                {"input":[-1,-3,-1,-7],"output":3},
            ]},
        ),
        (
            {
                "id": "am1_code_02",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the sum of the distinct even integers in items.",
                    "background": "The input list is stored in a yellow folder.",
                },
            },
            {"tests":[
                {"input":[],"output":0},
                {"input":[2,2,4,5,-2],"output":4},
                {"input":[1,3,5],"output":0},
                {"input":[-4,-4,0,6,6],"output":2},
            ]},
        ),
        (
            {
                "id": "am1_code_03",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return 0 for an empty list; otherwise return how many elements equal the minimum value.",
                    "background": "The caller may print the answer later.",
                },
            },
            {"tests":[
                {"input":[],"output":0},
                {"input":[3,1,1,2],"output":2},
                {"input":[-2,0,-2,-2],"output":3},
                {"input":[7],"output":1},
            ]},
        ),
        (
            {
                "id": "am1_code_04",
                "family": "coding",
                "instruction": "Return Python source defining solve(items).",
                "public": {
                    "requirement": "Return the sum of the squares of the distinct positive integers in items.",
                    "background": "Whitespace in the returned source is not important.",
                },
            },
            {"tests":[
                {"input":[],"output":0},
                {"input":[1,2,2,-3],"output":5},
                {"input":[3,3,4,0],"output":25},
                {"input":[-1,-2],"output":0},
            ]},
        ),
        (
            {
                "id": "am1_plan_01",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {k:[0,1,2,3] for k in "ABCD"},
                    "constraints": [["lt","A","B"],["lt","B","C"],["eq","C","D"]],
                    "background": "A train has six carriages.",
                },
            },
            {},
        ),
        (
            {
                "id": "am1_plan_02",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {k:[0,1,2,3] for k in "ABC"},
                    "constraints": [["lt","A","B"],["lt","A","C"],["ne","B","C"]],
                    "background": "The map uses a serif font.",
                },
            },
            {},
        ),
        (
            {
                "id": "am1_plan_03",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {k:[0,1,2,3,4] for k in "WXYZ"},
                    "constraints": [["lt","W","X"],["le","X","Y"],["lt","Y","Z"],["ne","W","Z"]],
                    "background": "The schedule was drafted on Tuesday.",
                },
            },
            {},
        ),
        (
            {
                "id": "am1_plan_04",
                "family": "constraint_planning",
                "instruction": "Return a complete assignment meeting every original constraint.",
                "public": {
                    "domains": {k:[0,1,2,3,4] for k in "PQRS"},
                    "constraints": [["eq","P","Q"],["lt","Q","R"],["ne","R","S"],["le","S",3]],
                    "background": "The room number is not part of the problem.",
                },
            },
            {},
        ),
    ]


def _tool_ms(record):
    return sum(
        float(event.get("ms", 0.0))
        for event in record.get("events", [])
        if event.get("kind") == "tool_result"
    )


def _generation_ms(record):
    total = 0.0
    for event in record.get("events", []):
        if event.get("kind") == "model_result":
            receipt = event.get("receipt")
            if type(receipt) is dict:
                total += float(receipt.get("generation_ms", event.get("ms", 0.0)))
    return total


def _peak_gpu_allocated(record):
    values = []
    for event in record.get("events", []):
        receipt = event.get("receipt")
        if type(receipt) is dict and type(receipt.get("gpu_peak_allocated_bytes")) is int:
            values.append(receipt["gpu_peak_allocated_bytes"])
    return max(values, default=0)


def _infrastructure_error(record):
    text = str(record.get("error") or "")
    hard = (
        "parameter mutation",
        "weights/tokenizer/precision drift",
        "actual token counts required",
        "token cap or accounting drift",
        "CUDA",
        "out of memory",
        "device-side",
        "core identity",
    )
    return any(piece.lower() in text.lower() for piece in hard)


def summarize(records):
    by_arm = {}
    by_family = defaultdict(dict)
    for arm in ARMS:
        rows = [record for record in records if record["arm"] == arm]
        accepted = sum(record.get("accepted") is True for record in rows)
        complete_ms = sum(float(record["complete_ms"]) for record in rows)
        generation_ms = sum(_generation_ms(record) for record in rows)
        model_tokens = sum(int(record["input_tokens"]) + int(record["output_tokens"]) for record in rows)
        output_tokens = sum(int(record["output_tokens"]) for record in rows)
        by_arm[arm] = {
            "observations": len(rows),
            "accepted": accepted,
            "capability": accepted / TASK_COUNT if len(rows) == TASK_COUNT else None,
            "complete_ms": complete_ms,
            "generation_ms": generation_ms,
            "tool_ms": sum(_tool_ms(record) for record in rows),
            "model_tokens": model_tokens,
            "output_tokens": output_tokens,
            "model_calls": sum(int(record["model_calls"]) for record in rows),
            "tool_calls": sum(int(record["tool_calls"]) for record in rows),
            "peak_gpu_allocated_bytes": max((_peak_gpu_allocated(record) for record in rows), default=0),
            "token_accounting_complete": all(record.get("token_accounting_complete") is True for record in rows),
            "infrastructure_errors": sum(_infrastructure_error(record) for record in rows),
        }
        for family in ("math_logic", "coding", "constraint_planning"):
            fam = [record for record in rows if record["family"] == family]
            by_family[arm][family] = {
                "observations": len(fam),
                "accepted": sum(record.get("accepted") is True for record in fam),
            }

    baseline_arms = ("B0", "B1", "B2", "B3")
    # Max capability; ties prefer fewer model tokens, then lower complete wall time.
    baseline = min(
        baseline_arms,
        key=lambda arm: (
            -by_arm[arm]["accepted"],
            by_arm[arm]["model_tokens"],
            by_arm[arm]["complete_ms"],
            arm,
        ),
    )
    b = by_arm[baseline]
    n = by_arm["N"]

    capability_gain = n["accepted"] - b["accepted"]
    m_a = (
        n["capability"] / b["capability"]
        if b["capability"] not in (None, 0) and n["capability"] is not None
        else None
    )
    latency_eff = (
        (n["accepted"] / n["complete_ms"]) / (b["accepted"] / b["complete_ms"])
        if n["accepted"] > 0 and b["accepted"] > 0 and n["complete_ms"] > 0 and b["complete_ms"] > 0
        else None
    )
    token_eff = (
        (n["accepted"] / n["model_tokens"]) / (b["accepted"] / b["model_tokens"])
        if n["accepted"] > 0 and b["accepted"] > 0 and n["model_tokens"] > 0 and b["model_tokens"] > 0
        else None
    )
    memory_ratio = (
        n["peak_gpu_allocated_bytes"] / b["peak_gpu_allocated_bytes"]
        if b["peak_gpu_allocated_bytes"] > 0
        else None
    )

    family_not_worse = True
    family_strictly_better = 0
    family_delta = {}
    for family in ("math_logic", "coding", "constraint_planning"):
        delta = by_family["N"][family]["accepted"] - by_family[baseline][family]["accepted"]
        family_delta[family] = delta
        family_not_worse &= delta >= 0
        family_strictly_better += int(delta > 0)

    infrastructure_valid = (
        len(records) == TASK_COUNT * len(ARMS)
        and all(by_arm[arm]["observations"] == TASK_COUNT for arm in ARMS)
        and all(by_arm[arm]["token_accounting_complete"] for arm in ARMS)
        and sum(by_arm[arm]["infrastructure_errors"] for arm in ARMS) == 0
        and b["accepted"] > 0
        and latency_eff is not None
        and memory_ratio is not None
    )

    pass_conditions = {
        "infrastructure_valid": infrastructure_valid,
        "neumann_at_least_8_of_12": n["accepted"] >= PASS_MIN_NEUMANN,
        "absolute_gain_at_least_2": capability_gain >= PASS_MIN_ABSOLUTE_GAIN,
        "not_worse_in_any_family": family_not_worse,
        "strictly_better_in_at_least_2_families": family_strictly_better >= 2,
        "latency_capability_efficiency_at_least_1_05": (
            latency_eff is not None and latency_eff >= PASS_MIN_LATENCY_EFFICIENCY
        ),
        "peak_gpu_memory_ratio_at_most_1_10": (
            memory_ratio is not None and memory_ratio <= PASS_MAX_PEAK_MEMORY_RATIO
        ),
    }

    if not infrastructure_valid:
        decision = "NOT_EVALUATED_INFRASTRUCTURE"
    elif all(pass_conditions.values()):
        decision = "PASS_ADMIT_ONE_SEALED_GENERAL_EVALUATION"
    else:
        decision = "FAIL_ARCHITECTURE_PIVOT"

    return {
        "by_arm": by_arm,
        "by_family": dict(by_family),
        "strongest_matched_baseline": baseline,
        "architecture_multiplier": {
            "M_A": m_a,
            "absolute_verified_task_gain": capability_gain,
            "M_E_complete_latency": latency_eff,
            "M_E_model_tokens_secondary": token_eff,
            "peak_gpu_memory_ratio": memory_ratio,
            "family_accepted_delta_N_minus_baseline": family_delta,
        },
        "pass_conditions": pass_conditions,
        "decision_2": decision,
    }


def execute(directory, frozen_head, core_factory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    tasks = opened_tasks()
    if len(tasks) != TASK_COUNT or len({task["id"] for task, _ in tasks}) != TASK_COUNT:
        raise ValueError("exact unique preregistered AM1 task count required")

    limits = Limits()
    order = [(task["id"], arm) for task, _ in tasks for arm in ARMS]
    random.Random(10701).shuffle(order)
    manifest = {
        "schema": SCHEMA,
        "frozen_head": frozen_head,
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "task_count": TASK_COUNT,
        "tasks": tasks,
        "task_sha256": sha(tasks),
        "arms": list(ARMS),
        "order": order,
        "limits": asdict(limits),
        "baseline_selection": "max verified accepted; ties fewer total model tokens; then lower complete wall",
        "pass_thresholds": {
            "neumann_min_accepted": PASS_MIN_NEUMANN,
            "absolute_gain_min_tasks": PASS_MIN_ABSOLUTE_GAIN,
            "latency_capability_efficiency_min": PASS_MIN_LATENCY_EFFICIENCY,
            "peak_gpu_memory_ratio_max": PASS_MAX_PEAK_MEMORY_RATIO,
            "family_rule": "N not worse in all 3 families and strictly better in at least 2",
        },
        "split": "opened_development_architecture_multiplier",
        "new_training": False,
        "frontier_calls": 0,
        "paid_api_calls": 0,
        "sealed_holdout_opened": False,
        "decision_1": "FAIL_STOP_CPU_MICROTUNING",
    }
    (directory / "manifest.json").write_text(canonical(manifest) + "\n")

    began = perf_counter_ns()
    records = []
    error = None
    failure_traceback = None
    core = None
    audit = None

    try:
        core = core_factory()
        (directory / "core.json").write_text(canonical(core.identity) + "\n")
        if core.identity.get("evidence_kind") != "actual_frozen_model":
            raise ValueError("actual frozen model evidence required")
        if core.identity.get("accelerator_class") is not True:
            raise ValueError("accelerator-class core required")
        lookup = {task["id"]:(task, private) for task, private in tasks}
        for index, (task_id, arm) in enumerate(order):
            task, private = lookup[task_id]
            record = run(task, private, arm, core, limits)
            (directory / ("query_%02d.json" % index)).write_text(canonical(record) + "\n")
            records.append(record)
        audit = core.audit()
        if not audit.get("unchanged"):
            raise ValueError("post-study core drift")
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
        failure_traceback = traceback.format_exc()

    summary = summarize(records) if len(records) == TASK_COUNT * len(ARMS) else None
    report = {
        "schema": SCHEMA,
        "status": "COMPLETE" if summary is not None and error is None and audit and audit.get("unchanged") else "INCOMPLETE",
        "error": error,
        "failure_traceback": failure_traceback,
        "observations": len(records),
        "expected_observations": TASK_COUNT * len(ARMS),
        "whole_study_ms": milliseconds(began),
        "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "core_audit": audit,
        "summary": summary,
        "general_capability_gate": "OPENED_DECISION_2_ONLY",
        "global_questions_closed": [],
        "new_training": False,
        "frontier_calls": 0,
        "sealed_holdout_opened": False,
        "resources": {
            "complete_latency": "measured",
            "model_tokens": "measured_secondary_proxy",
            "peak_gpu_allocated_memory": "measured",
            "energy_j": "unknown",
            "money": "unknown_unless_external_executor_adds_receipt",
            "FLOPs": "unknown",
        },
    }
    (directory / "report.json").write_text(canonical(report) + "\n")
    return report
