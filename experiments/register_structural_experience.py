"""Publish only local indices/pins for audited inactive D0 extensions."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save


def register(workspace):
    dataset = workspace / "Continuation/STRUCTURAL_EXPERIENCE_V2_2026-10-07"
    audit = workspace / "Continuation/STRUCTURAL_EXPERIENCE_AUDIT_2026-10-07/replay.json"
    replay = json.loads(audit.read_text(encoding="utf-8"))
    assert replay["status"] == "PASS" and digest(dataset / "report.json") == replay["dataset_report_sha256"]
    assert digest(dataset / "manifest.json") == replay["dataset_manifest_sha256"]
    report = json.loads((dataset / "report.json").read_text(encoding="utf-8"))
    index = json.loads((dataset / "index.json").read_text(encoding="utf-8"))
    assert not report["GPU_or_training"] and not report["G1_admitted"] and not index["training_activated"]
    save(ROOT / "experiments/structural_experience_asset_registry.json", {
        "schema": "neumann.structural-experience-registry.v1", "index": str((dataset / "index.json").relative_to(workspace)),
        "index_sha256": digest(dataset / "index.json"), "public_assets": index["public_assets"],
        "offline_supervision_assets": index["offline_supervision_assets"], "fresh_eligible": 0,
        "training_activated": False, "required_loader": "neumann1.structural_experience",
        "native_catalog": str((dataset / "native-catalog.json").relative_to(workspace)),
        "native_catalog_sha256": digest(dataset / "native-catalog.json")})
    pins = {"schema": "neumann.structural-experience-pins.v1", "sources": report["source_pins_this_extension"],
        "replay_source_sha256": digest(ROOT / "experiments/structural_experience_replay.py"),
        "report_sha256": digest(dataset / "report.json"), "manifest_sha256": digest(dataset / "manifest.json"),
        "replay_sha256": digest(audit), "original_sources": report["source_pins"],
        "fresh_eligible": 0, "training_activated": False, "G1_admitted": False}
    save(ROOT / "docs/experiments/structural_experience.pins.json", pins)
    ledger_path = ROOT / "docs/experiments/experiment_decision_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert not ledger["north_star_changed"] and not ledger["historical_verdicts_changed"] and ledger["global_questions_closed"] == []
    ledger["d0_structural_experience"] = {"status": "AVAILABLE_OPENED_DIAGNOSTIC_VIEWS_NOT_TRAINING",
        "raw_observations": report["raw_observations_preserved"], "experience_groups": report["experience_groups"],
        "public_problems": report["public_problems"], "native_unique_programs": report["catalog"]["native_unique_programs"],
        "topology_groups": report["catalog"]["topology_groups"], "rebind_development_checks": report["rebind_development_checks"],
        "fresh_eligible": 0, "training_activated": False, "G1_admitted": False,
        "result": "../../Continuation/STRUCTURAL_EXPERIENCE_V2_2026-10-07/report.json",
        "replay": "../../Continuation/STRUCTURAL_EXPERIENCE_AUDIT_2026-10-07/replay.json"}
    ledger["g1"]["additional_native_reuse_comparator"] = {
        "source": "neumann1/native_perspective_catalog.py", "learned": False,
        "scope": "label rename and dimension rebinding at fixed operand-order incidence; no unknown-topology discovery",
        "actual_new_cost_advantage_measured": False, "same_reuse_rights_required_for_all_arms": True}
    save(ledger_path, ledger)
    plan_path = ROOT / "docs/experiments/minimum_decisive_plan.v1.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["stages"]["D0"]["structural_experience_extension"] = ledger["d0_structural_experience"]
    save(plan_path, plan)
    print(json.dumps({"registered_experience_groups": report["experience_groups"], "native_programs": report["catalog"]["native_unique_programs"], "G1_admitted": False}))


if __name__ == "__main__":
    register(Path(sys.argv[1]))
