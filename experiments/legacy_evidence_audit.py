"""D0 core LP asset audit, not a performance experiment or training entry point.

Explicit allowlist only: v100..104 and their already-opened source authorities.
Reuses original first-byte/receipt guards and original LP certificate checker.
No sealed-set file, optimizer, generator, model, or pickle is opened/executed.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from unittest.mock import patch

from experiments.q5_first_archive import source_pin, result_pin
from experiments.q5_transfer_first_archive import pin as transfer_pin
from experiments.q5_register import evidence_module
from neumann1.structural_data_rights import LineageGuard


HEAD = "a0119180e743f5115b21847fdb6ac6741f97bbe2"
GIT = r"C:\Users\Seojun\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
PINS = {
    "v100_first_refit": "3f46a6b8672471dbcf68ca7c073df8d92572e710770a8b9a04dc8d920aad0082",
    "v101_first_expansion": "e468b676e72dc3b8922fdc0fc044a4400fdbba3728362c8ead8af02e4018971f",
    "v102_first_evaluation": "a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a",
    "v102_fresh_sources": "9420b10a44ca3101374a79d638cc209f1301d2b867cec8de3ebecb0f270c4202",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def run(repo, output):
    repo = repo.resolve()
    output.mkdir(exist_ok=False, parents=True)
    base = repo / "docs/experiments/results"
    ev = evidence_module()
    assets, experiences, summaries, public_assets = [], [], [], []
    guard = LineageGuard()
    counts = Counter()
    checked_hashes = {}

    def retain(path, expected=None, git_pin=False):
        raw = path.read_bytes()
        if expected and sha(raw) != expected:
            raise ValueError("first byte identity mismatch: " + str(path))
        if git_pin:
            rel = path.relative_to(repo).as_posix()
            original = subprocess.run([GIT, "cat-file", "blob", HEAD + ":" + rel],
                                      cwd=repo, capture_output=True, check=True).stdout
            if raw != original:
                raise ValueError("frozen Git authority changed: " + rel)
        checked_hashes[path] = sha(raw)
        assets.append({"path": path.relative_to(repo).as_posix(), "sha256": sha(raw),
                       "bytes": len(raw), "role": "H", "allowed_use": "historical_audit_only",
                       "identity_check": "EXTERNAL_FIRST_PIN" if expected else "FROZEN_GIT_BLOB" if git_pin else "PINNED_PARENT_RECEIPT",
                       "training_activation": "BLOCKED_UNTIL_G0_AND_G1_CONTRACT"})
        return raw

    def monolithic(stem):
        path = base / (stem + ".manifest.json")
        manifest = json.loads(retain(path, git_pin=True))
        packed = retain(base / manifest["file"], PINS[stem])
        raw = gzip.decompress(packed)
        if len(packed) != manifest["gzip_bytes"] or len(raw) != manifest["json_bytes"] or sha(raw) != manifest["json_sha256"]:
            raise ValueError("decoded legacy identity mismatch")
        obj = json.loads(raw)
        if manifest.get("summary") is not None and obj.get("summary") != manifest["summary"]:
            raise ValueError("archived summary consistency mismatch")
        return obj, base / manifest["file"], manifest

    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    import numpy as np
    from scipy import optimize
    from threadpoolctl import threadpool_limits
    from neumann1.lp_certificate_v081 import verify_standard_form_certificate
    from neumann1.lp_portfolio_v084 import decode_array

    def ingest(study, sources, rows, report, archive_path, source_refs):
        by_id = {s["id"]: s for s in sources}
        if len(by_id) != len(sources):
            raise ValueError("duplicate source ID")
        arrays = {}
        for s in sources:
            raw = s.get("arrays", s)
            has_coefficients = all(k in raw for k in ("A", "b", "c"))
            if has_coefficients:
                shapes = ((s["rows"], s["cols"]), (s["rows"],), (s["cols"],))
                arrays[s["id"]] = tuple(decode_array(raw[k], shape) if isinstance(raw[k], dict)
                    else np.asarray(raw[k], dtype=np.float64) for k, shape in zip(("A", "b", "c"), shapes))
            counts["source_coefficients_available" if has_coefficients else "source_metadata_only"] += 1
            family = s.get("family", "constructed_lp_support")
            # Explicit archived base/surface pairing; no invented isomorphism.
            group = study + ":" + s.get("pair_id", s["id"])
            ref = source_refs[s["id"]]
            declaration = {"equivalence_group": group, "training_exposure": True,
                           "source_artifact_sha256": ref["sha256"]}
            guard.register(declaration, "opened_development")
            public_assets.append({**ref, **declaration, "source_study": study,
                "original_problem_id": s["id"], "structural_family": family,
                "role": "D", "allowed_use": "opened_development_only",
                "coefficients_available": has_coefficients,
                "model_view": "A,b,c ONLY via load_json_view; hidden labels remain O",
                "oracle_role": "O", "oracle_runtime": False})
        reference_routes = {"DIRECT", "NATIVE", "IPM", "SPECIALIZED", "ASSIGNMENT"}
        direct_by_case = {}
        for row in rows:
            if row["route"] in reference_routes:
                direct_by_case.setdefault((row["case_id"], row["repeat"]), []).append(row)
        environment = report.get("environment")
        protocol = report.get("protocol", report.get("contract"))
        for index, row in enumerate(rows):
            s = by_id[row["case_id"]]
            witness = row.get("witness")
            if row["case_id"] not in arrays:
                certificate_status = "NOT_RECHECKED_ORIGINAL_ARRAYS_ABSENT_FROM_ARCHIVE"
                counts[certificate_status] += 1
            elif witness is None:
                certificate_status = "NO_RETAINED_WITNESS"
                if row["accepted"]:
                    raise ValueError("accepted legacy observation has no witness")
            else:
                certificate = verify_standard_form_certificate(*arrays[row["case_id"]], witness["x"], witness["y"])
                certificate_status = "D0_ORIGINAL_CERTIFICATE_PASS" if certificate["accepted"] else "D0_ORIGINAL_CERTIFICATE_REJECT"
                if row["accepted"] and not certificate["accepted"]:
                    raise ValueError("original accepted witness rejected on local audit")
                counts[certificate_status] += 1
            counts["observations"] += 1
            counts["original_accepted" if row["accepted"] else "original_rejected"] += 1
            if row["repeat"] < 0:
                counts["warmups_retained"] += 1
            cost_fields = ("total_ms", "proposal_ms", "post_ms", "amortized_investment_ms",
                           "worker_total_ms", "transport_and_receipt_ms")
            prior = direct_by_case.get((row["case_id"], row["repeat"]), [])
            record = {
                "record_id": f"{study}:observation:{index}", "source_study": study,
                "source_artifact_sha256": checked_hashes[archive_path],
                "evidence_status": "OPENED_DEVELOPMENT", "allowed_use": "development_only",
                "training_exposure": True, "equivalence_group": study + ":" + s.get("pair_id", s["id"]),
                "original_problem_id": row["case_id"], "original_problem_ref": source_refs[row["case_id"]],
                "structural_family": s.get("family", "constructed_lp_support"),
                "representation_id": row["route"], "repeat": row["repeat"],
                "transformation": {"archived_support": row.get("indices", row.get("top2")),
                                   "expanded": row.get("expanded"), "fallback_used": row.get("fallback_used"),
                                   "status": "ARCHIVED_ROUTE_ACTION_NOT_NEW_ABSTRACTION"},
                "validity_status": certificate_status, "original_accepted": row["accepted"],
                "oracle_given_free": row["route"] == "ORACLE", "oracle_runtime_allowed": False,
                "direct_cost": [{"route": r["route"], "accepted": r["accepted"],
                                 **{k: r.get(k) for k in cost_fields}} for r in prior],
                "transformed_cost": {k: row.get(k) for k in cost_fields},
                "cost_unit": "archived milliseconds", "cost_contract_sha256": sha(canonical(protocol)),
                "environment_sha256": sha(canonical(environment)),
                "cost_scope": "original study only; no cross-runtime time pooling; archived components may overlap",
                "unknown_costs": ["unreported stage breakdown", "energy", "FLOPs", "money"],
                "learning_signal": {"original_checked_acceptance": row["accepted"],
                                    "known_fallback": row.get("fallback_used"),
                                    "claim": "retained supervision candidate, not a learned transferable principle"},
            }
            experiences.append(record)
        summaries.append({"study": study, "sources": len(sources), "observations": len(rows),
                          "original_summary": report["summary"],
                          "environment": environment, "checkpoint_restore": "NOT_ATTEMPTED",
                          "d0_scope": "original bytes + receipts + original-task certificate; original cost decision unchanged"})
        print(study, len(sources), len(rows), "coefficient views", len(arrays), flush=True)

    forbidden = AssertionError("D0 may not run an optimizer")
    with threadpool_limits(limits=1), patch.object(optimize, "linprog", side_effect=forbidden), patch.object(optimize, "milp", side_effect=forbidden):
        for number, stem in ((100, "v100_first_refit"), (101, "v101_first_expansion"), (102, "v102_first_evaluation")):
            report, path, manifest = monolithic(stem)
            if number == 102:
                source_report, source_path, _ = monolithic("v102_fresh_sources")
                sources = source_report["sources"]
                refs = {s["id"]: {"path": source_path.relative_to(repo).as_posix(), "sha256": checked_hashes[source_path],
                                  "format": "gzip-json", "pointer": ["sources", i]} for i, s in enumerate(sources)}
            else:
                sources = report["development_sources"]
                refs = {s["id"]: {"path": path.relative_to(repo).as_posix(), "sha256": checked_hashes[path],
                                  "format": "gzip-json", "pointer": ["development_sources", i]} for i, s in enumerate(sources)}
            ingest(f"v0.0.{number}", sources, report["records"], report, path, refs)
        for number, source_dir, result_dir in ((103, base / "q5_first_sources", base / "q5_first_evaluation"),
                                               (104, base / "v104_transfer_admission_first", base / "v104_transfer_admission_first")):
            if number == 103:
                manifest = source_pin(source_dir)
                report, events = result_pin(result_dir)
                source_manifest_name = "manifest.json"
            else:
                manifest, report, events = transfer_pin(source_dir)
                source_manifest_name = "sources.json"
            for directory, names in ((source_dir, [source_manifest_name, "events.jsonl", "terminal.json"]),
                                     (result_dir, ["report.json", "events.jsonl", "terminal.json", "reservation.json"])):
                for name in names:
                    path = directory / name
                    if path not in checked_hashes:
                        retain(path)
            sources, refs, rows = [], {}, []
            for case in manifest["cases"]:
                obj = ev.unpack_case(source_dir, case["identity"])
                # v104 retains source metadata in a nested container; v103
                # keeps it beside arrays. Preserve the original file unchanged.
                normalized = {**obj.get("metadata", {}), **obj}
                path = source_dir / case["identity"]["file"]
                retain(path, case["identity"]["gzip_sha256"])
                sources.append(normalized)
                refs[normalized["id"]] = {"path": path.relative_to(repo).as_posix(), "sha256": checked_hashes[path], "format": "gzip-json"}
            for event in events:
                if event["kind"] == "observation":
                    identity = event["payload"]["identity"]
                    path = result_dir / identity["file"]
                    obj = ev.unpack_case(result_dir, identity)
                    retain(path, identity["gzip_sha256"])
                    rows.append(obj)
            ingest(f"v0.0.{number}", sources, rows, report, result_dir / "report.json", refs)

    # Re-read all accessed original bytes after audit; no original was rewritten.
    if any(sha(path.read_bytes()) != expected for path, expected in checked_hashes.items()):
        raise ValueError("original changed during D0")
    verifier_path = repo / "neumann1/lp_certificate_v081.py"
    verifier = {"id": "lp_standard_form_v081", "path": verifier_path.relative_to(repo).as_posix(),
                "sha256": sha(verifier_path.read_bytes()), "role": "B",
                "function": "verify_standard_form_certificate", "atol": 1e-8, "rtol": 1e-8,
                "scope": "original numerical primal/dual LP certificate, no optimizer or universal symbolic proof"}
    ledger = {"schema": "neumann.d0-core-ledger.v1", "status": "CORE_LP_BYTES_AND_AVAILABLE_WITNESSES_AUDITED_D0_OVERALL_IN_PROGRESS",
              "source_git_head": HEAD, "coverage": "v0.0.100..104 opened core LP only",
              "assets": assets, "public_problem_views": public_assets, "studies": summaries,
              "counts": dict(counts), "sealed_payloads_opened": 0, "new_model_calls": 0,
              "new_training": 0, "new_solver_calls": 0,
              "runtime": {"python": platform.python_version(), "system": platform.system(), "numpy": np.__version__},
              "pending": ["Decision1/2 raw-byte audit and contract-rights reconciliation", "P1.1..P1.13 full availability/pins audit including incomplete/not-evaluated runs", "REUSE_R0/CODE_GATE_C0/cache asset linkage", "new composition ancestry producers and fresh motif construction", "checkpoint restoration and cost-component coverage audit before G1"],
              "g0_status": "NOT_PREREGISTERED_NOT_EXECUTED", "g1_status": "BLOCKED_PENDING_G0_AND_NEW_CONTRACT",
              "g2_status": "UNAUTHORIZED_EXISTING_DECISION3_REMAINS_SEALED"}
    files = {
        "legacy_reuse_ledger.json": json.dumps(ledger, indent=2),
        "verifier_registry.json": json.dumps([verifier], indent=2),
        "structural_experiences.jsonl": "\n".join(json.dumps(x, separators=(",", ":")) for x in experiences) + "\n",
        "cost_records.jsonl": "\n".join(json.dumps({k: x[k] for k in ("record_id", "source_study", "repeat", "representation_id", "original_accepted", "direct_cost", "transformed_cost", "cost_unit", "cost_contract_sha256", "environment_sha256", "unknown_costs", "oracle_given_free")}, separators=(",", ":")) for x in experiences) + "\n",
        "leakage_guard_report.json": json.dumps({"status": "PASS_DECLARED_LEGACY_PAIR_LINEAGE", "equivalence_groups": len(guard.groups),
            "historical_views": len(public_assets), "fresh_eligible": 0, "automatic_arbitrary_equivalence_detection": False,
            "new_composition_ancestry_status": "NOT_YET_PRODUCED", "sealed_payloads_opened": 0}, indent=2),
    }
    for name, text in files.items():
        (output / name).write_text(text, encoding="utf-8")
    output_manifest = {name: sha((output / name).read_bytes()) for name in files}
    (output / "manifest.json").write_text(json.dumps(output_manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": ledger["status"], "assets": len(assets), "public_views": len(public_assets),
                      "counts": dict(counts), "equivalence_groups": len(guard.groups)}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.repo, args.output)
