"""First opened interface diagnostic; never a fresh holdout or capability gate."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import resource
from time import perf_counter_ns

from neumann1.general_runtime_v106 import ARMS, Limits, MODEL_ID, MODEL_REVISION, canonical, development_tasks, milliseconds, run, sha


def write(path, value):
    with path.open("x") as stream:
        stream.write(canonical(value) + "\n")


def execute(directory, frozen_head):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    tasks, limits = development_tasks(), Limits()
    order = [(t[0]["id"], a) for t in tasks for a in ARMS]
    random.Random(106).shuffle(order)
    manifest = {"schema": "neumann.general-development.v106.v1", "frozen_head": frozen_head,
                "model": MODEL_ID, "revision": MODEL_REVISION, "limits": asdict(limits),
                "tasks": tasks, "task_sha256": sha(tasks), "order": order,
                "split": "opened_development_interface_controls", "new_training": False,
                "frontier_calls": 0, "paid_api_calls": 0, "holdout_opened": False}
    write(directory / "manifest.json", manifest)
    records, error, core, audit = [], None, None, None
    load_started = perf_counter_ns()
    try:
        from experiments.general_hf_core_v106 import FrozenHFCore
        core = FrozenHFCore()
        write(directory / "core.json", core.identity)
        if core.identity["evidence_kind"] != "actual_frozen_model":
            raise ValueError("synthetic adapter cannot produce model evidence")
        lookup = {t[0]["id"]: t for t in tasks}
        for index, (task_id, arm) in enumerate(order):
            task, private = lookup[task_id]
            write(directory / ("query_%02d_started.json" % index), {"task_id": task_id, "arm": arm})
            record = run(task, private, arm, core, limits)
            write(directory / ("query_%02d.json" % index), record)
            records.append(record)
        audit = core.audit()
        if not audit["unchanged"]:
            raise ValueError("post-study core drift")
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        complete = len(records) == len(order) and error is None and audit and audit["unchanged"]
        startup = core.startup_ms if core else milliseconds(load_started)
        report = {"schema": manifest["schema"], "status": "COMPLETE_INTERFACE_DIAGNOSTIC" if complete else "INCOMPLETE",
                  "error": error, "observations": len(records), "expected_observations": len(order),
                  "startup_attempt_ms": startup, "whole_study_ms": milliseconds(began),
                  "core_audit": audit, "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                  "global_questions_closed": [], "general_capability_gate": "NOT_EVALUATED",
                  "frontier_calls": 0, "new_training": False,
                  "resources_unavailable": ["FLOPs", "energy_j", "money", "device_thermal", "VRAM"],
                  "by_arm": {a: {"accepted": sum(r["accepted"] for r in records if r["arm"] == a),
                                 "observations": sum(r["arm"] == a for r in records),
                                 "query_ms": sum(r["complete_ms"] for r in records if r["arm"] == a),
                                 "cold_single_query_ms": [startup + r["complete_ms"] for r in records if r["arm"] == a],
                                 "output_tokens": (sum(r["output_tokens"] for r in records if r["arm"] == a)
                                     if all(r["token_accounting_complete"] for r in records if r["arm"] == a)
                                     and sum(r["arm"] == a for r in records)==3 else None)} for a in ARMS}}
        write(directory / "report.json", report)
        files = {p.name: __import__("hashlib").sha256(p.read_bytes()).hexdigest() for p in sorted(directory.iterdir()) if p.is_file()}
        write(directory / "terminal.json", {"files": files, "complete": bool(complete), "no_replacement": True})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    result = execute(args.directory, args.frozen_head)
    print(canonical(result))
    raise SystemExit(0 if result["status"] == "COMPLETE_INTERFACE_DIAGNOSTIC" else 2)
