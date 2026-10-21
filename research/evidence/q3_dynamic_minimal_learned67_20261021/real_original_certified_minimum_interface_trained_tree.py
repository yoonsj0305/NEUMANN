"""POSTHOC test of whether a PROVED minimal source semantic input interface
enables actual fitted Boolean learner to verify full ORIGINAL safety.

Automatically obtain minimum feature indices from the source-independent dual
Z3/cvc5 feature-search algorithm. No hardcoded human invariant or variable
names. Reuse unchanged DecisionTree/SMT-calibration from PR411. Compare
original first-two-feature interface, selected minimal interface, and an
equal-data exact no-fit OR grammar on the selected minimal interface.
This is NOT source-blind and not proof of neural superiority.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from research.evidence.q3_minimum_exact_state_20261021.minimal_native_semantic_feature_subset import run as find_minimum
from research.evidence.q3_guarded_tree_83_20261021.actual_trained_tree_SMT_disjunction import (
    dataset,find_tree,find_no_fit,terms
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc,original_syguS,native_pdr
)
CASE="lib/Inv_Track/xujie_code2inv/67.c.sl"
GIT="5e1807ee5cbfa43c828fc3f67c3c31d4cb133a88"
def nowms(t):return (time.perf_counter_ns()-t)/1e6
def one(src,native,feature_indices):
    begin=time.perf_counter_ns()
    record={"indices":list(feature_indices),"status":"ABSTAIN","actual_trained":False}
    # Reorder both now and next, maintaining variable correspondence and
    # original complete source formula. The learned tree still sees two slots.
    view=dict(src)
    order=list(feature_indices)+[i for i in range(len(src["now"])) if i not in feature_indices]
    view["now"]=[src["now"][i] for i in order]
    view["next"]=[src["next"][i] for i in order]
    try:
        pos,neg=dataset(view,native)
        record["source_native_positive_samples"]=len(pos)
        record["source_native_negative_samples"]=len(neg)
        if len(pos)<8 or len(neg)<4:raise RuntimeError("SOURCE_NATIVE_DATA_INSUFFICIENT")
        X=np.asarray(pos+neg,dtype=np.int64)
        y=np.asarray([1]*len(pos)+[0]*len(neg),dtype=np.int64)
        t=time.perf_counter_ns()
        clf=DecisionTreeClassifier(max_depth=2,max_leaf_nodes=3,min_samples_leaf=2,
                                   class_weight="balanced",random_state=20261021).fit(X,y)
        record["training_ms"]=nowms(t)
        record["actual_trained"]=True
        record["fitted_tree_depth"]=clf.get_depth()
        record["fitted_tree_leaf_count"]=clf.get_n_leaves()
        record["fitted_DNF_before_threshold_calibration"]=terms(
            clf,{i:int(clf.tree_.threshold[i]//1)
                 for i in range(clf.tree_.node_count) if clf.tree_.children_left[i]>=0})
        t=time.perf_counter_ns()
        candidate,trainsearch=find_tree(view,native,clf,pos,neg)
        record["trained_calibration"]=trainsearch
        record["trained_calibration_ms"]=nowms(t)
        if candidate is not None:
            verified,receipts=verified_3vc(view,native,candidate)
            record["learned_disjunction_full_original_inductive"]=bool(verified)
            record["learned_disjunction_original_dual_3VC"]=receipts
            record["learned_disjunction_original_smt"]=candidate.sexpr()
        else:record["learned_disjunction_full_original_inductive"]=False
        t=time.perf_counter_ns()
        baseline,search=find_no_fit(view,native,pos,neg)
        record["exact_same_data_no_fit_OR_search"]=search
        record["exact_no_fit_search_ms"]=nowms(t)
        if baseline is not None:
            verified,receipts=verified_3vc(view,native,baseline)
            record["no_fit_disjunction_full_original_inductive"]=bool(verified)
            record["no_fit_disjunction_original_dual_3VC"]=receipts
            record["no_fit_original_smt"]=baseline.sexpr()
        else:record["no_fit_disjunction_full_original_inductive"]=False
        record["status"]="COMPLETE_ACTUAL_TRAINED_AND_CLASSICAL_EXACT_ORIGINAL_3VC"
    except Exception as ex:
        record["status"]="ABSTAIN_SOURCE_PROJECTED_DATA_OR_SOLVER"
        record["error"]=type(ex).__name__+":"+str(ex)[:340]
    record["source_sample_train_search_all_original_wall_ms"]=nowms(begin)
    return record
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    q=next(x for x in f["cases"] if x["path"]==CASE)
    if q["git_blob"]!=GIT:raise RuntimeError("GENUINE_ORIGINAL_GIT_BLOB_CHANGED")
    started=time.perf_counter_ns()
    exact=find_minimum(Path(a.root),f)
    if exact["status"]!="PROVED_FINITE_FEATURE_MINIMUM_ORIGINAL_NATIVE_Z3_CVC5":
        raise RuntimeError("MINIMUM_SEMANTIC_INFORMATION_NOT_INDEPENDENTLY_PROVEN")
    indices=exact["one_minimal_feature_indices"]
    if len(indices)!=2:raise RuntimeError("TRAINED_TREE_CURRENTLY_TWO_FEATURES_ONLY")
    raw,src,native,parity=prepare(Path(a.root),q)
    fixed=one(src,native,(0,1))
    minimal=one(src,native,indices)
    # Same original and full-rights classical original solver:
    sygus=original_syguS(raw,src,native,2.0)
    pdr=native_pdr(src,native)
    report={
      "schema":"neumann.q3.posthoc_semantic_minimum_interface_to_actual_trained_DNF_original.v1",
      "same_original_git_SHA":GIT,
      "real_original_native_source_parity":parity,
      "exact_Z3_cvc5_all_smaller_subsets_minimum_feature_proof":exact,
      "prior_original_first_two_state_interface":fixed,
      "algorithmically_selected_two_feature_interface":minimal,
      "same_source_original_cvc5_SyGuS_2s":sygus,
      "same_source_original_Z3_SPACER":pdr,
      "learned_proof_gain_from_interface_only":(
          minimal.get("learned_disjunction_full_original_inductive",False) and
          not fixed.get("learned_disjunction_full_original_inductive",False)),
      "novel_beyond_equal_rights_no_fit_OR":(
          minimal.get("learned_disjunction_full_original_inductive",False) and
          not minimal.get("no_fit_disjunction_full_original_inductive",False)),
      "original_full_source_total_wall_ms":nowms(started),
      "already_opened_program_this_is_POSTHOC":True,
      "human_preexisting_original_safety_solution_NOT_provided_to_learner":True,
      "model_fit_on_actual_original_pre_trans_post_data_not_weight_transfer":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"
    }
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True,default=lambda z:
        int(z) if isinstance(z,np.integer) else float(z) if isinstance(z,np.floating) else str(z))+"\n")
    print("Q3_MIN_FEATURE_SET",indices,flush=True)
    for label,r in (("FIXED_ORIGINAL_TWO",fixed),("MINIMUM_SEMANTIC_TWO",minimal)):
        print("Q3_ACTUAL_LEARNED_SEMANTIC_INPUT",label,"STATUS",r["status"],
              "FIT",r["actual_trained"],
              "LEARNED_PROOF",r.get("learned_disjunction_full_original_inductive"),
              "EXACT_OR",r.get("no_fit_disjunction_full_original_inductive"),
              "ERROR",r.get("error"),flush=True)
    print("Q3_NATIVE_3VC_STRONG_CLASSICAL_SYGUS",sygus["certified"],
          "SPACER",pdr["certified"],flush=True)
    print("Q3_GLOBAL_OPEN",flush=True)
if __name__=="__main__":main()
