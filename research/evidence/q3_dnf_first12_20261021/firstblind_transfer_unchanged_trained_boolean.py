"""FIRST unopened 12 authentic Code2Inv programs, SAME fitted DNF model/solver
that had already run on previously opened original 83 in PR411. Fail closed.
No per-source hand invariant, no source filename feature or posthoc architecture
change. A learned Boolean skeleton alone is not an independently learned proof:
exact SMT calibration and classical enumeration receive the same native source.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import z3
from sklearn.tree import DecisionTreeClassifier
from research.evidence.q3_guarded_tree_83_20261021.actual_trained_tree_SMT_disjunction import (
    dataset,find_tree,find_no_fit,terms
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc,original_syguS,native_pdr,dual,DUAL_S
)
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as classical
PRE_SOURCE_LOCK="ba08ffcf1760ef556d6f4fd058f81ef656263642"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def ms(t):return (time.perf_counter_ns()-t)/1e6
def proof(src,native,inv):
    if inv is None:return {"certified":False}
    ok,vc=verified_3vc(src,native,inv)
    return {"certified":bool(ok),"full_genuine_source_Z3_cvc5_3VC":vc,
            "typed_original_AST":inv.sexpr()}
def one(root,item):
    t=time.perf_counter_ns()
    out={"source":item["path"],"source_git_blob":item["git_blob"],
         "status":"ABSTAIN","model_trained":False}
    try:
        _,src,native,parity=prepare(root,item)
        out["full_original_native_Pre_Trans_Post_parity"]=parity
        unsafe=dual(z3.And(native["pre"],z3.Not(native["post"])),"sat",DUAL_S)
        out["initial_unsafety_dual_sat"]=unsafe
        if unsafe["dual_pass"]:
            out["status"]="ORIGINAL_UNSAFE_INIT_NOT_A_VALID_SAFE_PROOF_TARGET"
            return out
        pos,neg=dataset(src,native)
        out["positive_native_source_samples"]=len(pos)
        out["negative_native_NotPost_samples"]=len(neg)
        if len(pos)<8 or len(neg)<4:
            out["status"]="ABSTAIN_INSUFFICIENT_SOURCE_NATIVE_TRAINING"
            return out
        data=np.asarray(pos+neg,dtype=np.int64)
        label=np.asarray([1]*len(pos)+[0]*len(neg),dtype=np.int64)
        fit=time.perf_counter_ns()
        clf=DecisionTreeClassifier(max_depth=2,max_leaf_nodes=3,min_samples_leaf=2,
                                   class_weight="balanced",random_state=20261021)
        clf.fit(data,label)
        out["model_fit_wall_ms"]=ms(fit);out["model_trained"]=True
        out["model_tree_depth"]=int(clf.get_depth())
        out["model_positive_DNF_structure"]=terms(clf,{
            i:int(clf.tree_.threshold[i]//1) for i in range(clf.tree_.node_count)
            if clf.tree_.children_left[i]>=0})
        out["learned_nonconvex_boolean_two_positive_leaves"]=len(out["model_positive_DNF_structure"])>=2
        s=time.perf_counter_ns()
        candidate,search=find_tree(src,native,clf,pos,neg)
        out["model_symbolic_calibration_details"]=search
        out["model_train_then_calibrate_plus_verify_wall_ms"]=ms(s)+out["model_fit_wall_ms"]
        out["trained_DNF_full_original_native_safe"]=proof(src,native,candidate)
        s=time.perf_counter_ns()
        baseline,base=find_no_fit(src,native,pos,neg)
        out["strong_no_fit_boolean_OR_candidates"]=base
        out["strong_no_fit_search_and_dual_wall_ms"]=ms(s)
        out["same_data_no_fit_OR_full_original_native_safe"]=proof(src,native,baseline)
        # Third equal-authority strong solver baseline with native original 3VC.
        out["source_original_cvc5_SyGuS_2s"]=original_syguS((root/item["path"]).read_bytes(),src,native,2.0)
        out["status"]="EXECUTED_NEW_ORIGINAL_SOURCE_FULL_PROOF_COMPARISON"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_DATA_MODEL_OR_SOLVER"
        out["exception"]=type(e).__name__+":"+str(e)[:350]
    finally:
        out["whole_original_training_comparison_wall_ms"]=ms(t)
        print("Q3_FIRSTBLIND_TRAINED_DNF_ORIGINAL",out["source"].split("/")[-1],
              out["status"],"FIT",out["model_trained"],
              "TREE",out.get("trained_DNF_full_original_native_safe",{}).get("certified"),
              "EXACT_OR",out.get("same_data_no_fit_OR_full_original_native_safe",{}).get("certified"),
              "SYGUS",out.get("source_original_cvc5_SyGuS_2s",{}).get("certified"),
              "ERROR",out.get("exception"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args();f=json.loads(Path(a.freeze).read_text())
    assert f["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    assert f["original_revision"].split("@")[-1]==REV
    assert f["original_source_bodies_not_read_before_freeze"]
    items=f["cases"]
    assert len(items)==12 and len({x["git_blob"] for x in items})==12
    for item in items:
        raw=(Path(a.root)/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or sha(raw)!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_FROZEN_SHA_OR_SIZE_MISMATCH:"+item["path"])
    rows=[one(Path(a.root),item) for item in items]
    completed=[r for r in rows if r["status"]=="EXECUTED_NEW_ORIGINAL_SOURCE_FULL_PROOF_COMPARISON"]
    count=lambda field:sum(r.get(field,{}).get("certified",False) for r in completed)
    report={
        "schema":"neumann.q3.first_unseen_original12_actual_learned_boolean_DNF_vs_exact_classical.v1",
        "preregister_source_SHA_only_Git_commit":PRE_SOURCE_LOCK,
        "first_source_originals_sha_verified":12,
        "first_source_originals_actually_model_fitted":sum(r["model_trained"] for r in rows),
        "full_original_source_proof_comparisons":len(completed),
        "verified_new_original_learned_boolean_DNF_3VC":count("trained_DNF_full_original_native_safe"),
        "verified_new_original_nolearn_boolean_OR_3VC":count("same_data_no_fit_OR_full_original_native_safe"),
        "verified_new_original_classical_SyGuS_3VC":count("source_original_cvc5_SyGuS_2s"),
        "learned_success_nofit_fails":sum(r["trained_DNF_full_original_native_safe"]["certified"] and
           not r["same_data_no_fit_OR_full_original_native_safe"]["certified"] for r in completed),
        "nolearn_success_learned_fails":sum(not r["trained_DNF_full_original_native_safe"]["certified"] and
            r["same_data_no_fit_OR_full_original_native_safe"]["certified"] for r in completed),
        "new_original_unsafe_initial_dual":sum(r["status"]=="ORIGINAL_UNSAFE_INIT_NOT_A_VALID_SAFE_PROOF_TARGET" for r in rows),
        "model_DNF_not_model_only_verifier_calibrated":True,
        "same_data_strong_OR_classical_equal_math_rights":True,
        "source_specific_fitting_not_pretrained_weight_transfer":True,
        "benchmark_from_same_xujie_subcorpus":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "all_original_cases":rows}
    Path(a.out).write_text(json.dumps(report,sort_keys=True,indent=2,default=lambda z:int(z) if isinstance(z,np.integer) else float(z) if isinstance(z,np.floating) else str(z))+"\n")
    for k in ("first_source_originals_actually_model_fitted","full_original_source_proof_comparisons",
              "verified_new_original_learned_boolean_DNF_3VC","verified_new_original_nolearn_boolean_OR_3VC",
              "verified_new_original_classical_SyGuS_3VC","learned_success_nofit_fails",
              "nolearn_success_learned_fails","new_original_unsafe_initial_dual"):
        print("Q3_NEW_BLIND_BOOLEAN_MODEL",k,report[k],flush=True)
if __name__=="__main__":main()
