"""Independent model-free replay for first P1.11 development receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from neumann1.control_plane_v1 import digest, finite, snapshot
from experiments.control_plane_p111_registration import registration, BOUNDARY
from experiments.control_plane_p111_runtime import run_item, evaluate, totals


class RecordedEncoder:
    def __init__(self, receipt):
        self.receipt = snapshot(receipt)
        self.forward_calls = 0
        self.last_attempt = None

    def score(self, ir):
        if self.receipt.get("status") != "COMPLETE":
            raise ValueError("complete recorded P1.11 selector receipt required")
        if self.receipt.get("semantic_ir_sha256") != digest(ir):
            raise ValueError("P1.11 recorded semantic IR identity drift")
        self.forward_calls += 1
        self.last_attempt = {
            "input_rows": self.receipt["input_rows"],
            "input_tokens": self.receipt["input_tokens"],
            "padded_tokens": self.receipt["padded_tokens"],
            "forward_calls": 1,
            "tokenize_ms": self.receipt.get("tokenize_ms"),
        }
        return {
            "similarities": snapshot(self.receipt["similarities"]),
            "forward_calls": 1,
            "input_rows": self.receipt["input_rows"],
            "input_tokens": self.receipt["input_tokens"],
            "padded_tokens": self.receipt["padded_tokens"],
            "tokenize_ms": self.receipt.get("tokenize_ms"),
            "forward_ms": self.receipt.get("forward_ms"),
            "pooling_similarity_ms": self.receipt.get("pooling_similarity_ms"),
            "device": self.receipt.get("device"),
        }


def replay_record(row, ref, record):
    receipt = record.get("selector_receipt")
    if type(receipt) is not dict:
        if record.get("selector_complete") is False:
            for key in (
                "extraction_ms", "feasibility_ms", "ir_ms", "lexical_ms",
                "selection_ms", "complete_ms",
            ):
                finite(record.get(key), True)
            return
        raise ValueError("P1.11 item missing selector receipt")

    expected = run_item(row, ref, RecordedEncoder(receipt))
    keys = (
        "task_id", "stratum", "status", "accepted", "executed",
        "original_view_sha256", "selected_candidate", "selected_route",
        "raw_top_candidate", "model_calls", "neural_forward_calls",
        "generated_calls", "input_rows", "input_tokens", "padded_tokens",
        "tool_calls", "verifier_calls", "feasibility_calls",
        "feasibility_nodes", "feasibility_constraint_checks",
        "witness_cache_hits", "accounting_complete", "selector_complete",
        "selection_error", "eligible_indexes", "selection", "proposal",
        "selector_decision", "semantic_ir", "candidate_entities",
        "lexical_baseline", "bundle_sha256",
    )
    for key in keys:
        if record.get(key) != expected.get(key):
            raise ValueError("P1.11 semantic replay drift: " + key)

    if bool(record.get("error")) != bool(expected.get("error")):
        raise ValueError("P1.11 error coverage drift")

    observed = record.get("execution")
    replayed = expected.get("execution")
    if (observed is None) != (replayed is None):
        raise ValueError("P1.11 execution coverage drift")
    if observed is not None:
        for key in ("accepted", "executed", "answer", "error"):
            if observed.get(key) != replayed.get(key):
                raise ValueError("P1.11 execution semantic drift: " + key)

    for key in (
        "extraction_ms", "feasibility_ms", "ir_ms", "lexical_ms",
        "selection_ms", "compile_ms", "routing_ms", "execution_ms",
        "verification_ms", "complete_ms",
    ):
        finite(record.get(key), True)


def replay(directory):
    directory = Path(directory)
    read = lambda name: json.loads((directory / name).read_bytes())
    terminal = read("terminal.json")
    names = {
        path.name for path in directory.glob("*.json")
        if path.name != "terminal.json"
    }
    if names != set(terminal["files"]):
        raise ValueError("P1.11 terminal coverage drift")

    allowed = {"study_started.json", "manifest.json", "core.json", "report.json"}
    allowed.update(
        "task_%02d%s.json" % (index, suffix)
        for index in range(12)
        for suffix in ("", "_started")
    )
    if names - allowed:
        raise ValueError("unexpected P1.11 study member")

    for name, expected_sha in terminal["files"].items():
        path = directory / name
        if Path(name).name != name or path.is_symlink():
            raise ValueError("unsafe P1.11 terminal member")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError("P1.11 receipt byte drift: " + name)

    reg, rows, refs = registration()
    report = read("report.json")
    started = read("study_started.json")
    head = report["source_head"]
    if (
        not re.fullmatch(r"[0-9a-f]{40}", head)
        or started.get("frozen_head") != head
        or started.get("first_only") is not True
    ):
        raise ValueError("P1.11 first source identity drift")

    complete = report["status"] == "COMPLETE"
    records = []
    gap = False
    for index, (row, ref) in enumerate(zip(rows, refs)):
        name = "task_%02d.json" % index
        if name not in names:
            if complete:
                raise ValueError("complete P1.11 result missing task")
            gap = True
            continue
        if gap:
            raise ValueError("noncontiguous P1.11 partial receipts")
        record = read(name)
        marker = read("task_%02d_started.json" % index)
        if (
            record.get("task_id") != row["task_id"]
            or marker.get("task_id") != row["task_id"]
            or marker.get("view_sha256") != digest(row["view"])
        ):
            raise ValueError("P1.11 task identity drift")
        replay_record(row, ref, record)
        records.append(record)

    if complete and "core.json" not in names:
        raise ValueError("complete P1.11 result missing core identity")

    decision = evaluate(
        records,
        refs,
        report["core_audit"].get("unchanged"),
        complete,
        report["whole_study_ms"],
    )
    if (
        decision != report["decision"]
        or terminal["decision"] != decision["verdict"]
        or terminal["complete"] != complete
    ):
        raise ValueError("P1.11 decision drift")
    if report["observations"] != len(records) or report["cost_totals"] != totals(records):
        raise ValueError("P1.11 aggregate cost drift")
    if report.get("accounting_complete") != (
        complete and all(record.get("accounting_complete") is True for record in records)
    ):
        raise ValueError("P1.11 aggregate accounting drift")
    if terminal.get("no_replacement") is not True:
        raise ValueError("replacement P1.11 evidence forbidden")

    for obj in (report, terminal, started):
        for key, value in BOUNDARY.items():
            if obj.get(key) != value:
                raise ValueError("P1.11 boundary drift: " + key)

    for key, value in {
        "frontier_calls": 0,
        "fallback_calls": 0,
        "generated_calls": 0,
        "new_training": False,
        "sealed_data_opened": False,
        "historical_score_reuse": False,
        "p110_task_score_reuse": False,
    }.items():
        if report.get(key) != value:
            raise ValueError("forbidden P1.11 study drift: " + key)

    if complete and report.get("error") is not None:
        raise ValueError("complete P1.11 report hides error")
    if read("manifest.json") != {
        "registration": reg,
        "public_rows": rows,
        "frozen_head": head,
    }:
        raise ValueError("P1.11 manifest drift")

    return {
        "integrity_valid": True,
        "complete": complete,
        "decision": decision,
        "model_inference": False,
        "cost_replayed": True,
        **BOUNDARY,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.directory), sort_keys=True))
