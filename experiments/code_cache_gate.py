"""Measure Direct's exact cache; never rerun the model or claim novelty.

Run only in the original Linux evidence environment. Frozen reference pickle is
the first study's own trusted verification artifact, checked against its manifest
before loading. It is never exposed to the cache or a generator.
"""
import argparse
import hashlib
import json
import multiprocessing
import pickle
import time
from pathlib import Path

from evalplus.eval import untrusted_check
from neumann1.code_cache import ExactCodeCache


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(first, output):
    started = time.perf_counter()
    multiprocessing.set_start_method("spawn", force=True)
    output.mkdir(exist_ok=False)
    manifest = json.loads((first / "archive-manifest.json").read_text())
    for name, expected in manifest.items():
        if sha(first / name) != expected:
            raise ValueError("first evidence identity mismatch: " + name)
    reg = json.loads((first / "registration.json").read_text())
    freeze = json.loads((output.parent / "CODE_CACHE_FREEZE.json").read_text())
    repo = Path(__file__).resolve().parents[1]
    for name, expected in freeze["source_sha256"].items():
        if sha(repo / name) != expected:
            raise ValueError("cache source identity mismatch")
    public = json.loads((first / "public.json").read_text())
    private = json.loads((first / "references.private.json").read_text())
    rows = [json.loads(line) for line in (first / "records.jsonl").read_text().splitlines()]
    if not ([x["task_id"] for x in public] == reg["task_ids"] ==
            [x["task_id"] for x in private] == [x["task_id"] for x in rows]):
        raise ValueError("task alignment mismatch")
    # Load only our hash-verified original canonical-output artifact, not any
    # downloaded arbitrary pickle or model-produced object.
    reference = pickle.loads((first / "reference.private.pkl").read_bytes())
    populate_started = time.perf_counter()
    cache = ExactCodeCache()
    for task, row in zip(public, rows):
        cache.put(task, row["source"])
    populate_seconds = time.perf_counter() - populate_started
    receipts = []
    for task, authority, original in zip(public, private, rows):
        item_started = time.perf_counter()
        source = cache.get(task)
        lookup_seconds = time.perf_counter() - item_started
        if source != original["source"]:
            raise ValueError("not an identical source replay")
        checks = {}
        verify_started = time.perf_counter()
        for group in ("base", "plus"):
            gold = reference[task["task_id"]][group]
            status, details = untrusted_check("humaneval", source,
                authority[group + "_input"], authority["entry_point"],
                expected=gold["expected"], atol=authority["atol"],
                ref_time=gold["reference_times"], fast_check=False)
            checks[group] = {"status": status, "passed_cases": int(sum(details)),
                             "total_cases": len(authority[group + "_input"])}
        row = {"task_id": task["task_id"], "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
               "lookup_seconds": lookup_seconds,
               "verification_seconds": time.perf_counter() - verify_started,
               "complete_seconds": time.perf_counter() - item_started,
               "checks": checks, "joint_correct": all(x["status"] == "pass" for x in checks.values()),
               "same_test_results_as_first": checks == original["checks"]}
        receipts.append(row)
        print(task["task_id"], checks["base"]["status"], checks["plus"]["status"], flush=True)
    if not all(row["same_test_results_as_first"] for row in receipts):
        raise ValueError("independent replay disagreement; do not qualify cache")
    first_setup = json.loads((first / "setup.json").read_text())
    report = {"study": "CODE_CACHE_C0_v1", "status": "COMPLETE",
              "passed": sum(row["joint_correct"] for row in receipts), "total": len(receipts),
              "capability_floor": reg["capability_floor"], "model_calls": 0,
              "population_seconds": populate_seconds,
              "complete_items_seconds": sum(row["complete_seconds"] for row in receipts),
              "study_seconds": time.perf_counter() - started,
              "lookup_seconds": sum(row["lookup_seconds"] for row in receipts),
              "verification_seconds": sum(row["verification_seconds"] for row in receipts),
              "original_population_investment_launcher_seconds": first_setup["launcher_seconds"],
              "first_receipts_sha256": sha(first / "records.jsonl"), "freeze": freeze,
              "scope": "same exact problem replay; ordinary Direct cache, not fresh capability or NEUMANN gain",
              "unknown_cost": ["upstream model training", "energy", "FLOPs", "money", "GPU session allocation and idle", "storage and transfer overhead"]}
    for name, data in (("report.json", report), ("records.json", receipts)):
        (output / name).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.first, args.output)
