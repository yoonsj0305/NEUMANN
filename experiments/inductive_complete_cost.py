"""Frozen operational CPU cost screen, with equally capable public native synthesis.

Free provided coordinates are a diagnostic, never learned discovery. Includes
process startup, reads, synthesis/check/compile, actual requests, output writes
and parent's original-answer comparisons. Offline construction/research costs
remain separate/UNKNOWN; this is not full project cost or G1/G2 admission.
"""
from time import perf_counter
BOOT = perf_counter()
import argparse
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.inductive_cost_cases import make_case
from neumann1.inductive_perspective import CertifiedAcceleration, check_perspective, validate_problem
from neumann1.inductive_symbolic_baseline import state_closure
from neumann1.polynomial_translation_native import propose
from neumann1.representation_program import compile_program, sympy_transform

ROUTES = ["COMPILED_DIRECT", "PUBLIC_INTEGER_NATIVE", "PUBLIC_CAS_FACTOR", "FREE_COORDINATES"]
SOURCES = ["experiments/inductive_complete_cost.py", "experiments/inductive_cost_cases.py",
           "neumann1/polynomial_translation_native.py", "neumann1/inductive_perspective.py",
           "neumann1/inductive_symbolic_baseline.py", "neumann1/representation_program.py",
           "experiments/representation_headroom.py"]


def freeze(preparation):
    preparation.mkdir(parents=True, exist_ok=False)
    reg = {"experiment_id": "INDUCTIVE_COMPLETE_COST_V1", "degrees": [2, 4, 6], "shears": [-2, 3], "seed_base": 8127000,
           "cases": 6, "repetitions": 3, "reuse_counts": [1, 16], "routes": ROUTES, "worker_deadline_seconds": 15,
           "primary": "parent subprocess launch through exit, all request outputs loaded and compared with registered exact answers",
           "original_checker": "exact full integer output comparison, candidate universal induction proof additionally mandatory",
           "native_rights": "public spec only; known integer cancellation/antidifference, same induction checker/compiler/procedure reuse; optional CAS factor/CSE",
           "direct_rights": "goal dependency closure removes irrelevant state; compiler DCE/CSE; initial/transition/goal compilation once per process; validated integer inputs",
           "free_rights": "provided proposal read inside request; original-task certificate recomputed inside process; only offline discovery omitted",
           "reuse": "same public program,16 actual distinct parameters/horizons; both native and free compile once",
           "baseline_qualification": "all3 repetitions complete all actual requests in the reuse regime; all answers correct; fastest qualified native median",
           "rule": {"geometric_mean_at_least": 10, "individual_at_least_10x": 5, "case_count": 6, "both_regimes_required": True, "all_cases_evaluable": True},
           "positive": "ONE_DOMAIN_OPERATIONAL_HEADROOM_ONLY_NOT_G1_ADMISSION",
           "negative": "NO_10X_OPERATIONAL_HEADROOM_IN_REGISTERED_SCOPE", "incomplete": "INCOMPLETE_NO_ADMISSION",
           "offline_cost": "case/answer/proposal construction excluded and separately timed; research and any future learning investments UNKNOWN,never zero",
           "resource_axis": "CPU process wall seconds,not FLOPs,energy,money or actual peak memory",
           "fresh_eligible": 0, "independent_domains": 1, "G1_admitted": False, "GPU_or_learning": False,
           "sources": {p: digest(ROOT / p) for p in SOURCES}, "packages": {p: package_identity(p) for p in ["sympy", "mpmath"]}}
    save(preparation / "preregister.json", reg)
    for path in SOURCES:
        copy = preparation / "source" / path
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes((ROOT / path).read_bytes())
    save(preparation / "freeze-receipt.json", {"contract_sha256": digest(preparation / "preregister.json"), "performance_started": False})
    print(digest(preparation / "preregister.json"), flush=True)


