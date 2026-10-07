"""One prospective CPU tournament on constructed topology/dimension changes.

Warm-service headroom only. No neural learning, independent-domain admission,
original benchmark numeric claim, global optimum, or sealed evaluation.
"""
import argparse
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
from time import perf_counter

BOOT = perf_counter()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.contraction_kernel_calibration import agreement
from neumann1.contraction_structure import certify_path, public_plan, validate_public
from neumann1.cotengra_baseline import plan
from neumann1.native_perspective_catalog import NativePerspectiveCatalog, topology_key
from neumann1.public_path_reuse import PreparedPublicPriors, propose

IDS = ["tensor_gm_queen5_5_3.wcsp", "tensor_lm_batch_likelihood_brackets_4_4d",
       "tensor_lm_batch_likelihood_sentence_3_12d", "tensor_str_nw_mera_closed_120"]
ROUTES = ["GREEDY", "AUTO_HQ", "RECONF32", "PRIOR_FIRST", "PRIOR_BEST_MODEL", "GEOMETRY_CATALOG", "FREE_STRUCTURE"]
SOURCES = ["experiments/perspective_transfer_headroom.py", "neumann1/public_path_reuse.py",
           "neumann1/native_perspective_catalog.py", "neumann1/contraction_structure.py", "neumann1/cotengra_baseline.py",
           "experiments/contraction_kernel_calibration.py", "experiments/representation_headroom.py"]


def changed_problem(public, mode, seed):
    inputs, output, sizes = validate_public(public)
    dimensions = {x: 2 if x in output else min(3, n) for x, n in sizes.items()}
    original_key = topology_key(public)
    terms = [list(term) for term in inputs]
    selected = None
    if mode == "SPLICE":
        rng = random.Random(seed)
        positions = [(i, j, x) for i, term in enumerate(terms) for j, x in enumerate(term) if x not in output]
        for _ in range(256):
            a, b = rng.sample(positions, 2)
            if a[0] == b[0] or a[2] == b[2] or dimensions[a[2]] != dimensions[b[2]]:
                continue
            trial = [t[:] for t in terms]
            trial[a[0]][a[1]], trial[b[0]][b[1]] = b[2], a[2]
            query = {"equation": ",".join("".join(t) for t in trial) + "->" + output,
                     "shapes": [[dimensions[x] for x in t] for t in trial]}
            if topology_key(query) != original_key:
                terms, selected = trial, [a, b]
                break
        if selected is None:
            raise ValueError("Predeclared splice failed to change public incidence")
    elif mode != "REBOUND":
        raise ValueError("Declared mutation mode required")
    query = {"equation": ",".join("".join(t) for t in terms) + "->" + output,
             "shapes": [[dimensions[x] for x in t] for t in terms]}
    validate_public(query)
    return query, {"mode": mode, "seed": seed, "splice_positions": selected,
                   "old_topology_key": original_key, "new_topology_key": topology_key(query),
                   "same_tensor_count_and_ranks": True, "original_semantics_changed_for_splice": mode == "SPLICE"}


def freeze(preparation, workspace):
    preparation.mkdir(parents=True, exist_ok=False)
    source_root = workspace / "Continuation/STRUCTURAL_SCREEN_FIRST/cases"
    catalog = workspace / "Continuation/STRUCTURAL_EXPERIENCE_V2_2026-10-07/native-catalog.json"
    reg = {"experiment_id": "PERSPECTIVE_TRANSFER_HEADROOM_V1", "source_ids": IDS,
        "source_root": str(source_root), "source_pins": {identifier: digest(source_root / (identifier + ".json")) for identifier in IDS},
        "catalog": str(catalog), "catalog_sha256": digest(catalog), "modes": ["REBOUND", "SPLICE"],
        "seed_base": 6101000, "repetitions": 3, "actual_queries_per_procedure": 2, "routes": ROUTES,
        "values": "deterministic independent float64 uniform [.98,1.02] on registered modified shapes",
        "BLAS_threads": 1, "rtol": 1e-10, "atol": 0,
        "budget": {"modeled_work": 1_000_000_000, "peak_elements": 16 * 2**20, "input_bytes": 8 * 2**20},
        "worker_deadline_seconds": 120,
        "offline_free_selection": "minimum modeled work/peak among eligible original supplied paths, same-arity public priors, fresh greedy/auto-hq/GREEDY128/RECONF32 paths; selected before request timings",
        "reference": "two distinct structurally certified eligible paths must agree on full positive finite outputs",
        "primary": "warm persistent-engine first new-structure request: discovery, index certificate, compile, scan, kernel, full-output comparison",
        "verification_reuse": "native certificates computed inside the request may be reused without double checking; FREE offline certificate must be checked again inside the request",
        "historical_priority_sorting": "once at engine setup for all prior-using arms, separately charged investment",
        "secondary": "same setup plus two actual different-value queries; common reuse rights",
        "baseline_envelope": "per-case fastest eligible native median; at least one native route must complete all repetitions and queries",
        "rule": {"splice_geomean_at_least": 10, "splice_cases_at_least_10x": 3, "splice_cases": 4,
                 "all_eight_cases_evaluable": True, "both_first_and_two_query_required": True},
        "positive_decision": "ONE_DOMAIN_WARM_SERVICE_HEADROOM_ONLY_NOT_G1_ADMISSION",
        "negative_decision": "NO_HEADROOM_FOR_THIS_REGISTERED_TRANSFER_SCOPE",
        "incomplete_decision": "INCOMPLETE_NO_ADMISSION",
        "investment_accounting": "imports/engine setup, input generation, references and offline path discovery measured separately; prior source search/research not silently zero; no complete deployment or cold single-query gain claim",
        "fresh_eligible": 0, "independent_domains": 1, "constructed_development_only": True,
        "model_training_or_GPU": False, "G1_admitted": False, "Decision3_unsealed": False,
        "sources": {p: digest(ROOT / p) for p in SOURCES},
        "packages": {p: package_identity(p) for p in ["numpy", "opt_einsum", "cotengra", "autoray", "threadpoolctl"]}}
    save(preparation / "preregister.json", reg)
    for p in SOURCES:
        target = preparation / "source" / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / p).read_bytes())
    save(preparation / "freeze-receipt.json", {"contract_sha256": digest(preparation / "preregister.json"), "performance_run": False, "modified_cases_generated": False})
    print(digest(preparation / "preregister.json"), flush=True)


