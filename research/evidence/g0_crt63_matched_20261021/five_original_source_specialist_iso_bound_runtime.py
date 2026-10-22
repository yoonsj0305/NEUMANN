"""Same-CPU matched specialist-classical mod9 vs exact CRT63 for five
opened authentic QF_NIA original sources, with radius=50000 on each arm.
Posthoc after mod63 results already known. Old mod9 code frozen in PR344,
new CRT63 code frozen in PR345. No new SAT proof count on replay.
"""
from __future__ import annotations
import argparse,json,time,statistics
from pathlib import Path

from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
 SOURCE_COMMIT,structural_source,independent_original_grounded_certificate,exact_search
)
from research.evidence.g0_cubic_crt63_20261021.real_official_five_unknown_crt63_r50000 import (
 crt63_numeric_exact_search
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
 git_blob_sha1,sha256
)
RADIUS=50000
CASE_NAMES=("STC_0291.smt2","STC_0588.smt2","STC_0609.smt2","STC_0786.smt2","STC_0880.smt2")
CONTRACT_SHA_COMMIT="a5c00594d6e13a9072e9663deaad6aad17d9f2aa"

def one_arm(raw,source,method):
    start=time.perf_counter_ns()
    row={"method":method,"source":source,
         "original_numeric_satisfiability_if_no_witness":"UNKNOWN_NOT_UNSAT",
         "original_source_independent_SAT_certificate":False}
    try:
        target,names,original_solver=structural_source(raw)
        if method=="mod9":
            r=exact_search(target,radius=RADIUS)
            cand=r["actual_numeric_witness"]
            row["actual_numeric_work_pair_comparisons"]=r["candidate_pair_comparisons_executed"]
            row["actual_numeric_wall_ms"]=r["search_wall_ms"]
        elif method=="CRT63":
            r=crt63_numeric_exact_search(target,RADIUS)
            cand=r["actual_exact_integer_witness"]
            row["actual_numeric_work_pair_comparisons"]=r["actual_eligible_source_pairs_probed_before_witness_or_exhaustion"]
            row["actual_numeric_wall_ms"]=r["numeric_search_wall_ms"]
            row["exact_candidate_pair_universe"]=r["analytic_exact_bounded_search_space_count"]
        else:
            raise RuntimeError("UNREGISTERED_METHOD")
        row["true_original_target"]=target
        row["exact_true_numeric_witness"]=cand
        row["actual_numeric_exhaustion_or_witness"] = "SAT_WITNESS" if cand else "NO_WITNESS_WITHIN_FIXED_BOUND"
        if cand:
            cert=independent_original_grounded_certificate(
                raw.decode("utf-8"),names,cand,original_solver,"SAT")
            row["source_original_SMT2_independent_Z3_cvc5"]=cert
            row["original_source_independent_SAT_certificate"]=cert["independent_dual_result"]
            row["status"]="ORIGINAL_SOURCE_SAT_DUAL" if cert["independent_dual_result"] else "UNVERIFIED_CANDIDATE"
        else:
            row["status"]="EXACT_BOUNDED_SEARCH_MISS_UNBOUNDED_UNKNOWN"
    except Exception as e:
        row["status"]="ABSTAIN_EXCEPTION"
        row["error"]=type(e).__name__+":"+str(e)[:320]
    row["complete_original_parsing_numeric_and_true_source_certificate_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return row

def per_original(root,item,index):
    t=time.perf_counter_ns()
    rec={"source":item["path"],"true_source_git_blob":item["sha1_git_blob"],"status":"ABSTAIN"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("ORIGINAL_SHA_OR_BYTES_CHANGED")
        rec["authenticated_true_original_SHA256"]=sha256(raw)
        # Precommitted order alternates by file ordinal only to reduce source-order bias.
        arm_order=("mod9","CRT63") if index%2==0 else ("CRT63","mod9")
        rec["arm_order"]=list(arm_order)
        for arm in arm_order:
            rec[arm]=one_arm(raw,item["path"],arm)
        old,new=rec["mod9"],rec["CRT63"]
        all_recognized=all(r["status"] in (
            "ORIGINAL_SOURCE_SAT_DUAL","EXACT_BOUNDED_SEARCH_MISS_UNBOUNDED_UNKNOWN"
        ) for r in (old,new))
        same_status=old["status"]==new["status"]
        rec["original_source_same_certified_bounded_disposition"]=all_recognized and same_status
        rec["status"]="SCOPED_ORIGINAL_BOUNDED_ISO_CAPABILITY" if rec["original_source_same_certified_bounded_disposition"] else "ABSTAIN_MISMATCH_OR_FAILED_SOURCE"
        if rec["original_source_same_certified_bounded_disposition"]:
            rec["same_CPU_mod9_over_CRT63_complete_wall_ratio"]=(
                old["complete_original_parsing_numeric_and_true_source_certificate_wall_ms"]/
                new["complete_original_parsing_numeric_and_true_source_certificate_wall_ms"])
        else:
            rec["same_CPU_mod9_over_CRT63_complete_wall_ratio"]=None
        print("G0_MATCHED_SPECIALIST_ORIGINAL",rec["source"],
              "STATUS",rec["status"],
              "MOD9",old["status"],round(old["complete_original_parsing_numeric_and_true_source_certificate_wall_ms"],3),
              "CRT63",new["status"],round(new["complete_original_parsing_numeric_and_true_source_certificate_wall_ms"],3),
              "SPEED_RATIO",rec["same_CPU_mod9_over_CRT63_complete_wall_ratio"],
              flush=True)
    except Exception as e:
        rec["error"]=type(e).__name__+":"+str(e)[:380]
        rec["status"]="ABSTAIN_SOURCE_FILE_ERROR"
    rec["total_study_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    return rec

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,required=True)
    a.add_argument("--freeze",type=Path,required=True)
    a.add_argument("--contract",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    opts=a.parse_args()
    c=json.loads(opts.contract.read_text())
    meta=json.loads(opts.freeze.read_text())
    if c["schema"]!="neumann.g0.posthoc_5_original_iso_capability_mod9_vs_crt63_radius50k.v1" or c["numeric_radius"]!=RADIUS:
        raise RuntimeError("FROZEN_MATCHED_COMPARISON_PROTOCOL_CHANGED")
    if len(meta["first_transfer_cohort"])!=7 or meta["source"].split("@")[-1]!=SOURCE_COMMIT:
        raise RuntimeError("HISTORIC_FIRST_ORIGINAL_COHORT_CHANGED")
    targets={q["path"].split("/")[-1]:q for q in meta["first_transfer_cohort"]}
    if not all(k in targets for k in CASE_NAMES):raise RuntimeError("PREVIOUS_UNKNOWN_ORIGINALS_CHANGED")
    cases=[per_original(opts.root,targets[name],i) for i,name in enumerate(CASE_NAMES)]
    equal=all(x["status"]=="SCOPED_ORIGINAL_BOUNDED_ISO_CAPABILITY" for x in cases)
    old=sum(x.get("mod9",{}).get("complete_original_parsing_numeric_and_true_source_certificate_wall_ms",0) for x in cases)
    new=sum(x.get("CRT63",{}).get("complete_original_parsing_numeric_and_true_source_certificate_wall_ms",0) for x in cases)
    report={
      "schema":"neumann.g0.stronger_classical_specialist_matched_5_originals_posthoc.v1",
      "freeze_commit_before_matched_cost":"a5c00594d6e13a9072e9663deaad6aad17d9f2aa",
      "this_was_after_original_STC_results_opened_not_blind":True,
      "all_five_real_original_rows_retained":len(cases)==5,
      "same_numeric_bound_and_dual_source_checker":True,
      "both_methods_identical_bounded_witness_or_miss_all_five":equal,
      "base_mod9_original_total_full_arm_wall_ms":old,
      "new_CRT63_original_total_full_arm_wall_ms":new,
      "at_equal_complete_bounded_work_scope_mod9_over_CRT63_aggregate":old/new if equal and new else None,
      "at_equal_scope_CRT63_entire_five_faster":equal and new<old,
      "at_equal_scope_CRT63_entire_five_10x_faster":equal and new*10<=old,
      "new_source_authentication_count":sum(bool(x.get("authenticated_true_original_SHA256")) for x in cases),
      "source_new_SAT_not_counted_again":True,
      "no_claim_of_original_unbounded_UNSAT":True,
      "strongest_classical_specialist_allowed_CRT63_exactly":True,
      "not_new_neural_or_pareto_frontier_advantage":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "posthoc_source_rows":cases,
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("ORIGINAL_G0_FIVE_ISO_BOUNDED_CAPABILITY",equal,"/5")
    print("G0_FIVE_SPECIALIST_MOD9_FULL_WALL_MS",old)
    print("G0_FIVE_SPECIALIST_CRT63_FULL_WALL_MS",new)
    print("G0_FIVE_MOD9_OVER_CRT63_MATCHED_WALL_RATIO",report["at_equal_complete_bounded_work_scope_mod9_over_CRT63_aggregate"])
    print("G0_FIVE_CRT63_FAST_SCOPED",report["at_equal_scope_CRT63_entire_five_faster"])
    print("GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
