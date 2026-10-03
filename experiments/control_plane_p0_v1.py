"""Offline P0 prerequisite: replay the retained first Decision-2 failure bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from neumann1.control_plane_v1 import canonical, digest

ARCHIVE = Path("docs/experiments/results/am1_decision2_first_original")


def replay_failure(directory=ARCHIVE):
    directory = Path(directory)
    load = lambda name: json.loads((directory / name).read_bytes())
    pins = load("upload_pins.json")
    for name, pin in pins["files"].items():
        if Path(name).name != name:
            raise ValueError("archive file must have a flat safe name")
        raw = (directory / name).read_bytes()
        if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError("uploaded original byte drift: " + name)
    terminal, manifest, core, report = map(load, ("terminal.json", "manifest.json", "core.json", "report.json"))
    if terminal["complete"] is not True or terminal["no_replacement"] is not True:
        raise ValueError("first completed/no-replacement receipt required")
    for name, value in terminal["files"].items():
        if Path(name).name != name or hashlib.sha256((directory / name).read_bytes()).hexdigest() != value:
            raise ValueError("original terminal hash mismatch")
    if manifest["observations"] != 36 or len(manifest["order"]) != 36:
        raise ValueError("36 original observations required")
    if manifest["holdout_opened"] or manifest["new_training"] or manifest["frontier_calls"]:
        raise ValueError("first scientific boundary drift")
    if report["status"] != "COMPLETE" or report["core_audit"]["unchanged"] is not True:
        raise ValueError("complete frozen-core audit required")
    if digest(core) != report["core_sha256"]:
        raise ValueError("core receipt hash mismatch")
    queries = [load("query_%02d.json" % i) for i in range(36)]
    if sorted(p.name for p in directory.glob("query_??.json")) != ["query_%02d.json" % i for i in range(36)]:
        raise ValueError("exact query coverage required")
    calls = 0
    for row, order in zip(queries, manifest["order"]):
        if [row["task_id"], row["arm"]] != order or row["core_sha256"] != digest(core):
            raise ValueError("order/core mismatch")
        if row["trace_sha256"] != digest(row["events"]):
            raise ValueError("query trace hash mismatch")
        if row["accepted"] or row["answer"] is not None or row["tool_calls"] != 0:
            raise ValueError("retained all-zero result changed")
        receipts = [e["receipt"] for e in row["events"] if e["kind"] == "model_result"]
        if len(receipts) != row["model_calls"] or len(receipts) != 2:
            raise ValueError("retained model-call accounting mismatch")
        if sum(r["output_tokens"] for r in receipts) != row["output_tokens"]:
            raise ValueError("output accounting mismatch")
        if sum(r["input_tokens"] for r in receipts) != row["input_tokens"]:
            raise ValueError("input accounting mismatch")
        for receipt in receipts:
            if len(receipt["output_token_ids"]) != receipt["output_tokens"] or receipt["output_tokens"] != 256:
                raise ValueError("retained token cutoff drift")
            if not receipt["raw"].startswith("<|channel>thought") or "<|channel>final" in receipt["raw"]:
                raise ValueError("retained thought/final diagnosis drift")
            if receipt["deadline_reached"]:
                raise ValueError("retained generation deadline diagnosis drift")
        calls += len(receipts)
    for arm in ("DIRECT", "TOOL", "NEUMANN"):
        rows = [r for r in queries if r["arm"] == arm]
        summary = report["arm_results"][arm]
        if len(rows) != 12 or summary["successes"] != 0:
            raise ValueError("arm capability drift")
        for key in ("input_tokens", "output_tokens", "model_calls", "tool_calls"):
            if sum(r[key] for r in rows) != summary[key]:
                raise ValueError("arm aggregate drift: " + key)
        expected = math.fsum(r["complete_ms"] for r in rows)
        if not math.isclose(expected, summary["complete_ms"], rel_tol=0, abs_tol=2 * math.ulp(expected)):
            raise ValueError("arm latency drift")
    decision = report["decision_2"]
    if decision["verdict"] != "FAIL" or terminal["decision_2"] != "FAIL" or decision["sealed_general_evaluation_admitted"]:
        raise ValueError("frozen Decision-2 verdict drift")
    return {"schema": "neumann.control-plane-p0-original-replay.v1", "valid": True,
            "observations": 36, "model_calls": calls, "tool_calls": 0,
            "decision_2": "FAIL", "next": "CONTROL_PLANE_PIVOT_P1_NOT_ARMED",
            "model_inference_performed": False, "sealed_holdout_opened": False,
            "global_questions_closed": [], "source_zip_sha256": pins["zip_sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=str(ARCHIVE))
    args = parser.parse_args()
    print(canonical(replay_failure(args.directory)))
