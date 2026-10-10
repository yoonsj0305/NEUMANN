"""Single-source proof recipe, reusing existing verifiers; no new solver/loader.

Hash-pinned source and printed kernel are explicitly transcribed below. The
theorem is mathematical original-goal equivalence after first-component decode,
not compilation or execution of the printed OCaml fragment.
"""
import hashlib
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.recursive_state_evidence_triage import PINS, checked, read
from neumann1.representation_program import Builder, ProgramError, polynomial_forms, verify_original
from neumann1.source_bound_recursive import parse_representation, prove_flatten, source_binding, uncomment
from neumann1.synduce_solution import parse_solution

SOURCE_SHA = "e9a3436fe113e714f09baa701304f6eca9b8b2ae760812d319b8a128ef002810"
SOLUTION_SHA = "5e4ec657938e9b98e637f709902170dda17b341f4254566e061de30ffc265487"
REQUIRED_LAWS = {"EMPTY_SUFFIX_RESPONSE", "SINGLE_SUFFIX_RESPONSE", "CONCAT_SUFFIX_RESPONSE",
                 "ORIGINAL_GOAL_DECODE", "LEFT_IDENTITY", "RIGHT_IDENTITY", "ASSOCIATIVE"}


def identities():
    """Exact transcription: E=(0,1); leaf(a)=(a,x); merge=(v+f*w,f*g).

    rho((v,f),t)=v+f*t represents the original fold with arbitrary suffix value t.
    rho laws + induction on constructors establish the goal at t=0 for every tree.
    """
    inputs = ["x", "head", "lv", "lf", "rv", "rf", "cv", "cf", "tail"]
    b = Builder(inputs)
    x, h, lv, lf, rv, rf, cv, cf, t = [b.input(n) for n in inputs]
    zero, one = b.const(0), b.const(1)
    e, leaf, l, r, c = (zero, one), (h, x), (lv, lf), (rv, rf), (cv, cf)
    def merge(a, z):
        return b.add(a[0], b.mul(a[1], z[0])), b.mul(a[1], z[1])
    def rho(a, suffix):
        return b.add(a[0], b.mul(a[1], suffix))
    pairs = [
        ("EMPTY_SUFFIX_RESPONSE", [rho(e, t)], [t]),
        ("SINGLE_SUFFIX_RESPONSE", [rho(leaf, t)], [b.add(b.mul(x, t), h)]),
        ("CONCAT_SUFFIX_RESPONSE", [rho(merge(l, r), t)], [rho(l, rho(r, t))]),
        ("ORIGINAL_GOAL_DECODE", [rho(l, zero)], [lv]),
        ("LEFT_IDENTITY", list(merge(e, l)), list(l)),
        ("RIGHT_IDENTITY", list(merge(l, e)), list(l)),
        ("ASSOCIATIVE", list(merge(merge(l, r), c)), list(merge(l, merge(r, c)))),
    ]
    return [{"obligation": name, "original": b.finish(a), "candidate": b.finish(z)}
            for name, a, z in pairs]


def check_identities(laws, *, max_terms=8192, max_product_work=2_000_000):
    if len(laws) != 7 or {law.get("obligation") for law in laws} != REQUIRED_LAWS:
        return {"status": "UNKNOWN", "cause": "MISSING_PROOF_OBLIGATIONS", "obligations": []}
    records = []
    for law in laws:
        try:
            # Existing verifier budgets, never weakened to get acceptance.
            for side in ["original", "candidate"]:
                polynomial_forms(law[side], max_terms=max_terms, max_product_work=max_product_work)
            result = verify_original(law["original"], law["candidate"])
        except ProgramError as exc:
            return {"status": "UNKNOWN", "cause": "VERIFIER_RESOURCE_OR_SCHEMA_LIMIT",
                    "error": str(exc), "obligations": records}
        records.append({**law, "verification": result})
        if not result["accepted"]:
            # A failed sufficient lemma is not automatically an original-goal counterexample.
            return {"status": "UNKNOWN", "cause": "SUFFICIENT_IDENTITY_NOT_ESTABLISHED",
                    "failed_obligation": law["obligation"], "obligations": records}
    if len(records) != 7:
        return {"status": "UNKNOWN", "cause": "MISSING_PROOF_OBLIGATIONS", "obligations": records}
    return {"status": "ORIGINAL_CERTIFIED", "obligations": records,
            "authority": "EXISTING_EXACT_POLYNOMIAL_IDENTITIES_PLUS_STRUCTURAL_INDUCTION"}


