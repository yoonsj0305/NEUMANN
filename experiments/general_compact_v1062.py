"""Opened Runtime-0.2 compact repair execution.

Reuses only the Boot2 OPENED controls. Never a fresh holdout or capability gate.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import random
import resource
import traceback
from time import perf_counter_ns

from experiments.general_development_v106 import boot2_tasks
from neumann1.general_runtime_v106 import ARMS, MODEL_ID, MODEL_REVISION, canonical, milliseconds, sha
from neumann1.general_runtime_compact_v1062 import CompactLimits, run_compact


def write(path, value):
    with Path(path).open("x") as stream:
        stream.write(canonical(value) + "\n")


def strict_timeout(record):
    if "TimeoutError" in str(record.get("error")):
        return True
    return any(
        event.get("kind") == "model_result"
        and type(event.get("receipt")) is dict
        and event["receipt"].get("deadline_reached") is True
        for event in record.get("events", [])
    )


def readiness(records, expected, limits):
    complete = len(records) == expected
    timeouts = sum(strict_timeout(record) for record in records)
    accounted = complete and all(record.get("token_accounting_complete") for record in records)
    admitted = complete and all(
        not record.get("admission_blocked")
        and record.get("max_prompt_tokens", limits.admission_tokens + 1) <= limits.admission_tokens
        for record in records
    )
    answers = complete and all(record.get("answer") is not None for record in records)
    checked = complete and all(
        any(event.get("kind") == "verification" for event in record.get("events", []))
        for record in records
    )
    tool_records = [record for record in records if record["arm"] in ("B2", "B3", "N")]
    tools = len(tool_records) == 9 and all(record.get("tool_calls", 0) >= 1 for record in tool_records)
    return {
        "all_observations_complete": complete,
        "timeout_free": complete and timeouts == 0,
        "token_accounting_complete": accounted,
        "prompt_admission_clean": admitted,
        "answers_present": answers,
        "original_checker_exercised": checked,
        "tool_enabled_arms_exercised_tools": tools,
        "interface_ready": all((complete, timeouts == 0, accounted, admitted, answers, checked, tools)),
    }


def execute(directory, frozen_head):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    tasks = boot2_tasks()
    limits = CompactLimits()
    order = [(task[0]["id"], arm) for task in tasks for arm in ARMS]
    random.Random(1062).shuffle(order)

    manifest = {
        "schema": "neumann.general-compact-development.v1062.v1",
        "candidate": "Runtime-0.2 compact pointer actions",
        "frozen_head": frozen_head,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "limits": asdict(limits),
        "reasoning_policy": "compact_pointer_actions_hidden_thinking_disabled",
        "task_sha256": sha(tasks),
        "tasks": tasks,
        "order": order,
        "split": "opened_boot2_interface_controls_reused",
        "prior_evidence_preserved": [
            "v106_general_boot2",
            "v1061_general_repair_first",
        ],
        "new_training": False,
        "frontier_calls": 0,
        "paid_api_calls": 0,
        "holdout_opened": False,
        "global_questions_closed": [],
    }
    write(directory / "manifest.json", manifest)

    records = []
    error = None
    failure_traceback = None
    core = None
    audit = None
    load_started = perf_counter_ns()

    try:
        from experiments.general_hf_core_compact_v1062 import FrozenHFCompactCore

        core = FrozenHFCompactCore()
        write(directory / "core.json", core.identity)
        if core.identity.get("evidence_kind") != "actual_frozen_model":
            raise ValueError("synthetic adapter cannot produce model evidence")

        lookup = {task[0]["id"]: task for task in tasks}
        for index, (task_id, arm) in enumerate(order):
            task, private = lookup[task_id]
            write(directory / ("query_%02d_started.json" % index), {"task_id": task_id, "arm": arm})
            record = run_compact(task, private, arm, core, limits)
            write(directory / ("query_%02d.json" % index), record)
            records.append(record)

        audit = core.audit()
        if not audit["unchanged"]:
            raise ValueError("post-study core drift")
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
        failure_traceback = traceback.format_exc()
    finally:
        ready = readiness(records, len(order), limits)
        complete = len(records) == len(order) and error is None and audit and audit["unchanged"]
        startup = core.startup_ms if core else milliseconds(load_started)
        report = {
            "schema": manifest["schema"],
            "status": "COMPLETE_COMPACT_REPAIR_DIAGNOSTIC" if complete else "INCOMPLETE",
            "candidate": manifest["candidate"],
            "error": error,
            "failure_traceback": failure_traceback,
            "observations": len(records),
            "expected_observations": len(order),
            "startup_attempt_ms": startup,
            "whole_study_ms": milliseconds(began),
            "core_audit": audit,
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "readiness": ready,
            "general_capability_gate": "NOT_EVALUATED",
            "global_questions_closed": [],
            "frontier_calls": 0,
            "new_training": False,
            "resources_unavailable": ["FLOPs", "energy_j", "money", "device_thermal", "VRAM"],
            "by_arm": {
                arm: {
                    "accepted": sum(record["accepted"] for record in records if record["arm"] == arm),
                    "observations": sum(record["arm"] == arm for record in records),
                    "timeouts": sum(strict_timeout(record) for record in records if record["arm"] == arm),
                    "admission_blocks": sum(record.get("admission_blocked", False) for record in records if record["arm"] == arm),
                    "max_prompt_tokens": max(
                        [record.get("max_prompt_tokens", 0) for record in records if record["arm"] == arm],
                        default=0,
                    ),
                    "model_calls": sum(record["model_calls"] for record in records if record["arm"] == arm),
                    "tool_calls": sum(record["tool_calls"] for record in records if record["arm"] == arm),
                    "query_ms": sum(record["complete_ms"] for record in records if record["arm"] == arm),
                    "output_tokens": (
                        sum(record["output_tokens"] for record in records if record["arm"] == arm)
                        if all(record["token_accounting_complete"] for record in records if record["arm"] == arm)
                        else None
                    ),
                }
                for arm in ARMS
            },
        }
        write(directory / "report.json", report)
        files = {
            path.name: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.iterdir())
            if path.is_file()
        }
        write(
            directory / "terminal.json",
            {
                "files": files,
                "complete": bool(complete),
                "interface_ready": bool(ready["interface_ready"]),
                "no_replacement": True,
                "general_capability_gate": "NOT_EVALUATED",
            },
        )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    result = execute(args.directory, args.frozen_head)
    print(canonical(result))
    raise SystemExit(0 if result["status"] == "COMPLETE_COMPACT_REPAIR_DIAGNOSTIC" else 2)
