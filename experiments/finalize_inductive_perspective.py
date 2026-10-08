"""Append engineering readiness and compress candidates without gate promotion."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save
from neumann1.inductive_perspective import validate_problem
from neumann1.structural_data_rights import DataUseError, authorize, load_json_view
from neumann1.structural_experience import offline_experience


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(workspace):
    prep = workspace / "Continuation/INDUCTIVE_PERSPECTIVE_PREPARATION"
    first = workspace / "Continuation/INDUCTIVE_PERSPECTIVE_FIRST"
    audit = workspace / "Continuation/INDUCTIVE_PERSPECTIVE_AUDIT/replay.json"
    reg, report, replay = read(prep / "registration.json"), read(first / "report.json"), read(audit)
    receipt = read(prep / "first-result-receipt.json")
    assert report["status"] == "PASS_ENGINEERING_ONLY" and replay["status"] == "PASS_ENGINEERING_AUDIT"
    assert digest(first / "report.json") == receipt["report_sha256"] == replay["original_report_sha256"]
    assert digest(first / "manifest.json") == receipt["manifest_sha256"] == replay["original_manifest_sha256"]
    assert all(digest(first / p) == pin for p, pin in read(first / "manifest.json").items())
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    index = {"schema": "neumann.inductive-engineering-fixtures.v1", "fixtures": {}, "offline": {},
             "fresh_eligible": 0, "training_activated": False, "G1_admitted": False}
    denied = 0
    for summary in report["cases"]:
        identifier = summary["id"]
        common = {"problem_kind": "integer_recurrence", "allowed_use": "opened_development_only", "runtime": False,
                  "equivalence_group": "opened-inductive-engineering/" + identifier.split("_", 1)[0],
                  "historically_opened": True, "fresh_eligible": False}
        for role, folder, key in [("F", "problems", "fixtures"), ("O", "offline", "offline")]:
            source = first / folder / (identifier + ".json")
            asset = {**common, "role": role, "path": str(source.relative_to(workspace)), "sha256": digest(source)}
            index[key][identifier] = asset
            if role == "F":
                validate_problem(load_json_view(workspace, asset, "fixture"))
            else:
                assert "manual_reference" in offline_experience(workspace, asset)
            for purpose in ["train", "fresh_eval", "development_problem"]:
                try:
                    authorize(asset, purpose)
                except DataUseError:
                    denied += 1
                else:
                    raise AssertionError("Engineering fixture unexpectedly promoted")
    registry = ROOT / "experiments/inductive_perspective_asset_registry.json"
    save(registry, index)
    registration = ROOT / "docs/experiments/inductive_perspective.engineering-registration.json"
    registration.write_bytes((prep / "registration.json").read_bytes())
    prior = {"G0_FIRST": "a8869564d350c778c152891cc97b5417cbef031a768c26b616c4578ea625701f",
             "G0_COMPOSITION_FIRST": "fd39c305f236446596d19cc0b2a7244ae9173748692a99d76c7132035b84c39a",
             "STRUCTURAL_SCREEN_FIRST": "6101d85e271446350d7186259c3289065e9c1965e0c9d65d10f046d8acde996b",
             "TRANSFER_HEADROOM_FIRST": "35a3a02219340c95560abcf920a6fc32b527fc115e894a8e059fd17886ca03f1"}
    for folder, pin in prior.items():
        assert digest(workspace / "Continuation" / folder / "report.json") == pin
    portfolio = {"schema": "neumann.compressed-generation-portfolio.v1", "kind": "RESEARCH_PRIORITY_INFERENCE_NOT_GLOBAL_OPTIMALITY",
        "evidence_report_pins": prior, "shared_question": "Does generated goal-sufficient representation remove work beyond equally reusable native generation?",
        "deprioritized_in_registered_scope": [
            {"candidate": "role-scorer model replacement", "reason": "retained capability failures; no serial replacement mainline"},
            {"candidate": "known graph/matrix reduction selector", "evidence": "G0_FIRST", "reason": "strong native already captures most measured benefit"},
            {"candidate": "tensor order selector", "evidence": "TRANSFER_HEADROOM_FIRST", "reason": "6 completed weak margins,2 failed references; preserve incomplete decision"},
            {"candidate": "fixed integer rewrite selector", "evidence": "G0_COMPOSITION_FIRST", "reason": "registered first/reuse gates failed; keep CAS/proof infrastructure"}],
        "retained_for_headroom_design": [
            {"candidate": "generated sufficient coordinates and inductive summaries", "kernel_implemented": True,
             "native_generator_implemented": True, "learned_policy_implemented": False, "headroom_admitted": False,
             "current_easy_fixtures_solved_by_native": True, "training_on_these_fixtures": False},
            {"candidate": "goal-preserving recursive summaries", "kernel_implemented": False,
             "strong_comparator_required": "Synduce / equivalent recursive synthesis", "headroom_admitted": False}],
        "next_screen_requires": ["public semantic sufficiency", "capable equally reusable strongest declared baseline",
                                 "registered complete cost and bounded failures", "independent structural lineage", "joint candidate screen"],
        "G1_if_admitted": {"single_joint_tournament": True, "arms": ["Neural Direct", "Symbolic Generated", "Learned Fixed Selector", "Learned Generated Perspective"],
                           "ablations": ["generation", "verification", "transfer learning"]},
        "neural_training_authorized_by_this_portfolio": False, "global_questions_closed": [], "G1_admitted": False}
    portfolio_path = ROOT / "docs/experiments/representation_generation_portfolio.json"
    save(portfolio_path, portfolio)
    entry = {"kind": reg["kind"], "status": report["status"], "result": "../../Continuation/INDUCTIVE_PERSPECTIVE_FIRST/report.json",
             "audit": "../../Continuation/INDUCTIVE_PERSPECTIVE_AUDIT/replay.json", "certified_proposals": 8, "universal_identities": 40,
             "paired_numeric_comparisons": 96, "large_horizon_formula_checks": 24, "false_proposals_rejected": 3,
             "native_also_solves_all_fixtures": True, "learned_policy_implemented": False, "headroom_measured": False,
             "G0_passed": False, "G1_admitted": False, "fresh_eligible": 0}
    ledger_path = ROOT / "docs/experiments/experiment_decision_ledger.json"
    ledger = read(ledger_path)
    assert "inductive_generation_engineering" not in ledger
    ledger["inductive_generation_engineering"] = entry
    save(ledger_path, ledger)
    plan_path = ROOT / "docs/experiments/minimum_decisive_plan.v1.json"
    plan = read(plan_path)
    plan["stages"]["G1"]["engineering_generation_interface"] = entry
    plan["compressed_candidate_portfolio"] = str(portfolio_path.relative_to(ROOT))
    save(plan_path, plan)
    pins = {"schema": "neumann.inductive-engineering-pins.v1", "registration_sha256": digest(registration), "sources": reg["sources"],
            "first_report_sha256": digest(first / "report.json"), "first_manifest_sha256": digest(first / "manifest.json"),
            "audit_sha256": digest(audit), "audit_source_sha256": digest(ROOT / "experiments/inductive_perspective_replay.py"),
            "registry_sha256": digest(registry), "portfolio_sha256": digest(portfolio_path),
            "research_report_sha256": digest(ROOT / "docs/research/representation_generation_2026-10-07.md"),
            "finalization_source_sha256": digest(Path(__file__)), "old_first_report_pins_unchanged": prior,
            "G0_passed": False, "G1_admitted": False, "fresh_eligible": 0}
    pins_path = ROOT / "docs/experiments/inductive_perspective.pins.json"
    save(pins_path, pins)
    final = workspace / "Continuation/INDUCTIVE_PERSPECTIVE_FINALIZATION"
    final.mkdir(exist_ok=False)
    save(final / "receipt.json", {"status": "PASS_ENGINEERING_FINALIZATION", "first_evidence_unchanged": True,
         "fixtures_registered": 4, "O_offline_registered": 4, "rights_denials": denied, "old_first_reports_unchanged": list(prior),
         "pins_sha256": digest(pins_path), "test_checks_in_session": 116, "tests_are_capability_gate": False,
         "neural_policy_implemented": False, "training_activated": False, "G1_admitted": False})
    print((final / "receipt.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
