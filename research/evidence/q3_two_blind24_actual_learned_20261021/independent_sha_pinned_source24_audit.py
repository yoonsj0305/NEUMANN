"""Strict read-only joint authoritative original24 learned-structure FULL safety auditor.
NO new solver/learning execution, NO retroactive result change, source Git SHA
and original output JSON byte identity are required before aggregation.
Never represent synthetic tests, manual source posthoc work, or conditional
external theorem as original first-blind learned safety.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
HASH={
 "first":"eb2c7079c2de039048471ac72390406e5f13c4181e15be9186dd12aefdc573d5",
 "second":"08f81bba91d94452e76d1b0dd0159bd219840c430362956ddc8d272d824f4b87"
}
SCHEMAS={
 "first":"neumann.q3.v32_FIRST_ORIGINAL_UNOPENED_twelve_actual_learned_full_3VC.v1",
 "second":"neumann.q3.v32_SECOND_ORIGINAL_UNOPENED_twelve_replicated_learned_full_3VC.v1"
}
METHODS={
 "post":"POST_only_already_exact_original_dual",
 "basic":"simple_NOLEARN_plus_original_POST",
 "trained":"TRAINED_PCA_plus_original_POST",
 "exact":"EXACT_CLASSICAL_plus_original_POST"
}
def require(x,reason):
    if not x:raise AssertionError(reason)
def verified_json(path,key):
    data=Path(path).read_bytes()
    require(hashlib.sha256(data).hexdigest()==HASH[key],"IMMUTABLE_OFFICIAL_ACTUAL_JSON_SHA_MISMATCH:"+key)
    j=json.loads(data)
    require(j["schema"]==SCHEMAS[key],"ORIGINAL_COHORT_SCHEMA_CHANGED")
    return j
def cohort(data,kind):
    values=data["true_originals"]
    require(len(values)==12 and data["new_original_source_sha_preopen_authenticated_count"]==12,"NOT_AUTHENTIC_TWELVE")
    require(data["same_full_method_proven_executable_before_new_source_first_open"],"SAME_MODEL_NOT_PREVIOUSLY_FROZEN")
    require(data["matched_classical_has_equal_data_and_math_proof_tools"],"CLASSICAL_COMPARATOR_UNFAIR")
    require(data["global_Q3"]==data["global_Q4"]==data["global_Q6"]=="OPEN","FALSE_GLOBAL_Q3_PASS")
    need_commit=("cebc8f5609c483fdd9c3d6e10d982511e1298ca1"
                 if kind=="first" else "579f423cb09f04d64524c2e84f92b7d333f8c851")
    require(data["pre_SOURCE_body_sha_registration_commit"]==need_commit,"PRE_BODY_SOURCE_SHA_LOCK_CHANGED")
    ids=set();paths=set();count={n:0 for n in METHODS};trained_notbasic=0;trained_notexact=0;abstained=0
    individual=[]
    for row in values:
        name=row["source"];sha=row["true_original_git_blob"]
        require(sha not in ids and name not in paths,"DUPLICATE_REAL_ORIGINAL")
        ids.add(sha);paths.add(name)
        require(row["genuine_original_SHA_authenticated_after_prebody_lock"],"FILE_NOT_PRESHA_AUTHENTICATED")
        status=row["status"]
        passed={}
        for key,field in METHODS.items():
            proof=row.get(field)
            ok=bool(proof and proof["fully_verified_complete_original_3VC"])
            if ok:
                for vc in ("init","consecution","goal"):
                    require(proof["independent_original_pre_trans_post_dual_proofs"][vc]["dual_pass"] is True,
                            "FORGED_OR_MISSING_INDEPENDENT_NATIVE_ORIGINAL_Z3_CVC5:"+field+":"+vc)
                count[key]+=1
            passed[key]=ok
        if status!="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE":
            abstained+=1
            require(not any(passed.values()),"ABSTAIN_WRONGLY_COUNTED_AS_PROOF")
        if passed["trained"] and not passed["basic"]:trained_notbasic+=1
        if passed["trained"] and not passed["exact"]:trained_notexact+=1
        require(row.get("trained_full_3VC_success_not_no_learn",False)==(passed["trained"] and not passed["basic"]),
                "INCONSISTENT_TRAINED_ABLATION")
        require(row.get("trained_full_3VC_success_not_exact_classical",False)==(passed["trained"] and not passed["exact"]),
                "INCONSISTENT_STRONG_CLASSICAL_RIGHTS")
        individual.append({"source":name,"git_blob":sha,"status":status,"proof_methods":passed})
    fieldmap={
        "post":"Post_ONLY_actual_original_full3VC",
        "basic":"no_learn_basic_plus_Post_actual_original_full3VC",
        "trained":"TRAINED_PCA_plus_Post_actual_original_full3VC",
        "exact":"exact_classical_no_learn_plus_Post_original_full3VC"
    }
    for key,field in fieldmap.items():
        require(count[key]==data[field],"SINGLE_COHORT_STORED_COUNT_NOT_MATCHED_CASES:"+field)
    require(trained_notbasic==data["genuinely_new_orig_success_learned_where_basic_fails"],"TRAINED_VS_BASIC_WRONG")
    require(trained_notexact==data["genuinely_new_orig_success_learned_where_exact_classical_fails"],"TRAINED_VS_EXACT_WRONG")
    require(abstained==data["failed_or_abstained_original_count"],"ABSTAIN_UNCHANGED_SCOPE")
    return {"cohort":kind,"proven":count,"extra_vs_basic":trained_notbasic,
            "extra_vs_exact":trained_notexact,"abstained":abstained,
            "actual_CPU_trained_sources":data["new_original_model_fit_execution_count"],
            "records":individual}
def audit(first,second):
    a=cohort(first,"first");b=cohort(second,"second")
    allrows=a["records"]+b["records"]
    require(len(allrows)==24 and len({r["git_blob"] for r in allrows})==24 and
            len({r["source"] for r in allrows})==24,"NOT_24_DISTINCT_GENUINE_ORIGINAL_SHA")
    sums={k:a["proven"][k]+b["proven"][k] for k in METHODS}
    require(sums=={"post":7,"basic":17,"trained":19,"exact":20},"FROZEN_UNEXPECTED_ORIGINAL_PROOF_COUNTS")
    require(a["extra_vs_basic"]+b["extra_vs_basic"]==2,"FALSE_BOUNDED_LEARNED_INCREMENT")
    require(a["extra_vs_exact"]+b["extra_vs_exact"]==0,"FALSE_UNIQUE_LEARNED_ADVANTAGE")
    return {
      "schema":"neumann.q3.24_two_source_blind_original_actual_trained_full_induction_cross_audited.v1",
      "first_prior_official_run":39587212632,
      "second_prior_official_run":39587707176,
      "unchanged_full_source_train_fit_algorithm_pre_committed_before_both_new_original_cohorts":True,
      "source_Git_sha_prebody_frozen_distinct_originals":24,
      "source_authentic_original_3VC_certified":sums,
      "actual_CPU_model_fitted_original_cases":a["actual_CPU_trained_sources"]+b["actual_CPU_trained_sources"],
      "originals_total_abstained":a["abstained"]+b["abstained"],
      "learned_extra_proven_vs_fixed_no_fit":a["extra_vs_basic"]+b["extra_vs_basic"],
      "learned_extra_proven_vs_equal_mathematics_exact_classical":0,
      "same_upstream_benchmark_authorship_independence_NOT_proven":True,
      "per_original_source_specific_CPU_fit_NOT_pretrained_weight_transfer":True,
      "not_measured_end_to_end_frontier_10x":True,
      "not_closed_Q1_through_Q7":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "cohorts":[a,b]}
def main():
    p=argparse.ArgumentParser()
    for k in ("first","second","out"):p.add_argument("--"+k,required=True)
    x=p.parse_args()
    q=audit(verified_json(x.first,"first"),verified_json(x.second,"second"))
    out=Path(x.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(q,sort_keys=True,indent=2)+"\n")
    print("TRUE_ORIGINAL_TWO_COHORTS",q["source_Git_sha_prebody_frozen_distinct_originals"])
    print("ACTUAL_TRAINED_LEARNED_FULL_ORIGINAL_Z3_CVC5",q["source_authentic_original_3VC_certified"]["trained"])
    print("ACTUAL_NO_LEARN_BASIC_FULL_ORIGINAL_Z3_CVC5",q["source_authentic_original_3VC_certified"]["basic"])
    print("ACTUAL_EXACT_CLASSICAL_FULL_ORIGINAL_Z3_CVC5",q["source_authentic_original_3VC_certified"]["exact"])
    print("ACTUAL_LEARNED_EXTRA_VS_BASIC",q["learned_extra_proven_vs_fixed_no_fit"])
    print("ACTUAL_LEARNED_EXTRA_VS_STRONG_EXACT",q["learned_extra_proven_vs_equal_mathematics_exact_classical"])
    print("GLOBAL_Q3_Q4_Q6",q["global_Q3"],q["global_Q4"],q["global_Q6"])
if __name__=="__main__":main()
