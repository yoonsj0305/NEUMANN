"""Separate, preregistered CPU headroom screen; never rewrites G0 v1.

One exact-integer polynomial-program domain, not two independent domains.
CAS/public program arms cannot see the supplied factor construction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from neumann1.representation_program import (
    Builder, compile_program, polynomial_forms, sympy_transform, verify_original,
)

ROUTES = ["DIRECT", "CSE", "FACTOR_CSE", "FACTOR_TERMS_CSE", "HORNER_CSE", "FREE_COMPOSED"]
SOURCE_PATHS = ["experiments/representation_headroom.py", "neumann1/representation_program.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def package_identity(name):
    distribution = md.distribution(name)
    record = distribution.read_text("RECORD")
    return {"version": distribution.version,
            "record_sha256": hashlib.sha256(record.encode()).hexdigest()}


def contract():
    return {
        "experiment_id": "G0_COMPOSITION_V1", "status": "PREREGISTERED_BEFORE_GRID",
        "domain_count": 1, "domain": "exact_integer_polynomial_programs",
        "semantics": "unbounded_integer_add_multiply_ordered_outputs",
        "motifs": ["FACTORED", "PATCHED", "CANCELLED"], "degrees": [4, 6, 8],
        "replicas": 2, "cases": 18, "seed_base": 6100600, "input_variables": 4,
        "repetitions": 3, "rows_per_query": 64, "actual_reuse_queries": 64,
        "binding_range_inclusive": [-4, 4], "routes": ROUTES,
        "execution_backends": ["PYTHON_SCALAR", "NUMPY_OBJECT"],
        "strong_envelope": "fastest_correct_route_backend_per_case_median",
        "first_query_cost": "discovery+original_verification+compile+input_scan+execute+original_answer_check",
        "reuse64_cost": "one_discovery_verification_compile+64_actual_scans_execution_checks",
        "oracle_exclusions": ["offline_factor_generation", "global_optimum_not_proven"],
        "primary_two_regimes": ["first_query", "reuse64"],
        "screen_rule": {"geometric_mean_at_least": 10, "largest_degree_at_least_10x": 5,
                        "largest_degree_cases": 6, "all_cases_evaluable": True,
                        "both_regimes_required": True},
        "positive_decision": "ONE_DOMAIN_HEADROOM_ONLY_NOT_G1_ADMISSION",
        "negative_decision": "NO_HEADROOM_ADMISSION_FOR_THIS_REGISTERED_SCOPE",
        "worker_seconds_per_case": 120, "timeout_partial_results_retained": True,
        "worker_startup": "separately_recorded_investment_not_primary_warm_library_ratio",
        "cas_cache": "clear_before_each_fresh_procedure_trial_no_scored_warmup",
        "common_compiler": "DCE_commutative_hash_consing_zero_one_identities",
        "reference": "original_exact_polynomial_evaluation_all_rows_outside_timed_routes",
        "rights": {"originals": "D_OPENED_DEVELOPMENT", "supplied_programs": "O_OFFLINE_UPPER_BOUND_ONLY",
                   "fresh_eligible": 0, "sealed_access": False, "training": False},
        "limitations": ["constructed_programs_only", "matched_Python_and_NumPy_object_backends_only",
                        "no_frontier_or_learned_policy", "no_energy_FLOPs_or_money_measurement",
                        "not_a_global_optimum_or_universal_negative_result", "one_domain_cannot_admit_G1"],
        "sources": {p: digest(ROOT / p) for p in SOURCE_PATHS},
        "packages": {p: package_identity(p) for p in ["sympy", "mpmath", "numpy"]},
        "python": platform.python_version(),
    }


def freeze(directory):
    directory.mkdir(parents=True, exist_ok=False)
    registration = contract()
    save(directory / "preregister.json", registration)
    for path in SOURCE_PATHS:
        target = directory / "source" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    save(directory / "freeze-receipt.json", {
        "experiment_id": registration["experiment_id"], "contract_sha256": digest(directory / "preregister.json"),
        "source_pins": registration["sources"], "performance_grid_run": False,
        "prior_G0_v1": "preserved_unchanged_not_rejudged",
    })
    return registration


def cases(registration):
    for degree in registration["degrees"]:
        for motif in registration["motifs"]:
            for replica in range(registration["replicas"]):
                yield {"id": f"{motif.lower()}_d{degree}_r{replica}", "degree": degree,
                       "motif": motif, "replica": replica,
                       "seed": registration["seed_base"] + degree * 100 + registration["motifs"].index(motif) * 10 + replica}


def make_case(spec, registration):
    rng = random.Random(spec["seed"])
    names = [f"v{i}" for i in range(registration["input_variables"])]
    rng.shuffle(names)
    builder = Builder(names)
    variables = [builder.input(n) for n in names]
    factors = []
    for _ in range(spec["degree"]):
        coefficients = [rng.choice([-2, -1, 1, 2]) for _ in names]
        factors.append(builder.combine("add", [builder.mul(builder.const(c), x) for c, x in zip(coefficients, variables)]))
    factored = builder.combine("mul", factors)
    supplied = builder.finish([factored])
    # Expand the public problem completely; factors/seed/motif stay outside the public API.
    form = polynomial_forms(supplied)[0]
    original_builder = Builder(names)
    xs = [original_builder.input(n) for n in names]
    terms = []
    for powers, coefficient in sorted(form.items()):
        terms.append(original_builder.combine("mul", [original_builder.const(coefficient)] +
                     [xs[i] for i, power in enumerate(powers) for _ in range(power)]))
    output = original_builder.combine("add", terms)
    if spec["motif"] == "PATCHED":
        output = original_builder.add(output, original_builder.mul(xs[0], xs[-1]))
        factored = builder.add(factored, builder.mul(variables[0], variables[-1]))
    elif spec["motif"] == "CANCELLED":
        distraction = original_builder.combine("mul", [original_builder.add(xs[i], xs[(i + 1) % len(xs)])
                                                       for i in range(len(xs))])
        output = original_builder.add(output, original_builder.add(distraction,
                                      original_builder.mul(original_builder.const(-1), distraction)))
    original = original_builder.finish([output])
    supplied = builder.finish([factored])
    rows = [tuple(rng.randint(-4, 4) for _ in names)
            for _ in range(registration["rows_per_query"] * registration["actual_reuse_queries"])]
    return {"original": original, "supplied": supplied, "bindings": rows,
            "lineage": {"structural_family": "polynomial_program", "declared_motif": spec["motif"],
                        "factor_count": spec["degree"], "opened": True, "fresh_eligible": False}}


def reference_answers(original, rows):
    forms = polynomial_forms(original)
    return [tuple(sum(c * math.prod(x**power for x, power in zip(row, powers))
                      for powers, c in form.items()) for form in forms) for row in rows]


def execute_batch(compiled, rows, backend):
    if backend == "PYTHON_SCALAR":
        return compiled.run(rows)
    import numpy as np
    for row in rows:
        if len(row) != compiled.input_count or any(type(x) is not int for x in row):
            raise ValueError("Exact input required")
    columns = np.asarray(rows, dtype=object).T
    result = compiled.function(columns)
    vectors = [v if isinstance(v, np.ndarray) else np.full(len(rows), v, dtype=object) for v in result]
    return list(zip(*(v.tolist() for v in vectors)))


def trial(original, supplied, rows, expected, route, backend, batch_size):
    import sympy as sp
    sp.core.cache.clear_cache()
    start = perf_counter()
    candidate = original if route == "DIRECT" else supplied if route == "FREE_COMPOSED" else sympy_transform(original, route)
    proposal_end = perf_counter()
    proof = verify_original(original, candidate)
    verification_end = perf_counter()
    if not proof["accepted"]:
        raise ValueError("Original-task equivalence failed")
    compiled = compile_program(candidate)
    compile_end = perf_counter()
    query_seconds = []
    for offset in range(0, len(rows), batch_size):
        begin = perf_counter()
        actual = execute_batch(compiled, rows[offset:offset + batch_size], backend)
        if actual != expected[offset:offset + batch_size]:
            raise ValueError("Original answer mismatch")
        query_seconds.append(perf_counter() - begin)
    setup = compile_end - start
    return {"accepted": True, "candidate": candidate, "proof": proof["authority"],
            "discovery_seconds": proposal_end - start, "verification_seconds": verification_end - proposal_end,
            "compile_seconds": compile_end - verification_end, "first_query_seconds": setup + query_seconds[0],
            "reuse64_seconds": setup + sum(query_seconds), "query_seconds": query_seconds,
            "integer_add_calls_per_row": compiled.add_calls, "integer_mul_calls_per_row": compiled.mul_calls,
            "learned": False, "oracle_used": route == "FREE_COMPOSED"}


def worker(reg_path, case_path, observation_path):
    import numpy
    import sympy
    registration = json.loads(Path(reg_path).read_text(encoding="utf-8"))
    case = json.loads(Path(case_path).read_text(encoding="utf-8"))
    rows = [tuple(row) for row in case["bindings"]]
    begin = perf_counter()
    expected = reference_answers(case["original"], rows)
    reference_seconds = perf_counter() - begin
    with Path(observation_path).open("a", encoding="utf-8") as output:
        for repeat in range(registration["repetitions"]):
            # Seeded rotation limits fixed order bias, with no performance-adaptive selection.
            arms = [(route, backend) for route in ROUTES for backend in registration["execution_backends"]]
            random.Random(case["spec"]["seed"] + repeat).shuffle(arms)
            for route, backend in arms:
                start = perf_counter()
                try:
                    value = trial(case["original"], case["supplied"], rows, expected, route, backend,
                                  registration["rows_per_query"])
                except Exception as exc:
                    value = {"accepted": False, "error": f"{type(exc).__name__}: {exc}",
                             "failed_seconds": perf_counter() - start}
                value.update(case_id=case["spec"]["id"], route=route, backend=backend, repetition=repeat,
                             reference_seconds_investment=reference_seconds)
                output.write(json.dumps(value) + "\n"); output.flush()


def summarize(registration, observations, events):
    summaries = []
    for spec in cases(registration):
        group = [o for o in observations if o["case_id"] == spec["id"]]
        metrics = {}
        for regime in ["first_query", "reuse64"]:
            measures = {}
            for route in ROUTES:
                for backend in registration["execution_backends"]:
                    subset = [o for o in group if o["route"] == route and o["backend"] == backend]
                    if len(subset) == registration["repetitions"] and all(o["accepted"] for o in subset):
                        measures[(route, backend)] = statistics.median(o[f"{regime}_seconds"] for o in subset)
            native = {k: v for k, v in measures.items() if k[0] != "FREE_COMPOSED"}
            oracle = {k: v for k, v in measures.items() if k[0] == "FREE_COMPOSED"}
            if native and oracle:
                nk, ok = min(native, key=native.get), min(oracle, key=oracle.get)
                metrics[regime] = {"best_native": list(nk), "best_free": list(ok),
                                   "native_seconds": native[nk], "free_seconds": oracle[ok],
                                   "ratio": native[nk] / oracle[ok]}
        summaries.append({"spec": spec, "metrics": metrics})
    complete = len(observations) == registration["cases"] * len(ROUTES) * 2 * registration["repetitions"] and all(o["accepted"] for o in observations)
    verdicts = {}
    for regime in ["first_query", "reuse64"]:
        ratios = [s["metrics"][regime]["ratio"] for s in summaries if regime in s["metrics"]]
        gm = math.exp(sum(map(math.log, ratios)) / len(ratios)) if ratios else None
        largest = sum(s["metrics"].get(regime, {}).get("ratio", 0) >= 10 for s in summaries
                      if s["spec"]["degree"] == max(registration["degrees"]))
        passed = complete and gm is not None and gm >= 10 and largest >= 5
        verdicts[regime] = {"geometric_mean_ratio": gm, "largest_10x_count": largest, "passed": passed}
    positive = all(v["passed"] for v in verdicts.values())
    return {"experiment_id": registration["experiment_id"], "status": "COMPLETE" if complete else "INCOMPLETE_OR_FAILED",
            "decision": registration["positive_decision"] if positive else registration["negative_decision"] if complete else "NOT_EVALUATED_INCOMPLETE",
            "observations": len(observations), "accepted": sum(o["accepted"] for o in observations),
            "expected_observations": registration["cases"] * len(ROUTES) * 2 * registration["repetitions"],
            "domain_count": 1, "G1_admitted": False, "regimes": verdicts, "cases": summaries,
            "worker_events": events, "limitations": registration["limitations"]}


def run(preparation, output):
    registration = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    receipt = json.loads((preparation / "freeze-receipt.json").read_text(encoding="utf-8"))
    if digest(preparation / "preregister.json") != receipt["contract_sha256"]:
        raise RuntimeError("Contract hash mismatch")
    if any(digest(ROOT / p) != h for p, h in registration["sources"].items()):
        raise RuntimeError("Frozen source changed")
    if any(package_identity(p) != pin for p, pin in registration["packages"].items()):
        raise RuntimeError("Dependency identity changed")
    output.mkdir(parents=True, exist_ok=False)
    (output / "cases").mkdir()
    (output / "observations").mkdir()
    begin = perf_counter()
    events = []
    for spec in cases(registration):
        generation_start = perf_counter()
        value = make_case(spec, registration); value["spec"] = spec
        case_path = output / "cases" / f'{spec["id"]}.json'
        save(case_path, value)
        obs_path = output / "observations" / f'{spec["id"]}.jsonl'
        worker_start = perf_counter()
        try:
            child = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "worker",
                                    "--preparation", str(preparation), "--case", str(case_path), "--observations", str(obs_path)],
                                   timeout=registration["worker_seconds_per_case"], capture_output=True, text=True,
                                   env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
            event = {"case_id": spec["id"], "exit_code": child.returncode, "stderr": child.stderr[-4000:]}
        except subprocess.TimeoutExpired:
            event = {"case_id": spec["id"], "timeout": True}
        event.update(worker_wall_seconds=perf_counter() - worker_start,
                     generation_storage_seconds_investment=worker_start - generation_start)
        events.append(event)
        save(output / "events.json", events)
        print(json.dumps(event), flush=True)
    observations = []
    for path in sorted((output / "observations").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            observations.append(json.loads(line))
    result = summarize(registration, observations, events)
    result["whole_study_wall_seconds"] = perf_counter() - begin
    result["contract_sha256"] = digest(preparation / "preregister.json")
    save(output / "report.json", result)
    save(output / "manifest.json", {str(p.relative_to(output)).replace("\\", "/"): digest(p)
                                    for p in sorted(output.rglob("*")) if p.is_file() and p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"),
         "manifest_sha256": digest(output / "manifest.json"), "contract_sha256": result["contract_sha256"]})
    print(json.dumps({k: result[k] for k in ["status", "decision", "observations", "accepted", "regimes", "whole_study_wall_seconds"]}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run", "worker"])
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.preparation)
        print(digest(args.preparation / "preregister.json"))
    elif args.mode == "run":
        run(args.preparation, args.output)
    else:
        worker(args.preparation / "preregister.json", args.case, args.observations)


if __name__ == "__main__":
    main()
