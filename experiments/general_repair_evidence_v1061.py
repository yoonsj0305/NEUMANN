"""Replay Runtime-0.1 repair evidence without neural inference.

This module never edits original query/report bytes and never loads model weights.
It validates retained query hashes, recomputes strict timeout classification,
replays only already-emitted final envelopes against original checkers, and fits
an explicitly diagnostic one-token latency proxy on the nine tool-enabled
deadline observations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from experiments.general_development_v106 import boot2_tasks
from neumann1.general_runtime_repair_v1061 import parse_final
from neumann1.general_runtime_v106 import verify_original


SCHEMA = "neumann.general-repair-evidence.v1061.v1"


def _read(path):
    return json.loads(Path(path).read_text())


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _strict_timeout(record):
    if "TimeoutError" in str(record.get("error")):
        return True
    for event in record.get("events", []):
        receipt = event.get("receipt")
        if type(receipt) is dict and receipt.get("deadline_reached") is True:
            return True
    return False


def _parser_api_error(record):
    for event in record.get("events", []):
        receipt = event.get("receipt")
        if type(receipt) is dict and "unexpected keyword argument 'prefix'" in str(receipt.get("parser_error")):
            return True
    return False


def _first_receipt(record):
    for event in record.get("events", []):
        if event.get("kind") == "model_result" and type(event.get("receipt")) is dict:
            return event["receipt"]
    return None


def _linear_fit(points):
    # Ordinary least squares, diagnostic only. x=input tokens, y=generation seconds.
    n = len(points)
    if n < 2:
        return None
    xs = [float(x) for x, _ in points]
    ys = [float(y) for _, y in points]
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    sxx = sum((x - xbar) ** 2 for x in xs)
    if sxx == 0:
        return None
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sxx
    intercept = ybar - slope * xbar
    predicted = [slope * x + intercept for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, predicted))
    ss_tot = sum((y - ybar) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 1.0
    return {
        "points": n,
        "slope_seconds_per_input_token": slope,
        "intercept_seconds": intercept,
        "r2": r2,
        "estimated_input_tokens_at_120s_one_token": (120.0 - intercept) / slope,
        "estimated_input_tokens_at_90s_one_token": (90.0 - intercept) / slope,
        "scope": "same frozen Gemma4 E2B, same GitHub CPU run, tool-enabled observations ending after exactly one generated token; diagnostic proxy, not a scaling law",
    }


def analyze(directory):
    directory = Path(directory)
    terminal = _read(directory / "terminal.json")
    original_report = _read(directory / "report.json")
    if terminal.get("complete") is not True or original_report.get("observations") != 15:
        raise ValueError("complete retained repair diagnostic required")

    # The first terminal receipt is authority for immutable query bytes.
    for name, expected in terminal["files"].items():
        path = directory / name
        if not path.exists() or _sha256(path) != expected:
            raise ValueError("retained evidence byte drift: " + name)

    tasks = {task["id"]: (task, private) for task, private in boot2_tasks()}
    records = [_read(directory / ("query_%02d.json" % i)) for i in range(15)]

    by_arm = {}
    parser_errors = 0
    actual_timeouts = 0
    no_tool_non_timeout = 0
    raw_parseable = 0
    raw_verified = 0
    raw_unparseable = 0
    tool_starts = 0
    one_token_points = []

    for record in records:
        arm = record["arm"]
        timed_out = _strict_timeout(record)
        parser_errors += int(_parser_api_error(record))
        actual_timeouts += int(timed_out)
        tool_starts += sum(event.get("kind") == "tool_start" for event in record.get("events", []))
        row = by_arm.setdefault(arm, {"observations": 0, "actual_timeouts": 0, "parser_api_errors": 0})
        row["observations"] += 1
        row["actual_timeouts"] += int(timed_out)
        row["parser_api_errors"] += int(_parser_api_error(record))

        receipt = _first_receipt(record)
        if receipt and record["arm"] in ("B2", "B3", "N") and receipt.get("output_tokens") == 1 and timed_out:
            one_token_points.append((record["input_tokens"], float(receipt["generation_ms"]) / 1000.0))

        if arm in ("B0", "B1") and not timed_out:
            no_tool_non_timeout += 1
            raw = receipt.get("raw") if receipt else None
            try:
                answer = parse_final(raw)
            except Exception:
                raw_unparseable += 1
                continue
            raw_parseable += 1
            task, private = tasks[record["task_id"]]
            accepted = verify_original(task, answer, private, 2000.0)
            raw_verified += int(accepted)

    fit = _linear_fit(one_token_points)
    return {
        "schema": SCHEMA,
        "source_schema": original_report["schema"],
        "source_status": original_report["status"],
        "source_general_capability_gate": original_report["general_capability_gate"],
        "query_count": len(records),
        "actual_timeout_count": actual_timeouts,
        "processor_parser_api_error_count": parser_errors,
        "tool_start_count": tool_starts,
        "no_tool_non_timeout_count": no_tool_non_timeout,
        "raw_final_parseable_count": raw_parseable,
        "raw_final_unparseable_or_truncated_count": raw_unparseable,
        "raw_final_replay_verified_count": raw_verified,
        "by_arm": by_arm,
        "one_token_latency_proxy": fit,
        "corrected_readiness": {
            "all_observations_complete": len(records) == 15,
            "timeout_free": actual_timeouts == 0,
            "answers_present": False,
            "original_checker_exercised_online": False,
            "tool_enabled_arms_exercised_tools": tool_starts > 0,
            "interface_ready": False,
        },
        "general_capability_gate": "NOT_EVALUATED",
        "global_questions_closed": [],
        "new_training": False,
        "frontier_calls": 0,
        "holdout_opened": False,
        "interpretation": (
            "Runtime-0.1 remains an interface failure. Six no-tool observations finished generation but "
            "were rejected by an incompatible parse_response prefix call; four retained final envelopes "
            "can be replay-parsed and all four fail the original checker, while two coding finals are truncated. "
            "All nine tool-enabled observations exceed the wall gate after emitting only <|tool_call>; "
            "native tool-schema prompt inflation is therefore a measured CPU latency bottleneck."
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
        expected = Path(args.expect).read_text().strip()
        if text != expected:
            raise SystemExit("replay drift")
    print(text)


if __name__ == "__main__":
    main()
