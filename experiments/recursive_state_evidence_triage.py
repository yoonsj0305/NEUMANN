"""Opened causal analysis of stored evidence; never launches a solver/model cohort.

The fixed context collision refutes ONLY a join taking the original goal values.
Known prefix_lift is reused, not synthesized again. Source and certificate hashes
are anchored to historical manifests. Unknown full-task costs stay None.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.synduce_full_baseline_audit import independent_fold
from neumann1.recursive_summary import identity, interpret

PINS = {
    "SYNDuce_FULL_SOURCE_PORTABLE": "1c630004987740e2c50d0374fc2fcdbbc8984cc093729f151d0f056ce2735d0b",
    "SYNDuce_FULL_BASELINE_FIRST/extracted/baseline-first": "27cf88f152c61994c852c80c7f478c0c86985539647967875fb3d0bdfa099cf5",
    "SYNDuce_CVC4_FIRST/extracted/baseline-cvc4-first": "36a3e818f099f067fdc8576dd93d3fb92e50558c6b51a9ab34fd94212662c134",
    "SOURCE_BOUND_RECURSIVE_FIRST": "a768622790023280b4679d35e886eb190ffc9fff041d32c3adff2033e3756ac3",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def checked(path, expected):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"Evidence hash mismatch: {path.name}")
    return actual


def context_collision(public, left_a, left_b, right):
    a, b, r = [independent_fold(public, xs) for xs in (left_a, left_b, right)]
    ar, br = [independent_fold(public, xs + right) for xs in (left_a, left_b)]
    return {"left_a": left_a, "left_b": left_b, "right": right,
            "left_a_goal": a, "left_b_goal": b, "right_goal": r,
            "concat_a_goal": ar, "concat_b_goal": br,
            "goal_only_join_refuted": a == b and ar != br,
            "scope": "deterministic join receiving ONLY original child goal values, with original empty/leaf goals and no hidden state"}


def stored_lift(certificate, case):
    """Read authority from a hash-checked historical proof, never from a label alone."""
    public = certificate["binding"]["projection"]["public"]
    proposal = case["proposal"]["proposal"]
    proof = certificate["certificate"]
    if (certificate.get("accepted") is not True or proof.get("accepted") is not True
            or proof.get("status") != "CERTIFIED"
            or len(proof.get("obligations", [])) != 9
            or any(o.get("status") != "unsat" for o in proof["obligations"])
            or identity(public) != proof.get("problem_sha256")
            or identity(proposal) != proof.get("proposal_sha256")
            or identity(proposal) != certificate.get("proposal_sha256")
            or case["source"]["sha256"] != certificate["binding"]["source_sha256"]):
        raise ValueError("Historical goal certificate is missing, unknown or mismatched")
    return public, proposal


def analyze(continuation, contract):
    started = perf_counter()
    manifests = {}
    receipts = []
    for rel, pin in PINS.items():
        directory = continuation / rel
        checked(directory / "manifest.json", pin)
        manifests[rel] = read(directory / "manifest.json")
        receipts.append({"path": rel + "/manifest.json", "sha256": pin})

    source_root = continuation / "SYNDuce_FULL_SOURCE_PORTABLE/upstream"
    source_manifest = manifests["SYNDuce_FULL_SOURCE_PORTABLE"]
    if source_manifest["commit"] != "b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89":
        raise ValueError("Wrong upstream source revision")
    source_files = {f["path"]: f for f in source_manifest["files"]}
    cohorts = {}
    for rel in list(PINS)[1:3]:
        directory = continuation / rel
        manifest = manifests[rel]
        for name, digest in manifest.items():
            checked(directory / name.replace("\\", "/"), digest)
        rows = read(directory / "observations.json")
        prereg = read(directory / "preregister.json")
        if len(rows) != 87 or len(prereg["cases"]) != 29:
            raise ValueError("Historical cohort population changed")
        cohorts["CVC4" if "CVC4" in rel else "CVC5"] = (rows, prereg)

    joined = []
    for index in range(29):
        row_groups = {solver: [r for r in rows if r["case_index"] == index]
                      for solver, (rows, _) in cohorts.items()}
        paths = {r["path"] for rows in row_groups.values() for r in rows}
        if len(paths) != 1 or any(sorted(r["repeat"] for r in rows) != [0, 1, 2]
                                  for rows in row_groups.values()):
            raise ValueError("Source/repetition lineage mismatch")
        path = "benchmarks/" + paths.pop()
        source_sha = checked(source_root / path, source_files[path]["sha256"])
        joined.append({"case_index": index, "original_path": path, "source_sha256": source_sha,
                       "historical_results": {solver: {
                           "statuses": dict(Counter(r["status"] for r in rows)),
                           "tool_elapsed_median_seconds": statistics.median(r["seconds"] for r in rows),
                           "independently_certified_original_task": [r["independently_certified_original_task"] for r in rows],
                       } for solver, rows in row_groups.items()},
                       "complete_cost": None})

    rel = "SOURCE_BOUND_RECURSIVE_FIRST"
    directory = continuation / rel
    manifest = manifests[rel]
    label = contract["selected_source_sha256"][:16]
    for name in ["cases.json", f"certificates\\{label}.json"]:
        checked(directory / name.replace("\\", "/"), manifest[name])
        receipts.append({"path": rel + "/" + name.replace("\\", "/"), "sha256": manifest[name]})
    case = next(c for c in read(directory / "cases.json")
                if c["source"]["path"] == contract["selected_original"])
    cert = read(directory / "certificates" / (label + ".json"))
    checked(source_root / case["source"]["path"], contract["selected_source_sha256"])
    public, proposal = stored_lift(cert, case)
    witness = context_collision(public, **contract["fixed_witness"])
    if not witness["goal_only_join_refuted"]:
        raise ValueError("Registered context collision did not refute the interface")
    lifted = []
    for left in [witness["left_a"], witness["left_b"]]:
        def state(xs):
            s = list(proposal["empty"])
            for h in reversed(xs):
                s = interpret(proposal["step"], [h] + s)
            return s
        l, r = state(left), state(witness["right"])
        decoded = interpret(proposal["decode"], interpret(proposal["merge"], l + r))
        goal = independent_fold(public, left + witness["right"])
        if decoded != goal:
            raise ValueError("Stored lifted representation failed selected witness")
        lifted.append({"left_state": l, "right_state": r, "decoded_goal": decoded,
                       "original_goal": goal})
    return {"analysis_id": contract["analysis_id"], "status": "CAUSAL_DEVELOPMENT_CHECK_PASS",
            "population": {"registered_source_entries": 29, "source_byte_groups": len({r["source_sha256"] for r in joined}),
                           "historical_observations": 174, "fresh_independent_problems": 0},
            "source_revision": source_manifest["commit"], "evidence_receipts": receipts,
            "stored_cohort_scope": {s: {"cost_scope": p["cost_scope"], "cost_not_included": p["cost_not_included"]}
                                    for s, (_, p) in cohorts.items()},
            "joined_historical_cases": joined, "new_fixed_context_collision": witness,
            "existing_classical_lift": {"template": case["proposal"]["template"], "mechanism": case["proposal"]["mechanism"],
                "goal_state_width": len(public["empty"]), "latent_state_width": len(proposal["empty"]),
                "witness_checks": lifted, "stored_obligation_count": 9,
                "stored_verification_seconds": cert["certificate"]["verification_seconds"],
                "verification_scope": cert["certificate"]["scope"], "new_solver_calls": 0},
            "decision": "HOLD_LEARNING_EXISTING_RECURSIVE_MONOID_FAMILY",
            "reason": "a real goal-only interface obstruction exists, but the existing classical library already supplies and certifies the missing state; no residual economic advantage established",
            "complete_cost_advantage": None, "energy": None, "flops": None, "frontier_gap_measured": False,
            "new_model_calls": 0, "new_gpu_calls": 0, "new_native_cohort_runs": 0,
            "analysis_elapsed_seconds_not_task_cost": perf_counter() - started}


if __name__ == "__main__":
    continuation, contract_path, output = map(Path, sys.argv[1:])
    result = analyze(continuation, read(contract_path))
    result["contract_sha256"] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    result["analysis_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "population": result["population"], "decision": result["decision"]}))
