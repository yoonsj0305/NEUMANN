"""Reconstruct the original full-cost gate and independently verify all outputs."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.inductive_complete_cost import summarize
from experiments.inductive_cost_cases import make_case
from experiments.inductive_perspective_replay import independently_check, interpret
from neumann1.inductive_perspective import check_perspective


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def replay(preparation, first, output):
    reg, receipt = read(preparation/"preregister.json"), read(preparation/"first-result-receipt.json")
    assert digest(preparation/"preregister.json") == read(preparation/"freeze-receipt.json")["contract_sha256"]
    assert digest(first/"report.json") == receipt["report_sha256"] and digest(first/"manifest.json") == receipt["manifest_sha256"]
    manifest = read(first/"manifest.json")
    assert all(digest(first/path) == pin for path, pin in manifest.items())
    assert all(digest(ROOT/path) == pin and digest(preparation/"source"/path) == pin for path, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    report, events = read(first/"report.json"), read(first/"events.json")
    reconstructed = summarize(events, reg)
    assert all(report[key] == value for key, value in reconstructed.items())
    cases, index = {}, 0
    for degree in reg["degrees"]:
        for shear in reg["shears"]:
            identifier = f"d{degree}_m{shear}"
            problem, proposal, requests, expected, lineage = make_case(degree, shear, reg["seed_base"]+index)
            assert read(first/"public"/(identifier+".json")) == problem
            assert read(first/"requests"/(identifier+".json")) == requests
            # JSON object keys are strings; the producer's degree-indexed
            # coefficient mapping uses integers before serialization.
            rebuilt_oracle = json.loads(json.dumps({"proposal": proposal, "expected": expected, "lineage": lineage}))
            assert read(first/"oracle"/(identifier+".json")) == rebuilt_oracle
            assert all(independently_check(problem, proposal).values())
            cases[identifier] = {"problem": problem, "reference": proposal, "requests": requests, "expected": expected}
            index += 1
    audited_proposals, numeric, certified_workers, failed, short_original = set(), 0, 0, [], 0
    for event in events:
        identifier, count, rep, route = [event[k] for k in ["case_id", "count", "repetition", "route"]]
        folder = first/"runs"/f"{identifier}_n{count}_r{rep}_{route}"
        case = cases[identifier]
        if not event["accepted"]:
            certificate_file = folder/"certificate.json"
            if certificate_file.exists():
                stored = read(certificate_file)
                actual = check_perspective(case["problem"], read(folder/"proposal.json"))
                assert stored["accepted"] is False and actual["accepted"] is False
                assert stored["status"] == actual["status"] and stored.get("error") == actual.get("error")
            failed.append({"case_id": identifier, "route": route, "count": count, "repetition": rep,
                           "exit_code": event.get("exit_code"), "timeout": event.get("timeout", False),
                           "recorded_cost_seconds": event["complete_operational_seconds"],
                           "certificate_status": read(certificate_file)["status"] if certificate_file.exists() else None})
            continue
        result = read(folder/"result.json")
        assert result["route"] == route and result["count"] == count and len(result["queries"]) == count
        rows = [json.loads(line) for line in (folder/"queries.jsonl").read_text(encoding="utf-8").splitlines()]
        assert rows == result["queries"]
        assert event["build_seconds"] == result["build_seconds"] and event["complete_operational_seconds"] >= result["process_entry_to_saved_queries_seconds"]
        if route != "COMPILED_DIRECT":
            identity = (identifier, digest(folder/"proposal.json"))
            if identity not in audited_proposals:
                assert all(independently_check(case["problem"], read(folder/"proposal.json")).values())
                audited_proposals.add(identity)
            assert read(folder/"certificate.json")["accepted"]
            certified_workers += 1
        for query in rows:
            j = query["index"]
            request = case["requests"][j]
            assert query["parameters"] == request["parameters"] and query["steps"] == request["steps"]
            params, steps = query["parameters"], query["steps"]
            z = interpret(case["reference"]["closed_form"], params+[steps])
            reference = interpret(case["reference"]["decode"], params+z)
            assert query["actual"] == case["expected"][j] == reference
            numeric += 1
    # Original-spec interpretation is independent of compiled direct execution.
    # Universal induction plus exact closed DAG evaluation checks all large queries.
    for case in cases.values():
        for request in case["requests"][:3]:
            params = request["parameters"]
            for steps in [0, 1, 7]:
                current = interpret(case["problem"]["initial"], params)
                for _ in range(steps):
                    current = interpret(case["problem"]["transition"], params+current)
                original = interpret(case["problem"]["goal"], params+current)
                z = interpret(case["reference"]["closed_form"], params+[steps])
                assert original == interpret(case["reference"]["decode"], params+z)
                short_original += 1
    assert numeric == report["accepted_actual_queries"] and len(failed) == report["failed_workers"]
    assert not report["G1_admitted"] and report["fresh_eligible"] == 0
    output.mkdir(parents=True, exist_ok=False)
    save(output/"replay.json", {"status": "PASS_ORIGINAL_OPERATIONAL_COST_AND_CORRECTNESS",
         "manifest_files_checked": len(manifest), "constructed_cases_rebuilt": len(cases), "distinct_accepted_proposals_independently_verified": len(audited_proposals),
         "certified_workers": certified_workers, "timed_query_outputs_independently_verified": numeric,
         "short_original_spec_interpretations": short_original, "failed_workers_retained": failed,
         "report_reconstructed_without_retuning": True, "original_report_sha256": digest(first/"report.json"),
         "original_manifest_sha256": digest(first/"manifest.json"), "G1_admitted": False})
    print((output/"replay.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    replay(*(Path(p) for p in sys.argv[1:]))
