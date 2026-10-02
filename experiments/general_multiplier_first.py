"""First opened accelerator Architecture Multiplier execution.

One frozen core, twelve opened tasks, three arms, 36 terminal observations.
Failures are retained. No sealed holdout, frontier call, or fitting.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import hashlib
import json
from pathlib import Path
import random
import resource
import traceback
from time import perf_counter_ns

from experiments.general_multiplier_accelerator_core import FrozenAcceleratorCore
from experiments.general_multiplier_tasks import (
    TASK_SHA256,
    MODEL_VIEW_SHA256,
    manifest as task_manifest,
    model_view,
    multiplier_tasks,
)
from neumann1.general_multiplier_contract import (
    ARMS,
    MultiplierBudget,
    contract_manifest,
    evaluate_multiplier,
)
from neumann1.general_multiplier_runtime import run_observation
from neumann1.general_runtime_v106 import canonical, milliseconds, sha

SCHEMA = "neumann.architecture-multiplier-first.v1"


def _write(path, value):
    Path(path).write_text(canonical(value) + "\n")


def _file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _arm_result(arm, rows, core_sha, budget_sha):
    peak = max((int(row.get("peak_accelerator_memory_bytes", 0)) for row in rows), default=0)
    token_complete = all(row.get("token_accounting_complete") is True for row in rows)
    resource_complete = (
        len(rows) == 12
        and token_complete
        and all(type(row.get("complete_ms")) in (int, float) and row["complete_ms"] > 0 for row in rows)
        and peak > 0
    )
    return {
        "arm": arm,
        "core_sha256": core_sha,
        "task_sha256": TASK_SHA256,
        "budget_sha256": budget_sha,
        "observations": len(rows),
        "terminal_receipts": len(rows),
        "successes": sum(row.get("accepted") is True for row in rows),
        "complete_ms": sum(float(row["complete_ms"]) for row in rows),
        "model_calls": sum(int(row["model_calls"]) for row in rows),
        "tool_calls": sum(int(row["tool_calls"]) for row in rows),
        "input_tokens": sum(int(row["input_tokens"]) for row in rows),
        "output_tokens": sum(int(row["output_tokens"]) for row in rows),
        "peak_accelerator_memory_bytes": peak,
        "token_accounting_complete": token_complete,
        "resource_accounting_complete": resource_complete,
    }


def execute(directory, frozen_head):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    started = perf_counter_ns()
    budget = MultiplierBudget()
    budget_sha = sha(asdict(budget))
    tasks = multiplier_tasks()
    views = {task["id"]: model_view(task) for task, _ in tasks}
    lookup = {task["id"]: (task, private) for task, private in tasks}

    order = [(task["id"], arm) for task, _ in tasks for arm in ARMS]
    random.Random(12601).shuffle(order)

    prereg = {
        "schema": SCHEMA,
        "frozen_head": frozen_head,
        "task_manifest": task_manifest(),
        "task_sha256": TASK_SHA256,
        "model_view_sha256": MODEL_VIEW_SHA256,
        "contract": contract_manifest(TASK_SHA256, budget_sha),
        "order": order,
        "observations": len(order),
        "split": "opened_author_constructed_development",
        "new_training": False,
        "frontier_calls": 0,
        "paid_api_calls": 0,
        "holdout_opened": False,
        "edge_claim_allowed": False,
    }
    _write(directory / "manifest.json", prereg)

    core = None
    records = []
    audit = None
    error = None
    failure_traceback = None
    core_sha = None
    environment = None

    try:
        core = FrozenAcceleratorCore()
        core_sha = sha(core.identity)
        environment = core.environment
        _write(directory / "core.json", core.identity)
        _write(directory / "environment.json", environment)

        for index, (task_id, arm) in enumerate(order):
            task, private = lookup[task_id]
            _write(
                directory / ("query_%02d_started.json" % index),
                {"task_id": task_id, "arm": arm, "model_view_sha256": sha(views[task_id])},
            )
            record = run_observation(
                task,
                private,
                views[task_id],
                arm,
                core,
                budget,
            )
            _write(directory / ("query_%02d.json" % index), record)
            records.append(record)

        audit = core.audit()
        if audit.get("unchanged") is not True:
            raise ValueError("post-study frozen core audit failed")
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
        failure_traceback = traceback.format_exc()

    arm_results = {}
    verdict = {
        "verdict": "NOT_EVALUATED",
        "reason": "INCOMPLETE_EXECUTION",
        "global_questions_closed": [],
    }
    if core_sha and len(records) == 36:
        for arm in ARMS:
            arm_rows = [row for row in records if row["arm"] == arm]
            arm_results[arm] = _arm_result(arm, arm_rows, core_sha, budget_sha)
        try:
            verdict = evaluate_multiplier(arm_results)
        except Exception as exc:
            verdict = {
                "verdict": "NOT_EVALUATED",
                "reason": type(exc).__name__ + ": " + str(exc),
                "global_questions_closed": [],
            }

    complete = (
        error is None
        and len(records) == 36
        and audit is not None
        and audit.get("unchanged") is True
        and set(arm_results) == set(ARMS)
    )

    report = {
        "schema": SCHEMA,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "error": error,
        "failure_traceback": failure_traceback,
        "observations": len(records),
        "expected_observations": 36,
        "environment": environment,
        "core_sha256": core_sha,
        "core_audit": audit,
        "arm_results": arm_results,
        "decision_2": verdict,
        "whole_study_ms": milliseconds(started),
        "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "new_training": False,
        "frontier_calls": 0,
        "holdout_opened": False,
        "global_questions_closed": [],
        "next": (
            "ONE_SEALED_GENERAL_EVALUATION"
            if verdict.get("verdict") == "PASS"
            else "ARCHITECTURE_PIVOT"
            if verdict.get("verdict") == "FAIL"
            else "REPAIR_ENVIRONMENT_OR_MEASUREMENT_ONLY"
        ),
    }
    _write(directory / "report.json", report)

    files = {
        path.name: _file_hash(path)
        for path in sorted(directory.iterdir())
        if path.is_file()
    }
    terminal = {
        "schema": "neumann.architecture-multiplier-terminal.v1",
        "files": files,
        "complete": complete,
        "decision_2": verdict.get("verdict"),
        "no_replacement": True,
        "rerun_policy": (
            "no favorable rerun; only frozen environment/measurement repair after NOT_EVALUATED"
        ),
    }
    _write(directory / "terminal.json", terminal)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    report = execute(args.directory, args.frozen_head)
    print(canonical(report))
    raise SystemExit(0 if report["status"] == "COMPLETE" else 2)


if __name__ == "__main__":
    main()
