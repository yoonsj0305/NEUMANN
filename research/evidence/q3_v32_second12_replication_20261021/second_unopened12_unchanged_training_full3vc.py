"""SECOND original-source-body-blind 12-case replication of already FIXED PCA+Post.
Training, candidate generation, Houdini, Z3/cvc5 ALL come from unchanged PR402.
Original git blob metadata frozen separately at 37e26ee BEFORE ANY source open.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.evidence.q3_v32_posthoc_full_original_20261021.real_trained_PCA_plus_source_Post_3VC import one
LOCK="37e26ee320717c9e903f7e2b9fa512ff378c4c9c"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def run(root,f):
    if f["schema"]!="neumann.q3.v32_second12_first_body_unopened_replication_of_same_frozen_learner.v1":
        raise RuntimeError("SECOND_ORIGINAL_SOURCE_METADATA_CHANGED")
    if f["upstream"].split("@")[-1]!=REV or not f["new_source_original_BODIES_NOT_OPENED_BEFORE_SHA_commit"]:
        raise RuntimeError("SECOND_ORIGINAL_COHORT_NOT_FROZEN_BEFORE_SOURCE")
    items=f["cases"]
    if len(items)!=12 or len({x["git_blob"] for x in items})!=12:
        raise RuntimeError("SECOND_COHORT_NOT_TWELVE_DISTINCT_BLOBS")
    # FIRST source body opening only after metadata commitment
    for item in items:
        b=(root/item["path"]).read_bytes()
        if len(b)!=item["bytes"] or sha(b)!=item["git_blob"]:
            raise RuntimeError("NEW_ORIGINAL_SOURCE_BLOB_MISMATCH:"+item["path"])
    rows=[]
    for item in items:
        row=one(root,item)
        row["original_SHA_matched_prior_metadata_commit"]=True
        rows.append(row)
    def count(k):return sum(r.get(k,{}).get("fully_verified_complete_original_3VC",False) for r in rows)
    return {
        "schema":"neumann.q3.v32_second_source_unopened12_original_actual_learned_safety_replication.v1",
        "source_body_unopened_registration_commit":LOCK,
        "source_selection_only_SHA_metadata":True,
        "source_first_original_SHA_verified_count":12,
        "actual_PCA_model_fit_source_count":sum(r.get("actual_CPU_fitted_model",{}).get("real_CPU_PCA_model_fits",0)>0 for r in rows),
        "post_only_full_source_3VC":count("POST_only_already_exact_original_dual"),
        "simple_nolearn_plus_post_full_source_3VC":count("simple_NOLEARN_plus_original_POST"),
        "trained_PCA_plus_post_full_source_3VC":count("TRAINED_PCA_plus_original_POST"),
        "exact_classical_plus_post_full_source_3VC":count("EXACT_CLASSICAL_plus_original_POST"),
        "trained_additional_vs_simple_nolearn":sum(r.get("trained_full_3VC_success_not_no_learn",False) for r in rows),
        "trained_additional_vs_exact_classical":sum(r.get("trained_full_3VC_success_not_exact_classical",False) for r in rows),
        "actual_original_abstain_count":sum(r["status"]!="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE" for r in rows),
        "same_fixed_algorithm_previously_executed_on_earlier_unopened_12":True,
        "full_safety_only_if_both_Z3_and_cvc5_inductive_original_3VC":True,
        "no_cross_program_learned_weight_transfer":True,
        "equal_data_equal_math_authority_classical":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "new_originals":rows}
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    report=run(Path(a.root),json.loads(Path(a.freeze).read_text()))
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for k in ("source_first_original_SHA_verified_count","actual_PCA_model_fit_source_count","post_only_full_source_3VC","simple_nolearn_plus_post_full_source_3VC","trained_PCA_plus_post_full_source_3VC","exact_classical_plus_post_full_source_3VC","trained_additional_vs_simple_nolearn","trained_additional_vs_exact_classical","actual_original_abstain_count"):
        print("SECOND_SOURCE_FIRST_Q3_TRAINED_REPLICATION",k,report[k])
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
