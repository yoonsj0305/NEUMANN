"""All first original 20 previously frozen source tasks, no-neural gate.

Model invocation eliminated ONLY after original source safety or unsafety
is independently proved. A classical Direct comparator is allowed exactly
the same algorithms; no neural novelty, SOTA, or global Q3/Q4 claims.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from research.evidence.q3_functional_ablation_20261021.oraclefree_published_post_vs_real_invariant_20 import (
    load_four_freezes
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,original_syguS,native_pdr,verified_3vc
)
from research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc import (
    bounded_original_bad_path
)

COHORT=(
 "research/evidence/q3_affine_unopened_transfer_20261021/ORIGINAL_FOUR_PRESOURCE_FREEZE.json",
 "research/evidence/q3_other_origin_four_20261021/FROZEN_BEFORE_FIRST_OPEN.json",
 "research/evidence/q4_prospective_six_20261021/FROZEN_BEFORE_FIRST_SOURCE_OPEN.json",
 "research/evidence/q34_safety_triage_six_20261021/PRE_SOURCE_FROZEN_ORIGINALS.json"
)
CONTRACT_SHA_COMMIT="3172c4952adf8aa80fb862ae2bbf322800426183"

def no_neural_policy(root,entry):
    start=time.perf_counter_ns()
    row={"source":entry["path"],"expected_git_blob":entry["git_blob"],
         "classification":"UNKNOWN","route":"ABSTAIN",
         "neural_forwards":0,"neural_training_updates":0,
         "actual_verified_original_task":False,
         "attempts":[]}
    try:
        raw,src,native,proof=prepare(root,entry)
        row["source_original_pre_trans_post_sha_verified"]=True
        row["source_authenticity_semantic_parity"]=proof
        gate_start=time.perf_counter_ns()

        # The exact original safety property as an invariant is the cheapest
        # structural candidate. It must pass the unchanged source 3VC.
        post_ok,post_receipt=verified_3vc(src,native,native["post"])
        row["attempts"].append({
            "method":"direct_published_Post_candidate",
            "dual_original_3VC":post_receipt,"admitted":post_ok,
            "route_wall_ms":(time.perf_counter_ns()-gate_start)/1e6
        })
        if post_ok:
            row["classification"]="SAFE"
            row["route"]="NO_DISCOVERY_POST_ALONE"
            row["actual_verified_original_task"]=True
        if not row["actual_verified_original_task"]:
            t=time.perf_counter_ns()
            trace=bounded_original_bad_path(src,native)
            row["attempts"].append({"method":"generic_grounded_real_BMC_0_3",
                                    "receipt":trace,
                                    "admitted":trace["true_bounded_original_safety_refuted"],
                                    "route_wall_ms":(time.perf_counter_ns()-t)/1e6})
            if trace["true_bounded_original_safety_refuted"]:
                row["classification"]="UNSAFE"
                row["route"]="ACTUAL_ORIGINAL_REACHABLE_UNSAFE"
                row["actual_verified_original_task"]=True
        if not row["actual_verified_original_task"]:
            t=time.perf_counter_ns()
            syn=original_syguS(raw,src,native,0.75)
            row["attempts"].append({"method":"original_SyGuS_750ms",
                                    "receipt":syn,"admitted":syn["certified"],
                                    "route_wall_ms":(time.perf_counter_ns()-t)/1e6})
            if syn["certified"]:
                row["classification"]="SAFE"
                row["route"]="FAST_ORIGINAL_SYGUS_DUAL3VC"
                row["actual_verified_original_task"]=True
        if not row["actual_verified_original_task"]:
            t=time.perf_counter_ns()
            pdr=native_pdr(src,native)
            row["attempts"].append({"method":"original_PDR_source_inductive",
                                    "receipt":pdr,"admitted":pdr["certified"],
                                    "route_wall_ms":(time.perf_counter_ns()-t)/1e6})
            if pdr["certified"]:
                row["classification"]="SAFE"
                row["route"]="FULL_ORIGINAL_SPACER_DUAL3VC"
                row["actual_verified_original_task"]=True
        row["complete_policy_original_source_wall_ms"]=(time.perf_counter_ns()-start)/1e6
        # A genuine strong DIRECT comparator gets the identical native source,
        # identical SPACER solver, identical independent proof authority, and
        # no source-specific helper labels.
        t=time.perf_counter_ns()
        direct=native_pdr(src,native)
        row["direct_unmodified_PDR_original"]={
            "certified":direct["certified"],
            "receipt":direct,
            "end_to_end_direct_executor_wall_ms":(time.perf_counter_ns()-t)/1e6
        }
        row["both_policy_and_direct_certified_safe"]=direct["certified"] and row["classification"]=="SAFE"
        row["paired_Direct_PDR_over_policy_wall_ratio_when_same_SAFE_capability"]=(
            row["direct_unmodified_PDR_original"]["end_to_end_direct_executor_wall_ms"] /
            row["complete_policy_original_source_wall_ms"]
            if row["both_policy_and_direct_certified_safe"] else None
        )
    except Exception as ex:
        row["error"]=type(ex).__name__+":"+str(ex)[:350]
        row["route"]="ABSTAIN_ORIGINAL_SOURCE_OR_SOLVER_EXCEPTION"
    row["full_study_case_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("NEUMANN_Q3_ZERO_NEURAL_GATE",row["source"],row["classification"],
          row["route"],"DIRECT_PDR",row.get("direct_unmodified_PDR_original",{}).get("certified"),
          "ERROR",row.get("error"),flush=True)
    return row

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",type=Path,default=Path("."))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    first=load_four_freezes(args.repo,list(COHORT))
    results=[no_neural_policy(args.root,t) for t in first]
    routes={}
    for r in results:routes[r["route"]]=routes.get(r["route"],0)+1
    counts={k:sum(q["classification"]==k and q["actual_verified_original_task"]
                  for q in results) for k in ("SAFE","UNSAFE","UNKNOWN")}
    direct=sum(q.get("direct_unmodified_PDR_original",{}).get("certified",False)
               for q in results)
    same=[q["paired_Direct_PDR_over_policy_wall_ratio_when_same_SAFE_capability"]
          for q in results if q.get("paired_Direct_PDR_over_policy_wall_ratio_when_same_SAFE_capability") is not None]
    out={
        "schema":"neumann.q3q4.actual_source_20_no_neural_sufficient_compute_routing.v1",
        "already_opened_20_origins_not_unseen":True,
        "preregistered_protocol_commit":CONTRACT_SHA_COMMIT,
        "all_actual_source_rows_retained":len(results)==20,
        "true_original_sha_parity_verified_count":sum(q["source_original_pre_trans_post_sha_verified"] for q in results if "source_original_pre_trans_post_sha_verified" in q),
        "scope_exactly_20_unmodified_originals":len({q["source"] for q in results})==20,
        "neural_calls":0,"training_updates":0,"paid_api_calls":0,
        "no_neural_full_source_SAFE":counts["SAFE"],
        "no_neural_full_source_UNSAFE":counts["UNSAFE"],
        "no_neural_original_UNKNOWN_or_exception_count":20-counts["SAFE"]-counts["UNSAFE"],
        "origins_source_certified_disposition_count":counts["SAFE"]+counts["UNSAFE"],
        "matched_direct_original_PDR_independent_3VC_certified_count":direct,
        "original_source_structural_route_counts":routes,
        "same_verified_safety_paired_direct_pdr_over_policy_latency":same,
        "both_success_paired_count":len(same),
        "NO_strongest_direct_portfolio_cost_advantage_claim":True,
        "FULL_Q3_LEARNED_STRUCTURE":"NOT_DEMONSTRATED",
        "Q3_NO_ORACLE_CLASSICAL_STRUCTURE_DISCOVERY":"BOUNDED_MECHANISM_ONLY",
        "GLOBAL_Q3":"OPEN","GLOBAL_Q4":"OPEN","GLOBAL_Q5":"OPEN",
        "results":results,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("NO_NEURAL_ACTUAL_20_SOURCE_CLASSIFICATION",
          counts["SAFE"],"SAFE",counts["UNSAFE"],"UNSAFE",
          out["no_neural_original_UNKNOWN_or_exception_count"],"UNKNOWN")
    print("Q3_NO_NEURAL_REAL_ORIGINAL_ROUTE_COUNTS",routes)
    print("MATCHED_DIRECT_PDR_SAFETY_COVERAGE",direct,"/20")
    print("SAME_CERTIFIED_PAIRED_COST_RATIO",same)
    print("Q3_Q4_GLOBAL_OPEN",out["GLOBAL_Q3"],out["GLOBAL_Q4"])
if __name__=="__main__":
    main()
