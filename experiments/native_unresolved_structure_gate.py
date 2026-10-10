"""Retrospective join of existing evidence. No solver, model or timed task runs."""
from collections import Counter
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.recursive_state_evidence_triage import PINS, checked, read
from neumann1.recursive_summary import identity

EVIDENCE = ROOT / "research/development"
TRIAGE = "recursive-state-triage-2026-10-10"
POLY = "poly-no-fac-original-proof-2026-10-10"
MANIFEST_PINS = {
    "SYNDuce_FULL_SOURCE_PORTABLE": PINS["SYNDuce_FULL_SOURCE_PORTABLE"],
    "SYMBOLIC_DECODER_FIRST": "45aa6a7129b92592ec3cfda3e9e6b4c25b1aacba634603557e69b73e9e8e247e",
    "COMPRESSED_RECURSIVE_COST_FIRST": "cf515dd54a4826d10f562e79694e8b9f294f2738b5351906522981f3b0b49606",
}
LOCAL_FIRST_PINS = {
    TRIAGE: "401fb24597a3793312642c3a38a0a7b290d95baadf55fdb1b02ecd979c84d70e",
    POLY: "7e61a059fe3c40714e0b8e9f4af8042fc3f7690d8277a70b0897719f62ac32d0",
}
OBLIGATIONS = {
    "INITIAL_VALID", "STEP_VALID", "DECODE_EMPTY", "DECODE_STEP", "MERGE_VALID",
    "LEFT_IDENTITY", "RIGHT_IDENTITY", "CONS_NATURALITY", "ASSOCIATIVE",
}
CONDITIONS = (
    "native_classical_unresolved_or_expensive", "original_goal_certifiable",
    "representation_obstruction_confirmed", "residual_economic_basis",
)


def gate(conditions, equal_rights=None, hold_reason=None):
    """Unknown is not failure or a learning opportunity; prior HOLD stays HOLD."""
    if set(conditions) != set(CONDITIONS) or any(
        v is not None and type(v) is not bool for v in conditions.values()
    ):
        raise ValueError("Gate requires four explicit boolean/unknown conditions")
    if equal_rights is not None and type(equal_rights) is not bool:
        raise ValueError("Comparator rights require boolean/unknown evidence")
    if hold_reason:
        return "HOLD"
    return "PASS" if equal_rights is True and all(v is True for v in conditions.values()) else "UNKNOWN"


def stored_original_certificate(case, cert, native):
    """Check historical identity/status linkage; does NOT re-prove the theorem."""
    binding, proof = cert["binding"], cert["certificate"]
    public = binding["projection"]["public"]
    obligations = proof.get("obligations", [])
    flatten = binding.get("flatten_proof", {})
    records = flatten.get("proof_records", []) + flatten.get("clause_records", [])
    if (cert.get("accepted") is not True
            or cert.get("status") != "SOURCE_BOUND_MATHEMATICAL_GOAL_CERTIFIED"
            or binding["source_sha256"] != case["source"]["sha256"]
            or identity(public) != case["public_AST_sha256"]
            or identity(public) != proof.get("problem_sha256")
            or native.get("accepted") is not True or native.get("Oracle_used") is not False
            or native.get("learning_performed") is not False
            or identity(native["proposal"]) != cert.get("proposal_sha256")
            or identity(native["proposal"]) != proof.get("proposal_sha256")
            or proof.get("accepted") is not True or proof.get("status") != "CERTIFIED"
            or len(obligations) != 9
            or {o.get("obligation") for o in obligations} != OBLIGATIONS
            or any(o.get("status") != "unsat" for o in obligations)
            or flatten.get("accepted") is not True or not records
            or any(r.get("word_actual") != r.get("word_expected") for r in records)
            or any(r.get("termination_status") != "unsat" for r in flatten.get("proof_records", []))):
        raise ValueError("Missing, UNKNOWN or mismatched stored original certificate")
    return {"status": "STORED_SOURCE_BOUND_MATHEMATICAL_GOAL_CERTIFIED",
            "public_AST_sha256": identity(public), "proposal_sha256": identity(native["proposal"]),
            "scope": binding["scope"], "assertion": binding["assertion"],
            "goal_types": binding["projection"]["goal_types"],
            "reference_function": binding["projection"]["reference_function"],
            "original_hole_skeleton_implementable": case["original_hole_skeleton_implementable"],
            "classical_mechanism": native["mechanism"],
            "classical_template": native.get("origin", {}).get("template"),
            "machine_OCaml_execution_certified": False,
            "new_proof_calls": 0}


