"""Preregistered proof-component assay and external shape-only candidate screen.

Neither assay is G1 admission or a frontier/learned-system evaluation.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import sys
from time import perf_counter
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.representation_headroom_replay import interpret_original
from neumann1.contraction_structure import certify_path, is_matrix_chain, public_plan
from neumann1.public_rewrite_search import propose
from neumann1.representation_program import Builder, compile_program, validate, verify_original
from neumann1.representation_rewrite_certificate import check_certificate

SOURCES = ["experiments/structural_mechanism_screen.py", "neumann1/public_rewrite_search.py",
           "neumann1/contraction_structure.py", "neumann1/representation_program.py",
           "neumann1/representation_rewrite_certificate.py", "experiments/representation_headroom_replay.py",
           "experiments/representation_headroom.py"]
STRATEGIES = ["greedy", "auto", "auto-hq", "random-greedy-128", "dynamic-programming"]


def freeze(preparation, archive):
    preparation.mkdir(parents=True, exist_ok=False)
    registration = {"experiment_id": "STRUCTURAL_MECHANISM_SCREEN_V1",
        "status": "PREREGISTERED_BEFORE_PERFORMANCE", "source_archive_sha256": digest(archive),
        "metadata_origin": "tensor4all/strided-rs-benchmark-suite", "metadata_commit": "05506112eb40f7cff7ac102689614c180a7d6120",
        "metadata_scope": "all JSON instances in pinned archive; derived metadata, not original tensors",
        "proof_assay": {"degrees": [4, 8, 12], "motifs": ["ONE_STEP", "COMPOSED", "FALSE_SHARED"],
            "replicas": 2, "repetitions": 3, "rows": 64, "seed_base": 6100700,
            "routes": ["DIRECT", "PUBLIC_SYMBOLIC_CERT", "FREE_CERT", "FREE_FULL_POLYNOMIAL"],
            "paired_verifier_gain_target": 10, "all_controls_must_reject": True,
            "score_scope": "component ratio on ONE_STEP/COMPOSED only; complete pipeline costs also reported",
            "not_g0_admission": True},
        "contraction_screen": {"strategies": STRATEGIES, "repetitions": 1,
            "DP_eligibility": "public operand count<=16 OR connected matrix chain",
            "published_paths": "Oracle-only opt_size/opt_flops; never native planner input",
            "shape_shortlist_rule": "best native modeled work / best supplied modeled work >=10 AND supplied peak<=best-work native peak",
            "rule_scope": "candidate shortlist only; no actual tensor execution or accuracy/latency conclusion",
            "global_optimum_proven": False, "G1_admission": False},
        "worker_seconds_per_case": 45, "failed_time_and_partial_output_retained": True,
        "sealed_access": False, "GPU_or_training": False, "fresh_eligible": 0,
        "source_pins": {p: digest(ROOT / p) for p in SOURCES},
        "packages": {p: package_identity(p) for p in ["numpy", "sympy", "mpmath", "opt_einsum"]}}
    save(preparation / "preregister.json", registration)
    for p in SOURCES:
        destination = preparation / "source" / p
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / p).read_bytes())
    save(preparation / "freeze-receipt.json", {"contract_sha256": digest(preparation / "preregister.json"),
                                               "performance_grid_run": False})
    print(digest(preparation / "preregister.json"), flush=True)


def proof_case(spec, contract):
    rng = random.Random(spec["seed"])
    b = Builder([f"x{i}" for i in range(5)])
    xs = [b.input(n) for n in b.inputs]
    tail = b.combine("mul", [b.combine("add", [b.mul(b.const(rng.choice([-2, -1, 1, 2])), x) for x in xs])
                             for _ in range(spec["degree"])])
    left = b.mul(xs[0], xs[1])
    right = b.mul(xs[3] if spec["motif"] == "FALSE_SHARED" else xs[0], xs[2])
    pattern = b.add(left, right)
    goal = b.mul(pattern, tail)
    if spec["motif"] == "COMPOSED":
        goal = b.add(b.mul(goal, b.const(1)), b.const(0))
    original = b.finish([goal, xs[-1]])
    offline = propose(original)
    return {"original": original, "supplied": offline,
            "false_certificate": {"semantics": "exact_integer", "steps": [{"rule": "FACTOR_COMMON", "node": pattern}]},
            "bindings": [tuple(rng.randint(-2, 2) for _ in xs) for _ in range(contract["rows"])],
            "spec": spec, "exposure": "OPENED_DEVELOPMENT", "fresh_eligible": False}


def proof_trial(case, route, expected):
    start = perf_counter()
    proposal = propose(case["original"]) if route == "PUBLIC_SYMBOLIC_CERT" else case["supplied"]
    candidate = case["original"] if route == "DIRECT" else proposal["candidate"]
    discovery_end = perf_counter()
    if route in {"DIRECT", "FREE_FULL_POLYNOMIAL"} or not proposal["certificate"]["steps"]:
        check = verify_original(case["original"], candidate)
    else:
        check = check_certificate(case["original"], candidate, proposal["certificate"])
    verify_end = perf_counter()
    if not check["accepted"]:
        return {"accepted": False, "verification": check, "failed_seconds": perf_counter() - start}
    compiled = compile_program(candidate)
    compile_end = perf_counter()
    actual = compiled.run([tuple(row) for row in case["bindings"]])
    accepted = actual == expected
    end = perf_counter()
    control = None
    if case["spec"]["motif"] == "FALSE_SHARED":
        control = check_certificate(case["original"], candidate, case["false_certificate"])
        accepted = accepted and not control["accepted"]
    return {"accepted": accepted, "candidate": candidate, "certificate": proposal["certificate"] if route != "DIRECT" else None,
            "discovery_seconds": discovery_end - start, "verification_seconds": verify_end - discovery_end,
            "compile_seconds": compile_end - verify_end, "execute_check_seconds": end - compile_end,
            "complete_query_seconds": end - start, "authority": check["authority"], "false_control": control,
            "integer_operations_per_row": compiled.add_calls + compiled.mul_calls,
            "oracle_used": route.startswith("FREE_"), "learned": False}


def worker(case_path, observation_path, preparation):
    registration = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    case = json.loads(case_path.read_text(encoding="utf-8"))
    with observation_path.open("a", encoding="utf-8") as output:
        def emit(value):
            output.write(json.dumps(value) + "\n"); output.flush()
        if case["kind"] == "proof":
            begin = perf_counter()
            expected = interpret_original(case["original"], case["bindings"])
            investment = perf_counter() - begin
            for repeat in range(registration["proof_assay"]["repetitions"]):
                routes = list(registration["proof_assay"]["routes"])
                random.Random(case["spec"]["seed"] + repeat).shuffle(routes)
                for route in routes:
                    begin = perf_counter()
                    try:
                        result = proof_trial(case, route, expected)
                    except Exception as exc:
                        result = {"accepted": False, "error": repr(exc), "failed_seconds": perf_counter() - begin}
                    result.update(kind="proof", case_id=case["id"], route=route, repetition=repeat,
                                  original_reference_seconds_investment=investment)
                    emit(result)
        else:
            for strategy in STRATEGIES:
                if strategy == "dynamic-programming" and len(case["public"]["shapes"]) > 16 and not is_matrix_chain(case["public"]):
                    emit({"kind": "contraction", "case_id": case["id"], "strategy": strategy,
                          "status": "EXCLUDED_PREDECLARED_DP_BUDGET"})
                    continue
                begin = perf_counter()
                try:
                    result = public_plan(case["public"], strategy)
                    result.update(status="CERTIFIED_MODEL_ONLY", planner_and_check_seconds=perf_counter() - begin)
                except Exception as exc:
                    result = {"status": "FAILED", "error": repr(exc), "failed_seconds": perf_counter() - begin}
                result.update(kind="contraction", case_id=case["id"], strategy=strategy)
                emit(result)
            for label, data in case["supplied_paths"].items():
                begin = perf_counter()
                try:
                    result = {"certificate": certify_path(case["public"], data["path"]), "path": data["path"],
                              "status": "CERTIFIED_MODEL_ONLY", "check_seconds": perf_counter() - begin}
                except Exception as exc:
                    result = {"status": "FAILED", "error": repr(exc), "failed_seconds": perf_counter() - begin}
                result.update(kind="contraction", case_id=case["id"], strategy="FREE_PUBLISHED_" + label,
                              oracle_used=True, learned=False)
                emit(result)


def summarize(registration, case_values, observations, events):
    proof_cases = [c for c in case_values if c["kind"] == "proof"]
    proof_summary = []
    verification_ratios = []
    controls = []
    for case in proof_cases:
        group = [o for o in observations if o["case_id"] == case["id"]]
        valid = len(group) == 12 and all(o.get("accepted") for o in group)
        metrics = {}
        if valid:
            medians = {r: statistics.median(o["complete_query_seconds"] for o in group if o["route"] == r)
                       for r in registration["proof_assay"]["routes"]}
            native = min(medians["DIRECT"], medians["PUBLIC_SYMBOLIC_CERT"])
            free = medians["FREE_CERT"]
            if case["spec"]["motif"] != "FALSE_SHARED":
                old = statistics.median(o["verification_seconds"] for o in group if o["route"] == "FREE_FULL_POLYNOMIAL")
                new = statistics.median(o["verification_seconds"] for o in group if o["route"] == "FREE_CERT")
                verification_ratios.append(old / new)
                metrics["old_polynomial_vs_certificate_verifier_ratio"] = old / new
            else:
                controls.extend(not o["false_control"]["accepted"] for o in group)
            metrics.update(complete_query_native_over_free=native / free, complete_query_medians=medians)
        proof_summary.append({"id": case["id"], "spec": case["spec"], "complete": valid, "metrics": metrics})
    proof_complete = len(proof_summary) == 18 and all(c["complete"] for c in proof_summary)
    proof_gm = math.exp(sum(map(math.log, verification_ratios)) / len(verification_ratios)) if verification_ratios else None
    native_gm_ratios = [c["metrics"]["complete_query_native_over_free"] for c in proof_summary if c["metrics"]]
    native_gm = math.exp(sum(map(math.log, native_gm_ratios)) / len(native_gm_ratios)) if native_gm_ratios else None
    contraction_summary = []
    for case in [c for c in case_values if c["kind"] == "contraction"]:
        group = [o for o in observations if o["case_id"] == case["id"]]
        native = [o for o in group if not o["strategy"].startswith("FREE_") and o["status"] == "CERTIFIED_MODEL_ONLY"]
        supplied = [o for o in group if o["strategy"].startswith("FREE_") and o["status"] == "CERTIFIED_MODEL_ONLY"]
        metrics = {}
        if native and supplied:
            best_native = min(native, key=lambda o: o["certificate"]["dense_arithmetic_work_model"])
            best_supplied = min(supplied, key=lambda o: o["certificate"]["dense_arithmetic_work_model"])
            nc, oc = best_native["certificate"], best_supplied["certificate"]
            ratio = nc["dense_arithmetic_work_model"] / oc["dense_arithmetic_work_model"]
            metrics = {"native_strategy": best_native["strategy"], "supplied_strategy": best_supplied["strategy"],
                       "native_dense_work_model": nc["dense_arithmetic_work_model"], "supplied_dense_work_model": oc["dense_arithmetic_work_model"],
                       "ratio": ratio, "native_peak_elements": nc["largest_intermediate_elements"],
                       "supplied_peak_elements": oc["largest_intermediate_elements"],
                       "shortlist": ratio >= 10 and oc["largest_intermediate_elements"] <= nc["largest_intermediate_elements"]}
        contraction_summary.append({"id": case["id"], "tensor_count": len(case["public"]["shapes"]),
                                    "observations": len(group), "metrics": metrics})
    return {"experiment_id": registration["experiment_id"], "G1_admitted": False, "learned_model": False,
        "proof_assay": {"status": "COMPLETE" if proof_complete else "INCOMPLETE_OR_FAILED",
            "accepted": sum(o.get("accepted", False) for o in observations if o["kind"] == "proof"),
            "expected": 216, "paired_verifier_cases": len(verification_ratios), "verifier_ratio_geomean": proof_gm,
            "component_10x_pass": proof_complete and len(verification_ratios) == 12 and proof_gm >= 10 and len(controls) == 72 and all(controls),
            "false_controls_rejected": sum(controls), "complete_query_native_over_free_geomean": native_gm,
            "cases": proof_summary},
        "contraction_shape_screen": {"source_cases": len(contraction_summary), "cases": contraction_summary,
            "shortlist": [c["id"] for c in contraction_summary if c["metrics"].get("shortlist")],
            "actual_tensor_execution": False, "original_dataset_answers": "UNAVAILABLE_NOT_ASSUMED",
            "status": "SHAPE_MODEL_SCREEN_ONLY_NOT_G0_CAPABILITY_OR_LATENCY_PASS"},
        "worker_events": events}


def run(preparation, output, archive):
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    frozen = json.loads((preparation / "freeze-receipt.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == frozen["contract_sha256"]
    assert digest(archive) == reg["source_archive_sha256"]
    assert all(digest(ROOT / p) == h for p, h in reg["source_pins"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    output.mkdir(parents=True, exist_ok=False)
    (output / "cases").mkdir(); (output / "observations").mkdir()
    start = perf_counter()
    values = []
    cfg = reg["proof_assay"]
    for degree in cfg["degrees"]:
        for mi, motif in enumerate(cfg["motifs"]):
            for replica in range(cfg["replicas"]):
                spec = {"degree": degree, "motif": motif, "replica": replica,
                        "seed": cfg["seed_base"] + degree * 100 + mi * 10 + replica}
                case = proof_case(spec, cfg)
                case.update(kind="proof", id=f"proof_{motif.lower()}_d{degree}_r{replica}")
                values.append(case)
    with zipfile.ZipFile(archive) as upstream:
        for member in sorted(upstream.namelist()):
            if member.startswith("data/instances/") and member.endswith(".json"):
                data = json.loads(upstream.read(member))
                values.append({"kind": "contraction", "id": "tensor_" + Path(member).stem,
                    "source_file": member, "public": {"equation": data["format_string"], "shapes": data["shapes"]},
                    "supplied_paths": data.get("paths", {}), "exposure": "OPENED_DERIVED_METADATA", "fresh_eligible": False})
    events = []
    for case in values:
        path = output / "cases" / (case["id"] + ".json")
        save(path, case)
        observation_path = output / "observations" / (case["id"] + ".jsonl")
        begin = perf_counter()
        try:
            child = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "worker",
                                    "--preparation", str(preparation), "--case", str(path), "--observations", str(observation_path)],
                                   timeout=reg["worker_seconds_per_case"], capture_output=True, text=True)
            event = {"id": case["id"], "exit_code": child.returncode, "stderr": child.stderr[-2500:]}
        except subprocess.TimeoutExpired:
            event = {"id": case["id"], "timeout": True}
        event["worker_wall_seconds"] = perf_counter() - begin
        events.append(event)
        save(output / "events.json", events)
        print(json.dumps(event), flush=True)
    observations = [json.loads(line) for path in sorted((output / "observations").glob("*.jsonl"))
                    for line in path.read_text(encoding="utf-8").splitlines()]
    report = summarize(reg, values, observations, events)
    report.update(whole_study_wall_seconds=perf_counter() - start, contract_sha256=digest(preparation / "preregister.json"))
    save(output / "report.json", report)
    save(output / "manifest.json", {str(p.relative_to(output)).replace("\\", "/"): digest(p) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"), "manifest_sha256": digest(output / "manifest.json")})
    print(json.dumps({"proof": {k: v for k, v in report["proof_assay"].items() if k != "cases"},
                      "tensor_shortlist": report["contraction_shape_screen"]["shortlist"], "whole_study_wall_seconds": report["whole_study_wall_seconds"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run", "worker"])
    for name in ["preparation", "output", "archive", "case", "observations"]:
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.preparation, args.archive)
    elif args.mode == "run":
        run(args.preparation, args.output, args.archive)
    else:
        worker(args.case, args.observations, args.preparation)
