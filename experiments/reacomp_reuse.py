"""Prepare once, then run a frozen integration screen of reused ReaComp solvers.

Public development data; not fresh generalization, frontier, or novelty evidence.
Only training examples reach the worker. No gold program or heldout feedback.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import platform
from pathlib import Path
import sys
import time

from neumann1.reacomp_adapter import VENDOR, exact_check, solve, verify_vendor


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def write(path: Path, value) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare(external: Path, output: Path) -> None:
    manifest = verify_vendor()
    tasks, datasets = [], {}
    for name, filename, limit in (("lite", "lite_tasks_full_og.jsonl", 5),
                                  ("hard", "tasks_full_og.jsonl", 20)):
        path = external / "data" / "pbebench" / filename
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        datasets[name] = {"path": str(path.resolve()), "sha256": digest(path), "count": len(records)}
        ranked = []
        for index, record in enumerate(records):
            inputs, outputs = record["inputs"], record["outputs"]
            if len(inputs) != len(outputs) or len(inputs) < 5:
                raise ValueError("screen requires at least five matched examples")
            pairs = list(map(list, zip(inputs, outputs)))
            hashed = hashlib.sha256(("NEUMANN-REUSE-R0-v1:" + name + ":" + canonical(pairs)).encode()).hexdigest()
            ranked.append((hashed, index, pairs))
        for hashed, index, pairs in sorted(ranked)[:8]:
            split_at = len(pairs) * 4 // 5
            tasks.append({"id": f"{name}-{index}", "dataset": name, "original_index": index,
                          "selection_sha256": hashed, "max_programs": limit,
                          "training_examples": pairs[:split_at], "withheld_examples": pairs[split_at:]})
    repo = Path(__file__).resolve().parents[1]
    sources = {str(path.relative_to(repo)).replace("\\", "/"): digest(path)
               for path in (repo / "neumann1" / "reacomp_adapter.py", Path(__file__).resolve(),
                            VENDOR / "manifest.json")}
    registration = {"study": "REUSE_R0_v1", "purpose": "reuse integration and public development capability screen",
                    "source_origin": manifest["origin"], "source_revision": manifest["revision"],
                    "datasets": datasets, "source_sha256": sources,
                    "task_count": 16, "arms": ["cc", "qwen"], "timeout_seconds": 8,
                    "selection": "eight lowest salted IO SHA256 per dataset; no outcome selection",
                    "split": "first floor(0.8*n) IO examples to solver; remaining only to independent supervisor",
                    "acceptance": "strict DSL AND independent training exact AND upstream reward=1",
                    "capability_floor": 12,
                    "capability_metric": "accepted training AND all withheld IO correct, out of 16",
                    "order": "alternate arm order by frozen task position",
                    "timeouts": "failure; elapsed plus cleanup charged; no retries",
                    "policy": "qwen first; cc only if qwen training is not accepted; no withheld feedback",
                    "not_claimed": ["paper reproduction", "fresh holdout", "complete induction cost",
                                    "frontier comparison", "NEUMANN gain", "energy", "FLOPs", "money"]}
    output.mkdir(parents=True, exist_ok=False)
    write(output / "registration.json", registration)
    write(output / "tasks.private.json", tasks)
    write(output / "freeze.json", {"registration_sha256": digest(output / "registration.json"),
                                   "tasks_sha256": digest(output / "tasks.private.json")})
    print(f"PREPARED {len(tasks)} tasks; frozen before any solver call", flush=True)


def run(output: Path) -> None:
    freeze = json.loads((output / "freeze.json").read_text(encoding="utf-8"))
    for filename, key in (("registration.json", "registration_sha256"), ("tasks.private.json", "tasks_sha256")):
        if digest(output / filename) != freeze[key]:
            raise ValueError("freeze identity mismatch")
    registration = json.loads((output / "registration.json").read_text(encoding="utf-8"))
    tasks = json.loads((output / "tasks.private.json").read_text(encoding="utf-8"))
    repo = Path(__file__).resolve().parents[1]
    for relative, expected in registration["source_sha256"].items():
        if digest(repo / relative) != expected:
            raise ValueError(f"registered source changed: {relative}")
    verify_vendor()
    started = time.perf_counter()
    rows = []
    with (output / "records.jsonl").open("x", encoding="utf-8") as handle:
        for index, task in enumerate(tasks):
            order = registration["arms"] if index % 2 == 0 else registration["arms"][::-1]
            for arm in order:
                result = solve(arm, task["training_examples"], task["max_programs"], registration["timeout_seconds"])
                checked_at = time.perf_counter()
                withheld = (exact_check(result["program"], task["withheld_examples"])
                            if result.get("accepted") else {"correct": 0, "total": len(task["withheld_examples"]), "all_correct": False})
                verifier_seconds = time.perf_counter() - checked_at
                row = {"task": task["id"], "arm": arm, **result,
                       "withheld_check": withheld, "withheld_verifier_seconds": verifier_seconds,
                       "complete_per_item_seconds": result["elapsed_seconds"] + verifier_seconds,
                       "joint_correct": bool(result.get("accepted") and withheld["all_correct"])}
                rows.append(row)
                handle.write(canonical(row) + "\n")
                handle.flush()
            print(f"{index+1}/{len(tasks)} complete", flush=True)
    arms = {}
    for arm in registration["arms"]:
        arm_rows = [row for row in rows if row["arm"] == arm]
        joint = sum(row["joint_correct"] for row in arm_rows)
        arms[arm] = {"training_accepted": sum(row["accepted"] for row in arm_rows),
                     "joint_correct": joint, "total": len(arm_rows),
                     "statuses": dict(Counter(row["status"] for row in arm_rows)),
                     "complete_seconds": sum(row["complete_per_item_seconds"] for row in arm_rows),
                     "screen_floor_met": joint >= registration["capability_floor"]}
    policy_rows = []
    for task in tasks:
        paired = {row["arm"]: row for row in rows if row["task"] == task["id"]}
        first, second = paired["qwen"], paired["cc"]
        chosen = first if first["accepted"] else second
        # Policy selection depends only on training verification, never withheld correctness.
        policy_rows.append({"task": task["id"], "selected": chosen["arm"],
                            "cc_called": not first["accepted"], "joint_correct": chosen["joint_correct"],
                            "policy_seconds": first["elapsed_seconds"] +
                            (second["elapsed_seconds"] if not first["accepted"] else 0) +
                            chosen["withheld_verifier_seconds"]})
    write(output / "policy.json", policy_rows)
    report = {"study": registration["study"], "status": "COMPLETE", "source_revision": registration["source_revision"],
              "scope": "public development screen with 20% withheld IO; inherited solver training overlap unknown",
              "arms": arms, "registered_policy": {"joint_correct": sum(row["joint_correct"] for row in policy_rows),
                         "total": len(tasks), "fallback_calls": sum(row["cc_called"] for row in policy_rows),
                         "replayed_policy_seconds": sum(row["policy_seconds"] for row in policy_rows),
                         "timing_scope": "derived from paired isolated calls; not a separately timed deployed policy"},
              "study_seconds": time.perf_counter() - started,
              "runtime": {"python": sys.version, "platform": platform.platform()},
              "neural_inference_calls": 0,
              "cost_unknown": ["upstream solver induction and failed attempts", "original training",
                               "acquisition before study", "energy", "FLOPs", "money"],
              "evidence_sha256": {"registration.json": digest(output / "registration.json"),
                                  "tasks.private.json": digest(output / "tasks.private.json"),
                                  "records.jsonl": digest(output / "records.jsonl"),
                                  "policy.json": digest(output / "policy.json")}}
    write(output / "report.json", report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    parser.add_argument("--external", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.external is None:
            parser.error("prepare requires --external")
        prepare(args.external, args.output)
    else:
        run(args.output)