def analyze(continuation):
    receipts = []

    def load(directory, name, digest):
        checked(directory / name, digest)
        relative = (directory / name).relative_to(ROOT if directory.is_relative_to(ROOT) else continuation)
        receipts.append({"store": "repository" if directory.is_relative_to(ROOT) else "Continuation",
                         "path": relative.as_posix(), "sha256": digest})
        return read(directory / name)

    prior = {}
    for directory, pin in LOCAL_FIRST_PINS.items():
        prior[directory] = load(EVIDENCE / directory, "first_result.json", pin)
    joined = prior[TRIAGE]["joined_historical_cases"]
    if (len(joined) != 29 or [r["case_index"] for r in joined] != list(range(29))
            or prior[TRIAGE]["population"]["historical_observations"] != 174):
        raise ValueError("Historical source population changed")

    manifests = {rel: load(continuation / rel, "manifest.json", pin)
                 for rel, pin in MANIFEST_PINS.items()}
    sources = manifests["SYNDuce_FULL_SOURCE_PORTABLE"]
    if sources["commit"] != "b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89":
        raise ValueError("Upstream revision changed")
    source_files = {f["path"]: f for f in sources["files"]}

    def artifact(rel, name):
        return load(continuation / rel, name, manifests[rel][name.replace("/", "\\")]
                    if name.replace("/", "\\") in manifests[rel] else manifests[rel][name])

    symbolic_cases = artifact("SYMBOLIC_DECODER_FIRST", "cases.json")
    cost_report = artifact("COMPRESSED_RECURSIVE_COST_FIRST", "report.json")
    cost_contract = artifact("COMPRESSED_RECURSIVE_COST_FIRST", "preregister.json")
    if cost_contract["rule"]["geometric_mean_at_least"] != 10:
        raise ValueError("Historical headroom contract changed")
    cost_cases = {regime: {r["case"]: r for r in cost_report["analysis"]["regimes"][regime]["cases"]}
                  for regime in ("1", "16")}
    poly_contract = load(EVIDENCE / POLY, "verification_contract.json",
                         "103ed266b607f482216e71edd2ebeed6e87d9d3e6fe95e7e07abe4109b968aee")
    rows = []
    for historical in joined:
        path, digest = historical["original_path"], historical["source_sha256"]
        source_path = continuation / "SYNDuce_FULL_SOURCE_PORTABLE/upstream" / path
        if source_files[path]["sha256"] != digest:
            raise ValueError("Source ledger changed")
        checked(source_path, digest)
        receipts.append({"store": "Continuation", "path": source_path.relative_to(continuation).as_posix(), "sha256": digest})
        restricted = "--no-lifting" in source_path.read_text(encoding="utf-8")
        row = {**historical, "conditions": dict.fromkeys(CONDITIONS), "equal_rights_evidence": None,
               "restricted_no_lifting": restricted, "original_certificate": None,
               "matched_adapted_cost": None, "hold_reason": None,
               "missing": ["independent source-bound original certification",
                           "equal-rights unresolved Classical-Hybrid evidence", "residual complete-cost opportunity"],
               "reason": "Upstream synthesis status alone does not establish original-goal correctness or a structural gap"}
        # A byte-identical source at another path is retained as an alias, not
        # silently substituted for this original's binding/assertion.
        candidates = [c for c in symbolic_cases if c["source"]["sha256"] == digest and c["source"]["path"] == path]
        row["excluded_byte_aliases"] = [c["source"]["path"] for c in symbolic_cases
            if c["source"]["sha256"] == digest and c["source"]["path"] != path]
        if candidates:
            certificates = []
            for case in candidates:
                cert = artifact("SYMBOLIC_DECODER_FIRST", f"certificates/{case['label']}.json")
                native = artifact("SYMBOLIC_DECODER_FIRST", f"native/{case['public_AST_sha256']}.json")
                certificates.append(stored_original_certificate(case, cert, native))
            if len({c["public_AST_sha256"] for c in certificates}) != 1:
                raise ValueError("Conflicting source-to-goal bindings")
            row["original_certificate"] = certificates[0]
            ast = certificates[0]["public_AST_sha256"]
            matched = {regime: cost_cases[regime].get(ast) for regime in ("1", "16")}
            row["conditions"]["original_goal_certifiable"] = True
            if all(c is not None and c["qualified"] is True for c in matched.values()):
                row["matched_adapted_cost"] = matched
                row["equal_rights_evidence"] = True
                if all(c["native_over_free"] < 10 for c in matched.values()):
                    row["conditions"].update(native_classical_unresolved_or_expensive=False, residual_economic_basis=False)
                    row["hold_reason"] = "EXISTING_CERTIFIED_CLASSICAL_STRUCTURE_AND_NO_REGISTERED_TENFOLD_ADAPTED_HEADROOM"
                    row["reason"] = "Known classical generation and same-goal AST/DAG cost evidence already cover this structure; full source deployment cost remains UNKNOWN"
                    row["missing"] = ["full original OCaml deployment complete-cost and machine semantics"]
        if path == poly_contract["original_path"]:
            poly = prior[POLY]
            if digest != poly_contract["original_sha256"] or poly["status"] != "ORIGINAL_CERTIFIED":
                raise ValueError("Prior affine-goal certificate changed")
            row["original_certificate"] = {"status": "STORED_ORIGINAL_CERTIFIED", "scope": poly["scope"],
                                            "not_certified": poly["not_certified"], "new_proof_calls": 0}
            row["conditions"]["original_goal_certifiable"] = True
            row["hold_reason"] = "PRIOR_USER_HOLD_CLASSICAL_AFFINE_DISCOVERY_ALREADY_EXISTS"
            row["reason"] = "Preserve c39bbdf: Native already generates the certified affine representation; paired complete-cost advantage remains UNKNOWN"
            row["missing"] = ["paired complete-cost opportunity", "full compiled OCaml and machine semantics"]
        if path == "benchmarks/list/mps_no_sum.ml":
            row["conditions"]["representation_obstruction_confirmed"] = prior[TRIAGE]["new_fixed_context_collision"]["goal_only_join_refuted"]
        if restricted:
            row["equal_rights_evidence"] = False
            row["reason"] = "Source explicitly forbids lifting; restricted unrealizability is not strongest unconstrained Classical-Hybrid failure"
            row["missing"].append("same state-extension/lifting rights for the strongest classical comparator")
        row["gate_verdict"] = gate(row["conditions"], row["equal_rights_evidence"], row["hold_reason"])
        rows.append(row)
    counts = dict(Counter(r["gate_verdict"] for r in rows))
    counts.setdefault("PASS", 0)
    return {"analysis_id": "NATIVE_UNRESOLVED_STRUCTURE_GATE_20261010", "kind": "RETROSPECTIVE_OPENED_EVIDENCE_JOIN",
            "baseline_commit": "c39bbdfecea75232e9307c548baf3bea991973af", "counts": counts,
            "population": {"source_entries": 29, "source_byte_groups": len({r['source_sha256'] for r in rows}),
                           "saved_native_observations": 174, "independent_motif_count": None, "fresh_problems": 0},
            "source_revision": sources["commit"], "source_gates": rows, "evidence_receipts": receipts,
            "adapted_cost_scope": {k: cost_contract[k] for k in ("primary_cost", "query_scope", "proof_reuse", "native_rights", "free_rights", "rule")},
            "cost_warning": "Synduce synthesis seconds and adapted DAG operational seconds are DIFFERENT workloads; never divide them into a speedup",
            "decision": "STOP_ACTIVE_LEARNING_CANDIDATE_SEARCH_IN_EXISTING_29" if counts["PASS"] == 0 else "CONSIDER_PREREGISTERED_FREE_VALID_HEADROOM_ONLY",
            "learning": "HOLD", "frozen_Gemma_F0": "BLOCKED_SMALL_MODEL_RUNTIME", "frontier_gap_measured": False,
            "new_synthesis_runs": 0, "new_proof_calls": 0, "new_model_calls": 0, "new_gpu_calls": 0, "paid_calls": 0,
            "complete_source_cost_advantage": None, "energy": None, "flops": None}


