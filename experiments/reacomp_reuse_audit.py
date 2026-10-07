"""Model-free replay and ambiguity certificates; gold programs are diagnosis only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from neumann1.reacomp_adapter import exact_check, normalize, verify_vendor


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(program, text):
    for pattern, replacement in program:
        text = text.replace(pattern, replacement)
    return text


def audit(output: Path) -> dict:
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    for name, expected in report["evidence_sha256"].items():
        if sha(output / name) != expected:
            raise ValueError(f"retained evidence changed: {name}")
    verify_vendor()
    registration = json.loads((output / "registration.json").read_text(encoding="utf-8"))
    tasks = {task["id"]: task for task in json.loads((output / "tasks.private.json").read_text(encoding="utf-8"))}
    records = [json.loads(line) for line in (output / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(records) != 32 or len({(row["task"], row["arm"]) for row in records}) != 32:
        raise ValueError("missing or duplicated paired receipt")
    originals = {}
    for name, spec in registration["datasets"].items():
        path = Path(spec["path"])
        if sha(path) != spec["sha256"]:
            raise ValueError("original dataset changed")
        originals[name] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    certificates = []
    joint_counts = {arm: 0 for arm in registration["arms"]}
    accepted_counts = {arm: 0 for arm in registration["arms"]}
    for row in records:
        task = tasks[row["task"]]
        if row["arm"] not in joint_counts:
            raise ValueError("unregistered arm")
        if row["status"] == "COMPLETE":
            program = normalize(row["program"], task["max_programs"])
            train = exact_check(program, task["training_examples"])
            accepted = train["all_correct"] and row["upstream_reward"] == 1
            joint = accepted and exact_check(program, task["withheld_examples"])["all_correct"]
            if accepted != row["accepted"] or joint != row["joint_correct"]:
                raise ValueError("stored score differs from independent replay")
            accepted_counts[row["arm"]] += int(accepted)
            joint_counts[row["arm"]] += int(joint)
            if accepted and not joint:
                original = originals[task["dataset"]][task["original_index"]]
                gold = normalize(original["original_programs"], task["max_programs"])
                all_examples = task["training_examples"] + task["withheld_examples"]
                if not exact_check(gold, all_examples)["all_correct"]:
                    raise ValueError("original program does not certify original IO")
                witness = next([source, target, apply(program, source)]
                               for source, target in task["withheld_examples"]
                               if apply(program, source) != target)
                certificates.append({"task": task["id"], "arm": row["arm"],
                    "training_program": program, "diagnostic_original_program": gold,
                    "both_fit_all_permitted_examples": True,
                    "withheld_witness": {"input": witness[0], "original_output": witness[1],
                                         "returned_program_output": witness[2]},
                    "scope": "two admissible DSL programs agree on training and disagree on unseen input; no universal inference claim"})
        elif row["accepted"] or row["joint_correct"]:
            raise ValueError("noncomplete row falsely promoted")
    for arm in joint_counts:
        if (joint_counts[arm] != report["arms"][arm]["joint_correct"]
                or accepted_counts[arm] != report["arms"][arm]["training_accepted"]):
            raise ValueError("aggregate replay mismatch")
    result = {"status": "REPLAY_VERIFIED", "records": len(records),
              "independent_counts": {arm: {"training_accepted": accepted_counts[arm],
                                           "joint_correct": joint_counts[arm]} for arm in joint_counts},
              "ambiguity_certificates": certificates,
              "ambiguity_arm_cells": len(certificates),
              "ambiguity_distinct_tasks": len({cert["task"] for cert in certificates}),
              "interpretation": "Provided examples do not uniquely identify target behavior in these certificates. Learned priors may improve expected prediction; neither solver fit nor this audit certifies unseen equivalence.",
              "gold_authority": "offline diagnosis only; never supplied to registered solver or policy"}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = audit(args.output)
    with (args.output / "audit.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "ambiguity_certificates"}, indent=2))
