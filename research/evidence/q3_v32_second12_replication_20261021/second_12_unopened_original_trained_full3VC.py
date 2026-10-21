"""Second disjoint source-blind 12 genuine original programs; unchanged PR402 trained PCA+Post."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.evidence.q3_v32_posthoc_full_original_20261021.real_trained_PCA_plus_source_Post_3VC import one

LOCK="579f423cb09f04d64524c2e84f92b7d333f8c851"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def run(root,f):
    if f["schema"]!="neumann.q3.v32_second12_first_body_unopened_replication_of_same_frozen_learner.v1":
        raise RuntimeError("FROZEN_SOURCE_CONTRACT_CHANGED")
    if f["upstream"].split("@")[-1]!=REV or not f["new_source_original_BODIES_NOT_OPENED_BEFORE_SHA_commit"]:
        raise RuntimeError("NOT_FIRST_GENUINE_ORIGINAL_SOURCE")
    items=f["cases"]
    if len(items)!=12 or len({x["git_blob"] for x in items})!=12:
        raise RuntimeError("ORIGINAL_SOURCE_DUPLICATE")
    for item in items:
        b=(root/item["path"]).read_bytes()
        if len(b)!=item["bytes"] or sha(b)!=item["git_blob"]:
            raise RuntimeError("FIRST_SOURCE_SHA_OR_BYTE_MISMATCH:"+item["path"])
    results=[]
    for item in items:
        outcome=one(root,item)
        outcome["genuine_original_SHA_authenticated_after_prebody_lock"]=True
        results.append(outcome)
    def count(k):
        return sum(r.get(k,{}).get("fully_verified_complete_original_3VC",False) for r in results)
    return {
        "schema":"neumann.q3.v32_SECOND_ORIGINAL_UNOPENED_twelve_replicated_learned_full_3VC.v1",
        "pre_SOURCE_body_sha_registration_commit":LOCK,
        "same_full_method_proven_executable_before_new_source_first_open":True,
        "new_original_source_sha_preopen_authenticated_count":12,
        "new_original_model_fit_execution_count":sum(r.get("actual_CPU_fitted_model",{}).get("real_CPU_PCA_model_fits",0)>0 for r in results),
        "Post_ONLY_actual_original_full3VC":count("POST_only_already_exact_original_dual"),
        "no_learn_basic_plus_Post_actual_original_full3VC":count("simple_NOLEARN_plus_original_POST"),
        "TRAINED_PCA_plus_Post_actual_original_full3VC":count("TRAINED_PCA_plus_original_POST"),
        "exact_classical_no_learn_plus_Post_original_full3VC":count("EXACT_CLASSICAL_plus_original_POST"),
        "genuinely_new_orig_success_learned_where_basic_fails":sum(r.get("trained_full_3VC_success_not_no_learn",False) for r in results),
        "genuinely_new_orig_success_learned_where_exact_classical_fails":sum(r.get("trained_full_3VC_success_not_exact_classical",False) for r in results),
        "failed_or_abstained_original_count":sum(r["status"]!="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE" for r in results),
        "source_specific_numeric_fit_of_FIXED_algorithm_not_pretrained_weight_transfer":True,
        "matched_classical_has_equal_data_and_math_proof_tools":True,
        "same_upstream_author_independence_unproven":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "true_originals":results}
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    data=run(Path(a.root),json.loads(Path(a.freeze).read_text()))
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
    for k in ("new_original_source_sha_preopen_authenticated_count","new_original_model_fit_execution_count","Post_ONLY_actual_original_full3VC",
              "no_learn_basic_plus_Post_actual_original_full3VC","TRAINED_PCA_plus_Post_actual_original_full3VC",
              "exact_classical_no_learn_plus_Post_original_full3VC","genuinely_new_orig_success_learned_where_basic_fails",
              "genuinely_new_orig_success_learned_where_exact_classical_fails","failed_or_abstained_original_count"):
        print("SECOND_TRUE_UNOPENED_Q3_LEARNED_FULL_ORIGINAL",k,data[k])
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
