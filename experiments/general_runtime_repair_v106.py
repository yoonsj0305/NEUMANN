"""Opened Runtime-0.1 repair diagnostic on the already-opened Boot2 controls.

This is not v0.0.107, a fresh holdout, a capability gate, or frontier evidence.
It measures whether the repaired protocol can complete model -> action -> tool ->
checker -> answer loops under the unchanged v0.0.106 query caps.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import random
import resource
import traceback
from time import perf_counter_ns

from experiments.general_development_v106 import boot2_tasks, write
from experiments.general_hf_core_repair_v106 import FrozenHFCoreRepair
from neumann1.general_runtime_repair_v106 import REPAIR_ID, Runtime01ProtocolAdapter
from neumann1.general_runtime_v106 import ARMS, Limits, canonical, milliseconds, run, sha


FIRST_BOOT2_ARCHIVE = "c57fd111b249d442e63113ae223801b2987e7b82"
FIRST_BOOT2_MAIN_MERGE = "f43242ae09fb5343257e8f83eacf01dfaa4548d8"


def _timeout(record):
    error = record.get("error") or ""
    return "TimeoutError" in error or record["complete_ms"] > record["limits"]["wall_ms"]


def _interface_summary(records):
    by_arm_tools = {
        arm: sum(record["tool_calls"] for record in records if record["arm"] == arm)
        for arm in ARMS
    }
    checks = [
        any(event.get("kind") == "verification" for event in record["events"])
        for record in records
    ]
    all_answers = all(record.get("answer") is not None for record in records)
    no_timeouts = all(not _timeout(record) for record in records)
    accounting = all(
        record.get("token_accounting_complete") is True
        and type(record.get("complete_ms")) in (int, float)
        and record["complete_ms"] >= 0
        for record in records
    )
    tool_paths = all(by_arm_tools[arm] > 0 for arm in ("B2", "B3", "N"))
    checker_paths = all(checks)
    return {
        "all_queries_have_candidate_answer": all_answers,
        "no_query_timeout": no_timeouts,
        "all_queries_reach_original_checker": checker_paths,
        "charged_latency_and_token_accounting_complete": accounting,
        "tool_calls_by_arm": by_arm_tools,
        "B2_B3_N_each_exercise_tool_path": tool_paths,
        "action_rejections": sum(
            event.get("kind") == "action_rejected"
            for record in records for event in record["events"]
        ),
        "accepted_by_arm": {
            arm: sum(record["accepted"] for record in records if record["arm"] == arm)
            for arm in ARMS
        },
        "ready": bool(
            len(records) == 15
            and all_answers
            and no_timeouts
            and checker_paths
            and accounting
            and tool_paths
        ),
    }


def execute(directory, frozen_head):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    tasks, limits = boot2_tasks(), Limits()
    order = [(task[0]["id"], arm) for task in tasks for arm in ARMS]
    random.Random(106).shuffle(order)

    manifest = {
        "schema": "neumann.general-runtime-repair.v106r1.v1",
        "candidate": REPAIR_ID,
        "parent_boot2_archive": FIRST_BOOT2_ARCHIVE,
        "parent_boot2_main_merge": FIRST_BOOT2_MAIN_MERGE,
        "frozen_head": frozen_head,
        "limits": asdict(limits),
        "tasks": tasks,
        "task_sha256": sha(tasks),
        "order": order,
        "split": "opened_development_interface_controls",
        "new_training": False,
        "frontier_calls": 0,
        "paid_api_calls": 0,
        "holdout_opened": False,
        "changes_from_parent": [
            "explicit response-parser prefix",
            "hidden thinking forced off",
            "charged immediate-action prompt suffix",
            "unambiguous missing-action-key normalization only",
        ],
    }
    write(directory / "manifest.json", manifest)

    records, error, audit, failure_traceback = [], None, None, None
    core = None
    load_started = perf_counter_ns()
    try:
        base = FrozenHFCoreRepair()
        core = Runtime01ProtocolAdapter(base)
        write(directory / "core.json", {
            "model": core.identity,
            "protocol_candidate": REPAIR_ID,
        })
        lookup = {task[0]["id"]: task for task in tasks}
        for index, (task_id, arm) in enumerate(order):
            task, private = lookup[task_id]
            write(directory / ("query_%02d_started.json" % index), {
                "task_id": task_id,
                "arm": arm,
                "candidate": REPAIR_ID,
            })
            record = run(task, private, arm, core, limits)
            write(directory / ("query_%02d.json" % index), record)
            records.append(record)
        audit = core.audit()
        if not audit["unchanged"]:
            raise ValueError("post-study core drift")
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
        failure_traceback = traceback.format_exc()
    finally:
        complete = len(records) == len(order) and error is None and audit and audit["unchanged"]
        interface = _interface_summary(records) if len(records) == len(order) else {
            "ready": False,
            "observations": len(records),
        }
        report = {
            "schema": manifest["schema"],
            "status": "COMPLETE_OPENED_REPAIR_DIAGNOSTIC" if complete else "INCOMPLETE",
            "candidate": REPAIR_ID,
            "error": error,
            "failure_traceback": failure_traceback,
            "observations": len(records),
            "expected_observations": len(order),
            "startup_attempt_ms": core.startup_ms if core else milliseconds(load_started),
            "whole_study_ms": milliseconds(began),
            "core_audit": audit,
            "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            "interface_readiness": interface,
            "general_capability_gate": "NOT_EVALUATED",
            "global_questions_closed": [],
            "frontier_calls": 0,
            "new_training": False,
            "holdout_opened": False,
            "resources_unavailable": ["FLOPs", "energy_j", "money", "device_thermal", "VRAM"],
        }
        write(directory / "report.json", report)
        files = {
            path.name: __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.iterdir()) if path.is_file()
        }
        write(directory / "terminal.json", {
            "files": files,
            "complete": bool(complete),
            "interface_ready": bool(interface.get("ready")),
            "parent_boot2_preserved": True,
        })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    result = execute(args.directory, args.frozen_head)
    print(canonical(result))
    raise SystemExit(0 if result["status"] == "COMPLETE_OPENED_REPAIR_DIAGNOSTIC" else 2)
