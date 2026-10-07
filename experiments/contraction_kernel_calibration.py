"""Opened-structure CPU calibration; no original benchmark or G1 admission."""
import argparse
import json
import math
import random
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from neumann1.contraction_structure import certify_path, public_plan
from neumann1.cotengra_baseline import plan

SOURCES = ["experiments/contraction_kernel_calibration.py", "neumann1/contraction_structure.py",
           "neumann1/cotengra_baseline.py", "experiments/representation_headroom.py"]
ROUTES = ["CACHED_NATIVE_BEST", "PUBLIC_GREEDY", "PUBLIC_AUTO_HQ", "PUBLIC_RECONF32", "FREE_PUBLISHED"]


def agreement(actual, expected, tolerance=1e-10):
    import numpy as np
    a, b = np.asarray(actual), np.asarray(expected)
    return bool(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
                and np.all(b > 0) and np.allclose(a, b, rtol=tolerance, atol=0))


def freeze(preparation, case_path, native_path):
    preparation.mkdir(parents=True, exist_ok=False)
    case = json.loads(case_path.read_text(encoding="utf-8"))
    # Selection depends on already opened structural models, never kernel timing.
    supplied = min(case["supplied_paths"], key=lambda k: certify_path(case["public"], case["supplied_paths"][k]["path"])["dense_arithmetic_work_model"])
    registration = {"experiment_id": "OPENED_CONTRACTION_CPU_CALIBRATION_V1", "case_id": case["id"],
        "case_path": str(case_path), "case_sha256": digest(case_path), "native_path": str(native_path),
        "native_sha256": digest(native_path), "supplied_label": supplied, "routes": ROUTES,
        "repetitions": 3, "query_seeds": [6100801, 6100802, 6100803], "dtype": "float64",
        "synthetic_values": "independent uniform [0.5,1.5]; published shapes, original arrays unavailable",
        "BLAS_threads": 1, "relative_tolerance": 1e-10, "absolute_tolerance": 0,
        "reference": "full-output agreement of two supplied independently certified paths; no independent original dataset answers",
        "cache_rights": "all routes reuse their compiled path across three actual different-value queries",
        "cached_native_investment": "prior full six-plan challenge remains recorded separately; not silently free",
        "first_cost": "discovery or cached artifact read+hash, index certificate, expression compilation, input scan, kernel, full-output check",
        "three_query_cost": "one setup plus all three actual input scans, kernels and checks",
        "budgets": {"input_bytes": 64 * 2**20, "largest_intermediate_bytes": 256 * 2**20, "modeled_work": 20_000_000_000},
        "excluded_investments_separate": ["imports/cold start", "input generation", "reference execution", "prior native search", "published path research"],
        "energy_or_actual_RSS_measured": False, "fresh_eligible": False, "G1_admitted": False,
        "learning_or_GPU": False, "sources": {p: digest(ROOT / p) for p in SOURCES},
        "packages": {p: package_identity(p) for p in ["numpy", "opt_einsum", "cotengra", "autoray", "threadpoolctl"]}}
    save(preparation / "preregister.json", registration)
    for p in SOURCES:
        destination = preparation / "source" / p
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / p).read_bytes())
    save(preparation / "freeze-receipt.json", {"contract_sha256": digest(preparation / "preregister.json"), "kernel_performance_run": False})
    print(digest(preparation / "preregister.json"), flush=True)


