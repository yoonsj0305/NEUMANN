"""Complete-source Q3 posthoc hybrid: generic existing classical Houdini
followed by strong cvc5 SyGuS and Z3 SPACER. NO per-program case dispatch,
original solution lookup, learned parameter, model or novel theorem claim.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as base
from research.evidence.q3_auto_linear_houdini_20261021.source_agnostic_linear_Houdini_source12 import (
    generate,initialization_filter,houdini
)
from research.evidence.q4_source12_budget_20261021.real_12_native_full_cost_portfolio import ms

def certified_houdini(src,native):
    start=time.perf_counter_ns()
    res={"route":"source_agnostic_classical_Houdini_linear","certified":False}
    try:
        contract_candidate_cap=2500
        x,constants=generate(src,native,contract_candidate_cap)
        possible,refuted,unknown=initialization_filter(x,native,2500)
        clauses,history,verdict=houdini(src,native,possible,100,2500)
        res["actual_original_native_constants"]=constants
        res["syntactic_candidate_count"]=len(x)
        res["native_Pre_admitted_count"]=len(possible)
        res["source_CEGAR_Houdini_iterations"]=history
        res["actual_Trans_inductive_verdict"]=verdict
        res["unknown_or_false_init_candidates"]=unknown+refuted
        res["remaining_final_candidate_conjuncts"]=len(clauses)
        if verdict=="PROVED_INDUCTIVE_FIXED_POINT":
            inv=z3.And(*clauses)
            proved,receipts=base.verified_3vc(src,native,inv)
            res["original_full_3VC_independent_Z3_cvc5"]=receipts
            res["candidate_full_ast_sha256"]=hashlib.sha256(inv.sexpr().encode()).hexdigest()
            res["certified"]=bool(proved)
        res["status"]="FULL_NATIVE_3VC_CERTIFIED" if res["certified"] else "ABSTAIN_ORIGINAL_SAFE_UNPROVEN"
    except Exception as e:
        res["status"]="ABSTAIN_HOUDINI_ERROR"
        res["exception"]=type(e).__name__+":"+str(e)[:420]
    res["complete_source_candidate_init_trans_verification_wall_ms"]=ms(start)
    return res

def do_sequence(raw,src,native,kind):
    t=time.perf_counter_ns()
    sequence={
      "H_then_S_then_D":("H","S","D"),
      "S_then_D":("S","D"),
      "D_then_S":("D","S")
    }[kind]
    attempts=[];certified=False
    for arm in sequence:
        if arm=="H":o=certified_houdini(src,native)
        elif arm=="S":o=base.original_syguS(raw,src,native,3.0)
        else:o=base.native_pdr(src,native)
        attempts.append({"arm":arm,"verifiable_result":o})
        if o["certified"]:
            certified=True
            break
    return {
      "fixed_classical_route":kind,
      "all_original_source_solver_calls_including_failures":attempts,
      "fully_actual_original_inductive_SAFE_certified":certified,
      "total_dynamic_actual_wall_ms":ms(t),
      "any_unsupported_or_unknown_not_safety_proof":not certified
    }
def per_source(root,item,index):
    begin=time.perf_counter_ns()
    row={"source":item["path"],"original_git_blob":item["git_blob"],"status":"ABSTAIN"}
    try:
        t=time.perf_counter_ns()
        raw,src,native,ident=base.prepare(root,item)
        row["genuine_original_full_independent_semantic_source_identity"]=ident
        row["common_native_source_compile_double_parity_wall_ms"]=ms(t)
        first=do_sequence(raw,src,native,"H_then_S_then_D")
        if index%2:
            second=do_sequence(raw,src,native,"D_then_S")
            third=do_sequence(raw,src,native,"S_then_D")
        else:
            second=do_sequence(raw,src,native,"S_then_D")
            third=do_sequence(raw,src,native,"D_then_S")
        row["generic_Houdini_first_full_hybrid"]=first
        row["static_original_SyGuS_then_SPACER"]=third if index%2 else second
        row["static_original_SPACER_then_SyGuS"]=second if index%2 else third
        row["all_matched_originals_full_inductive_success"]={
            "hybrid":first["fully_actual_original_inductive_SAFE_certified"],
            "S_then_D":row["static_original_SyGuS_then_SPACER"]["fully_actual_original_inductive_SAFE_certified"],
            "D_then_S":row["static_original_SPACER_then_SyGuS"]["fully_actual_original_inductive_SAFE_certified"]
        }
        prep=row["common_native_source_compile_double_parity_wall_ms"]
        row["individual_deploy_source_wall_including_prep_ms"]={
            "hybrid":prep+first["total_dynamic_actual_wall_ms"],
            "S_then_D":prep+row["static_original_SyGuS_then_SPACER"]["total_dynamic_actual_wall_ms"],
            "D_then_S":prep+row["static_original_SPACER_then_SyGuS"]["total_dynamic_actual_wall_ms"]
        }
        row["status"]="COMPLETE_ALL_THREE_TRUE_ORIGINAL_SOURCE_PROGRAMS"
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_AUTH_OR_RUNTIME"
        row["error"]=type(e).__name__+":"+str(e)[:450]
    row["full_experiment_all_original_provers_wall_ms"]=ms(begin)
    print("Q3_CLASSICAL_HYBRID_ORIGINAL",index+1,item["path"],
          "VERDICTS",row.get("all_matched_originals_full_inductive_success"),
          "H_FIRST",row.get("generic_Houdini_first_full_hybrid",{}).get("all_original_source_solver_calls_including_failures",[{}])[0].get("arm"),
          "STATUS",row["status"],"ERROR",row.get("error"),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    for arg in ("root","freeze","contract","out"):p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    contract=json.loads(Path(a.contract).read_text())
    manifest=json.loads(Path(a.freeze).read_text())
    if contract["schema"]!="neumann.q3.posthoc_original12_generic_Houdini_syguS_spacer_complete_hybrid_v1":
        raise RuntimeError("HYBRID_FIXED_METHOD_CONTRACT_CHANGED")
    if len(manifest["new_originals"])!=12:
        raise RuntimeError("PRIOR_AUTHENTIC_TWELVE_SOURCE_SET_CHANGED")
    base.PDR_MS=5000
    results=[per_source(Path(a.root),t,i) for i,t in enumerate(manifest["new_originals"])]
    valid=[r for r in results if r["status"]=="COMPLETE_ALL_THREE_TRUE_ORIGINAL_SOURCE_PROGRAMS"]
    allthree=[r for r in valid if all(r["all_matched_originals_full_inductive_success"].values())]
    hybrid_count=sum(r["all_matched_originals_full_inductive_success"]["hybrid"] for r in valid)
    s_count=sum(r["all_matched_originals_full_inductive_success"]["S_then_D"] for r in valid)
    d_count=sum(r["all_matched_originals_full_inductive_success"]["D_then_S"] for r in valid)
    q={
       "schema":"neumann.q3.classical_houdini_first_true_original12_dual_inductive_hybrid_v1",
       "originals":results,
       "original_source_auth_native_parity_count":len(valid),
       "full_original_native_independently_Z3_cvc5_hybrid_certified_count":hybrid_count,
       "original_strong_static_sygus_first_certified_count":s_count,
       "original_strong_static_pdr_first_certified_count":d_count,
       "all_methods_inductively_certified_same_originals":len(allthree),
       "hybrid_minus_best_static_original_extra_under_frozen_caps":hybrid_count-max(s_count,d_count),
       "source_agnostic_no_per_file_manual_invariant":True,
       "all_source_bodies_previous_opened_and_hypothesis_posthoc":True,
       "full_original_source_verifier_authority_same_for_all":True,
       "strong_classical_with_same_Houdini_can_copy_mechanism":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
       "neural_training_updates":0,"neural_model_calls":0
    }
    if allthree:
        costs={k:sum(r["individual_deploy_source_wall_including_prep_ms"][k] for r in allthree)
               for k in ("hybrid","S_then_D","D_then_S")}
        q["matched_original_three_method_total_full_wall_ms"]=costs
        q["matched_best_static_after_source_open_over_hybrid_ratio"]=(
             min(costs["S_then_D"],costs["D_then_S"])/costs["hybrid"] if costs["hybrid"] else None)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(q,sort_keys=True,indent=2)+"\n")
    for key in ("original_source_auth_native_parity_count",
                "full_original_native_independently_Z3_cvc5_hybrid_certified_count",
                "original_strong_static_sygus_first_certified_count",
                "original_strong_static_pdr_first_certified_count",
                "all_methods_inductively_certified_same_originals",
                "hybrid_minus_best_static_original_extra_under_frozen_caps",
                "matched_best_static_after_source_open_over_hybrid_ratio"):
        print("Q3_TRUE_ORIGINAL_HYBRID",key,q.get(key))
    print("Q3_GLOBAL_LEARNED_NOT_PROVEN",q["global_Q3"])
if __name__=="__main__":main()