def worker(public_file, oracle_file, requests_file, route, count, output):
    output.mkdir(parents=True, exist_ok=False)
    problem = json.loads(public_file.read_text(encoding="utf-8"))
    requests = json.loads(requests_file.read_text(encoding="utf-8"))[:count]
    validate_problem(problem)
    progress = {"route": route, "count": count, "phase": "public input loaded", "entry_seconds": perf_counter()-BOOT,
                "learned": False, "oracle_used": route == "FREE_COORDINATES"}
    save(output / "progress.json", progress)
    build_start = perf_counter()
    if route == "COMPILED_DIRECT":
        retained = state_closure(problem)
        positions = [problem["state"].index(v) for v in retained]
        initial = compile_program(problem["initial"])
        transition = compile_program({**problem["transition"], "outputs": [problem["transition"]["outputs"][i] for i in positions]})
        goal = compile_program(problem["goal"])
        progress["retained_state"] = retained
        progress["original_transition_arithmetic_calls"] = transition.add_calls + transition.mul_calls
        def solve(params, steps):
            current = list(initial.run([tuple(params)])[0])
            for _ in range(steps):
                update = transition.function(tuple(params)+tuple(current))
                for i, value in zip(positions, update):
                    current[i] = value
            return goal.run([tuple(params)+tuple(current)])[0]
    else:
        if route == "FREE_COORDINATES":
            proposal = json.loads(oracle_file.read_text(encoding="utf-8"))["proposal"]
        else:
            proposal = propose(problem)
            if route == "PUBLIC_CAS_FACTOR":
                proposal = {key: sympy_transform(value, "FACTOR_CSE") for key, value in proposal.items()}
        progress["phase"] = "proposal generated, checking"
        save(output / "proposal.json", proposal)
        save(output / "progress.json", progress)
        certificate = check_perspective(problem, proposal)
        save(output / "certificate.json", certificate)
        assert certificate["accepted"], "Unverified proposal cannot bypass original execution"
        engine = CertifiedAcceleration(len(problem["parameters"]), compile_program(proposal["closed_form"]), compile_program(proposal["decode"]), certificate)
        solve = engine.run
    progress["build_seconds"] = perf_counter()-build_start
    progress["phase"] = "engine ready"
    save(output / "progress.json", progress)
    rows = []
    with (output / "queries.jsonl").open("w", encoding="utf-8") as stream:
        for index, request in enumerate(requests):
            params, steps = request["parameters"], request["steps"]
            start = perf_counter()
            assert len(params) == len(problem["parameters"]) and all(type(p) is int for p in params) and type(steps) is int and steps >= 0
            actual = solve(params, steps)
            row = {"index": index, "parameters": params, "steps": steps, "actual": list(actual), "request_seconds": perf_counter()-start}
            stream.write(json.dumps(row)+"\n")
            stream.flush()
            rows.append(row)
    save(output / "result.json", {"route": route, "count": count, "queries": rows, "process_entry_to_saved_queries_seconds": perf_counter()-BOOT,
                                  "build_seconds": progress["build_seconds"], "learned": False, "oracle_used": route == "FREE_COORDINATES"})


def summarize(events, reg):
    import math
    regimes = {}
    for count in reg["reuse_counts"]:
        case_rows = []
        for identifier in sorted({e["case_id"] for e in events}):
            qualified = {}
            for route in reg["routes"]:
                rows = [e for e in events if e["case_id"] == identifier and e["route"] == route and e["count"] == count and e["accepted"]]
                if len(rows) == reg["repetitions"]:
                    qualified[route] = statistics.median(e["complete_operational_seconds"] for e in rows)
            complete = "FREE_COORDINATES" in qualified and any(r != "FREE_COORDINATES" for r in qualified)
            row = {"case_id": identifier, "complete": complete, "route_median_seconds": qualified}
            if complete:
                native = min((r for r in qualified if r != "FREE_COORDINATES"), key=qualified.get)
                row.update(best_native=native, native_over_free=qualified[native]/qualified["FREE_COORDINATES"],
                           direct_over_free=qualified.get("COMPILED_DIRECT", 0)/qualified["FREE_COORDINATES"] if "COMPILED_DIRECT" in qualified else None)
            case_rows.append(row)
        ratios = [c["native_over_free"] for c in case_rows if c["complete"]]
        complete = len(case_rows) == reg["cases"] and len(ratios) == reg["cases"]
        geometric = math.exp(sum(map(math.log, ratios))/len(ratios)) if complete else None
        wins = sum(r >= 10 for r in ratios)
        regimes[str(count)] = {"cases": case_rows, "all_evaluable": complete, "geomean_native_over_free": geometric,
                               "individual_10x_count": wins, "passed": complete and geometric >= 10 and wins >= 5}
    decision = reg["positive"] if all(r["passed"] for r in regimes.values()) else reg["negative"] if all(r["all_evaluable"] for r in regimes.values()) else reg["incomplete"]
    return {"experiment_id": reg["experiment_id"], "decision": decision, "regimes": regimes,
            "worker_observations": len(events), "accepted_workers": sum(e["accepted"] for e in events),
            "accepted_actual_queries": sum(e.get("actual_queries", 0) for e in events if e["accepted"]),
            "failed_workers": sum(not e["accepted"] for e in events), "G1_admitted": False, "fresh_eligible": 0,
            "scope": "one-domain constructed-development operational free-coordinate ceiling,not learned NEUMANN or complete R&D investment"}