def run(preparation, output):
    import numpy as np
    import opt_einsum as oe
    from threadpoolctl import threadpool_limits, threadpool_info
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    assert all(digest(ROOT / p) == v for p, v in reg["sources"].items())
    assert all(package_identity(p) == v for p, v in reg["packages"].items())
    case_path, native_path = Path(reg["case_path"]), Path(reg["native_path"])
    assert digest(case_path) == reg["case_sha256"] and digest(native_path) == reg["native_sha256"]
    case = json.loads(case_path.read_text(encoding="utf-8"))
    public = case["public"]
    assert sum(math.prod(s) * 8 for s in public["shapes"]) <= reg["budgets"]["input_bytes"]
    output.mkdir(parents=True, exist_ok=False)
    save(output / "public.json", public)
    begin = perf_counter()
    investment_start = perf_counter()
    batches = [[np.random.default_rng(seed + i * 100).uniform(0.5, 1.5, s) for i, s in enumerate(public["shapes"])] for seed in reg["query_seeds"]]
    for q, arrays in enumerate(batches):
        np.savez(output / f"inputs_{q}.npz", **{f"t{i}": a for i, a in enumerate(arrays)})
    generation_seconds = perf_counter() - investment_start
    observations, reference_seconds = [], 0
    with threadpool_limits(limits=1):
        pools = threadpool_info()
        # Only unrelated tiny BLAS initialization. No scored input/path warmup.
        np.ones((16, 16)) @ np.ones((16, 16))
        reference_start = perf_counter()
        references = []
        for q, arrays in enumerate(batches):
            outputs = [oe.contract(public["equation"], *arrays, optimize=[tuple(s) for s in v["path"]], backend="numpy") for v in case["supplied_paths"].values()]
            assert len(outputs) == 2 and agreement(outputs[0], outputs[1], reg["relative_tolerance"])
            expected = np.asarray(outputs[0])
            assert not agreement(np.zeros_like(expected), expected)
            assert not agreement(np.reshape(expected, (1,) + expected.shape), expected)
            np.savez(output / f"reference_{q}.npz", expected=expected, second=np.asarray(outputs[1]))
            references.append(expected)
        reference_seconds = perf_counter() - reference_start
        for repeat in range(reg["repetitions"]):
            routes = list(ROUTES)
            random.Random(6100900 + repeat).shuffle(routes)
            for route in routes:
                start = perf_counter()
                result = {"route": route, "repetition": repeat, "learned": False, "oracle_used": route == "FREE_PUBLISHED"}
                try:
                    if route == "CACHED_NATIVE_BEST":
                        assert digest(native_path) == reg["native_sha256"]
                        path = json.loads(native_path.read_text(encoding="utf-8"))["path"]
                    elif route == "FREE_PUBLISHED":
                        # Deliberately optimistic supplied-path access, not native learning.
                        path = case["supplied_paths"][reg["supplied_label"]]["path"]
                    elif route == "PUBLIC_RECONF32":
                        path = plan(public, "RECONF32", 47)["path"]
                    else:
                        path = public_plan(public, "greedy" if route == "PUBLIC_GREEDY" else "auto-hq")["path"]
                    certificate = certify_path(public, path)
                    if certificate["largest_intermediate_elements"] * 8 > reg["budgets"]["largest_intermediate_bytes"] or certificate["dense_arithmetic_work_model"] > reg["budgets"]["modeled_work"]:
                        result.update(status="EXCLUDED_PREDECLARED_RESOURCE_BUDGET", certificate=certificate, path=path, failed_seconds=perf_counter() - start)
                    else:
                        discovery_end = perf_counter()
                        expression = oe.contract_expression(public["equation"], *map(tuple, public["shapes"]), optimize=[tuple(s) for s in path])
                        setup_end = perf_counter()
                        queries = []
                        for q, arrays in enumerate(batches):
                            qbegin = perf_counter()
                            assert all(a.dtype == np.float64 and np.isfinite(a).all() for a in arrays)
                            scan_end = perf_counter()
                            actual = np.asarray(expression(*arrays, backend="numpy"))
                            kernel_end = perf_counter()
                            accepted = agreement(actual, references[q], reg["relative_tolerance"])
                            end = perf_counter()
                            queries.append({"accepted": accepted, "scan_seconds": scan_end - qbegin,
                                            "kernel_seconds": kernel_end - scan_end, "check_seconds": end - kernel_end,
                                            "query_seconds": end - qbegin})
                            # Witness I/O is outside query timing and separately in whole-study wall.
                            np.savez(output / f"witness_{repeat}_{route}_{q}.npz", actual=actual)
                        result.update(status="ACCEPTED" if all(q["accepted"] for q in queries) else "NUMERICAL_AGREEMENT_FAILURE",
                                      path=path, certificate=certificate, queries=queries,
                                      discovery_certificate_seconds=discovery_end - start, compile_seconds=setup_end - discovery_end,
                                      first_query_seconds=setup_end - start + queries[0]["query_seconds"],
                                      three_query_seconds=setup_end - start + sum(q["query_seconds"] for q in queries))
                except Exception as exc:
                    result.update(status="FAILED", error=repr(exc), failed_seconds=perf_counter() - start)
                observations.append(result)
                save(output / "observations.json", observations)
                print(json.dumps({k: v for k, v in result.items() if k in ["route", "repetition", "status", "first_query_seconds", "three_query_seconds", "error"]}), flush=True)
    route_metrics = {}
    import statistics
    for route in ROUTES:
        rows = [o for o in observations if o["route"] == route and o["status"] == "ACCEPTED"]
        route_metrics[route] = {"accepted_repetitions": len(rows)}
        if len(rows) == reg["repetitions"]:
            route_metrics[route].update({key: statistics.median(o[key] for o in rows) for key in ["first_query_seconds", "three_query_seconds", "discovery_certificate_seconds", "compile_seconds"]})
            route_metrics[route]["median_kernel_seconds"] = statistics.median(q["kernel_seconds"] for o in rows for q in o["queries"])
    complete = all(v["accepted_repetitions"] == reg["repetitions"] for v in route_metrics.values())
    ratios = {}
    if complete:
        for key in ["first_query_seconds", "three_query_seconds", "median_kernel_seconds"]:
            best = min(ROUTES[:-1], key=lambda r: route_metrics[r][key])
            ratios[key] = {"best_native_route": best, "native_over_free": route_metrics[best][key] / route_metrics["FREE_PUBLISHED"][key]}
    report = {"experiment_id": reg["experiment_id"], "scope": "CPU calibration on synthetic positive float64 inputs with opened public shapes; original dataset arrays/answers unavailable",
              "complete": complete, "observations": len(observations), "actual_queries": sum(len(o.get("queries", [])) for o in observations),
              "route_metrics": route_metrics, "ratios": ratios, "input_generation_and_save_seconds": generation_seconds,
              "two_path_reference_and_save_seconds": reference_seconds, "controlled_threadpools": pools,
              "whole_study_wall_seconds": perf_counter() - begin, "contract_sha256": digest(preparation / "preregister.json"),
              "prior_native_six_plan_search_wall_seconds": 23.397583099998883,
              "published_path_research_cost": None, "G1_admitted": False, "fresh_eligible": False,
              "independent_original_dataset_ground_truth": False, "energy_or_actual_RSS_measured": False}
    save(output / "report.json", report)
    save(output / "manifest.json", {p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"), "manifest_sha256": digest(output / "manifest.json")})
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run"])
    for key in ["preparation", "output", "case", "native"]:
        parser.add_argument("--" + key, type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.preparation, args.case, args.native)
    else:
        run(args.preparation, args.output)
