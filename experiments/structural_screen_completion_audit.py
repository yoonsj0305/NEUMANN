"""Post-result audit/analysis. Never changes frozen contracts or first reports."""
import importlib.metadata as md
import json
import math
from pathlib import Path
import statistics
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.contraction_kernel_calibration import agreement
from neumann1.contraction_structure import certify_path


def check_run(preparation, first):
    reg = json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))
    receipt = json.loads((preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(preparation / "preregister.json") == json.loads((preparation / "freeze-receipt.json").read_text())["contract_sha256"]
    assert digest(first / "report.json") == receipt["report_sha256"]
    assert digest(first / "manifest.json") == receipt["manifest_sha256"]
    files = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(first / p) == pin for p, pin in files.items())
    assert all(digest(ROOT / p) == pin and digest(preparation / "source" / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    return reg, len(files)


def audit(workspace):
    import numpy as np
    import opt_einsum as oe
    from threadpoolctl import threadpool_limits
    continuation = workspace / "Continuation"
    destination = continuation / "STRUCTURAL_SCREEN_COMPLETION_AUDIT"
    destination.mkdir(parents=True, exist_ok=False)
    challenge_first = continuation / "CONTRACTION_CHALLENGE_FIRST"
    challenge, challenge_files = check_run(continuation / "CONTRACTION_CHALLENGE_PREPARATION", challenge_first)
    source = continuation / "STRUCTURAL_SCREEN_FIRST"
    assert digest(source / "report.json") == challenge["source_first_report_sha256"]
    challenge_paths = 0
    for identifier in challenge["selected"]:
        case_path = source / "cases" / (identifier + ".json")
        assert digest(case_path) == challenge["case_pins"][identifier]
        public = json.loads(case_path.read_text(encoding="utf-8"))["public"]
        for variant in challenge["variants"]:
            for seed in challenge["seeds"]:
                observation = json.loads((challenge_first / f"{identifier}_{variant}_{seed}.json").read_text(encoding="utf-8"))
                assert observation["status"] == "CERTIFIED_MODEL_ONLY"
                assert certify_path(public, observation["path"]) == observation["certificate"]
                _, independent = oe.contract_path(public["equation"], *map(tuple, public["shapes"]), shapes=True, optimize=[tuple(s) for s in observation["path"]])
                assert int(independent.opt_cost) == observation["certificate"]["dense_arithmetic_work_model"]
                challenge_paths += 1
    calibration_first = continuation / "CONTRACTION_KERNEL_FIRST"
    calibration, calibration_files = check_run(continuation / "CONTRACTION_KERNEL_PREPARATION", calibration_first)
    assert digest(Path(calibration["case_path"])) == calibration["case_sha256"]
    assert digest(Path(calibration["native_path"])) == calibration["native_sha256"]
    public = json.loads((calibration_first / "public.json").read_text(encoding="utf-8"))
    case = json.loads(Path(calibration["case_path"]).read_text(encoding="utf-8"))
    assert public == case["public"]
    batches, references = [], []
    with threadpool_limits(limits=1):
        for q, seed in enumerate(calibration["query_seeds"]):
            with np.load(calibration_first / f"inputs_{q}.npz", allow_pickle=False) as stored:
                arrays = [stored[f"t{i}"] for i in range(len(public["shapes"]))]
            assert all(a.dtype == np.float64 and np.array_equal(a, np.random.default_rng(seed + i * 100).uniform(0.5, 1.5, public["shapes"][i])) for i, a in enumerate(arrays))
            with np.load(calibration_first / f"reference_{q}.npz", allow_pickle=False) as stored:
                expected, second = stored["expected"], stored["second"]
            assert agreement(expected, second)
            independent = oe.contract(public["equation"], *arrays, optimize=[tuple(s) for s in case["supplied_paths"]["opt_size"]["path"]], backend="numpy")
            assert agreement(independent, expected)
            batches.append(arrays); references.append(expected)
        observations = json.loads((calibration_first / "observations.json").read_text(encoding="utf-8"))
        numerical = 0
        exclusions = []
        for o in observations:
            assert certify_path(public, o["path"]) == o["certificate"]
            if o["status"] == "EXCLUDED_PREDECLARED_RESOURCE_BUDGET":
                limits = calibration["budgets"]
                assert o["certificate"]["largest_intermediate_elements"] * 8 > limits["largest_intermediate_bytes"] or o["certificate"]["dense_arithmetic_work_model"] > limits["modeled_work"]
                exclusions.append({"route": o["route"], "repetition": o["repetition"], "planning_failed_budget_seconds": o["failed_seconds"]})
                continue
            assert o["status"] == "ACCEPTED"
            for q, arrays in enumerate(batches):
                with np.load(calibration_first / f"witness_{o['repetition']}_{o['route']}_{q}.npz", allow_pickle=False) as stored:
                    witness = stored["actual"]
                independently_executed = oe.contract(public["equation"], *arrays, optimize=[tuple(s) for s in o["path"]], backend="numpy")
                assert o["queries"][q]["accepted"] and agreement(witness, references[q]) and agreement(independently_executed, witness)
                numerical += 1
    # Descriptive eligible-route envelope only. The first report's complete=False is retained.
    complete_routes = [r for r in calibration["routes"] if len([o for o in observations if o["route"] == r and o["status"] == "ACCEPTED"]) == calibration["repetitions"]]
    metrics = {}
    for route in complete_routes:
        rows = [o for o in observations if o["route"] == route]
        metrics[route] = {k: statistics.median(o[k] for o in rows) for k in ["first_query_seconds", "three_query_seconds"]}
        metrics[route]["median_kernel_seconds"] = statistics.median(q["kernel_seconds"] for o in rows for q in o["queries"])
    envelope = {}
    for key in ["first_query_seconds", "three_query_seconds", "median_kernel_seconds"]:
        native = min((r for r in complete_routes if r != "FREE_PUBLISHED"), key=lambda r: metrics[r][key])
        envelope[key] = {"best_eligible_native_route": native, "native_over_free": metrics[native][key] / metrics["FREE_PUBLISHED"][key]}
    save(destination / "replay.json", {"status": "PASS", "challenge_manifest_files": challenge_files,
        "challenge_paths_rechecked": challenge_paths, "calibration_manifest_files": calibration_files,
        "actual_numerical_witnesses_reexecuted": numerical, "exclusions_rechecked": len(exclusions),
        "challenge_report_sha256": digest(challenge_first / "report.json"), "calibration_report_sha256": digest(calibration_first / "report.json"),
        "original_dataset_answer_claimed": False, "sources_dependencies_and_first_external_pins_match": True})
    save(destination / "eligible-route-analysis.json", {"post_result_descriptive_analysis_only": True,
        "first_report_modified": False, "original_complete_false_preserved": True, "eligible_route_metrics": metrics,
        "envelope": envelope, "excluded_route_costs": exclusions,
        "scope": "three constructed numeric inputs of ONE already opened tensor topology; not G0 admission or fresh generalization",
        "cached_native_full_search_investment_seconds_separate": 23.397583099998883,
        "published_path_research_investment": None, "G1_admitted": False})
    software = []
    reuse = continuation / "CONTRACTION_REUSE_PREPARATION"
    for package, version in [("opt_einsum", "3.4.0"), ("cotengra", "0.8.2"), ("autoray", "0.11.0")]:
        wheel = reuse / "wheels" / f"{package}-{version}-py3-none-any.whl"
        dist = md.distribution(package)
        assert dist.version == version
        count, licenses = 0, []
        with zipfile.ZipFile(wheel) as archive:
            for member in archive.namelist():
                if member.startswith(package + "/") and not member.endswith("/"):
                    assert Path(dist.locate_file(member)).read_bytes() == archive.read(member), member
                    count += 1
                if ".dist-info/" in member and "license" in member.lower() and not member.endswith("/"):
                    target = reuse / "licenses" / package / Path(member).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(member))
                    licenses.append({"path": str(target.relative_to(reuse)), "sha256": digest(target)})
        software.append({"package": package, "version": version, "installed_files_match_wheel": count,
                         "wheel_sha256": digest(wheel), "licenses": licenses})
    archive_path = reuse / "metadata-source.zip"
    with zipfile.ZipFile(archive_path) as archive:
        target = reuse / "licenses/derived-metadata-LICENSE"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read("LICENSE"))
    save(destination / "software-reuse.json", {"status": "PASS", "software": software,
         "derived_metadata_archive_sha256": digest(archive_path), "derived_metadata_license_sha256": digest(target),
         "upstream_research_investment": "UNKNOWN_NOT_NEUMANN_LEARNED_TRAINING"})
    save(destination / "manifest.json", {p.name: digest(p) for p in destination.glob("*.json") if p.name != "manifest.json"})
    print(json.dumps({"status": "PASS", "numerical_witnesses": numerical, "envelope": envelope, "wheel_files": {s["package"]: s["installed_files_match_wheel"] for s in software}}))


if __name__ == "__main__":
    audit(Path(sys.argv[1]))
