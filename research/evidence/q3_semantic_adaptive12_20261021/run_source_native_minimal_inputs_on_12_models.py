"""POSTHOC original twelve: automatically choose per-source proved minimum
0/1-step state projection BEFORE actual CPU DecisionTree training; compare
same old frozen first-two-variable trained and no-fit OR on equal input.
For tautological Post cases, do not compute any learner: certify I=True
with independent real source Z3+cvc5 all three VCs.
No source-specific manual invariant, original bodies already opened PR412.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
import numpy as np
from research.evidence.q3_original12_state_information_profile_20261021.dual_verified_minimum_feature_distribution import once as select
from research.evidence.q3_dynamic_minimal_learned67_20261021.real_original_certified_minimum_interface_trained_tree import one as train
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc
)
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    sexprs,compile_typed_original,compile_independent_native
)
def ms(t):return (time.perf_counter_ns()-t)/1e6
def per(root,item):
    start=time.perf_counter_ns()
    out={"source":item["path"],"real_original_blob":item["git_blob"],"status":"ABSTAIN"}
    try:
        evidence=select(root,item)
        out["fully_independent_original_minimal_feature_proof"]=evidence
        if evidence["status"]!="MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS":
            out["status"]="ABSTAIN_SOURCE_INFO_MINIMUM_UNPROVEN"
            return out
        required=evidence["one_minimal_original_feature_indices"]
        if len(required)==0:
            raw=(root/item["path"]).read_bytes()
            src=compile_typed_original(sexprs(raw))
            native=compile_independent_native(sexprs(raw),src)
            certified,cert=verified_3vc(src,native,z3.BoolVal(True))
            out["trivial_zero_model_original_3VC_certified"]=bool(certified)
            out["trivial_original_all_dual_3VC"]=cert
            out["status"]="EXACT_POST_TAUTOLOGY_NO_MODEL_NEEDED"
            return out
        if len(required)>2:
            out["status"]="ABSTAIN_CURRENT_TREE_HAS_TWO_VISIBLE_VARIABLES"
            return out
        raw,src,native,identity=prepare(root,item)
        out["genuine_original_native_PreTransPost_parity"]=identity
        # Pad a proven single-feature projection to the existing fixed-width
        # two-slot tree interface. This is an implementation padding slot,
        # not an additional *mathematically required* feature.
        padded=list(required)
        for i in range(len(src["now"])):
            if len(padded)>=2:break
            if i not in padded:padded.append(i)
        out["source_minimum_semantic_features"]=required
        out["two_slot_model_feature_indices_including_padding"]=padded
        out["previous_frozen_two_slot_interface"]=train(src,native,(0,1))
        out["automatically_selected_semantic_interface"]=train(src,native,padded)
        out["status"]="ACTUAL_MODEL_TRAIN_AND_MATCHED_NOFIT_BOTH_INTERFACES"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_LEARNER_OR_PROOF"
        out["error"]=type(e).__name__+":"+str(e)[:420]
    finally:
        out["full_native_preflight_minimum_source_learning_and_proofs_ms"]=ms(start)
        adapt=out.get("automatically_selected_semantic_interface",{})
        old=out.get("previous_frozen_two_slot_interface",{})
        print("Q3_TRUE_ORIGINAL_ADAPTIVE_MODEL",out["source"].split("/")[-1],
              out["status"],
              "OLD_FIT",old.get("actual_trained"),
              "OLD_LEARN",old.get("learned_disjunction_full_original_inductive"),
              "NEW_FIT",adapt.get("actual_trained"),
              "NEW_LEARN",adapt.get("learned_disjunction_full_original_inductive"),
              "NEW_NOFIT",adapt.get("no_fit_disjunction_full_original_inductive"),
              "ERROR",out.get("error"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    assert f["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    assert len(f["cases"])==12 and len({x["git_blob"] for x in f["cases"]})==12
    rows=[per(Path(a.root),it) for it in f["cases"]]
    def cnt(which,field):
        return sum(x.get(which,{}).get(field,False) for x in rows)
    originals=[x for x in rows if x["status"]=="ACTUAL_MODEL_TRAIN_AND_MATCHED_NOFIT_BOTH_INTERFACES"]
    proof_zero=sum(x.get("trivial_zero_model_original_3VC_certified",False) for x in rows)
    report={
        "schema":"neumann.q3.12_originals_exact_minimum_semantic_feature_then_actual_trained_DNF.v1",
        "original_source_bodies_already_opened_by_prior_PR412":True,
        "genuine_originals":len(rows),
        "exact_source_state_minimum_proved_before_model_count":sum(
            r.get("fully_independent_original_minimal_feature_proof",{}).get("status")==
            "MINIMUM_ORIGINAL_SOURCE_INFO_PROVED_BY_BOTH_SOLVERS" for r in rows),
        "no_model_needed_original_Post_tautology_full_dual_proof":proof_zero,
        "source_specific_model_executed_cases":len(originals),
        "original_fixed_two_input_model_fitted":cnt("previous_frozen_two_slot_interface","actual_trained"),
        "semantic_adaptive_two_input_model_fitted":cnt("automatically_selected_semantic_interface","actual_trained"),
        "original_fixed_two_input_learned_full_3VC":cnt("previous_frozen_two_slot_interface","learned_disjunction_full_original_inductive"),
        "semantic_adaptive_learned_full_3VC":cnt("automatically_selected_semantic_interface","learned_disjunction_full_original_inductive"),
        "semantic_adaptive_no_fit_OR_full_3VC":cnt("automatically_selected_semantic_interface","no_fit_disjunction_full_original_inductive"),
        "learned_gain_over_adaptive_no_fit_count":sum(
            r["automatically_selected_semantic_interface"].get("learned_disjunction_full_original_inductive",False) and
            not r["automatically_selected_semantic_interface"].get("no_fit_disjunction_full_original_inductive",False)
            for r in originals),
        "adaptive_no_fit_gain_over_learned_count":sum(
            r["automatically_selected_semantic_interface"].get("no_fit_disjunction_full_original_inductive",False) and
            not r["automatically_selected_semantic_interface"].get("learned_disjunction_full_original_inductive",False)
            for r in originals),
        "automatic_tautology_or_adaptive_learned_full_original_safe":proof_zero+cnt("automatically_selected_semantic_interface","learned_disjunction_full_original_inductive"),
        "automatic_tautology_or_adaptive_no_fit_full_original_safe":proof_zero+cnt("automatically_selected_semantic_interface","no_fit_disjunction_full_original_inductive"),
        "no_trained_weights_transferred_between_sources":True,
        "positive_result_only_original_source_Z3_cvc5_three_VC":True,
        "do_not_confuse_0_1_step_input_minimum_with_complete_proof":True,
        "same_source_matched_full_original_dual_solver_rights":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "cases":rows}
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True,default=lambda z:int(z) if isinstance(z,np.integer) else float(z) if isinstance(z,np.floating) else str(z))+"\n")
    for k in ("exact_source_state_minimum_proved_before_model_count",
              "no_model_needed_original_Post_tautology_full_dual_proof",
              "original_fixed_two_input_model_fitted","semantic_adaptive_two_input_model_fitted",
              "original_fixed_two_input_learned_full_3VC",
              "semantic_adaptive_learned_full_3VC","semantic_adaptive_no_fit_OR_full_3VC",
              "automatic_tautology_or_adaptive_learned_full_original_safe",
              "automatic_tautology_or_adaptive_no_fit_full_original_safe"):
        print("Q3_TWELVE_ACTUAL_SEMANTIC_LEARNED_RESULT",k,report[k],flush=True)
    print("GLOBAL_Q3_OPEN")
if __name__=="__main__":main()
