"""Q3 structural information lower bound on 12 real new Code2Inv originals.

For projection pi(x)=(first two original state variables), if there exist
state a with genuine Pre(a), b with genuine !Post(b) and pi(a)==pi(b), then
NO classifier g(pi(x)) can satisfy simultaneously:
  forall Pre(x) -> g(pi(x)); forall g(pi(x)) -> Post(x).
This is a *representational impossibility* for any decision tree, neural
network, classifier or rule using ONLY pi, irrespective of training compute.
It's NOT proof that a reachable state is unsafe. Distinguish actual Pre & Bad
on SAME original state vs separate states sharing the projected observation.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import DUAL_S
def check(phi):
    s=z3.Solver();s.set(timeout=6000);s.add(phi)
    r=s.check()
    if r==z3.unknown:return {"status":"UNKNOWN","independent_dual":False}
    expected="sat" if r==z3.sat else "unsat"
    witness=dual(phi,expected,DUAL_S)
    result={"status":expected.upper(),"independent_dual":witness["dual_pass"],
            "z3_cvc5_native_source_receipt":witness}
    if r==z3.sat:result["concrete_symbolic_Z3_witness"]=s.model().sexpr()[:5000]
    return result
def per(root,item):
    begin=time.perf_counter_ns()
    row={"source":item["path"],"git_blob":item["git_blob"],"status":"ABSTAIN"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_FIRST_PREBODY_GIT_SHA_NOT_MATCHED")
        src=compile_typed_original(sexprs(raw))
        native=compile_independent_native(sexprs(raw),src)
        parity={k:check(z3.Xor(src[k],native[k])) for k in ("pre","trans","post")}
        if not all(r["status"]=="UNSAT" and r["independent_dual"] for r in parity.values()):
            raise RuntimeError("SOURCE_UNCHANGED_NATIVE_AST_PARITY_UNCERTIFIED")
        first=src["now"][:2]
        cloned=[z3.Const(f"projection_other_original_{i}",s.sort()) for i,s in enumerate(src["now"])]
        bad= z3.substitute(z3.Not(native["post"]),*list(zip(src["now"],cloned)))
        two=z3.And(native["pre"],bad,*(a==b for a,b in zip(first,cloned[:2])))
        all_vars=z3.And(native["pre"],bad,*(a==b for a,b in zip(src["now"],cloned)))
        same=z3.And(native["pre"],z3.Not(native["post"]))
        row["exact_dual_original_source_parity"]=parity
        row["Pre_satisfiable"]=check(native["pre"])
        row["NotPost_satisfiable"]=check(z3.Not(native["post"]))
        row["two_slot_positive_vs_negative_indistinguishable"]=check(two)
        row["all_state_slots_positive_vs_negative_indistinguishable"]=check(all_vars)
        row["actual_same_original_state_Pre_and_NotPost"]=check(same)
        if not all(r["independent_dual"] for r in (
            row["Pre_satisfiable"],row["NotPost_satisfiable"],
            row["two_slot_positive_vs_negative_indistinguishable"],
            row["all_state_slots_positive_vs_negative_indistinguishable"],
            row["actual_same_original_state_Pre_and_NotPost"])):
            raise RuntimeError("INDEPENDENT_NATIVE_SMT_DISAGREEMENT")
        aliased=row["two_slot_positive_vs_negative_indistinguishable"]["status"]=="SAT"
        unsafe=row["actual_same_original_state_Pre_and_NotPost"]["status"]=="SAT"
        row["two_input_classifier_mathematically_impossible_IA_AND_GOAL"]=aliased
        row["genuine_original_unsafe_at_initial_state"]=unsafe
        row["projection_alias_without_actual_initial_unsafety"]=aliased and not unsafe
        row["status"]="ACTUAL_ORIGINAL_SOURCE_EXACT_PROJECTION_BAR_INTERVAL_VERIFIED"
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_OR_INDEPENDENT_PROOF"
        row["exception"]=type(e).__name__+":"+str(e)[:400]
    row["actual_full_original_dual_source_projection_cost_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("Q3_PROJECTION_INFO_THEOREM",row["source"].rsplit("/",1)[-1],row["status"],
          "TWO_SLOT_IMPOSSIBLE",row.get("two_input_classifier_mathematically_impossible_IA_AND_GOAL"),
          "SAME_STATE_UNSAFE",row.get("genuine_original_unsafe_at_initial_state"),
          "ALIAS_ONLY",row.get("projection_alias_without_actual_initial_unsafety"),
          flush=True)
    return row
def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    freeze=json.loads(Path(a.freeze).read_text())
    assert freeze["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    assert len(freeze["cases"])==12
    rows=[per(Path(a.root),case) for case in freeze["cases"]]
    accepted=[r for r in rows if r["status"]=="ACTUAL_ORIGINAL_SOURCE_EXACT_PROJECTION_BAR_INTERVAL_VERIFIED"]
    result={
        "schema":"neumann.q3.original12_first_two_feature_information_lower_bound_dual.v1",
        "original_SHA_prebody_frozen_source_count":12,
        "originals_completely_dual_audited":len(accepted),
        "two_slot_representation_mathematically_insufficient_count":
            sum(r["two_input_classifier_mathematically_impossible_IA_AND_GOAL"] for r in accepted),
        "true_initial_unsafe_original_count":
            sum(r["genuine_original_unsafe_at_initial_state"] for r in accepted),
        "pure_information_alias_without_initial_unsafety_count":
            sum(r["projection_alias_without_actual_initial_unsafety"] for r in accepted),
        "all_source_variables_cannot_separate_count":
            sum(r["all_state_slots_positive_vs_negative_indistinguishable"]["status"]=="SAT" for r in accepted),
        "not_claim_of_neural_or_boolean_model_unique_success":True,
        "original_programs_ALREAdy_opened_by_PR412":True,
        "proof_implication":"Projection collision means ANY g(pi(x)) is impossible as entire Init/Post separator, not that no richer-state invariant exists",
        "model_training_or_neural_forwards":0,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "source_rows":rows}
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for key in ("originals_completely_dual_audited",
                "two_slot_representation_mathematically_insufficient_count",
                "true_initial_unsafe_original_count",
                "pure_information_alias_without_initial_unsafety_count",
                "all_source_variables_cannot_separate_count"):
        print("Q3_EXACT_INFORMATION_LOWER_BOUND",key,result[key])
    print("Q3_GLOBAL_OPEN")
if __name__=="__main__":main()
