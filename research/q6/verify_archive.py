"""Read-only integrity audit; this does not replace original semantic grading."""
from __future__ import annotations
import gzip
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from neumann1.q6.contracts import digest

OUT = ROOT / "docs/research/q6/results/source_v1_20261112"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT / name).read_text())


def fold(tid):
    return int(hashlib.sha256(("q6-transport-fold-v1:" + tid).encode()).hexdigest(), 16) % 5


def audit():
    freeze, primary = load("freeze.json"), load("result.json")
    for name, expected in freeze["code_sha256"].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in freeze["protected_sha256"].items():
        assert sha(ROOT / name) == expected, name
        original = subprocess.check_output(["git", "-C", str(ROOT), "show", freeze["base_commit"] + ":" + name])
        assert hashlib.sha256(original).hexdigest() == expected, name
    assert sha(OUT / "source_artifacts.json") == freeze["source_artifacts_sha256"]
    artifacts = load("source_artifacts.json")
    assert len(artifacts) == freeze["admitted_artifacts"] == 57
    for a in artifacts:
        assert digest({k: v for k, v in a.items() if k != "artifact_id"}) == a["artifact_id"]
        assert a["source_verification"]["method_digest"] == digest(a["executable_method"])
    for f in range(5):
        path = OUT / ("inventory_fold_%d.json" % f)
        assert sha(path) == freeze["folds"][str(f)]["file_sha256"]
        inventory = json.loads(path.read_text())
        assert all(fold(tid) != f for tid in inventory["donor_ids"])
    assert sha(OUT / "programs.jsonl") == primary["programs_sha256_before_grading"]
    programs = [json.loads(line) for line in (OUT / "programs.jsonl").open()]
    grades = {(r["id"], r["arm"]): r for r in primary["grades"]}
    assert len(programs) == len(grades) == primary["jobs"] == 320
    ledger = {}
    with gzip.open(OUT / "rejected_correspondences.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            key = r["id"], r["arm"]
            assert key not in ledger
            ledger[key] = r["rejected_candidates"]
    for r in programs:
        key = r["id"], r["arm"]
        assert all(grades[key][k] == v for k, v in r.items())
        assert len(ledger[key]) == r["rejected_candidate_ledger_count"]
        assert digest(ledger[key]) == r["rejected_candidate_ledger_sha256"]
    assert set(ledger) == set(grades)
    control = load("primitive_control_result.json")
    assert sha(OUT / "primitive_control_programs.jsonl") == control["programs_sha256_before_control_grading"]
    assert control["tasks"] == 40 and control["same_original_witnesses_solved_without_source_kernels"] == []
    assert primary["compound_attributed_exclusive"] == control["source_principle_attribution_survives"] == ["rule/c130"]
    assert primary["mechanism_positive"] and not primary["strong_source_gate"]
    assert primary["global_Q6"] == "OPEN" and not primary["independent_FRESH_opened"]
    assert not primary["errors"]
    replay = load("witness_generation_replay.json")["records"]
    assert next(r for r in replay if r["arm"] == "C")["generation_reproduced_exact_AST"]
    assert next(r for r in replay if r["arm"] == "C-no-map")["no_map_still_UNKNOWN"]
    negative = load("negative_controls_complete.json")
    assert negative["all_changed_source_controls_rejected"]
    assert len(negative["shuffled_controls"]) == 102
    return {
        "scope": "archive integrity/consistency only; not a fresh semantic evaluation",
        "frozen_code_files_unchanged": len(freeze["code_sha256"]),
        "protected_baseline_files_unchanged": len(freeze["protected_sha256"]),
        "fold_libraries_verified": 5,
        "artifact_digests_verified": len(artifacts),
        "primary_programs_and_grades_verified": len(programs),
        "failed_candidate_ledgers_verified": len(ledger),
        "failed_reconstructed_candidates_preserved": sum(len(x) for x in ledger.values()),
        "post_primary_programs_hash_verified": True,
        "recorded_witness_generation_reproduced": True,
        "decision_consistent": True,
    }


if __name__ == "__main__":
    report = audit()
    seal = OUT / "seal.json"
    if seal.exists():
        entries = json.loads(seal.read_text())["files"]
        for name, expected in entries.items():
            p = ROOT / name
            assert p.stat().st_size == expected["bytes"] and sha(p) == expected["sha256"], name
        report["final_seal_entries_verified"] = len(entries)
    print(json.dumps(report, indent=2))