def allowed(public, path, reg):
    check = certify_path(public, path)
    b = reg["budget"]
    return check["dense_arithmetic_work_model"] <= b["modeled_work"] and check["largest_intermediate_elements"] <= b["peak_elements"], check


def worker(preparation, case_path, output):
    import numpy as np
    import opt_einsum as oe
    from threadpoolctl import threadpool_limits, threadpool_info
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    case = json.loads(case_path.read_text(encoding="utf-8"))
    p = case["public"]
    output.mkdir(parents=True, exist_ok=False)
    stream = (output / "observations.jsonl").open("w", encoding="utf-8")
    def emit(record):
        stream.write(json.dumps(record) + "\n"); stream.flush()
    investment = {}
    with threadpool_limits(limits=1):
        library_start = perf_counter()
        assert digest(Path(reg["catalog"])) == reg["catalog_sha256"]
        records = json.loads(Path(reg["catalog"]).read_text(encoding="utf-8"))["records"]
        catalog = NativePerspectiveCatalog(records)
        prepared_priors = PreparedPublicPriors(records)
        investment["catalog_load_check_seconds"] = perf_counter() - library_start
        investment["process_entry_to_catalog_ready_seconds"] = perf_counter() - BOOT
        assert sum(math.prod(s) * 8 for s in p["shapes"]) <= reg["budget"]["input_bytes"]
        begin = perf_counter()
        batches = [[np.random.default_rng(case["seed"] + q * 10000 + i).uniform(.98, 1.02, shape) for i, shape in enumerate(p["shapes"])] for q in range(2)]
        for q, arrays in enumerate(batches):
            np.savez(output / f"inputs_{q}.npz", **{f"t{i}": a for i, a in enumerate(arrays)})
        investment["input_generation_save_seconds"] = perf_counter() - begin
        begin = perf_counter()
        options, offline_events = [], []
        for origin, path in [("old_supplied_" + label, obj["path"]) for label, obj in case["offline_original_paths"].items()] + [("public_prior", r["path"]) for r in records if len(r["public"]["shapes"]) == len(p["shapes"])]:
            fits, check = allowed(p, path, reg)
            if fits:
                options.append({"origin": origin, "path": path, "certificate": check})
        for strategy in ["greedy", "auto-hq", "GREEDY128", "RECONF32"]:
            start = perf_counter()
            try:
                proposal = public_plan(p, strategy) if strategy in {"greedy", "auto-hq"} else plan(p, strategy, 47)
                fits, check = allowed(p, proposal["path"], reg)
                if fits:
                    options.append({"origin": "offline_" + strategy, "path": proposal["path"], "certificate": check})
                offline_events.append({"strategy": strategy, "status": "ELIGIBLE" if fits else "RESOURCE_MODEL_REJECTED", "seconds": perf_counter() - start})
            except Exception as exc:
                offline_events.append({"strategy": strategy, "status": "FAILED", "error": repr(exc), "seconds": perf_counter() - start})
        unique = {}
        for option in options:
            unique.setdefault(json.dumps(option["path"]), option)
        options = sorted(unique.values(), key=lambda o: (o["certificate"]["dense_arithmetic_work_model"], o["certificate"]["largest_intermediate_elements"]))
        assert len(options) >= 2, "Two distinct eligible reference programs required"
        free = options[0]
        save(output / "offline-options.json", {"selected": free, "options": options, "events": offline_events})
        investment["offline_discovery_save_seconds"] = perf_counter() - begin
        begin = perf_counter()
        references = []
        for q, arrays in enumerate(batches):
            results = [np.asarray(oe.contract(p["equation"], *arrays, optimize=[tuple(s) for s in o["path"]], backend="numpy")) for o in options[:2]]
            assert agreement(results[0], results[1], reg["rtol"])
            assert not agreement(np.zeros_like(results[0]), results[0])
            assert not agreement(results[0].reshape((1,) + results[0].shape), results[0])
            references.append(results[0])
            np.savez(output / f"reference_{q}.npz", expected=results[0], second=results[1])
        investment["reference_generation_save_seconds"] = perf_counter() - begin
        emit({"kind": "investment", "case_id": case["id"], "seconds": investment, "threadpools": threadpool_info(), "original_dataset_answers_available": False})
        for repetition in range(reg["repetitions"]):
            routes = list(ROUTES)
            random.Random(case["seed"] + repetition).shuffle(routes)
            for route in routes:
                start = perf_counter()
                row = {"kind": "query", "case_id": case["id"], "repetition": repetition, "route": route, "learned": False, "oracle_used": route == "FREE_STRUCTURE"}
                try:
                    if route == "FREE_STRUCTURE":
                        proposal = free
                    elif route == "GEOMETRY_CATALOG":
                        proposal = catalog.propose(p, max_work=reg["budget"]["modeled_work"], max_intermediate_elements=reg["budget"]["peak_elements"])
                    elif route.startswith("PRIOR_"):
                        proposal = propose(p, prepared_priors, "FIRST" if route == "PRIOR_FIRST" else "BEST_MODEL", max_work=reg["budget"]["modeled_work"], max_elements=reg["budget"]["peak_elements"])
                    elif route == "RECONF32":
                        proposal = plan(p, "RECONF32", 47)
                    else:
                        proposal = public_plan(p, "greedy" if route == "GREEDY" else "auto-hq")
                    if "path" not in proposal:
                        row.update(status="ABSTAINED", reason=proposal.get("status"), failed_seconds=perf_counter() - start)
                    else:
                        if route == "FREE_STRUCTURE":
                            fits, check = allowed(p, proposal["path"], reg)
                        else:
                            # Produced by trusted common checker on THIS public goal
                            # inside the timer, not supplied as model/Oracle authority.
                            check = proposal["certificate"]
                            fits = check["dense_arithmetic_work_model"] <= reg["budget"]["modeled_work"] and check["largest_intermediate_elements"] <= reg["budget"]["peak_elements"]
                        if not fits:
                            row.update(status="RESOURCE_MODEL_REJECTED", path=proposal["path"], certificate=check, failed_seconds=perf_counter() - start)
                        else:
                            discovery_end = perf_counter()
                            expression = oe.contract_expression(p["equation"], *map(tuple, p["shapes"]), optimize=[tuple(s) for s in proposal["path"]])
                            setup_end = perf_counter()
                            queries = []
                            for q, arrays in enumerate(batches):
                                begin = perf_counter()
                                assert all(np.isfinite(a).all() for a in arrays)
                                scan_end = perf_counter()
                                actual = np.asarray(expression(*arrays, backend="numpy"))
                                kernel_end = perf_counter()
                                accepted = agreement(actual, references[q], reg["rtol"])
                                end = perf_counter()
                                queries.append({"accepted": accepted, "scan_seconds": scan_end - begin, "kernel_seconds": kernel_end - scan_end,
                                                "check_seconds": end - kernel_end, "query_seconds": end - begin})
                                np.savez(output / f"witness_{repetition}_{route}_{q}.npz", actual=actual)
                            row.update(status="ACCEPTED" if all(q["accepted"] for q in queries) else "NUMERICAL_FAILURE", path=proposal["path"], certificate=check,
                                discovery_certificate_seconds=discovery_end - start, compile_seconds=setup_end - discovery_end, queries=queries,
                                first_query_seconds=setup_end - start + queries[0]["query_seconds"], two_query_seconds=setup_end - start + sum(q["query_seconds"] for q in queries))
                except Exception as exc:
                    row.update(status="FAILED", error=repr(exc), failed_seconds=perf_counter() - start)
                emit(row)
    stream.close()


