"""Independent model-free replay of first P1.7 opened-development receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from neumann1.control_plane_v1 import digest, finite, snapshot
from neumann1.control_plane_p17 import interpret_and_execute
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p17_dev import evaluate, totals
from experiments.control_plane_p17_registration import registration, BOUNDARY


class RecordedSelector:
    def __init__(self, receipt):
        self.receipt = snapshot(receipt)

    def score(self, view, bundle, remaining_ms):
        return snapshot(self.receipt)


def replay_record(row, ref, record):
    if ref["semantic_path"] == "UNIQUE":
        def forbidden():
            raise AssertionError("unique replay must not construct selector")
        expected = interpret_and_execute(
            row["view"], _executor, _hidden_verifier(ref), forbidden
        )
    else:
        receipt = record.get("selector_receipt")
        if type(receipt) is not dict:
            if record.get("accounting_complete") is False and record.get("accepted") is False:
                # A retained selector/core startup failure cannot be reconstructed
                # model-free. It remains a non-admissible first-result failure.
                if record.get("tool_calls") != 0 or record.get("verifier_calls") != 0:
                    raise ValueError("unreplayable selector failure cannot conceal authority calls")
                return
            raise ValueError("ambiguous item missing selector receipt")
        expected = interpret_and_execute(
            row["view"], _executor, _hidden_verifier(ref),
            lambda: RecordedSelector(receipt),
        )

    keys = (
        "schema", "status", "accepted", "executed", "original_view_sha256",
        "selected_candidate", "selected_route", "model_calls",
        "neural_forward_calls", "generated_calls", "evaluated_tokens",
        "padded_tokens", "tool_calls", "verifier_calls", "accounting_complete",
        "bundle", "selection", "selector_receipt", "proposal", "execution",
    )
    for key in keys:
        if record.get(key) != expected.get(key):
            raise ValueError("P1.7 semantic replay drift: " + key)
    if bool(record.get("error")) != bool(expected.get("error")):
        raise ValueError("P1.7 failure explanation coverage drift")
    for key in (
        "extraction_ms", "selection_ms", "compile_ms", "routing_ms",
        "execution_ms", "verification_ms", "complete_ms",
    ):
        finite(record.get(key), True)


def replay(directory):
    directory = Path(directory)
    read = lambda name: json.loads((directory / name).read_bytes())
    terminal = read("terminal.json")

    names = {p.name for p in directory.glob("*.json") if p.name != "terminal.json"}
    if names != set(terminal["files"]):
        raise ValueError("P1.7 terminal coverage drift")

    allowed = {"study_started.json", "manifest.json", "core.json", "report.json"}
    allowed.update(
        "task_%02d%s.json" % (i, suffix)
        for i in range(12)
        for suffix in ("", "_started")
    )
    if names - allowed:
        raise ValueError("unexpected P1.7 study member")

    for name, expected in terminal["files"].items():
        path = directory / name
        if Path(name).name != name or path.is_symlink():
            raise ValueError("unsafe terminal member")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("P1.7 receipt byte drift: " + name)

    reg, rows, refs = registration()
    report = read("report.json")
    started = read("study_started.json")
    head = report["source_head"]
    if (
        not re.fullmatch(r"[0-9a-f]{40}", head)
        or started.get("frozen_head") != head
        or started.get("first_only") is not True
    ):
        raise ValueError("P1.7 first source identity drift")

    if report["status"] not in ("COMPLETE", "INCOMPLETE"):
        raise ValueError("unknown P1.7 terminal status")
    complete = report["status"] == "COMPLETE"
    records = []
    gap = False
    for i, (row, ref) in enumerate(zip(rows, refs)):
        name = "task_%02d.json" % i
        if name not in names:
            if complete:
                raise ValueError("complete P1.7 result missing task receipt")
            gap = True
            continue
        if gap:
            raise ValueError("noncontiguous P1.7 partial receipt coverage")

        record = read(name)
        marker = read("task_%02d_started.json" % i)
        if (
            record.get("task_id") != row["task_id"]
            or record.get("kind") != ref["kind"]
            or record.get("semantic_path") != ref["semantic_path"]
            or marker != {"task_id": row["task_id"], "view_sha256": digest(row["view"])}
        ):
            raise ValueError("P1.7 task/started identity drift")
        replay_record(row, ref, record)
        records.append(record)

    if complete and "core.json" not in names:
        raise ValueError("complete P1.7 result missing frozen core identity")

    decision = evaluate(
        records, refs, report["core_audit"].get("unchanged"),
        complete, report["whole_study_ms"],
    )
    if (
        decision != report["decision"]
        or terminal["decision"] != decision["verdict"]
        or terminal["complete"] != complete
    ):
        raise ValueError("P1.7 decision/terminal drift")
    if report["observations"] != len(records) or report["cost_totals"] != totals(records):
        raise ValueError("P1.7 aggregate cost drift")
    if report.get("accounting_complete") != (
        complete and all(r.get("accounting_complete") is True for r in records)
    ):
        raise ValueError("P1.7 aggregate accounting drift")
    if terminal.get("no_replacement") is not True:
        raise ValueError("P1.7 replacement evidence forbidden")

    for obj in (report, terminal, started):
        for key, value in BOUNDARY.items():
            if obj.get(key) != value:
                raise ValueError("P1.7 study boundary drift: " + key)

    for key, value in {
        "frontier_calls": 0,
        "fallback_calls": 0,
        "new_training": False,
        "sealed_data_opened": False,
        "historical_score_reuse": False,
    }.items():
        if report.get(key) != value:
            raise ValueError("P1.7 forbidden-study drift: " + key)

    if complete and report.get("error") is not None:
        raise ValueError("completed P1.7 report cannot hide run error")

    if "manifest.json" in names:
        manifest = read("manifest.json")
        if manifest != {
            "registration": reg,
            "public_rows": rows,
            "frozen_head": head,
        }:
            raise ValueError("P1.7 frozen manifest drift")
    elif complete:
        raise ValueError("complete P1.7 result missing manifest")

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
