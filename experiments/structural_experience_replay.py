"""Independent provenance/semantic replay of extracted opened experiences."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save
from neumann1.contraction_structure import certify_path
from neumann1.native_perspective_catalog import NativePerspectiveCatalog
from neumann1.representation_program import verify_original
from neumann1.representation_rewrite_certificate import check_certificate
from neumann1.structural_experience import problem_view, offline_experience


def read_observation(workspace, reference):
    path = workspace / reference["path"]
    assert digest(path) == reference["sha256"]
    if path.suffix == ".jsonl":
        return json.loads(path.read_text(encoding="utf-8").splitlines()[reference["position"] - 1])
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj[reference["position"]] if reference["position"] is not None else obj


def candidate_digest(candidate):
    return hashlib.sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def replay(workspace, dataset, output):
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(dataset / path) == pin for path, pin in manifest.items())
    original_report = json.loads((dataset / "report.json").read_text(encoding="utf-8"))
    for pin in original_report["source_pins"]:
        source = workspace / "Continuation" / pin["first"]
        assert digest(source / "report.json") == pin["report_sha256"]
        assert digest(source / "manifest.json") == pin["manifest_sha256"]
    assert all(digest(ROOT / source) == pin for source, pin in original_report["source_pins_this_extension"].items())
    index = json.loads((dataset / "index.json").read_text(encoding="utf-8"))
    sample_count, neg_count = 0, 0
    distinct_counterexamples = set()
    statuses = Counter()
    public = {identifier: problem_view(workspace, asset) for identifier, asset in index["public_assets"].items()}
    for asset in index["offline_supervision_assets"]:
        e = offline_experience(workspace, asset)
        original_view = public[e["original_problem_id"]]
        original = original_view["original"] if original_view["kind"] == "proof" else {k: original_view[k] for k in ["equation", "shapes"]}
        assert not e["fresh_eligible"] and not e["training_activated"] and not e["learned"]
        proposals = {candidate_digest(p): p for p in e["representation_candidates"]}
        for p in proposals.values():
            if original_view["kind"] == "proof":
                if p["proof"] and p["proof"]["steps"] and e["route"] != "FREE_FULL_POLYNOMIAL":
                    checked = check_certificate(original, p["program"], p["proof"])
                else:
                    checked = verify_original(original, p["program"])
                assert checked["accepted"] and checked["authority"] == p["authority"]
                if e["counterexample"]:
                    assert not check_certificate(original, p["program"], e["counterexample"])["accepted"]
                    distinct_counterexamples.add(e["original_problem_id"])
            else:
                assert certify_path(original, p["path"]) == p["certificate"]
        for sample in e["cost_samples"]:
            raw = read_observation(workspace, sample["source"])
            expected_status = raw.get("status", "ORIGINAL_TASK_ACCEPTED" if raw.get("accepted") else "ORIGINAL_TASK_FAILED")
            assert sample["status"] == expected_status
            statuses[expected_status] += 1
            measured = {k: v for k, v in raw.items() if k.endswith("_seconds") and isinstance(v, (int, float))}
            if "queries" in raw:
                measured["actual_queries"] = raw["queries"]
            assert measured == sample["measured_latency_fields"] and sample["latency_unit"] == "seconds"
            assert sample["total_cost_missing"] == ("complete_query_seconds" not in raw and "first_query_seconds" not in raw)
            if sample["candidate_sha256"] is not None:
                p = proposals[sample["candidate_sha256"]]
                if original_view["kind"] == "proof":
                    assert p["program"] == raw["candidate"] and p["proof"] == raw["certificate"]
                    if raw["false_control"] is not None:
                        assert not raw["false_control"]["accepted"]
                        neg_count += 1
                else:
                    assert p["path"] == raw["path"] and p["certificate"] == raw["certificate"]
            else:
                assert "path" not in raw and "candidate" not in raw
            sample_count += 1
    saved = json.loads((dataset / "native-catalog.json").read_text(encoding="utf-8"))
    catalog = NativePerspectiveCatalog(saved["records"])
    # JSON object keys are strings; normalize the in-memory integer histogram.
    assert json.loads(json.dumps(catalog.summary())) == saved["summary"]
    for entry in saved["records"]:
        raw = read_observation(workspace, entry["source"])
        assert raw["oracle_used"] is False and raw.get("learned") is False
        assert entry["path"] == raw["path"]
        assert entry["public"] == {k: public[raw["case_id"]][k] for k in ["equation", "shapes"]}
    assert sample_count == original_report["raw_observations_preserved"] and dict(statuses) == original_report["source_observation_status_counts"]
    assert neg_count == original_report["counterexample_checks_replayed"]
    output.mkdir(parents=True, exist_ok=False)
    save(output / "replay.json", {"status": "PASS", "dataset_manifest_files_checked": len(manifest),
        "dataset_report_sha256": digest(dataset / "report.json"), "dataset_manifest_sha256": digest(dataset / "manifest.json"),
        "original_observation_cost_candidate_links_rechecked": sample_count,
        "experience_groups": len(index["offline_supervision_assets"]), "public_projections_checked": len(public),
        "false_controls_replayed": neg_count, "distinct_counterexample_originals": len(distinct_counterexamples),
        "native_nonoracle_procedure_provenance_checked": len(saved["records"]), "source_reports_modified": False,
        "model_training_or_new_performance_claim": False})
    print((output / "replay.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    replay(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
