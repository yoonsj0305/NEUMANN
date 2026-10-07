"""Register opened projections and append a result without changing first evidence."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save
from neumann1.structural_experience import problem_view, offline_experience
from neumann1.structural_data_rights import authorize, DataUseError


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(workspace):
    prep = workspace / "Continuation/TRANSFER_HEADROOM_PREPARATION"
    first = workspace / "Continuation/TRANSFER_HEADROOM_FIRST"
    audit = workspace / "Continuation/TRANSFER_HEADROOM_AUDIT_2026-10-07/replay.json"
    assets = workspace / "Continuation/TRANSFER_HEADROOM_ASSETS_2026-10-07"
    final = workspace / "Continuation/TRANSFER_HEADROOM_FINALIZATION_2026-10-07"
    reg, report, replay = read(prep / "preregister.json"), read(first / "report.json"), read(audit)
    assert report["decision"] == "INCOMPLETE_NO_ADMISSION"
    assert replay["status"] == "PASS_RETAINED_COMPLETE_AND_FAILED_EVIDENCE"
    receipt = read(prep / "first-result-receipt.json")
    assert digest(first / "report.json") == receipt["report_sha256"] == replay["report_sha256"]
    assert digest(first / "manifest.json") == receipt["manifest_sha256"] == replay["manifest_sha256"]
    assert all(digest(first / p) == pin for p, pin in read(first / "manifest.json").items())
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    assets.mkdir(exist_ok=False)
    (assets / "public").mkdir()
    (assets / "offline").mkdir()
    index = {"schema": "neumann.transfer-opened-assets.v1", "public_assets": {}, "offline_assets": {},
             "fresh_eligible": 0, "training_activated": False, "G1_admitted": False}
    events = read(first / "events.json")
    for summary in report["cases"]:
        identifier = summary["id"]
        source = first / "cases" / (identifier + ".json")
        case = read(source)
        public_path, offline_path = assets / "public" / source.name, assets / "offline" / source.name
        save(public_path, {"public": case["public"], "lineage": case["lineage"], "source_case_sha256": digest(source)})
        rows = [json.loads(line) for line in (first / identifier / "observations.jsonl").read_text(encoding="utf-8").splitlines()]
        save(offline_path, {"case": case, "summary": summary, "worker_event": next(e for e in events if e["id"] == identifier),
                            "observations": rows, "first_source_case_sha256": digest(source),
                            "upstream_prior_research_cost": "UNKNOWN", "original_dataset_answers_available": False})
        common = {"problem_kind": "contraction", "allowed_use": "opened_development_only", "historically_opened": True,
                  "fresh_eligible": False, "equivalence_group": "opened-transfer-source/" + identifier.rsplit("_", 1)[0]}
        for role, path, field in [("D", public_path, "public_assets"), ("O", offline_path, "offline_assets")]:
            index[field][identifier] = {**common, "role": role, "runtime": role == "D", "path": str(path.relative_to(workspace)), "sha256": digest(path)}
    save(assets / "index.json", index)
    denied = 0
    for identifier, asset in index["public_assets"].items():
        assert set(problem_view(workspace, asset)) == {"kind", "equation", "shapes"}
        assert offline_experience(workspace, index["offline_assets"][identifier])["case"]["id"] == identifier
        for candidate, purpose in [(asset, "train"), (asset, "fresh_eval"), (index["offline_assets"][identifier], "development_problem")]:
            try:
                authorize(candidate, purpose)
            except DataUseError:
                denied += 1
            else:
                raise AssertionError("Opened asset unexpectedly authorized")
    registry_path = ROOT / "experiments/perspective_transfer_asset_registry.json"
    save(registry_path, {**index, "index": str((assets / "index.json").relative_to(workspace)), "index_sha256": digest(assets / "index.json")})
    contract = ROOT / "docs/experiments/perspective_transfer_headroom.preregister.json"
    contract.write_bytes((prep / "preregister.json").read_bytes())
    entry = {"contract": str(contract.relative_to(ROOT)), "decision": report["decision"], "cases": 8, "evaluable_cases": 6,
             "first_result": "../../Continuation/TRANSFER_HEADROOM_FIRST/report.json",
             "replay": "../../Continuation/TRANSFER_HEADROOM_AUDIT_2026-10-07/replay.json",
             "query_observations": 126, "accepted_observations": 117, "abstained_observations": 9,
             "actual_numeric_queries": 234, "cases_without_reference": 2, "offline_failure_trace_available": False,
             "regimes": report["regimes"], "completed_case_ratios": {c["id"]: c["ratios"] for c in report["cases"] if c["complete"]},
             "scope": report["scope"], "first_evidence_no_replacement": True, "fresh_eligible": 0, "G1_admitted": False}
    ledger_path = ROOT / "docs/experiments/experiment_decision_ledger.json"
    ledger = read(ledger_path)
    assert "perspective_transfer_headroom" not in ledger
    ledger["perspective_transfer_headroom"] = entry
    save(ledger_path, ledger)
    plan_path = ROOT / "docs/experiments/minimum_decisive_plan.v1.json"
    plan = read(plan_path)
    plan["stages"]["G0"]["perspective_transfer_headroom"] = entry
    save(plan_path, plan)
    prior_pins = read(ROOT / "docs/experiments/structural_experience.pins.json")
    old_verified = []
    for old in prior_pins["original_sources"] + [{"first": "STRUCTURAL_EXPERIENCE_V2_2026-10-07", "report_sha256": prior_pins["report_sha256"], "manifest_sha256": prior_pins["manifest_sha256"]}]:
        folder = workspace / "Continuation" / old["first"]
        assert digest(folder / "report.json") == old["report_sha256"] and digest(folder / "manifest.json") == old["manifest_sha256"]
        old_verified.append(old["first"])
    pins = {"schema": "neumann.transfer-headroom-pins.v1", "contract_sha256": digest(contract), "sources": reg["sources"],
            "report_sha256": digest(first / "report.json"), "manifest_sha256": digest(first / "manifest.json"), "replay_sha256": digest(audit),
            "replay_source_sha256": digest(ROOT / "experiments/perspective_transfer_replay.py"), "asset_index_sha256": digest(assets / "index.json"),
            "research_report_sha256": digest(ROOT / "docs/research/perspective_transfer_headroom_2026-10-07.md"),
            "registry_sha256": digest(registry_path), "finalization_source_sha256": digest(Path(__file__)),
            "prior_first_pins_unchanged": old_verified, "G1_admitted": False, "fresh_eligible": 0}
    pins_path = ROOT / "docs/experiments/perspective_transfer_headroom.pins.json"
    save(pins_path, pins)
    final.mkdir(exist_ok=False)
    save(final / "receipt.json", {"status": "PASS", "first_evidence_unchanged": True, "all_first_manifest_files_rechecked": 286,
                                 "D_public_projections": 8, "O_offline_records": 8, "rights_denials": denied,
                                 "prior_first_pins_unchanged": old_verified, "pins_sha256": digest(pins_path),
                                 "decision": report["decision"], "training_activated": False, "G1_admitted": False})
    print((final / "receipt.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
