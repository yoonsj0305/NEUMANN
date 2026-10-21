"""Posthoc true original SyGuS program 6-case source BMC triage.
Five first study PDR-SAT candidates and one fib32 UNKNOWN.
Full original Pre, Trans*, NotPost grounded all state and independently
proved SAT by Z3+cvc5. Zero model training, prior-source-open honest.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc as bmc
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as expert

FIRST_FREEZE="6a5792e196b2234358dca31ec9dd733f3ffed42d"
POST_REGISTER="bfe2c4457aa281a038dfeb422ffe940b27ccf694"

def one(root,item,purpose):
    start=time.perf_counter_ns()
    rec={"source":item["path"],"family":item["family"],"purpose":purpose,
         "true_source_authentic":False,"independently_grounded_UNSAFE":False,
         "independently_inductive_SAFE":False,"status":"UNKNOWN"}
    try:
        raw,src,native,identity=expert.prepare(root,item)
        rec["true_source_authentic"]=True
        rec["unchanged_original_pre_trans_post_parity_and_nonvacuity"]=identity
        trace=bmc.bounded_original_bad_path(src,native)
        rec["full_original_0_to_5_BMC_dual_Z3_cvc5"]=trace
        if trace["true_bounded_original_safety_refuted"]:
            rec["independently_grounded_UNSAFE"]=True
            rec["status"]="UNSAFE_FULL_ORIGINAL_ALL_STATES_GROUNDED_Z3_CVC5"
        elif purpose=="FIB32_HARD":
            synth=expert.original_syguS(raw,src,native,20.0)
            pdr=expert.native_pdr(src,native)
            rec["longer_original_native_cvc5_SyGuS_20sec"]=synth
            rec["longer_original_native_Z3_SPACER_20sec"]=pdr
            rec["independently_inductive_SAFE"]=synth["certified"] or pdr["certified"]
            rec["status"]="SAFE_FULL_ORIGINAL_DUAL_3VC" if rec["independently_inductive_SAFE"] else "UNKNOWN_LONGER_BMC_AND_EXPERT"
        else:
            rec["status"]="UNKNOWN_PDR_SAT_BUT_NO_GROUNDED_PATH_UNDER_5"
    except Exception as e:
        rec["status"]="UNKNOWN_ORIGINAL_SOURCE_OR_VERIFIER_EXCEPTION"
        rec["error"]=type(e).__name__+":"+str(e)[:350]
    rec["all_original_proof_attempt_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_CODE2INV_SIX_TRUE_ORIGINAL",item["path"].split("/")[-1],
          "SAFE",rec["independently_inductive_SAFE"],
          "UNSAFE",rec["independently_grounded_UNSAFE"],
          "STATUS",rec["status"],"ERR",rec.get("error"),flush=True)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    m=json.loads(a.freeze.read_text());f=json.loads(a.protocol.read_text())
    if m["schema"]!="neumann.q3.20261021.fresh24_code2inv_2018_expert_headroom.v1" or f["schema"]!="neumann.q3.posthoc_first24_source_5_PDR_SAT_plus_one_HARD_BMC_replay.v1":
        raise RuntimeError("FROZEN_REAL_SOURCE_TWENTYFOUR_SIX_PROTOCOL_CHANGED")
    if len(m["cases"])!=24 or len(f["strict_frozen_six"])!=6:
        raise RuntimeError("CANNOT_CHANGE_FROZEN_SOURCE_SIX_ORIGINALS")
    bmc.BMC_MAX_DEPTH=5
    bmc.SAT_TIMEOUT_MS=4000
    bmc.INDEPENDENT_SAT_TIMEOUT_S=6
    expert.DUAL_S=5
    expert.PDR_MS=20000
    src_by_name={x["path"].split("/")[-1]:x for x in m["cases"]}
    cases=[]
    for spec in f["strict_frozen_six"]:
        original=src_by_name[spec["name"]]
        if original["family"]!=spec["family"]:raise RuntimeError("FROZEN_ORIGINAL_FAMILY_MISMATCH")
        purpose="FIB32_HARD" if spec["name"]=="fib_32.sl" else "SPACER_SAT"
        cases.append(one(a.root,original,purpose))
    safe=sum(x["independently_inductive_SAFE"] for x in cases)
    unsafe=sum(x["independently_grounded_UNSAFE"] for x in cases)
    report={
        "schema":"neumann.q3.true_original_six_posthoc_independent_BMC_unsafe.v1",
        "original_first_24_true_source_hash_frozen_before_read":FIRST_FREEZE,
        "six_suspected_source_tasks_posthoc_frozen_commit":POST_REGISTER,
        "original_six_full_source_identifiers_kept":len(cases)==6,
        "all_six_true_original_source_authenticated":sum(x["true_source_authentic"] for x in cases),
        "five_PDR_sat_replayed_as_independently_certified_UNSAFE":sum(x["purpose"]=="SPACER_SAT" and x["independently_grounded_UNSAFE"] for x in cases),
        "fib32_original_proved_SAFE":int(cases[-1]["independently_inductive_SAFE"]),
        "fib32_original_proved_UNSAFE":int(cases[-1]["independently_grounded_UNSAFE"]),
        "true_original_safe_count":safe,
        "true_original_unsafe_count":unsafe,
        "true_original_UNKNOWN_count":6-safe-unsafe,
        "unproved_and_timeout_are_not_actual_SAFE_or_UNSAFE":True,
        "no_neural_training_or_unique_Q3_claim":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
        "original_six":cases
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_CODE2INV_FIVE_PDR_SAT_ACTUAL_ORIGINAL_UNSAFE",report["five_PDR_sat_replayed_as_independently_certified_UNSAFE"],"/5")
    print("Q3_CODE2INV_FIB32_FINAL_SAFE",report["fib32_original_proved_SAFE"])
    print("Q3_CODE2INV_FIB32_FINAL_UNSAFE",report["fib32_original_proved_UNSAFE"])
    print("Q3_CODE2INV_SIX_TOTAL_SAFE_UNSAFE_UNKNOWN",safe,unsafe,6-safe-unsafe)
    print("Q3_CODE2INV_GLOBAL_Q3",report["global_Q3"])
if __name__=="__main__":
    main()
