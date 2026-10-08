"""Register verified opened evidence without rewriting historical decisions."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save


def register(workspace):
    cont = workspace / "Continuation"
    screen = json.loads((cont / "STRUCTURAL_SCREEN_FIRST/report.json").read_text(encoding="utf-8"))
    replay = json.loads((cont / "STRUCTURAL_SCREEN_AUDIT/replay.json").read_text(encoding="utf-8"))
    completed = json.loads((cont / "STRUCTURAL_SCREEN_COMPLETION_AUDIT/replay.json").read_text(encoding="utf-8"))
    assert replay["status"] == completed["status"] == "PASS"
    assert digest(cont / "STRUCTURAL_SCREEN_FIRST/report.json") == replay["first_report_sha256"]
    challenge = json.loads((cont / "CONTRACTION_CHALLENGE_FIRST/report.json").read_text(encoding="utf-8"))
    kernel = json.loads((cont / "CONTRACTION_KERNEL_FIRST/report.json").read_text(encoding="utf-8"))
    assert digest(cont / "CONTRACTION_CHALLENGE_FIRST/report.json") == completed["challenge_report_sha256"]
    assert digest(cont / "CONTRACTION_KERNEL_FIRST/report.json") == completed["calibration_report_sha256"]
    assets = []
    for source in sorted((cont / "STRUCTURAL_SCREEN_FIRST/cases").glob("*.json")):
        case = json.loads(source.read_text(encoding="utf-8"))
        assets.append({"record_id": case["id"], "source_file": str(source.relative_to(workspace)),
            "source_sha256": digest(source), "kind": case["kind"], "evidence_status": "OPENED_DEVELOPMENT",
            "public_keys": ["public"] if case["kind"] == "contraction" else ["original", "bindings"],
            "oracle_keys": ["supplied_paths"] if case["kind"] == "contraction" else ["supplied"],
            "declared_equivalence_group": "structural-screen-opened/" + case["id"],
            "allowed_use": "diagnostics and building blocks only; no activated training or fresh evaluation",
            "original_tensor_values_available": False if case["kind"] == "contraction" else None,
            "training_activation": False, "fresh_eval_activation": False})
    save(ROOT / "experiments/structural_screen_asset_registry.json", {
        "schema": "neumann.structural-asset-registry.v1", "historical_container": "immutable H; explicit opened D/O projections",
        "assets": assets, "fresh_eligible": 0, "scope": "18 proof programs and 14 third-party derived tensor metadata instances",
        "calibration_numeric_inputs": "Continuation/CONTRACTION_KERNEL_FIRST/inputs_*.npz: constructed opened D",
        "calibration_references": "reference_*.npz: validation-only O, never native planner inputs",
        "native_cached_procedure": "public search result; identical procedural reuse permitted to all comparators",
        "equivalence_guard_scope": "declared identifiers only, not arbitrary mathematical equivalence discovery"})
    mappings = [
        ("STRUCTURAL_SCREEN_PREPARATION", "STRUCTURAL_SCREEN_FIRST", "structural_mechanism_screen.preregister.json"),
        ("CONTRACTION_CHALLENGE_PREPARATION", "CONTRACTION_CHALLENGE_FIRST", "contraction_shortlist_challenge.preregister.json"),
        ("CONTRACTION_KERNEL_PREPARATION", "CONTRACTION_KERNEL_FIRST", "contraction_kernel_calibration.preregister.json")]
    receipts = []
    for prep, first, filename in mappings:
        registration = cont / prep / "preregister.json"
        shutil.copyfile(registration, ROOT / "docs/experiments" / filename)
        receipts.append({"contract": filename, "contract_sha256": digest(registration),
                         "first_report_sha256": digest(cont / first / "report.json"),
                         "first_manifest_sha256": digest(cont / first / "manifest.json")})
    save(ROOT / "docs/experiments/structural_screen_infrastructure.pins.json", {
        "registrations": receipts, "source_replay_sha256": digest(cont / "STRUCTURAL_SCREEN_AUDIT/replay.json"),
        "completion_replay_sha256": digest(cont / "STRUCTURAL_SCREEN_COMPLETION_AUDIT/replay.json"),
        "descriptive_analysis_sha256": digest(cont / "STRUCTURAL_SCREEN_COMPLETION_AUDIT/eligible-route-analysis.json"),
        "software_reuse_sha256": digest(cont / "STRUCTURAL_SCREEN_COMPLETION_AUDIT/software-reuse.json"),
        "learned_model": False, "fresh_eligible": 0, "G1_admitted": False})
    ledger_path = ROOT / "docs/experiments/experiment_decision_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert not ledger["north_star_changed"] and not ledger["historical_verdicts_changed"]
    ledger["structural_mechanism_screen"] = {
        "contract": "docs/experiments/structural_mechanism_screen.preregister.json",
        "first_result": "../../Continuation/STRUCTURAL_SCREEN_FIRST/report.json",
        "proof_assay": {k: screen["proof_assay"][k] for k in ["accepted", "paired_verifier_cases", "verifier_ratio_geomean", "component_10x_pass", "false_controls_rejected", "complete_query_native_over_free_geomean"]},
        "derived_tensor_cases": 14, "certified_modeled_paths": 89, "initial_modeled_shortlist": screen["contraction_shape_screen"]["shortlist"],
        "G1_admitted": False, "original_tensor_answers_available": False, "first_evidence_no_replacement": True}
    ledger["contraction_shortlist_challenge"] = {
        "contract": "docs/experiments/contraction_shortlist_challenge.preregister.json", "cases": challenge["cases"],
        "observations": challenge["observations"], "modeled_work_only": True, "G1_admitted": False,
        "first_evidence_no_replacement": True}
    analysis = json.loads((cont / "STRUCTURAL_SCREEN_COMPLETION_AUDIT/eligible-route-analysis.json").read_text(encoding="utf-8"))
    ledger["contraction_cpu_calibration"] = {
        "contract": "docs/experiments/contraction_kernel_calibration.preregister.json",
        "scope": kernel["scope"], "original_report_complete": kernel["complete"], "actual_queries": kernel["actual_queries"],
        "predeclared_resource_exclusions": completed["exclusions_rechecked"], "descriptive_eligible_envelope": analysis["envelope"],
        "original_dataset_ground_truth": False, "fresh_eligible": 0, "G1_admitted": False,
        "first_evidence_no_replacement": True}
    save(ledger_path, ledger)
    plan_path = ROOT / "docs/experiments/minimum_decisive_plan.v1.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["stages"]["G0"]["subsequent_component_and_external_structure_screens"] = {
        "ledger_keys": ["structural_mechanism_screen", "contraction_shortlist_challenge", "contraction_cpu_calibration"],
        "training_admitted": False, "not_new_global_negative_claim": True,
        "remaining_question": "Does learned discovery improve complete cost on genuinely unseen structures versus equally reusable mature symbolic planners?",
        "next_design_requirement": "independent economically meaningful structural domains; same cheap proof/compiler/cache rights; register thresholds before performance"}
    save(plan_path, plan)
    print(json.dumps({"opened_assets_registered": len(assets), "fresh_eligible": 0, "GPU_or_training_started": False}))


if __name__ == "__main__":
    register(Path(sys.argv[1]))