def summarize(cases, observations, events, reg):
    summaries = []
    for case in cases:
        rows = [o for o in observations if o.get("kind") == "query" and o["case_id"] == case["id"]]
        metrics = {}
        for route in ROUTES:
            accepted = [o for o in rows if o["route"] == route and o["status"] == "ACCEPTED"]
            if len(accepted) == reg["repetitions"]:
                metrics[route] = {k: statistics.median(o[k] for o in accepted) for k in ["first_query_seconds", "two_query_seconds"]}
        complete = len(rows) == len(ROUTES) * reg["repetitions"] and "FREE_STRUCTURE" in metrics and len(metrics) >= 2
        ratios = {}
        if complete:
            for k in ["first_query_seconds", "two_query_seconds"]:
                best = min((r for r in metrics if r != "FREE_STRUCTURE"), key=lambda r: metrics[r][k])
                ratios[k] = {"best_native": best, "native_over_free": metrics[best][k] / metrics["FREE_STRUCTURE"][k]}
        summaries.append({"id": case["id"], "mode": case["lineage"]["mode"], "complete": complete, "ratios": ratios, "route_medians": metrics})
    all_complete = all(c["complete"] for c in summaries) and len(summaries) == 8 and all(e.get("exit_code") == 0 for e in events)
    regimes = {}
    for key in ["first_query_seconds", "two_query_seconds"]:
        ratios = [c["ratios"][key]["native_over_free"] for c in summaries if c["mode"] == "SPLICE" and c["complete"]]
        mean = math.exp(sum(math.log(x) for x in ratios) / len(ratios)) if len(ratios) == 4 else None
        wins = sum(x >= 10 for x in ratios)
        regimes[key] = {"splice_geomean": mean, "splice_10x_cases": wins, "passed": all_complete and mean >= 10 and wins >= 3}
    decision = reg["positive_decision"] if all(v["passed"] for v in regimes.values()) else reg["negative_decision"] if all_complete else reg["incomplete_decision"]
    return {"experiment_id": reg["experiment_id"], "decision": decision, "cases": summaries, "regimes": regimes,
            "all_cases_evaluable": all_complete, "query_observations": sum(o.get("kind") == "query" for o in observations),
            "actual_numeric_queries": sum(len(o.get("queries", [])) for o in observations),
            "status_counts": {s: sum(o.get("status") == s for o in observations) for s in sorted({o["status"] for o in observations if "status" in o})},
            "G1_admitted": False, "fresh_eligible": 0, "scope": "one-domain warm-service constructed development screening, not original benchmark or learned discovery evidence"}


