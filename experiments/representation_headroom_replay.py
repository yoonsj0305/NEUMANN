"""Untimed original-task replay; never changes first results or measured costs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.representation_headroom import digest, execute_batch, package_identity, save, summarize
from neumann1.representation_program import compile_program, validate, verify_original


def interpret_original(program, rows):
    """Independent direct IR interpreter, without normal forms or generated code."""
    validate(program)
    positions = {n: i for i, n in enumerate(program["inputs"])}
    outputs = []
    for row in rows:
        values = []
        for node in program["nodes"]:
            if node[0] == "input":
                value = row[positions[node[1]]]
            elif node[0] == "const":
                value = node[1]
            elif node[0] == "add":
                value = values[node[1]] + values[node[2]]
            else:
                value = values[node[1]] * values[node[2]]
            values.append(value)
        outputs.append(tuple(values[i] for i in program["outputs"]))
    return outputs


def replay(preparation, output, replay_output):
    start = perf_counter()
    registration = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    frozen = json.loads((preparation / "freeze-receipt.json").read_text(encoding="utf-8"))
    receipt = json.loads((preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == frozen["contract_sha256"] == receipt["contract_sha256"]
    assert digest(output / "report.json") == receipt["report_sha256"]
    assert digest(output / "manifest.json") == receipt["manifest_sha256"]
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(output / path) == sha for path, sha in manifest.items())
    assert {str(p.relative_to(output)).replace("\\", "/") for p in output.rglob("*") if p.is_file()} == set(manifest) | {"manifest.json"}
    assert all(package_identity(p) == pin for p, pin in registration["packages"].items())
    root = Path(__file__).resolve().parents[1]
    assert all(digest(root / path) == sha == digest(preparation / "source" / path) for path, sha in registration["sources"].items())
    observations = []
    checked_programs = 0
    checked_observations = 0
    interpreted_rows = 0
    for path in sorted((output / "cases").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        rows = [tuple(row) for row in case["bindings"]]
        expected = interpret_original(case["original"], rows)
        interpreted_rows += len(rows)
        obs_path = output / "observations" / (path.stem + ".jsonl")
        case_observations = [json.loads(line) for line in obs_path.read_text(encoding="utf-8").splitlines()]
        cache = set()
        for observation in case_observations:
            observations.append(observation)
            if not observation["accepted"]:
                continue
            candidate = observation["candidate"]
            identity = json.dumps(candidate, sort_keys=True, separators=(",", ":"))
            if identity not in cache:
                assert verify_original(case["original"], candidate)["accepted"]
                compiled = compile_program(candidate)
                for backend in registration["execution_backends"]:
                    for offset in range(0, len(rows), registration["rows_per_query"]):
                        assert execute_batch(compiled, rows[offset:offset + registration["rows_per_query"]], backend) == expected[offset:offset + registration["rows_per_query"]]
                cache.add(identity)
                checked_programs += 1
            if observation["route"] == "DIRECT":
                assert candidate == case["original"]
            if observation["route"] == "FREE_COMPOSED":
                assert candidate == case["supplied"] and observation["oracle_used"]
            else:
                assert not observation["oracle_used"]
            assert len(observation["query_seconds"]) == registration["actual_reuse_queries"]
            assert not observation["learned"]
            checked_observations += 1
        print(f"Replayed {path.stem}", flush=True)
    events = json.loads((output / "events.json").read_text(encoding="utf-8"))
    recomputed = summarize(registration, observations, events)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert all(report[key] == value for key, value in recomputed.items())
    result = {"status": "PASS", "report_sha256": receipt["report_sha256"],
              "manifest_files_checked": len(manifest), "accepted_observations_rechecked": checked_observations,
              "distinct_case_candidate_programs_rechecked": checked_programs,
              "original_rows_independently_interpreted": interpreted_rows,
              "both_backends_all_bindings_checked": True, "verdict_recomputed": report["decision"],
              "original_results_modified": False, "replay_seconds_not_added_to_measurements": perf_counter() - start}
    replay_output.parent.mkdir(parents=True, exist_ok=True)
    if replay_output.exists():
        raise RuntimeError("Preserve first replay; use a new audit path")
    save(replay_output, result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay-output", type=Path, required=True)
    args = parser.parse_args()
    replay(args.preparation, args.output, args.replay_output)
