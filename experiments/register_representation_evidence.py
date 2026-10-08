"""Register completed opened evidence; preserve prior science and sealed rights."""
from datetime import datetime, timezone
import importlib.metadata as md
import json
from pathlib import Path
import shutil
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.representation_headroom import ROOT, digest, save


def register(workspace):
    preparation = workspace / "Continuation/G0_COMPOSITION_PREPARATION"
    first = workspace / "Continuation/G0_COMPOSITION_FIRST"
    audit = workspace / "Continuation/G0_COMPOSITION_AUDIT"
    replay = json.loads((audit / "replay.json").read_text(encoding="utf-8"))
    assert replay["status"] == "PASS"
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    assert digest(first / "report.json") == replay["report_sha256"]
    receipt = preparation / "software-reuse-receipt.json"
    if receipt.exists():
        raise RuntimeError("Preserve existing first software audit")
    software = []
    for package, version in [("sympy", "1.14.0"), ("mpmath", "1.3.0")]:
        wheel = preparation / "wheels" / f"{package}-{version}-py3-none-any.whl"
        distribution = md.distribution(package)
        assert distribution.version == version
        count = 0
        licenses = []
        with zipfile.ZipFile(wheel) as archive:
            for member in archive.namelist():
                if member.startswith(package + "/") and not member.endswith("/"):
                    actual = distribution.locate_file(member)
                    assert Path(actual).read_bytes() == archive.read(member), member
                    count += 1
                if "license" in member.lower() and ".dist-info/" in member and not member.endswith("/"):
                    target = preparation / "licenses" / package / Path(member).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(member))
                    licenses.append({"path": str(target.relative_to(preparation)), "sha256": digest(target)})
        software.append({"package": package, "version": version, "wheel_sha256": digest(wheel),
                         "installed_package_files_match_wheel": count, "licenses": licenses})
    save(receipt, {"status": "PASS", "software": software,
                   "audit_utc": datetime.now(timezone.utc).isoformat(),
                   "upstream_development_investment": "UNKNOWN_NOT_NEUMANN_LEARNED_TRAINING"})
    save(audit / "audit-manifest.json", {p.name: digest(p) for p in audit.glob("*.json") if p.name != "audit-manifest.json"})
    assets = []
    for path in sorted((first / "cases").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        assets.append({"record_id": case["spec"]["id"], "source_file": str(path.relative_to(first)),
            "source_sha256": digest(path), "structural_family": "exact_integer_polynomial_programs",
            "equivalence_group": "composition-opened/" + case["spec"]["id"],
            "motif_lineage": case["lineage"], "exposure": "OPENED_DEVELOPMENT",
            "public_keys": ["original", "bindings"], "oracle_keys": ["supplied"],
            "metadata_not_runtime_keys": ["spec", "lineage"], "training_activation": False,
            "fresh_eval_activation": False,
            "runtime_projection": "Typed original program only to CAS/compiler; supplied only FREE_COMPOSED offline upper-bound arm"})
    save(ROOT / "experiments/representation_asset_registry.json", {
        "schema": "neumann.structural-asset-registry.v1", "origin": "../../Continuation/G0_COMPOSITION_FIRST",
        "manifest_sha256": digest(first / "manifest.json"), "role": "H container with explicit D/O projections",
        "domain_count": 1, "fresh_eligible": 0, "assets": assets})
    shutil.copyfile(preparation / "preregister.json", ROOT / "docs/experiments/g0_composition.preregister.json")
    pins = {"schema": "neumann.representation-infrastructure-pins.v1",
        "learned_model": False, "G1_admitted": False,
        "registered_core_sources": json.loads((preparation / "preregister.json").read_text(encoding="utf-8"))["sources"],
        "certificate_interface_post_result_not_scored": {
            "source": "neumann1/representation_rewrite_certificate.py",
            "sha256": digest(ROOT / "neumann1/representation_rewrite_certificate.py"),
            "status": "SEMANTIC_TESTS_ONLY_NO_TIMED_HEADROOM_OR_LEARNED_DISCOVERY_RESULT"},
        "software_reuse_receipt_sha256": digest(receipt), "first_report_sha256": digest(first / "report.json"),
        "first_manifest_sha256": digest(first / "manifest.json"), "replay_sha256": digest(audit / "replay.json"),
        "phase_analysis_sha256": digest(audit / "phase-analysis.json")}
    save(ROOT / "docs/experiments/representation_infrastructure.pins.json", pins)
    ledger_path = ROOT / "docs/experiments/experiment_decision_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["g0_composition"] = {"contract": "docs/experiments/g0_composition.preregister.json",
        "first_result": "../../Continuation/G0_COMPOSITION_FIRST/report.json", "decision": report["decision"],
        "domain_count": 1, "cases": 18, "accepted_observations": report["accepted"],
        "regimes": report["regimes"], "first_evidence_no_replacement": True,
        "original_task_replay": replay["accepted_observations_rechecked"], "G1_admitted": False}
    ledger["g1"]["new_headroom_required"] = True
    ledger["g1"]["certificate_interface"] = pins["certificate_interface_post_result_not_scored"]
    save(ledger_path, ledger)
    plan_path = ROOT / "docs/experiments/minimum_decisive_plan.v1.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["stages"]["G0"]["additional_registered_screen"] = ledger["g0_composition"]
    save(plan_path, plan)
    print(json.dumps({"registered_opened_cases": len(assets), "fresh_eligible": 0,
                      "installed_wheel_package_files_verified": {s["package"]: s["installed_package_files_match_wheel"] for s in software}}))


if __name__ == "__main__":
    register(Path(sys.argv[1]))