def run(preparation, output):
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    assert digest(Path(reg["catalog"])) == reg["catalog_sha256"]
    output.mkdir(parents=True, exist_ok=False)
    (output / "cases").mkdir()
    cases, observations, events = [], [], []
    begin = perf_counter()
    for i, identifier in enumerate(IDS):
        source = Path(reg["source_root"]) / (identifier + ".json")
        assert digest(source) == reg["source_pins"][identifier]
        original = json.loads(source.read_text(encoding="utf-8"))
        for mode in reg["modes"]:
            seed = reg["seed_base"] + 2 * i + (mode == "SPLICE")
            public, lineage = changed_problem(original["public"], mode, seed)
            case = {"id": identifier + "_" + mode.lower(), "seed": seed, "public": public, "lineage": lineage,
                    "source_sha256": digest(source), "offline_original_paths": original["supplied_paths"], "fresh_eligible": False}
            case_path = output / "cases" / (case["id"] + ".json")
            save(case_path, case)
            cases.append(case)
            target = output / case["id"]
            start = perf_counter()
            try:
                child = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "worker", "--preparation", str(preparation), "--case", str(case_path), "--output", str(target)],
                    capture_output=True, text=True, timeout=reg["worker_deadline_seconds"], env={**os.environ, "PYTHONHASHSEED": "0"})
                event = {"id": case["id"], "exit_code": child.returncode, "stderr": child.stderr[-3000:]}
            except subprocess.TimeoutExpired:
                event = {"id": case["id"], "timeout": True}
            event["worker_wall_seconds"] = perf_counter() - start
            events.append(event)
            if (target / "observations.jsonl").exists():
                observations.extend(json.loads(line) for line in (target / "observations.jsonl").read_text(encoding="utf-8").splitlines())
            save(output / "events.json", events)
            print(json.dumps(event), flush=True)
    report = summarize(cases, observations, events, reg)
    report.update(contract_sha256=digest(preparation / "preregister.json"), whole_study_wall_seconds=perf_counter() - begin)
    save(output / "report.json", report)
    save(output / "manifest.json", {str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"), "manifest_sha256": digest(output / "manifest.json")})
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run", "worker"])
    for name in ["preparation", "workspace", "output", "case"]:
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.preparation, args.workspace)
    elif args.mode == "run":
        run(args.preparation, args.output)
    else:
        worker(args.preparation, args.case, args.output)
