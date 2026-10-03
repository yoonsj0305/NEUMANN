"""Model-free integrity replay for completed AM1 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from experiments.general_multiplier_first import _arm_result
from experiments.general_multiplier_tasks import TASK_SHA256
from neumann1.general_multiplier_contract import ARMS, MultiplierBudget, evaluate_multiplier
from neumann1.general_runtime_v106 import canonical, sha

SCHEMA = "neumann.am1-evidence-replay.v1"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_terminal_hashes(directory, terminal):
    directory = Path(directory)
    files = terminal.get("files")
    if type(files) is not dict:
        raise ValueError("terminal file hash map required")
    mismatches = {}
    for name, expected in files.items():
        path = directory / name
        actual = _hash(path) if path.is_file() else None
        if actual != expected:
            mismatches[name] = {"expected": expected, "actual": actual}
    return mismatches


def replay(directory):
    directory = Path(directory)
    terminal = _load(directory / "terminal.json")
    report = _load(directory / "report.json")
    manifest = _load(directory / "manifest.json")
    core = _load(directory / "core.json")

    mismatches = verify_terminal_hashes(directory, terminal)
    query_paths = sorted(
        path for path in directory.glob("query_??.json")
        if not path.name.endswith("_started.json")
    )
    records = [_load(path) for path in query_paths]

    budget_sha = sha(asdict(MultiplierBudget()))
    core_sha = sha(core)
    arm_results = {}
    if len(records) == 36:
        for arm in ARMS:
            rows = [row for row in records if row.get("arm") == arm]
            arm_results[arm] = _arm_result(arm, rows, core_sha, budget_sha)

    recomputed = None
    replay_error = None
    try:
        if len(records) != 36:
            raise ValueError("exactly 36 terminal observations required")
        if manifest.get("task_sha256") != TASK_SHA256:
            raise ValueError("frozen task identity mismatch")
        if report.get("core_sha256") != core_sha:
            raise ValueError("core identity mismatch")
        if mismatches:
            raise ValueError("terminal file hash mismatch")
        recomputed = evaluate_multiplier(arm_results)
    except Exception as exc:
        replay_error = type(exc).__name__ + ": " + str(exc)

    report_decision = report.get("decision_2")
    terminal_decision = terminal.get("decision_2")
    exact_decision_match = (
        recomputed is not None
        and report_decision == recomputed
        and terminal_decision == recomputed.get("verdict")
    )
    valid = bool(
        replay_error is None
        and report.get("status") == "COMPLETE"
        and terminal.get("complete") is True
        and exact_decision_match
    )

    return {
        "schema": SCHEMA,
        "valid": valid,
        "directory": str(directory),
        "observation_count": len(records),
        "terminal_hash_mismatches": mismatches,
        "task_sha256": manifest.get("task_sha256"),
        "core_sha256": core_sha,
        "budget_sha256": budget_sha,
        "arm_results": arm_results,
        "recomputed_decision_2": recomputed,
        "reported_decision_2": report_decision,
        "terminal_decision_2": terminal_decision,
        "exact_decision_match": exact_decision_match,
        "error": replay_error,
        "model_inference_performed": False,
        "sealed_holdout_opened": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = replay(args.directory)
    payload = canonical(result)
    print(payload)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    raise SystemExit(0 if result["valid"] else 2)


if __name__ == "__main__":
    main()
