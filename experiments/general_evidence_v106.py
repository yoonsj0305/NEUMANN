"""Replay retained original checks and accounting, never neural inference.

Receipts attest the original workflow execution; replay does not independently
reproduce neural generations, timing, energy or arbitrary-program correctness.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from neumann1.general_runtime_v106 import ARMS, Limits, MODEL_ID, MODEL_REVISION, sha, verify_original


def check_record(record, task, private, core, limits):
    assert record["task_id"] == task["id"] and record["task_sha256"] == sha(task)
    assert record["family"] == task["family"] and record["core"] == core
    assert record["limits"] == limits and record["evidence_kind"] == "actual_frozen_model"
    assert record["new_fitting"] is False
    if record["arm"] in ("B0","B1"):
        assert record["tool_calls"] == 0
    if record["arm"] == "B2":
        assert record["tool_calls"] <= 1
    events = record["events"]
    assert sha(events) == record["trace_sha256"]
    starts = [e for e in events if e["kind"] == "model_start"]
    receipts = [e["receipt"] for e in events if e["kind"] == "model_result"]
    assert len(starts) == record["model_calls"] <= limits["model_calls"]
    assert record["token_accounting_complete"] == (len(receipts) == len(starts))
    assert sum(r["input_tokens"] for r in receipts) == record["input_tokens"]
    assert sum(r["output_tokens"] for r in receipts) == record["output_tokens"] <= limits["output_tokens"]
    for receipt in receipts:
        assert receipt["core_sha256"] == sha(core)
        assert receipt["output_tokens"] == len(receipt["output_token_ids"])
        assert receipt["output_tokens"] <= limits["per_call_tokens"]
        assert receipt["input_tokens"] + receipt["output_tokens"] <= limits["context_tokens"]
    assert sum(e["kind"] == "tool_start" for e in events) == record["tool_calls"] <= limits["tool_calls"]
    assert record["complete_ms"] >= 0
    if record["accepted"]:
        assert record["complete_ms"] <= limits["wall_ms"]
        checks = [e for e in events if e["kind"] == "verification"]
        assert checks and checks[-1]["accepted"] and checks[-1].get("error") is None
        assert verify_original(task,record["answer"],private,limits["tool_ms"])
        if record["arm"] == "N":
            assert any(e["kind"] == "tool_result" and e.get("tool") == "reduce"
                       and "ir" in e.get("result",{}) for e in events)


def replay(directory):
    directory = Path(directory)
    load = lambda name: json.loads((directory/name).read_text())
    terminal, manifest, report = load("terminal.json"), load("manifest.json"), load("report.json")
    files = {p.name for p in directory.iterdir() if p.is_file() and p.name != "terminal.json"}
    assert set(terminal["files"]) == files
    for name, digest in terminal["files"].items():
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == digest
    assert manifest["split"] == "opened_development_interface_controls"
    assert manifest["model"] == MODEL_ID and manifest["revision"] == MODEL_REVISION
    assert manifest["limits"] == asdict(Limits()) and manifest["task_sha256"] == sha(manifest["tasks"])
    assert manifest["new_training"] is False and manifest["frontier_calls"] == manifest["paid_api_calls"] == 0
    assert manifest["holdout_opened"] is False
    assert report["general_capability_gate"] == "NOT_EVALUATED" and not report["global_questions_closed"]
    assert report["new_training"] is False and report["frontier_calls"] == 0
    assert len(manifest["order"]) == report["expected_observations"] == 15
    assert len(set(map(tuple,manifest["order"]))) == 15
    lookup = {task["id"]:(task,private) for task,private in manifest["tasks"]}
    assert set(map(tuple,manifest["order"])) == {(task_id,arm) for task_id in lookup for arm in ARMS}
    records = []
    core = load("core.json") if (directory/"core.json").exists() else None
    if core is not None:
        assert core["model_id"] == MODEL_ID and core["revision"] == MODEL_REVISION
        assert core["weights_frozen"] and core["precision"] == "bfloat16" and core["device"] == "cpu"
    for index,(task_id,arm) in enumerate(manifest["order"]):
        path = directory/("query_%02d.json"%index)
        if not path.exists():
            continue
        record = json.loads(path.read_text())
        assert record["arm"] == arm
        task,private = lookup[task_id]
        check_record(record,task,private,core,manifest["limits"])
        records.append(record)
    assert len(records) == report["observations"]
    for arm in ARMS:
        subset = [r for r in records if r["arm"] == arm]
        arm_report = report["by_arm"][arm]
        assert arm_report["observations"] == len(subset)
        assert arm_report["accepted"] == sum(r["accepted"] for r in subset)
        assert arm_report["query_ms"] == sum(r["complete_ms"] for r in subset)
        expected_tokens = sum(r["output_tokens"] for r in subset) if len(subset)==3 and all(r["token_accounting_complete"] for r in subset) else None
        assert arm_report["output_tokens"] == expected_tokens
        prior = report.get("prior_failed_setup_ms",0.)
        assert arm_report["cold_single_query_ms"] == [prior+report["startup_attempt_ms"]+r["complete_ms"] for r in subset]
    if report["status"] == "COMPLETE_INTERFACE_DIAGNOSTIC":
        assert len(records)==15 and terminal["complete"] and report["core_audit"]["unchanged"]
        assert report["core_audit"]["after_sha256"] == core["artifact_sha256"]
    else:
        assert report["status"] == "INCOMPLETE" and not terminal["complete"]
    return {"status":report["status"],"observations":len(records),"by_arm":report["by_arm"],
            "general_capability_gate":"NOT_EVALUATED","neural_replay_calls":0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory",required=True)
    print(json.dumps(replay(parser.parse_args().directory),sort_keys=True))
