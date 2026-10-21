"""Read-only independent cross-cohort validation of first-source Q3 results.

No new proof, training, rerun, or claim of trained-model frontier superiority.
Verifies exact immutable official per-source ORIGINAL Z3+cvc5 proof receipts
from 2 FIRST source-body-blind SHA-selected cohorts; distinguishes the 2
bounded learned-only improvements over cheap no-fit from stronger classical
rational-nullspace (equal-authority) which outperforms the learner overall.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
SHA={
"first":"eb2c7079c2de039048471ac72390406e5f13c4181e15be9186dd12aefdc573d5",
"second":"f4b29de520497be3253dc1014b9aec6688569fd617c0ee70e95a1189540c63b5"}
KEYS={
"post":"POST_only_already_exact_original_dual",
"basic":"simple_NOLEARN_plus_original_POST",
"learned":"TRAINED_PCA_plus_original_POST",
"exact":"EXACT_CLASSICAL_plus_original_POST"}
SCHEMA={
"first":"neumann.q3.v32_FIRST_ORIGINAL_UNOPENED_twelve_actual_learned_full_3VC.v1",
"second":"neumann.q3.v32_SECOND_ORIGINAL_UNOPENED_twelve_replicated_learned_full_3VC.v1"}
def need(ok,tag):
    if not ok:raise AssertionError(tag)
def read_exact(filename,name):
    b=Path(filename).read_bytes()
    need(hashlib.sha256(b).hexdigest()==SHA[name],"OFFICIAL_FULL_JSON_DIGEST_CHANGED_"+name)
    return json.loads(b)
def status(row,k):
    obj=row.get(KEYS[k],{})
    need(isinstance(obj,dict),"PROOF_OBJECT_MISSING_"+k)
    b=obj.get("fully_verified_complete_original_3VC")
    need(type(b) is bool,"BOOLEAN_VERDICT_NOT_PRESENT_"+k)
    receipts=obj.get("independent_original_pre_trans_post_dual_proofs")
    if b:
        need(isinstance(receipts,dict) and set(receipts)=={"pre","trans","post"},
             "NOT_ORIGINAL_THREE_COMPLETE_VCS")
        for formula,d in receipts.items():
            need(d.get("dual_pass") is True,
                 "UNSUPPORTED_DUAL_SOLVER_CERTIFICATE_"+k+"_"+formula)
            need(isinstance(d.get("Z3"),str) and isinstance(d.get("cvc5"),str),
                 "MISSING_SOLVER_RESULT_"+k)
    return b
def check_one(blob,source_freeze,label,all_seen):
    rows=blob["true_originals"]
    need(blob["schema"]==SCHEMA[label],"WRONG_SAVED_REPORT_SCHEMA_"+label)
    need(len(rows)==12 and len(source_freeze["cases"])==12,"NOT_TWELVE_"+label)
    need(blob["new_original_source_sha_preopen_authenticated_count"]==12,"SOURCE_IDENTITY_COUNT_"+label)
    need(blob["same_full_method_proven_executable_before_new_source_first_open"] is True,
         "NOT_FROZEN_BEFORE_SOURCE_"+label)
    need(blob["matched_classical_has_equal_data_and_math_proof_tools"] is True,
         "WEAK_CLASSICAL_BASELINE_"+label)
    need(all(blob["global_"+k]=="OPEN" for k in ("Q3","Q4","Q6")),"FAKE_GLOBAL_CLOSE_"+label)
    frozen={z["path"]:z["git_blob"] for z in source_freeze["cases"]}
    need(len(frozen)==12,"DUPLICATE_SOURCE_IN_METADATA_"+label)
    ledger=[]; totals={k:0 for k in KEYS}
    for row in rows:
        path=row.get("source");sha=row.get("true_original_git_blob")
        need(path in frozen and sha==frozen[path],"SOURCE_SHA_NOT_LOCKED_BEFORE_BODY_"+str(path))
        need(sha not in all_seen,"CROSS_COHORT_DUPLICATE_GIT_BLOB")
        all_seen.add(sha)
        actual=row.get("status")
        success={}
        if actual=="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE":
            need("actual_CPU_fitted_model" in row and
                 row.get("actual_original_pre_trans_post_native_parity"),
                 "ORIGINAL_PROGRAM_NATIVE_PARITY_MISSING")
            for k in KEYS:
                success[k]=status(row,k)
                totals[k]+=int(success[k])
            need(row.get("trained_full_3VC_success_not_no_learn") is (
                success["learned"] and not success["basic"]),"MISREPORTED_LEARNING_BASIC_GAIN")
            need(row.get("trained_full_3VC_success_not_exact_classical") is (
                success["learned"] and not success["exact"]),"MISREPORTED_LEARNING_EXACT_GAIN")
        else:
            need(actual=="ABSTAIN_REAL_SOURCE_OR_PROOF","UNEXPECTED_STATE_"+str(actual))
            success={k:False for k in KEYS}
        delta=[]
        if success["learned"] and not success["basic"]:
            proof=row[KEYS["learned"]]
            base=set(x["smt"] for x in row[KEYS["basic"]].get("retained_candidate_formulas",[]))
            delta=[{"smt":x["smt"],"origins":x["origins"]}
                   for x in proof.get("retained_candidate_formulas",[])
                   if "FITTED_PCA" in x["origins"] and x["smt"] not in base]
            need(len(delta)>0,"TRAINED_SUCCESS_WITHOUT_ANY_LEARNED_WITNESS")
        ledger.append({"source":path,"original_sha":sha,"family":label,
                       "status":actual,"proofs":success,"fitted_PCA_only_witness":delta,
                       "full_original_runtime_observed_ms":row.get(
                           "full_original_source_preflight_fit_propose_and_3VC_wall_ms")})
    for k in KEYS:
        bfield={"post":"Post_ONLY_actual_original_full3VC",
                "basic":"no_learn_basic_plus_Post_actual_original_full3VC",
                "learned":"TRAINED_PCA_plus_Post_actual_original_full3VC",
                "exact":"exact_classical_no_learn_plus_Post_original_full3VC"}[k]
        need(blob[bfield]==totals[k],"HEADER_DOES_NOT_MATCH_ORIGINAL_RECEIPTS_"+k)
    need(blob["genuinely_new_orig_success_learned_where_basic_fails"]==
         sum(x["proofs"]["learned"] and not x["proofs"]["basic"] for x in ledger),
         "FAKE_NEW_LEARNED_INCREMENT")
    need(blob["genuinely_new_orig_success_learned_where_exact_classical_fails"]==
         sum(x["proofs"]["learned"] and not x["proofs"]["exact"] for x in ledger),
         "FAKE_EXACT_CLASSICAL_BONUS")
    return ledger,totals
def run(first,second,freeze1,freeze2):
    need(first["pre_SOURCE_body_sha_registration_commit"]==
         "cebc8f5609c483fdd9c3d6e10d982511e1298ca1","FIRST_METADATA_COMMIT_CHANGED")
    need(second["pre_SOURCE_body_sha_registration_commit"]==
         "579f423cb09f04d64524c2e84f92b7d333f8c851","SECOND_METADATA_COMMIT_CHANGED")
    need(freeze1["source_bodies_UNOPENED_at_this_registration"] is True and
         freeze2["new_source_original_BODIES_NOT_OPENED_BEFORE_SHA_commit"] is True,
         "NOT_PRE_SOURCE_BODY_REGISTERED")
    seen=set()
    a,ta=check_one(first,freeze1,"first",seen)
    b,tb=check_one(second,freeze2,"second",seen)
    rows=a+b
    need(len(rows)==24 and len(seen)==24,"NOT_TWENTYFOUR_DISJOINT_ORIGINAL_BLOBS")
    totals={k:ta[k]+tb[k] for k in KEYS}
    wins=[r for r in rows if r["proofs"]["learned"] and not r["proofs"]["basic"]]
    reverses=[r for r in rows if r["proofs"]["basic"] and not r["proofs"]["learned"]]
    exact_wins=[r for r in rows if r["proofs"]["exact"] and not r["proofs"]["learned"]]
    learned_exact_wins=[r for r in rows if r["proofs"]["learned"] and not r["proofs"]["exact"]]
    # Exact paired-sign diagnostic only, no statistical generalization claim.
    n=len(wins)+len(reverses)
    def bintail(n,k):
        return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else None
    result={
      "schema":"neumann.q3.24_immutable_originals_learned_causal_witness_cross_run_audit.v1",
      "official_run_ids":[39587212632,39587851842],
      "official_full_report_SHA256":SHA,
      "first_original_source_count":12,"second_original_source_count":12,
      "disjoint_true_original_source_count":len(seen),
      "full_source_inductive_certificate_counts":totals,
      "learned_solved_baseline_failed_count":len(wins),
      "baseline_solved_learned_failed_count":len(reverses),
      "strong_exact_classical_only_solved_count":len(exact_wins),
      "learned_only_vs_strong_classical_solved_count":len(learned_exact_wins),
      "paired_one_sided_sign_diagnostic_not_generalizable":bintail(n,len(wins)),
      "bounded_PCA_witnesses":[{"source":r["source"],"original_sha":r["original_sha"],
          "retained_trained_only_new_rels":r["fitted_PCA_only_witness"]}
          for r in wins],
      "source_metadata_committed_before_source_first_open":True,
      "model_fitted_separately_for_every_source_no_weight_transfer":True,
      "exact_linear_algebra_equal_rights_and_can_match_exceed_PCA":True,
      "24_source_freshness_same_upstream_not_independent_authors":True,
      "not_machine_learning_unique_new_theorem":True,
      "not_any_model_quality_or_10x_superiority_claim":True,
      "all_global_Q1_to_Q7":"OPEN",
      "ledger":rows
    }
    need(totals=={"post":7,"basic":17,"learned":19,"exact":20},"HISTORICAL_CROSS_RUN_TOTAL_CHANGED")
    need(len(wins)==2 and len(reverses)==0 and len(exact_wins)==1 and len(learned_exact_wins)==0,
         "HISTORICAL_BOUNDED_CAUSAL_REPRODUCTION_CHANGED")
    return result
def main():
    p=argparse.ArgumentParser()
    for k in ("first","second","freeze1","freeze2","out"):p.add_argument("--"+k,required=True)
    args=p.parse_args()
    out=run(read_exact(args.first,"first"),read_exact(args.second,"second"),
            json.loads(Path(args.freeze1).read_text()),json.loads(Path(args.freeze2).read_text()))
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("SOURCE_FIRST_TWO_DISJOINT_ORIGINALS",out["disjoint_true_original_source_count"])
    print("COMPLETE_ORIGINAL_DUAL_PROOF_COUNTS",out["full_source_inductive_certificate_counts"])
    print("TRAINED_ONLY_VS_SIMPLE",out["learned_solved_baseline_failed_count"])
    print("CLASSICAL_ONLY_VS_TRAINED",out["strong_exact_classical_only_solved_count"])
    for w in out["bounded_PCA_witnesses"]:
        print("TRUE_ORIGINAL_TRAINED_EXTRA_SOURCE",w["source"],"RETAINED_TRAINED_PCA_TERMS",len(w["retained_trained_only_new_rels"]))
        for t in w["retained_trained_only_new_rels"][:5]:
            print("LEARNED_SOURCE_TYPED_AFFINE_RELATION",t["smt"][:250])
    print("GLOBAL_Q1_TO_Q7_OPEN")
if __name__=="__main__":main()
