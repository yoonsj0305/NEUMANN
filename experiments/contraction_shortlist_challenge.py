"""Separate prospective strong-comparator challenge on opened shortlisted data."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from neumann1.cotengra_baseline import plan

SOURCES = ["experiments/contraction_shortlist_challenge.py", "neumann1/cotengra_baseline.py", "neumann1/contraction_structure.py"]


def freeze(preparation, first):
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    preparation.mkdir(parents=True, exist_ok=False)
    selected = report["contraction_shape_screen"]["shortlist"]
    registration = {"experiment_id": "CONTRACTION_SHORTLIST_CHALLENGE_V1", "source_first_report_sha256": digest(first / "report.json"),
        "selection": "all >=10x/peak-compatible candidates from frozen first shape screen", "selected": selected,
        "seeds": [19, 23, 47], "variants": ["GREEDY128", "RECONF32"], "worker_deadline_seconds": 45,
        "same_public_equation_shapes_only": True, "separate_from_original_shape_screen": True,
        "rule": "Take lowest modeled arithmetic work over all old and new eligible native plans; retain >=10x AND peak-compatible shortlist",
        "case_pins": {c: digest(first / "cases" / (c + ".json")) for c in selected},
        "sources": {p: digest(ROOT / p) for p in SOURCES},
        "packages": {p: package_identity(p) for p in ["cotengra", "autoray", "opt_einsum", "numpy"]},
        "PYTHONHASHSEED": "0", "shape_only": True, "actual_dataset_answers_checked": False,
        "G1_admitted": False, "global_optimum_claimed": False, "GPU_or_training": False}
    save(preparation / "preregister.json", registration)
    for p in SOURCES:
        target = preparation / "source" / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / p).read_bytes())
    save(preparation / "freeze-receipt.json", {"contract_sha256": digest(preparation / "preregister.json"), "performance_run": False})
    print(digest(preparation / "preregister.json"), flush=True)


def run(preparation, first, output):
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    assert digest(first / "report.json") == reg["source_first_report_sha256"]
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    old = json.loads((first / "report.json").read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=False)
    begin = perf_counter()
    events, observations, summaries = [], [], []
    for identifier in reg["selected"]:
        source = first / "cases" / (identifier + ".json")
        assert digest(source) == reg["case_pins"][identifier]
        case = json.loads(source.read_text(encoding="utf-8"))
        for variant in reg["variants"]:
            for seed in reg["seeds"]:
                target = output / f"{identifier}_{variant}_{seed}.json"
                start = perf_counter()
                try:
                    child = subprocess.run([sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "worker", "--case", str(source),
                                            "--observation", str(target), "--variant", variant, "--seed", str(seed)],
                                           capture_output=True, text=True, timeout=reg["worker_deadline_seconds"],
                                           env={**os.environ, "PYTHONHASHSEED": "0"})
                    event = {"id": identifier, "variant": variant, "seed": seed, "exit_code": child.returncode, "stderr": child.stderr[-2500:]}
                except subprocess.TimeoutExpired:
                    event = {"id": identifier, "variant": variant, "seed": seed, "timeout": True}
                event["worker_wall_seconds"] = perf_counter() - start
                events.append(event)
                if target.exists():
                    observations.append(json.loads(target.read_text(encoding="utf-8")))
                save(output / "events.json", events)
                print(json.dumps(event), flush=True)
        previous = next(c for c in old["contraction_shape_screen"]["cases"] if c["id"] == identifier)["metrics"]
        eligible = [o for o in observations if o["case_id"] == identifier and o.get("status") == "CERTIFIED_MODEL_ONLY"]
        best = min(eligible, key=lambda o: o["certificate"]["dense_arithmetic_work_model"]) if eligible else None
        work = min(previous["native_dense_work_model"], best["certificate"]["dense_arithmetic_work_model"]) if best else previous["native_dense_work_model"]
        peak = best["certificate"]["largest_intermediate_elements"] if best and best["certificate"]["dense_arithmetic_work_model"] <= previous["native_dense_work_model"] else previous["native_peak_elements"]
        complete = len(eligible) == len(reg["seeds"]) * len(reg["variants"])
        ratio = work / previous["supplied_dense_work_model"]
        summaries.append({"id": identifier, "challenge_complete": complete, "original_shape_ratio": previous["ratio"],
                          "stronger_native_work_model": work, "supplied_work_model": previous["supplied_dense_work_model"],
                          "new_ratio": ratio, "best_new_variant": best["variant"] if best else None,
                          "best_new_seed": best["seed"] if best else None,
                          "remaining_shortlist": complete and ratio >= 10 and previous["supplied_peak_elements"] <= peak})
    result = {"experiment_id": reg["experiment_id"], "cases": summaries, "observations": len(observations),
              "worker_events": events, "whole_study_wall_seconds": perf_counter() - begin,
              "contract_sha256": digest(preparation / "preregister.json"), "G1_admitted": False,
              "actual_tensor_execution": False, "source_first_report_modified": False}
    save(output / "report.json", result)
    save(output / "manifest.json", {p.name: digest(p) for p in output.glob("*.json") if p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"), "manifest_sha256": digest(output / "manifest.json")})
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze", "run", "worker"])
    for name in ["preparation", "first", "output", "case", "observation"]:
        p.add_argument("--" + name, type=Path)
    p.add_argument("--variant"); p.add_argument("--seed", type=int)
    a = p.parse_args()
    if a.mode == "freeze":
        freeze(a.preparation, a.first)
    elif a.mode == "run":
        run(a.preparation, a.first, a.output)
    else:
        value = json.loads(a.case.read_text(encoding="utf-8"))
        start = perf_counter()
        try:
            result = plan(value["public"], a.variant, a.seed)
            result["status"] = "CERTIFIED_MODEL_ONLY"
        except Exception as exc:
            result = {"status": "FAILED", "error": repr(exc), "failed_seconds": perf_counter() - start}
        result.update(case_id=value["id"], variant=a.variant, seed=a.seed)
        save(a.observation, result)