if __name__ == "__main__":
    continuation, output = map(Path, sys.argv[1:])
    if not output.is_dir() or any((output / n).exists() for n in ("gate_result.json", "source_gate.csv")):
        raise ValueError("Use a prepared new output directory; do not overwrite first analysis")
    result = analyze(continuation)
    policy_path = output / "screening_policy.json"
    policy = read(policy_path)
    if policy["analysis_id"] != result["analysis_id"] or policy["baseline_commit"] != result["baseline_commit"]:
        raise ValueError("Decision policy identity mismatch")
    import hashlib
    result["screening_policy_sha256"] = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    with (output / "gate_result.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    fields = ["case_index", "original_path", "source_sha256", "gate_verdict", *CONDITIONS,
              "CVC4_statuses", "CVC5_statuses", "CVC4_synthesis_median_seconds", "public_AST_sha256",
              "adapted_native_over_free_1", "adapted_native_over_free_16", "reason", "missing"]
    with (output / "source_gate.csv").open("x", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in result["source_gates"]:
            costs = row["matched_adapted_cost"] or {}
            writer.writerow({**{k: row[k] for k in fields[:4]},
                **{k: json.dumps(row["conditions"][k]) for k in CONDITIONS},
                "CVC4_statuses": json.dumps(row["historical_results"]["CVC4"]["statuses"], sort_keys=True),
                "CVC5_statuses": json.dumps(row["historical_results"]["CVC5"]["statuses"], sort_keys=True),
                "CVC4_synthesis_median_seconds": row["historical_results"]["CVC4"]["tool_elapsed_median_seconds"],
                "public_AST_sha256": (row["original_certificate"] or {}).get("public_AST_sha256", "UNKNOWN"),
                **{f"adapted_native_over_free_{regime}": costs.get(regime, {}).get("native_over_free", "UNKNOWN") for regime in ("1", "16")},
                "reason": row["reason"], "missing": "; ".join(row["missing"])})
    print(json.dumps({"counts": result["counts"], "decision": result["decision"], "new_experiment_runs": 0}))
