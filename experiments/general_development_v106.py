"""First opened interface diagnostic; never a fresh holdout or capability gate."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import resource
import traceback
from time import perf_counter_ns

from neumann1.general_runtime_v106 import ARMS, Limits, MODEL_ID, MODEL_REVISION, canonical, development_tasks, milliseconds, run, sha


def write(path, value):
    with path.open("x") as stream:
        stream.write(canonical(value) + "\n")


def boot2_tasks():
    """Distinct opened controls after a zero-forward dependency failure."""
    return [
        ({"id":"runtime0_boot2_math","family":"math_logic","public":{
          "expression":"(p*q-r)/(s+t)","bindings":{"p":29,"q":11,"r":7,"s":3,"t":9,"unused":123},
          "background":"The receipt is printed on green paper."},
          "instruction":"Return the exact rational value."},{"exact":"26"}),
        ({"id":"runtime0_boot2_code","family":"coding","public":{
          "requirement":"Return the number of distinct negative integers in items, a list of integers.",
          "background":"The caller likes music."},
          "instruction":"Return Python source defining solve(items)."},
         {"tests":[{"input":[],"output":0},{"input":[-2,-2,0,3,-5],"output":2},
                   {"input":[0,1,3],"output":0},{"input":[-1,-3,-1,-7],"output":3}]}),
        ({"id":"runtime0_boot2_plan","family":"constraint_planning","public":{
          "domains":{k:[0,1,2,3] for k in "ABCD"},
          "constraints":[["lt","A","B"],["lt","B","C"],["eq","C","D"]],
          "background":"A train has six carriages."},
          "instruction":"Return a complete assignment meeting every original constraint."},{})]


def execute(directory, frozen_head, study="first"):
    if study not in ("first","boot2"):
        raise ValueError("registered opened diagnostic required")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    began = perf_counter_ns()
    tasks, limits = (development_tasks() if study=="first" else boot2_tasks()), Limits()
    order = [(t[0]["id"], a) for t in tasks for a in ARMS]
    random.Random(106).shuffle(order)
    manifest = {"schema": "neumann.general-development.v106.v1", "frozen_head": frozen_head,
                "model": MODEL_ID, "revision": MODEL_REVISION, "limits": asdict(limits),
                "tasks": tasks, "task_sha256": sha(tasks), "order": order, "study": study,
                "split": "opened_development_interface_controls", "new_training": False,
                "frontier_calls": 0, "paid_api_calls": 0, "holdout_opened": False}
    write(directory / "manifest.json", manifest)
    records, error, core, audit, failure_traceback = [], None, None, None, None
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
        failure_traceback = traceback.format_exc()
    finally:
        complete = len(records) == len(order) and error is None and audit and audit["unchanged"]
        startup = core.startup_ms if core else milliseconds(load_started)
        prior_failed_setup_ms = 41258.945662 if study=="boot2" else 0.
        report = {"schema": manifest["schema"], "status": "COMPLETE_INTERFACE_DIAGNOSTIC" if complete else "INCOMPLETE",
                  "error": error, "failure_traceback":failure_traceback,
                  "study":study,"prior_failed_setup_ms":prior_failed_setup_ms,
                  "observations": len(records), "expected_observations": len(order),
                  "startup_attempt_ms": startup, "whole_study_ms": milliseconds(began),
                  "core_audit": audit, "peak_process_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                  "global_questions_closed": [], "general_capability_gate": "NOT_EVALUATED",
                  "frontier_calls": 0, "new_training": False,
                  "resources_unavailable": ["FLOPs", "energy_j", "money", "device_thermal", "VRAM"],
                  "by_arm": {a: {"accepted": sum(r["accepted"] for r in records if r["arm"] == a),
                                 "observations": sum(r["arm"] == a for r in records),
                                 "query_ms": sum(r["complete_ms"] for r in records if r["arm"] == a),
                                 "cold_single_query_ms": [prior_failed_setup_ms+startup+r["complete_ms"] for r in records if r["arm"] == a],
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
    parser.add_argument("--study",choices=("first","boot2"),default="first")
    args = parser.parse_args()
    result = execute(args.directory, args.frozen_head,args.study)
    print(canonical(result))
    raise SystemExit(0 if result["status"] == "COMPLETE_INTERFACE_DIAGNOSTIC" else 2)
