"""D0 extension from already audited opened evidence; no new model experiment."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save
from neumann1.contraction_structure import certify_path, validate_public
from neumann1.native_perspective_catalog import NativePerspectiveCatalog, topology_key
from neumann1.representation_program import verify_original
from neumann1.representation_rewrite_certificate import check_certificate
from neumann1.structural_data_rights import LineageGuard, DataUseError
from neumann1.structural_experience import problem_view, offline_experience


def verified_source(cont, preparation, first, key):
    receipt = json.loads((cont / preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(cont / first / "report.json") == receipt[key]
    assert digest(cont / first / "manifest.json") == receipt["manifest_sha256"]
    manifest = json.loads((cont / first / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(cont / first / filename) == pin for filename, pin in manifest.items())
    return {"first": first, "report_sha256": digest(cont / first / "report.json"), "manifest_sha256": digest(cont / first / "manifest.json")}


def build(workspace, output):
    cont = workspace / "Continuation"
    screen = cont / "STRUCTURAL_SCREEN_FIRST"
    source_pins = [verified_source(cont, prep, first, "report_sha256") for prep, first in [
        ("STRUCTURAL_SCREEN_PREPARATION", "STRUCTURAL_SCREEN_FIRST"),
        ("CONTRACTION_CHALLENGE_PREPARATION", "CONTRACTION_CHALLENGE_FIRST"),
        ("CONTRACTION_KERNEL_PREPARATION", "CONTRACTION_KERNEL_FIRST")]]
    cases = {p.stem: (p, json.loads(p.read_text(encoding="utf-8"))) for p in (screen / "cases").glob("*.json")}
    output.mkdir(parents=True, exist_ok=False)
    (output / "records").mkdir()
    groups = defaultdict(list)
    for source in sorted((screen / "observations").glob("*.jsonl")):
        for line, packed in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            o = json.loads(packed)
            route = o.get("route", o.get("strategy"))
            groups[("STRUCTURAL_SCREEN", o["case_id"], route)].append((source, line, o))
    for source in sorted((cont / "CONTRACTION_CHALLENGE_FIRST").glob("tensor_*.json")):
        o = json.loads(source.read_text(encoding="utf-8"))
        groups[("CONTRACTION_CHALLENGE", o["case_id"], f"{o['variant']}_seed{o['seed']}")].append((source, None, o))
    source = cont / "CONTRACTION_KERNEL_FIRST/observations.json"
    for position, o in enumerate(json.loads(source.read_text(encoding="utf-8"))):
        groups[("CONTRACTION_KERNEL", "tensor_lm_batch_likelihood_brackets_4_4d", o["route"])].append((source, position, o))
    experiences, native, negatives = [], [], 0
    public_assets = {}
    statuses = Counter()
    for number, ((study, identifier, route), samples) in enumerate(sorted(groups.items())):
        case_path, case = cases[identifier]
        original = case["original"] if case["kind"] == "proof" else case["public"]
        public_assets[identifier] = {"role": "D", "path": str(case_path.relative_to(workspace)), "sha256": digest(case_path),
            "problem_kind": case["kind"], "allowed_use": "opened_development_only", "runtime": True,
            "equivalence_group": "opened-structural-screen/" + identifier,
            "historically_opened": True, "fresh_eligible": False}
        representative = samples[0][2]
        proposals = []
        cost_samples = []
        for artifact, position, o in samples:
            status = o.get("status", "ORIGINAL_TASK_ACCEPTED" if o.get("accepted") else "ORIGINAL_TASK_FAILED")
            statuses[status] += 1
            reference = {"path": str(artifact.relative_to(workspace)), "sha256": digest(artifact), "position": position,
                         "position_convention": "1-based JSONL line" if artifact.suffix == ".jsonl" else "0-based array index or single JSON"}
            costs = {k: v for k, v in o.items() if k.endswith("_seconds") and isinstance(v, (float, int))}
            if "queries" in o:
                costs["actual_queries"] = o["queries"]
            cost_samples.append({"status": status, "source": reference, "measured_latency_fields": costs,
                "latency_unit": "seconds", "total_cost_missing": "complete_query_seconds" not in o and "first_query_seconds" not in o,
                "unknown_resources": ["energy", "money", "hardware_FLOPs", "actual_peak_RSS"],
                "measurement_contract": source_pins[["STRUCTURAL_SCREEN", "CONTRACTION_CHALLENGE", "CONTRACTION_KERNEL"].index(study)]["report_sha256"]})
            if case["kind"] == "proof":
                if o["certificate"] and o["certificate"]["steps"] and route != "FREE_FULL_POLYNOMIAL":
                    validity = check_certificate(original, o["candidate"], o["certificate"])
                else:
                    validity = verify_original(original, o["candidate"])
                assert validity["accepted"] and o["accepted"]
                candidate = {"program": o["candidate"], "proof": o["certificate"], "authority": validity["authority"]}
                if o["false_control"] is not None:
                    false = check_certificate(original, o["candidate"], case["false_certificate"])
                    assert not false["accepted"] and not o["false_control"]["accepted"]
                    negatives += 1
            elif "path" in o:
                certificate = certify_path(original, o["path"])
                assert certificate == o["certificate"]
                candidate = {"path": o["path"], "certificate": certificate,
                             "authority": "INDEX_CONSERVATION_NOT_ORIGINAL_DATASET_ANSWER"}
                if o.get("oracle_used") is False and study != "CONTRACTION_KERNEL":
                    native.append({"public": original, "path": o["path"], "source": reference,
                                   "oracle_used": False, "learned": False})
            else:
                candidate = None
            cost_samples[-1]["candidate_sha256"] = hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if candidate is not None else None
            if candidate is not None and candidate not in proposals:
                proposals.append(candidate)
        experience = {"schema": "neumann.structural-experience.v1", "record_id": f"experience_{number:04d}",
            "source_study": study, "original_problem_id": identifier, "source_artifact_sha256": digest(case_path),
            "problem_asset": public_assets[identifier], "route": route,
            "representation_candidates": proposals, "cost_samples": cost_samples,
            "evidence_status": "OPENED_DEVELOPMENT", "allowed_use": "offline_diagnostic_only",
            "oracle_used": representative.get("oracle_used", False), "learned": False,
            "fresh_eligible": False, "training_activated": False,
            "counterexample": case["false_certificate"] if case["kind"] == "proof" and case["spec"]["motif"] == "FALSE_SHARED" else None,
            "validity_scope": "exact program identity / registered integer-law proof" if case["kind"] == "proof" else
                              "mathematical index conservation; kernel study additionally checks constructed-input numerical agreement",
            "reward_limit": "No per-operation causal cost credit, global optimum or iso-capability efficiency inferred"}
        experiences.append(experience)
        save(output / "records" / (experience["record_id"] + ".json"), experience)
    catalog = NativePerspectiveCatalog(native)
    save(output / "native-catalog.json", {"records": catalog.records, "summary": catalog.summary(), "oracle_excluded": True})
    experience_assets = [{"role": "O", "path": str((output / "records" / (e["record_id"] + ".json")).relative_to(workspace)),
                          "sha256": digest(output / "records" / (e["record_id"] + ".json")), "runtime": False,
                          "allowed_use": "opened_development_only"} for e in experiences]
    save(output / "index.json", {"public_assets": public_assets, "offline_supervision_assets": experience_assets,
                                "fresh_eligible": 0, "training_activated": False})
    # Development-only rebinding regressions, not new holdout/performance evidence.
    checks = []
    for identifier, (_, case) in sorted(cases.items()):
        if case["kind"] != "contraction":
            continue
        p = case["public"]
        _, _, sizes = validate_public(p)
        renamed = {x: chr(0x400 + i) for i, x in enumerate(sizes)}
        variants = {"original": p,
                    "labels_renamed": {"equation": "".join(renamed.get(x, x) for x in p["equation"]), "shapes": p["shapes"]},
                    "dimensions_changed": {"equation": p["equation"], "shapes": [[sizes[x] + 1 for x in term] for term in p["equation"].split("->")[0].split(",")]}}
        for mode, query in variants.items():
            assert topology_key(query) == topology_key(p)
            result = catalog.propose(query, max_work=20_000_000_000, max_intermediate_elements=32 * 2**20)
            if result["status"] == "CERTIFIED_NATIVE_PRIOR":
                assert certify_path(query, result["path"]) == result["certificate"]
            checks.append({"case": identifier, "mode": mode, "status": result["status"],
                           "candidate_count": result["candidate_count"], "numerical_execution": False,
                           "fresh_generalization_claimed": False})
    guard = LineageGuard()
    for identifier, a in public_assets.items():
        record = {"equivalence_group": a["equivalence_group"], "source_artifact_sha256": a["sha256"], "training_exposure": True}
        # Conservative exposure marker is disclosure, not an assertion of training.
        guard.register(record, "opened_development")
        try:
            guard.register(record, "novel_motif")
        except DataUseError:
            pass
        else:
            raise AssertionError("Opened evidence was incorrectly reclassified as fresh")
        assert problem_view(workspace, a)
    assert all(offline_experience(workspace, a)["training_activated"] is False for a in experience_assets)
    save(output / "rebind-regressions.json", checks)
    save(output / "report.json", {"status": "PASS_DATA_EXTRACTION_AND_DEVELOPMENT_REGRESSIONS", "source_pins": source_pins,
        "raw_observations_preserved": sum(len(v) for v in groups.values()), "experience_groups": len(experiences),
        "source_observation_status_counts": dict(statuses), "counterexample_checks_replayed": negatives,
        "public_problems": len(public_assets), "native_procedures_before_deduplication": len(native), "catalog": catalog.summary(),
        "rebind_development_checks": len(checks), "rebind_status_counts": dict(Counter(c["status"] for c in checks)),
        "fresh_eval_reclassification_rejections": len(public_assets), "fresh_eligible": 0,
        "GPU_or_training": False, "G1_admitted": False, "actual_new_tensor_numeric_execution": False,
        "cost_samples_never_pooled_across_contracts": True, "missing_costs_are_not_zero": True,
        "source_pins_this_extension": {p: digest(ROOT / p) for p in ["experiments/build_structural_experience.py", "neumann1/structural_experience.py", "neumann1/native_perspective_catalog.py"]}})
    save(output / "manifest.json", {str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    print((output / "report.json").read_text(encoding="utf-8"), flush=True)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
