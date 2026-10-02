"""Replay first Runtime-0.2 evidence without model inference.

Validates byte-pinned retained evidence and recomputes Decision-1 readiness.
Never loads model weights, generates tokens, executes tools, or edits source bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA = "neumann.general-compact-evidence.v1062.v1"
SOURCE_RUN_ID = 37013632396
SOURCE_TRIGGER_HEAD = "7a47dba21934675e7f6a1c44c67ee9326bd30db3"
SOURCE_EVIDENCE_COMMIT = "0185661132822e7b62c37dc8a24d64ca45af1d75"
ADMISSION_TOKENS = 240
TOOL_ARMS = ("B2", "B3", "N")


def _read(path):
    return json.loads(Path(path).read_text())


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _timeout(record):
    if "TimeoutError" in str(record.get("error")):
        return True
    return any(
        event.get("kind") == "model_result"
        and type(event.get("receipt")) is dict
        and event["receipt"].get("deadline_reached") is True
        for event in record.get("events", [])
    )


def analyze(directory):
    directory = Path(directory)
    terminal = _read(directory / "terminal.json")
    report = _read(directory / "report.json")
    manifest = _read(directory / "manifest.json")

    if terminal.get("complete") is not True:
        raise ValueError("complete first compact evidence required")
    if report.get("observations") != 15 or report.get("expected_observations") != 15:
        raise ValueError("exact fifteen-observation first diagnostic required")
    if manifest.get("frozen_head") != SOURCE_TRIGGER_HEAD:
        raise ValueError("unexpected first-execution trigger head")

    # terminal.json pins every file that existed before terminal.json itself.
    for name, expected in terminal.get("files", {}).items():
        path = directory / name
        if not path.exists() or _sha256(path) != expected:
            raise ValueError("retained evidence byte drift: " + name)

    records = [_read(directory / ("query_%02d.json" % i)) for i in range(15)]
    by_arm = {}
    actual_timeouts = 0
    prompt_admitted = 0
    token_complete = 0
    answers = 0
    checker_reached = 0
    tool_starts = 0
    tool_arm_records = 0
    tool_arm_records_with_tool = 0
    accepted = 0

    for record in records:
        arm = record["arm"]
        row = by_arm.setdefault(
            arm,
            {
                "observations": 0,
                "actual_timeouts": 0,
                "tool_starts": 0,
                "checker_reached": 0,
                "answers_present": 0,
                "accepted": 0,
                "max_prompt_tokens": 0,
            },
        )
        row["observations"] += 1

        timed_out = _timeout(record)
        row["actual_timeouts"] += int(timed_out)
        actual_timeouts += int(timed_out)

        admitted = (
            not record.get("admission_blocked", False)
            and int(record.get("max_prompt_tokens", ADMISSION_TOKENS + 1)) <= ADMISSION_TOKENS
        )
        prompt_admitted += int(admitted)
        token_complete += int(record.get("token_accounting_complete") is True)

        answer_present = record.get("answer") is not None
        row["answers_present"] += int(answer_present)
        answers += int(answer_present)

        checked = any(event.get("kind") == "verification" for event in record.get("events", []))
        row["checker_reached"] += int(checked)
        checker_reached += int(checked)

        starts = sum(event.get("kind") == "tool_start" for event in record.get("events", []))
        row["tool_starts"] += starts
        tool_starts += starts

        row["accepted"] += int(record.get("accepted") is True)
        accepted += int(record.get("accepted") is True)
        row["max_prompt_tokens"] = max(row["max_prompt_tokens"], int(record.get("max_prompt_tokens", 0)))

        if arm in TOOL_ARMS:
            tool_arm_records += 1
            tool_arm_records_with_tool += int(int(record.get("tool_calls", 0)) >= 1)

    primary = {
        "fifteen_queries_complete_without_timeout": len(records) == 15 and actual_timeouts == 0,
        "all_tool_enabled_observations_call_tools": (
            tool_arm_records == 9 and tool_arm_records_with_tool == 9
        ),
        "all_observations_reach_original_checker": checker_reached == 15,
    }
    decision1_pass = all(primary.values())

    return {
        "schema": SCHEMA,
        "source_run_id": SOURCE_RUN_ID,
        "source_trigger_head": SOURCE_TRIGGER_HEAD,
        "source_evidence_commit": SOURCE_EVIDENCE_COMMIT,
        "source_schema": report["schema"],
        "source_status": report["status"],
        "query_count": len(records),
        "actual_timeout_count": actual_timeouts,
        "prompt_admitted_count": prompt_admitted,
        "token_accounting_complete_count": token_complete,
        "answer_present_count": answers,
        "checker_reached_count": checker_reached,
        "tool_start_count": tool_starts,
        "tool_enabled_observation_count": tool_arm_records,
        "tool_enabled_observations_with_tool_calls": tool_arm_records_with_tool,
        "accepted_count": accepted,
        "by_arm": by_arm,
        "decision_1_primary": primary,
        "decision_1": "FAIL" if not decision1_pass else "PASS",
        "general_capability_gate": "NOT_EVALUATED",
        "global_questions_closed": [],
        "new_training": False,
        "frontier_calls": 0,
        "holdout_opened": False,
        "cpu_runtime_mainline": (
            "STOP_MICROTUNING_MOVE_ACCELERATOR" if not decision1_pass else "INTERFACE_READY"
        ),
        "interpretation": (
            "Runtime-0.2 removed native-schema inflation and all fifteen prompts passed the "
            "240-token admission gate, but five observations still timed out, only one of nine "
            "tool-enabled observations executed a tool, and only seven of fifteen reached the "
            "original checker. Under the frozen critical-path contract this ends single-thread "
            "CPU runtime micro-tuning; it is not a General Capability verdict."
        ),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--expect", default=None)
    args = parser.parse_args()

    result = analyze(args.directory)
    text = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if args.expect:
        expected = json.loads(Path(args.expect).read_text())
        if json.loads(text) != expected:
            raise SystemExit("compact evidence replay drift")
    print(text)


if __name__ == "__main__":
    main()
