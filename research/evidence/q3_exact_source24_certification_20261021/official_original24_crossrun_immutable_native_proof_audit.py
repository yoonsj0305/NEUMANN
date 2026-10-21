"""Cross-run independent immutable receipt audit.

Prior posthoc 12 with a single integrated zero-neural original safety proof;
second source-body-PREREGISTERED 12 with UNCHANGED algorithm. The original
JSON was produced by separate official CI runs and pinned by SHA256; verify
no duplicate original blobs, every historical Git SHA, and ALL trusted 3VC
original independent Z3 AND cvc5 receipts. Check real dual SAT original
UNSAFE witness, never relabel it as a missing SAFE proof.

This does NOT rerun source solvers or add a new Q3 model/theorem.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
SHA={
    "development":"9ed24123f75253df4dc073bb5af24f7abbe88454b3376671d30a44890f7322c6",
    "blind":"dd1ef91bcf1aecf2b2a04431ff1bc2d7df6fba94f42e9f68edefeb65d4fe8541"}
ORIGINAL_RUNS={"development":39601391011,"blind":39602090265}
def must(yes,detail):
    if not yes:raise AssertionError(detail)
def load(path,label):
    b=Path(path).read_bytes()
    must(hashlib.sha256(b).hexdigest()==SHA[label],"OFFICIAL_ORIGINAL_RAW_SHA256_CHANGED:"+label)
    return json.loads(b)
def certify_case(row,registered):
    path=row["source"];old_sha=row["original_git_blob"]
    must(path in registered and old_sha==registered[path],
         "ORIGINAL_GIT_SHA_NOT_REG_BEFORE_CONTENT:"+path)
    must(len(old_sha)==40,"GIT_BLOB_SHA_INVALID")
    parity=row["source_original_PreTransPost_independent_parity"]
    must(set(parity)=={"pre","trans","post"},"ACTUAL_NATIVE_SOURCE_PARITY_MISSING")
    must(all(x["dual_pass"] for x in parity.values()),"SOURCE_GENUINE_AST_CHANGED")
    if row["certified_SAFE"]:
        must(row["status"].startswith("PASS_ORIGINAL_FULL_3VC_"),"FAKE_SAFE_STATE")
        name=row["winner"]
        if name=="tautology_delete":
            proof=row["certified_trivial_True_original_3VC"]
        elif name=="exact_no_fit_OR_with_min_info":
            proof=row["original_dual_3VC_nofit_OR"]
        elif name=="generic_affine_Houdini":
            proof=row["original_dual_3VC_Houdini_conjunction"]
        elif name=="original_cvc5_SyGuS":
            p=row["strong_original_cvc5_SyGuS_native_source"]
            must(p["certified"],"UNVERIFIED_SYGUS")
            proof=p["original_native_Z3_cvc5_3VC"]
        elif name=="original_Z3_SPACER":
            p=row["strong_original_Z3_SPACER_native_source"]
            must(p["certified"],"UNVERIFIED_SPACER")
            matches=[m for m in p["original_independently_certified_candidates"] if m["certified"]]
            must(matches,"SPACER_NO_CERTIFIED_FULL_SOURCE")
            proof=matches[0]["original_full_dual_3VC"]
        else:raise AssertionError("NO_KNOWN_PROOF_ROUTE:"+str(name))
        must(set(proof)=={"init","consecution","goal"},"NOT_ALL_3_ORIGINAL_VCS")
        must(all(x["dual_pass"] for x in proof.values()),"UNSUPPORTED_NATIVE_DUAL_3VC")
        label="SAFE"
    elif row["status"]=="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE":
        w=row["original_UNSAFE_witness"]
        must(w["dual_pass"] is True,"UNSUPPORTED_ORIGINAL_UNSAFE_SAT")
        must("winner" not in row,"UNSAFE_FALSE_SAFE_ROUTE")
        label="UNSAFE"
    else:
        must(row.get("winner") is None,"UNSUPPORTED_UNKNOWN_WINNER")
        label="UNKNOWN"
    must(row["neural_forward_count"]==0 and row["machine_learning_fit_count"]==0,
         "MODEL_COMPUTATION_HIDDEN_IN_ORIGINAL_RUN")
    return {"source":path,"original_git_blob":old_sha,"verdict":label,
            "proof_route":row.get("winner"),
            "actual_original_whole_work_ms":row["total_original_source_parse_minimum_search_proof_wall_ms"],
            "independent_original_Z3_cvc5_verdict_proven":label!="UNKNOWN"}
def main():
    p=argparse.ArgumentParser()
    for name in ("development","blind","freeze_dev","freeze_blind","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    d=load(a.development,"development");b=load(a.blind,"blind")
    must(d["schema"]=="neumann.q3.proof_first_integrated_original12_zero_neural_exact_OR_Houdini_SyGuS_PDR.v2",
         "PR424_ORIGINAL_SCHEMA_CHANGED")
    must(b["schema"]=="neumann.q3.first_body_blind12_unchanged_classical_PROOF_FIRST_full_native_3VC.v1",
         "PR427_FIRST_BODY_ORIGINAL_SCHEMA_CHANGED")
    must(b["before_any_original_body_Git_metadata_commit"]=="916c2c3e3c1f08c5ef804ca3179231f60d46dcff",
         "FIRST_SOURCE_PREOPEN_COMMIT_MISMATCH")
    must(b["method_unmodified_since_pr424_success_original12"] is True,
         "CHANGED_FIRST_SOURCE_TESTED_ALGORITHM")
    meta_d=json.loads(Path(a.freeze_dev).read_text())
    meta_b=json.loads(Path(a.freeze_blind).read_text())
    must(meta_b["original_source_BODIES_NOT_VIEWED_before_metadata_commit"] is True,
         "NO_SOURCE_FIRST_SHA_LOCK")
    m1={x["path"]:x["git_blob"] for x in meta_d["cases"]}
    m2={x["path"]:x["git_blob"] for x in meta_b["cases"]}
    must(len(m1)==12 and len(m2)==12,"NOT_TWO_TWELVE_SIZED_SOURCE_COLLECTIONS")
    must(not(set(m1)&set(m2)) and not(set(m1.values())&set(m2.values())),
         "SOURCE_ORIGINALS_DUPLICATE_ACROSS_COHORTS")
    rows_d=d["per_original"]
    rows_b=b["all_first_source_originals_and_native_3VC_receipts"]
    must(len(rows_d)==len(rows_b)==12,"MISSING_ORIGINAL_ROW")
    audit_d=[certify_case(r,m1) for r in rows_d]
    audit_b=[certify_case(r,m2) for r in rows_b]
    def counts(rows):
        return {k:sum(x["verdict"]==k for x in rows) for k in ("SAFE","UNSAFE","UNKNOWN")}
    cd=counts(audit_d);cb=counts(audit_b)
    must(cd=={"SAFE":12,"UNSAFE":0,"UNKNOWN":0},"PR424_SOURCE_VERDICT_NOT_REPRODUCED")
    must(cb=={"SAFE":11,"UNSAFE":1,"UNKNOWN":0},"PR427_SOURCE_FIRST_VERDICT_CHANGED")
    must(d["fully_certified_original_safe_independent_Z3_cvc5"]==cd["SAFE"],
         "PR424_HEADER_NOT_SAME_AS_CERTS")
    must(b["first_blind_true_original_full_dual_3VC_safe"]==cb["SAFE"] and
         b["first_blind_true_original_unsafety_proven"]==cb["UNSAFE"],
         "PR427_HEADER_NOT_SAME_AS_CERTS")
    all_rows=audit_d+audit_b
    result={
       "schema":"neumann.q3.official_two_original_cohorts_24_source_native_dual_receipt_audit.v1",
       "official_action_runs":ORIGINAL_RUNS,
       "pinned_official_RAW_JSON_SHA256":SHA,
       "original_programs_24_all_git_sha_disjoint":24,
       "previously_opened_12_exact_native_verdicts":cd,
       "prospectively_source_unopened_12_exact_native_verdicts":cb,
       "both_cohorts_total_true_Z3_cvc5_SAFE":23,
       "both_cohorts_total_true_Z3_cvc5_UNSAFE":1,
       "both_cohorts_total_UNKNOWN":0,
       "all_programs_double_solver_original_3VC_or_unsafe_sat":True,
       "zero_neural_forwards_and_zero_fitted_models":True,
       "previous_cohort_original_all_work_ms_sum":d["whole_source_total_observed_wall_ms"],
       "source_blind_cohort_original_all_work_ms_sum":b["source_full_wall_ms_sum"],
       "sum_separate_original_CI_runs_wall_ms_no_causal_speed_claim":
           d["whole_source_total_observed_wall_ms"]+b["source_full_wall_ms_sum"],
       "same_code2inv_source_family_not_cross_author_generalization":True,
       "pre_source_body_metadata_frozen_for_second_cohort":True,
       "not_new_neural_structure_learning_or_frontier_10x":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
       "source_audit_ledger":all_rows}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for k in ("both_cohorts_total_true_Z3_cvc5_SAFE",
              "both_cohorts_total_true_Z3_cvc5_UNSAFE",
              "both_cohorts_total_UNKNOWN",
              "sum_separate_original_CI_runs_wall_ms_no_causal_speed_claim"):
        print("NEUMANN_AUTHENTIC_ORIGINAL24_INDEPENDENT_AUDIT",k,result[k],flush=True)
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
