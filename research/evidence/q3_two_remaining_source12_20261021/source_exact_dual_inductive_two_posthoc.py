"""Posthoc independent ORIGINAL full three-VC proof of 2 previously timeouted
source-first heldout genuine SyGuS original programs. Candidate structure was
derived by human inspection AFTER PR389 first source open. NO learned Q3 claim.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc,dual,DUAL_S
)

PRIOR_SHA="63270250aa9f422bb06d55569ece27e3200bc8355994d8ffe294a9b53b3ff06a"
SCHEMA="neumann.q3.two_posthoc_original_unresolved_inductive_witness_preregister_v1"
def timed(t):return (time.perf_counter_ns()-t)/1e6

def build(src,name):
    original_names=[n for n,sort in src["states"]]
    now={key:val for key,val in zip(original_names,src["now"])}
    if name=="fib_21.sl":
        if original_names!=["i","j","k","c1","c2","n","v"]:
            raise RuntimeError("FIB21_ORIGINAL_SEVEN_STATE_SIGNATURE_CHANGED")
        i,k,c1,c2,n=(now[q] for q in ("i","k","c1","c2","n"))
        base_terms=[n>0,i>=0,c1>=2000,c2>=2000]
        distinguishing=k>=2000*i
    elif name=="jmbl_hola.41.sl":
        if original_names!=["i","j","k","n"]:
            raise RuntimeError("HOLA41_ORIGINAL_FOUR_STATE_SIGNATURE_CHANGED")
        i,j,k,n=(now[q] for q in ("i","j","k","n"))
        base_terms=[k>=0,n>=0,i>=0,j>=0,i<=n+1]
        distinguishing=j>=i-1
    else:raise RuntimeError("ORIGINAL_SOURCE_NOT_REGISTERED")
    inv=z3.And(*(base_terms+[distinguishing]))
    mutation=z3.And(*base_terms)
    return inv,mutation,{
        "original_source_state_names":original_names,
        "true_source_invariant_AST_SHA256":hashlib.sha256(inv.sexpr().encode()).hexdigest(),
        "synthetic_ablation_weak_AST_SHA256":hashlib.sha256(mutation.sexpr().encode()).hexdigest(),
        "human_read_original_source_after_previous_first_open":True
    }

def case(root,item,contract_item):
    t=time.perf_counter_ns()
    out={"source":item["path"],"original_git_blob":item["git_blob"],
         "posthoc_human_discovered_NOT_learned":True,
         "source_original_independent_dual_3VC_certified":False,"status":"ABSTAIN"}
    try:
        if item["path"]!=contract_item["path"] or item["git_blob"]!=contract_item["original_git_blob"]:
            raise RuntimeError("SOURCE_PROSPECTIVE_SHA_CONTRACT_DIVERGES")
        raw,src,native,identity=prepare(root,item)
        out["original_source_identity_and_full_native_three_formula_parity"]=identity
        inv,weak,meta=build(src,item["path"].rsplit("/",1)[-1])
        if meta["original_source_state_names"]!=contract_item["expected_states"]:
            raise RuntimeError("SOURCE_VARIABLES_CHANGED_AFTER_REGISTERED_WITNESS")
        out["typed_exact_symbolic_candidate"]=meta
        pass3,steps=verified_3vc(src,native,inv)
        out["original_full_pre_trans_post_inductive_three_VCs_both_Z3_cvc5"]=steps
        out["source_original_independent_dual_3VC_certified"]=bool(pass3)
        weak_goal=dual(z3.And(weak,z3.Not(native["post"])),"sat",DUAL_S)
        out["negative_synthetic_weakened_invariant_COUNTERMODEL_dual"]=weak_goal
        out["negative_synthetic_ablation_shows_missing_constraint"]=bool(weak_goal["dual_pass"])
        out["negative_not_an_original_program_unsafe_claim"]=True
        out["status"]="EXACT_ORIGINAL_TRUE_SAFE_FULL_INDUCTIVE_DUAL_PROOF" if (
            pass3 and weak_goal["dual_pass"]) else "HOLD_UNPROVEN_OR_NEGATIVE_CONTROL_FAILED"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_OR_ORIGINAL_DUAL_PROOF_ERROR"
        out["error"]=type(e).__name__+":"+str(e)[:420]
    out["source_compile_candidate_dual3VC_and_negative_wall_ms"]=timed(t)
    print("Q3_PREVIOUS_UNSOLVED_ORIGINAL",item["path"],"VERDICT",out["status"],
          "FULL_SOURCE_DUAL_3VC",out["source_original_independent_dual_3VC_certified"],
          "INDEPENDENT_SYNTHETIC_WEAK_REFUTATION",out.get("negative_synthetic_ablation_shows_missing_constraint"),
          "ERROR",out.get("error"),flush=True)
    return out

def audit(prior,manifest,contract,root):
    if contract["schema"]!=SCHEMA:raise RuntimeError("CANDIDATE_CONTRACT_CHANGED")
    cases=manifest["new_originals"]
    if len(cases)!=12 or len({v["git_blob"] for v in cases})!=12:
        raise RuntimeError("SOURCE12_FIRST_LOCK_CHANGED")
    prev=prior["original_new_programs"]
    if len(prev)!=12 or prior["trained_new_original_full_native_3VC_success"]!=10:
        raise RuntimeError("HISTORICAL_FIRST_ORIGINAL_10_SUCCESS_NOT_PRESERVED")
    if [v["git_blob"] for v in prev]!=[v["git_blob"] for v in cases]:
        raise RuntimeError("PREVIOUS_RUN_ORIGINAL_SOURCE_SHA_ORDER_CONFLICT")
    independent_first_certified=[z for z in prev if z["status"]=="COMPLETE_SAME_NATIVE_ORIGINAL_CPU_ROUTE_COMPARISON" and z["matched_trained_success"]]
    unresolved=[z for z in prev if not z.get("matched_trained_success",False)]
    targets=contract["case_contracts"]
    if len(unresolved)!=2 or len(targets)!=2:raise RuntimeError("EXPECTED_EXACTLY_2_PREVIOUS_UNRESOLVED")
    frozen={x["path"]:x for x in cases}
    if {x["source"] for x in unresolved}!={x["path"] for x in targets}:
        raise RuntimeError("POSTHOC_CANDIDATES_NOT_HISTORICAL_UNKNOWN")
    experiments=[case(root,frozen[z["path"]],z) for z in targets]
    successful=sum(x["status"]=="EXACT_ORIGINAL_TRUE_SAFE_FULL_INDUCTIVE_DUAL_PROOF" for x in experiments)
    return {
      "schema":"neumann.q3.original_first12_fully_proof_partition_10_existing_plus2_new_posthoc_v1",
      "prior_action_original_first_run":39579514369,
      "prior_JSON_SHA256":PRIOR_SHA,
      "original_all_sha_first_metadata_frozen_before_program_body_count":12,
      "previous_first_CPU_router_native_inductively_certified_original_count":len(independent_first_certified),
      "previous_original_unresolved_count":len(unresolved),
      "new_posthoc_original_independently_Z3_cvc5_inductive_safe_proven":successful,
      "total_distinct_true_original_full_inductive_safe_proven":len(independent_first_certified)+successful,
      "newly_confirmed_authentic_source_proof_cases":experiments,
      "manually_source_inspected_after_first_original_test":True,
      "no_model_unique_structure_claim":True,
      "no_new_neural_gradient_or_inference":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"
    }

def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","contract","prior","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    raw=Path(a.prior).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PRIOR_SHA:raise RuntimeError("OLD_OFFICIAL_ACTION_ORIGINAL_SOURCE_JSON_SHA_MISMATCH")
    out=audit(json.loads(raw),json.loads(Path(a.freeze).read_text()),
              json.loads(Path(a.contract).read_text()),Path(a.root))
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("Q3_ORIGINAL_FIRST12_PREV_DUAL_SOURCE_CERTIFIED",out["previous_first_CPU_router_native_inductively_certified_original_count"])
    print("Q3_ORIGINAL_FIRST12_NEW_POSTHOC_INDEPENDENT_TRUE_SOURCE_SAFE",out["new_posthoc_original_independently_Z3_cvc5_inductive_safe_proven"])
    print("Q3_ORIGINAL_FIRST12_TOTAL_GENUINE_INDUCTIVE_PROVEN",out["total_distinct_true_original_full_inductive_safe_proven"])
    print("Q3_GLOBAL_LEARNED_DISCOVERY_OPEN")
if __name__=="__main__":main()
