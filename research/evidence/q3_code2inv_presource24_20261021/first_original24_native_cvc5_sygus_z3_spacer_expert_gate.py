"""First actual full original precommitted 24 Code2Inv/InvTrack expert headroom.

Prior git source blob identities frozen WITHOUT any original source body.
Run same-source authentic CVC5 native SyGuS, Z3 SPACER, cheap SyGuS and
independent original native Pre/Trans/Post Z3+cvc5 3VC certificates.
Important: failure of safety proof doesn't imply unsafe, nor that a
learned model could solve it. Only a typed source-valid task with a real
verified residual is eligible for a prospectively registered model gate.
NO model train nor hidden source gold here.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path

import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as classical

REV="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE_FREEZE_COMMIT="6a5792e196b2234358dca31ec9dd733f3ffed42d"

def evaluate(root,item):
    tic=time.perf_counter_ns()
    rec={"source":item["path"],"family":item["family"],
         "original_git_blob_expected":item["git_blob"],
         "authentic_true_source":False,"strong_classical_verified_SAFE":False,
         "status":"ABSTAIN"}
    try:
        raw,source,native,identity=classical.prepare(root,item)
        rec["original_source_provenance"]=identity
        rec["authentic_true_source"]=True
        rec["raw_original_sha256"]=hashlib.sha256(raw).hexdigest()
        rec["original_source_state_count"]=len(source["states"])
        rec["typed_native_Pre_Trans_Post_Z3_cvc5_dual_parity"]=True
        # All routes from the EXACT same native full original source; none
        # receive gold invariant, answer, or source-name-specific options.
        strong=classical.original_syguS(raw,source,native,3.0)
        pdr=classical.native_pdr(source,native)
        fast=classical.original_syguS(raw,source,native,1.2)
        rec["full_native_cvc5_SyGuS_3s"]=strong
        rec["full_native_Z3_SPACER_6s"]=pdr
        rec["fast_native_cvc5_SyGuS_1p2s"]=fast
        rec["strong_classical_verified_SAFE"]=bool(strong["certified"] or pdr["certified"])
        rec["cheap_original_fast_route_verified_SAFE"]=bool(fast["certified"])
        if rec["strong_classical_verified_SAFE"]:
            rec["status"]="SOURCE_SAFE_INDUCTIVE_NATIVE_3VC_Z3_CVC5_CERTIFIED"
        elif pdr.get("original_PDR_reachability")=="sat":
            rec["status"]="PDR_SAT_UNREPLAYED_ORIGINAL_SAFETY_UNRESOLVED"
        elif pdr.get("original_PDR_reachability")=="unknown":
            rec["status"]="GOLD_FREE_HARD_SAFE_UNPROVEN_PDR_UNKNOWN"
        else:
            rec["status"]="GOLD_FREE_HARD_SAFE_UNPROVEN_CLASSICAL_OR_MISSING_INVARIANT"
    except Exception as e:
        rec["status"]="ABSTAIN_ORIGINAL_TRUE_SOURCE_UNSUPPORTED"
        rec["error"]=type(e).__name__+":"+str(e)[:450]
    rec["all_original_source_three_arms_parsing_and_dual_ms"]=(time.perf_counter_ns()-tic)/1e6
    print("Q3_FIRST_FRESH_PROGRAM_INVARIANT",rec["source"].split("/")[-1],
          "FAMILY",rec["family"],"AUTHENTIC",rec["authentic_true_source"],
          "PDR",rec.get("full_native_Z3_SPACER_6s",{}).get("original_PDR_reachability"),
          "SAFE",rec["strong_classical_verified_SAFE"],
          "STATUS",rec["status"],"ERR",rec.get("error"),flush=True)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    arg=p.parse_args()
    x=json.loads(arg.freeze.read_text())
    if x["schema"]!="neumann.q3.20261021.fresh24_code2inv_2018_expert_headroom.v1" or x["prior_revision"].split("@")[-1]!=REV or len(x["cases"])!=24:
        raise RuntimeError("TRUE_SOURCE_PROGRAM_INVARIANT_METADATA_FREEZE_CHANGED")
    if len({t["git_blob"] for t in x["cases"]})!=24:
        raise RuntimeError("DUPLICATE_TRUE_ORIGINAL_SOURCE_GIT_BLOB")
    # source-independent budgets chosen before any original body seen.
    classical.PDR_MS=6000
    classical.DUAL_S=5
    cases=[evaluate(arg.root,src) for src in x["cases"]]
    report={
      "schema":"neumann.q3.real_original_code2inv_first24_strong_classical_ceiling.v1",
      "first_original_git_sha_frozen_before_first_source_inspection_commit":SOURCE_FREEZE_COMMIT,
      "original_content_unopened_before_register":True,
      "original_upstream_pinned_revision":REV,
      "all_24_authentic_original_source_rows_preserved":len(cases)==24,
      "all_original_24_true_source_valid_and_parity_verified":sum(x["authentic_true_source"] for x in cases),
      "strong_classical_SAFE_inductively_proved_originals":sum(x["strong_classical_verified_SAFE"] for x in cases),
      "fast_original_cvc5_SAFE_dual_certificates":sum(x.get("cheap_original_fast_route_verified_SAFE",False) for x in cases),
      "source_safety_unproven_not_unsafe_or_learned_headroom":sum(x["authentic_true_source"] and not x["strong_classical_verified_SAFE"] for x in cases),
      "original_source_PDR_sat_without_replayed_counterexample":sum(x["status"]=="PDR_SAT_UNREPLAYED_ORIGINAL_SAFETY_UNRESOLVED" for x in cases),
      "original_source_not_supported_by_true_original_compiler":sum(not x["authentic_true_source"] for x in cases),
      "training_weights_updated":0,"neural_proposed_invariants":0,
      "all_24_source_labels_unused":True,
      "no_new_global_Q3_Q4_or_frontier_claim":True,
      "no_valid_closed_Q3_just_from_original_unsafe_or_unsolved":True,
      "cannot_reuse_first_opened_24_as_virgin_test_anymore":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "per_family":{f:{"total":sum(z["family"]==f for z in cases),
                       "eligible":sum(z["family"]==f and z["authentic_true_source"] for z in cases),
                       "classical_inductive_SAFE":sum(z["family"]==f and z["strong_classical_verified_SAFE"] for z in cases)}
                    for f in ("CODE2INV_NATIVE","CODE2INV_CONF5","OTHER_2018")},
      "full_originals":cases
    }
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_NEW_CODE2INV_FIRST_24_AUTHENTIC",report["all_original_24_true_source_valid_and_parity_verified"],"/24")
    print("Q3_NEW_CODE2INV_STRONG_CLASSICAL_SAFE",report["strong_classical_SAFE_inductively_proved_originals"],"/24")
    print("Q3_NEW_CODE2INV_UNPROVEN_NOT_YET_LEARNED",report["source_safety_unproven_not_unsafe_or_learned_headroom"])
    print("Q3_NEW_CODE2INV_PDR_SAT_NOT_REPLAYED",report["original_source_PDR_sat_without_replayed_counterexample"])
    print("Q3_NEW_CODE2INV_BY_FAMILY",report["per_family"])
    print("Q3_GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":
    main()