def run(preparation, output):
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    output.mkdir(parents=True, exist_ok=False)
    for sub in ["public", "oracle", "requests", "runs"]:
        (output/sub).mkdir()
    start = perf_counter()
    begin_construction = perf_counter()
    cases = []
    for degree in reg["degrees"]:
        for shear in reg["shears"]:
            identifier = f"d{degree}_m{shear}"
            problem, proposal, requests, expected, lineage = make_case(degree, shear, reg["seed_base"]+len(cases))
            save(output / "public" / (identifier+".json"), problem)
            save(output / "oracle" / (identifier+".json"), {"proposal": proposal, "expected": expected, "lineage": lineage})
            save(output / "requests" / (identifier+".json"), requests)
            cases.append(identifier)
    save(output / "construction.json", {"seconds": perf_counter()-begin_construction, "upstream_research_investment": "UNKNOWN", "learning_investment": "NOT_PERFORMED"})
    tasks = [(identifier, count, rep, route) for identifier in cases for count in reg["reuse_counts"] for rep in range(reg["repetitions"]) for route in reg["routes"]]
    random.Random(8127499).shuffle(tasks)
    events = []
    for identifier, count, rep, route in tasks:
        target = output / "runs" / f"{identifier}_n{count}_r{rep}_{route}"
        oracle = output / "oracle" / (identifier+".json")
        expected = json.loads(oracle.read_text(encoding="utf-8"))["expected"][:count]
        begin = perf_counter()
        event = {"case_id": identifier, "count": count, "repetition": rep, "route": route, "accepted": False}
        try:
            child = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "worker",
                "--public", str(output/"public"/(identifier+".json")), "--oracle", str(oracle),
                "--requests", str(output/"requests"/(identifier+".json")), "--route", route,
                "--count", str(count), "--output", str(target)], capture_output=True, text=True,
                timeout=reg["worker_deadline_seconds"], env={**os.environ, "PYTHONHASHSEED": "0"})
            event.update(exit_code=child.returncode, stderr=child.stderr[-2000:])
            if child.returncode == 0:
                result = json.loads((target/"result.json").read_text(encoding="utf-8"))
                actual = [q["actual"] for q in result["queries"]]
                event.update(accepted=len(actual)==count and actual==expected, actual_queries=len(actual), build_seconds=result["build_seconds"])
        except subprocess.TimeoutExpired:
            event["timeout"] = True
        event["complete_operational_seconds"] = perf_counter()-begin
        events.append(event)
        save(output / "events.json", events)
        print(json.dumps({k: event[k] for k in ["case_id", "count", "repetition", "route", "accepted", "complete_operational_seconds"]}), flush=True)
    report = summarize(events, reg)
    report.update(whole_study_wall_seconds=perf_counter()-start, contract_sha256=digest(preparation/"preregister.json"))
    save(output/"report.json", report)
    save(output/"manifest.json", {str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    save(preparation/"first-result-receipt.json", {"report_sha256": digest(output/"report.json"), "manifest_sha256": digest(output/"manifest.json")})
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze", "run", "worker"])
    for name in ["preparation", "output", "public", "oracle", "requests"]:
        p.add_argument("--"+name, type=Path)
    p.add_argument("--route", choices=ROUTES)
    p.add_argument("--count", type=int)
    args = p.parse_args()
    if args.mode == "freeze":
        freeze(args.preparation)
    elif args.mode == "run":
        run(args.preparation, args.output)
    else:
        worker(args.public, args.oracle, args.requests, args.route, args.count, args.output)