def analyze(continuation, contract):
    if (contract["original_path"] != "benchmarks/list/poly_no_fac.ml"
            or contract["original_sha256"] != SOURCE_SHA
            or contract["printed_native_solution_sha256"] != SOLUTION_SHA
            or contract["original_goal"] != "spec x (repr tree)"
            or contract["decoded_native_goal"] != "first component of the stored lifted h tree, with the same immutable x at every leaf"):
        raise ValueError("This proof recipe binds only the exact declared source, goal and Native kernel")
    start = perf_counter()
    receipts, upstream, cohorts = [], None, {}
    for rel in list(PINS)[:3]:
        directory = continuation / rel
        checked(directory / "manifest.json", PINS[rel])
        m = read(directory / "manifest.json")
        receipts.append({"path": rel + "/manifest.json", "sha256": PINS[rel]})
        if "SOURCE_PORTABLE" in rel:
            upstream = {f["path"]: f for f in m["files"]}
            continue
        for name in ["observations.json", "preregister.json"] + [f"22-{i}.{ext}" for i in range(3) for ext in ["stdout", "stderr"]]:
            checked(directory / name, m[name])
            receipts.append({"path": rel + "/" + name, "sha256": m[name]})
        all_rows = read(directory / "observations.json")
        rows = [r for r in all_rows if r["case_index"] == 22]
        if len(all_rows) != 87 or sorted(r["repeat"] for r in rows) != [0, 1, 2] or any(r["path"] != "list/poly_no_fac.ml" for r in rows):
            raise ValueError("Stored cohort lineage mismatch")
        solver = "CVC4" if "CVC4" in rel else "CVC5"
        cohorts[solver] = {"statuses": [r["status"] for r in rows],
                           "tool_elapsed_seconds": [r["seconds"] for r in rows],
                           "tool_elapsed_median_seconds": statistics.median(r["seconds"] for r in rows),
                           "cost_scope": read(directory / "preregister.json")["cost_scope"],
                           "independent_original_certification_in_first_run": False}
        if solver == "CVC4":
            for i in range(3):
                printed = read(directory / f"22-{i}.stdout")["solution"]
                if hashlib.sha256(printed.encode()).hexdigest() != contract["printed_native_solution_sha256"]:
                    raise ValueError("Printed Native kernel binding mismatch")
    source_root = continuation / "SYNDuce_FULL_SOURCE_PORTABLE/upstream"
    source_path = source_root / contract["original_path"]
    checked(source_path, contract["original_sha256"])
    if upstream[contract["original_path"]]["sha256"] != contract["original_sha256"]:
        raise ValueError("Source manifest binding mismatch")
    for path in [contract["original_path"], "src/se2gis/Lifting.ml", "src/se2gis/Equations.ml", "src/common/Pretty.ml", "src/common/ProblemFinder.ml"]:
        checked(source_root / path, upstream[path]["sha256"])
        receipts.append({"path": "SYNDuce_FULL_SOURCE_PORTABLE/upstream/" + path, "sha256": upstream[path]["sha256"]})
    source = source_path.read_text(encoding="utf-8")
    limitations = []
    for label, reader, content in [("piecewise_linear_emitted_reader", parse_solution, printed),
                                    ("explicit_assertion_full_source_reader", source_binding, source)]:
        try:
            reader(content)
        except ValueError as exc:
            limitations.append({"reader": label, "status": "UNKNOWN", "cause": "UNSUPPORTED_BINDING_OR_LANGUAGE", "error": str(exc)})
    begin = perf_counter()
    try:
        flatten = prove_flatten(parse_representation(uncomment(source), "repr"), "repr")
    except ValueError as exc:
        return {"status": "UNKNOWN", "cause": "EXISTING_REPR_VERIFIER_DID_NOT_ESTABLISH_PROOF",
                "error": str(exc), "evidence_receipts": receipts,
                "counterexample_established": False, "timeout_distinguishable_from_existing_error": False}
    flatten_seconds = perf_counter() - begin
    begin = perf_counter()
    proof = check_identities(identities())
    identity_seconds = perf_counter() - begin
    if not flatten["accepted"]:
        proof["status"] = "UNKNOWN"
    return {"analysis_id": contract["analysis_id"], "status": proof["status"],
            "scope": contract["scope"], "goal": contract["original_goal"],
            "decoded_native_goal": contract["decoded_native_goal"], "not_certified": contract["not_certified"],
            "binding_authority": contract["binding"], "evidence_receipts": receipts,
            "historical_native_results": cohorts, "existing_adapter_limitations": limitations,
            "original_representation_proof": flatten, "polynomial_goal_proof": proof,
            "new_flatten_verification_seconds": flatten_seconds,
            "new_identity_verification_seconds": identity_seconds,
            "new_analysis_elapsed_seconds_not_deployment_cost": perf_counter() - start,
            "raw_printed_program_compilation_status": "UNKNOWN",
            "original_goal_counterexamples_found": 0,
            "complete_cost_advantage": None, "flops": None, "energy": None, "memory": None,
            "decision": "HOLD_LEARNING_CLASSICAL_AFFINE_POLYNOMIAL_SUMMARY",
            "reason": "existing Native already acquires the sufficient affine representation; independent mathematical-goal verification needs no learned discovery; no residual headroom established",
            "fresh_independent_problems": 0, "new_native_synthesis_runs": 0, "new_model_calls": 0,
            "new_gpu_calls": 0, "paid_calls": 0, "frontier_gap_measured": False}


if __name__ == "__main__":
    continuation, output = map(Path, sys.argv[1:])
    if output.exists():
        raise FileExistsError("First verification output must be preserved")
    contract_path = Path(__file__).with_name("verification_contract.json")
    try:
        result = analyze(continuation, read(contract_path))
    except (ValueError, KeyError, OSError) as exc:
        result = {"status": "UNKNOWN", "cause": "SOURCE_OR_EVIDENCE_BINDING_NOT_ESTABLISHED", "error": str(exc)}
    result["contract_sha256"] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    result["verification_recipe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({k: result.get(k) for k in ["status", "decision", "new_flatten_verification_seconds", "new_identity_verification_seconds", "cause"]}))
