"""Reconcile selected OPENED historical evidence; never open sealed datasets.

This is D0 + retrospective cost sensitivity, not a performance experiment or
rejudgment. Inputs are an explicit historical whitelist, not a workspace scan.
No solver, training, benchmark execution or hidden Oracle payload is invoked.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import exp, log
from pathlib import Path
from statistics import median
import subprocess


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def identity_row(root, path, expected=None):
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("declared evidence path leaves root")
    if not resolved.is_file():
        return {"path": path, "status": "MISSING_EXCLUDED"}
    observed = file_sha(resolved)
    return {"path": path, "sha256": observed, "bytes": resolved.stat().st_size,
            "status": "MATCH" if expected == observed else "MISMATCH" if expected else "RECORDED",
            "expected_sha256": expected}


def recursive_sensitivity(work):
    """Delete one measured stage counterfactually, keep all other costs fixed.

    This optimistic bound grants FREE a right unavailable to native. It is only
    useful for rejecting verifier-only investment in this measured cold scope.
    It does not measure a new executor, a warm service or an intrinsic bound.
    """
    root = work / "Continuation/COMPRESSED_RECURSIVE_COST_FIRST"
    prior_audit = load(work / "GitHub/NEUMANN/docs/experiments/results/structural_evidence_2026_10_07/compressed_recursive_cost_audit.json")
    if (file_sha(root / "report.json") != prior_audit["first_report_sha256"] or
            file_sha(root / "manifest.json") != prior_audit["first_manifest_sha256"]):
        raise ValueError("historical cost evidence differs from published independent audit")
    manifest = load(root / "manifest.json")
    for relative, expected in manifest.items():
        entry = identity_row(root, relative, expected)
        if entry["status"] != "MATCH":
            raise ValueError("historical cost manifest mismatch")
    report = load(root / "report.json")
    observations = load(root / "observations.json")
    values = {}
    component_rows = []
    for row in observations:
        result_path = root / row["worker"] / "result.json"
        if not result_path.resolve().is_relative_to(root.resolve()):
            raise ValueError("historical worker path leaves opened study")
        result = load(result_path)
        proof_compile = result["certificate_and_engine_seconds"]
        total = row["complete_operational_seconds"]
        if not row["accepted"] or not 0 <= proof_compile < total:
            raise ValueError("all historical observations and valid decomposition required")
        key = (row["case"], row["count"], row["route"])
        values.setdefault(key, []).append((total, proof_compile))
        component_rows.append({"case": row["case"], "count": row["count"],
            "route": row["route"], "repeat": row["repeat"],
            "complete_seconds": total, "verify_compile_seconds": proof_compile,
            "generation_seconds": result["generation_seconds"],
            "result_sha256": file_sha(result_path)})
    regimes = {}
    for count in (1, 16):
        bounds, rows = [], []
        for case in sorted({r["case"] for r in observations}):
            native = values[(case, count, "PUBLIC_GENERATIVE_NATIVE")]
            free = values[(case, count, "FREE_VALID_REFERENCE")]
            assert len(native) == len(free) == 3
            bound = median(v[0] for v in native) / median(v[0] - v[1] for v in free)
            bounds.append(bound)
            rows.append({"case": case, "native_over_free_with_zero_verify_compile": bound})
        regimes[str(count)] = {"cases": rows, "geometric_mean": exp(sum(map(log, bounds))/len(bounds)),
                               "maximum": max(bounds), "count_at_least_10": sum(x >= 10 for x in bounds)}
    return {"scope": "retrospective fixed-other-cost sensitivity only; not a new measured speedup",
            "source_report_sha256": file_sha(root / "report.json"),
            "source_observations_sha256": file_sha(root / "observations.json"),
            "first_manifest_sha256": file_sha(root / "manifest.json"),
            "first_manifest_files_rechecked": len(manifest),
            "original_decision_unchanged": report["analysis"]["decision"],
            "observations": len(observations), "components": component_rows,
            "regimes": regimes,
            "decision": "REJECT_VERIFIER_ONLY_AS_10X_ROUTE_IN_THIS_COLD_SCOPE",
            "warm_service_and_other_problem_families": "UNKNOWN"}


def run(work, repo, git, ci_receipt):
    commit = lambda ref: subprocess.check_output([git, "rev-parse", ref], cwd=repo, text=True).strip()
    manifest_path = "docs/experiments/results/structural_evidence_2026_10_07/publication_manifest.json"
    manifest = load(repo / manifest_path)
    rows = []
    for group in ("audit_reports_and_validation", "frozen_registrations"):
        for entry in manifest[group]:
            rows.append(identity_row(repo, entry["path"], entry["sha256"]))
    archives = [identity_row(work, a["local_relative_path"], a["sha256"])
                for a in manifest["original_archives"]]
    source_rows = []
    for study in ("INDUCTIVE_COMPLETE_COST_PREPARATION", "COMPRESSED_RECURSIVE_COST_PREPARATION"):
        registration = load(work / "Continuation" / study / "preregister.json")
        source_rows.extend({**identity_row(repo, p, h), "executed_registration": study}
                           for p, h in registration["sources"].items())
    p112 = work / "Continuation/P112_FIRST/diagnosis.json"
    diagnosis = load(p112)
    p112_archive = identity_row(work, "Continuation/P112_FIRST/NEUMANN_P112_FIRST_EVIDENCE.zip",
                                diagnosis["archive_sha256"])
    ci = load(ci_receipt)
    refs = {ref: commit(ref) for ref in ("HEAD", "origin/main",
            "origin/research/p112-opened-development-v1",
            "origin/research/neumann1-structural-evidence-2026-10-07")}
    ancestry = subprocess.run([git, "merge-base", "--is-ancestor",
        refs["origin/research/p112-opened-development-v1"],
        refs["origin/research/neumann1-structural-evidence-2026-10-07"]], cwd=repo).returncode
    science_trees = {prefix: {ref: commit(ref + ":" + prefix) for ref in (
        "e2a05f5cd31140ad1336708c4f53db0a64a0eae8", "12412bfe88d5efcf6a5a15cf037e9cd79d0ed7a8")}
        for prefix in ("neumann1", "experiments")}
    ok = (all(row["status"] == "MATCH" for row in rows + archives + source_rows + [p112_archive])
          and ancestry == 0 and len(ci["workflow_runs"]) == 7
          and all(r["status"] == "completed" and r["conclusion"] == "success" for r in ci["workflow_runs"])
          and all(len(set(v.values())) == 1 for v in science_trees.values()))
    return {"created_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS_SELECTED_OPENED_EVIDENCE_WITH_EXCLUSIONS" if ok else "INCOMPLETE_OR_MISMATCH",
            "refs": refs, "pr174_is_ancestor_of_pr175": ancestry == 0,
            "ci_receipt_sha256": file_sha(ci_receipt), "ci_commit": "12412bfe88d5efcf6a5a15cf037e9cd79d0ed7a8",
            "previous_publication_science_trees": science_trees,
            "publication_manifest_sha256": file_sha(repo / manifest_path),
            "publication_files": rows, "original_archives": archives, "current_executed_source_pins": source_rows,
            "P112": {"diagnosis_sha256": file_sha(p112), "archive": p112_archive,
                     "source_head": diagnosis["source_head"], "decision": diagnosis["decision"],
                     "note": "PR174 body describes pre-execution state; later opened first evidence is FAIL 7/12"},
            "protected_reference_sha256": file_sha(repo / "docs/research/frozen_north_star.md"),
            "exclusions": ["sealed Decision3 payloads not read or hashed", "absent old raw archives",
                           "lost 26-view OCaml5 first archive remains lost; separate recovery not a replacement",
                           "source pins are not a complete environment closure",
                           "D0 identity repair and original duplicate-ID result remain separate",
                           "no new performance, fresh evaluation, learned discovery, GPU or training"],
            "recursive_cost_sensitivity": recursive_sensitivity(work),
            "G0_new_execution": False, "G1_admitted": False, "G2_admitted": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--git", required=True)
    parser.add_argument("--ci-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.workspace, args.repo, args.git, args.ci_receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "sensitivity": {
        key: {k: v for k, v in value.items() if k != "cases"}
        for key, value in result["recursive_cost_sensitivity"]["regimes"].items()}}))
