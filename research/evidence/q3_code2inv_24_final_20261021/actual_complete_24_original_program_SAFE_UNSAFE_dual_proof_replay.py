"""Coherent POSTHOC full true-source replay of 24 original Code2Inv/from2018.

All originals SHA frozen before first source body in PR371.
Native source cvc5 SyGuS + original Z3 Spacer and independent 3VC for SAFE;
full original 0..5 bounded state path Z3 and cvc5 SAT for UNSAFE;
one real original fib32 source manually derived parity induction Z3+cvc5.
This is a deterministic classical proof portfolio with explicit authored
source specialist after inspection, NOT a learned neural unique Q3 result.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import research.evidence.q3_code2inv_presource24_20261021.first_original24_native_cvc5_sygus_z3_spacer_expert_gate as expert
import research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc as bmc
import research.evidence.q3_fib32_parity_20261021.source_fib32_native_k_b_i_j_n_mod2_inductive_certificate as parity

FIRST_SOURCE_GIT_FREEZE="6a5792e196b2234358dca31ec9dd733f3ffed42d"
BEFORE_REPLAY="0af15ba44e9a2ba5a7592e019090a32fe0eb3d64"
FIB32_SOURCE="lib/Inv_Track/from_2018/fib_32.sl"

def evaluate_one(root,item):
    t=time.perf_counter_ns()
    row={"source":item["path"],"family":item["family"],
         "source_safe_original_full_3VC":False,
         "source_unsafe_original_full_grounded_path":False,
         "route":"UNKNOWN","source_native_git_sha_authenticated":False}
    e=expert.evaluate(root,item)
    row["original_strong_classical_competing_source_certificate"]=e
    row["source_native_git_sha_authenticated"]=e["authentic_true_source"]
    if e["strong_classical_verified_SAFE"]:
        row["source_safe_original_full_3VC"]=True
        row["route"]="GENERIC_NATIVE_ORIGINAL_SYGUS_OR_Z3_PDR_SAFE_DUAL_3VC"
    elif e["authentic_true_source"]:
        raw,src,native,proof=expert.classical.prepare(root,item)
        trace=bmc.bounded_original_bad_path(src,native)
        row["original_unsafe_bounded_grounded_two_solver_trace"]=trace
        if trace["true_bounded_original_safety_refuted"]:
            row["source_unsafe_original_full_grounded_path"]=True
            row["route"]="GENERIC_SOURCE_ORIGINAL_ALL_STATES_GROUNDED_UNSAFE_DUAL"
        elif item["path"]==FIB32_SOURCE:
            # Specific manual parity insight was developed after first source
            # opening. Do not claim learned generalizable system automation.
            v=parity.check(root,item)
            row["posthoc_MANUAL_source_parity_specialist"]=v
            if v["actual_true_original_parity_3VC_Z3_cvc5"]:
                row["source_safe_original_full_3VC"]=True
                row["route"]="POSTHOC_MANUAL_FIB32_PARITY_DUAL_3VC"
    row["independent_original_proof_status"]=(
        "SAFE" if row["source_safe_original_full_3VC"] else
        "UNSAFE" if row["source_unsafe_original_full_grounded_path"] else "UNKNOWN"
    )
    row["whole_source_native_baseline_BMC_and_optional_parity_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    print("Q3_UNIFIED_REAL_PROGRAM24",item["path"].split("/")[-1],
          "FINAL",row["independent_original_proof_status"],"AUTH",row["source_native_git_sha_authenticated"],
          "ROUTE",row["route"],flush=True)
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    f=json.loads(a.freeze.read_text())
    c=json.loads(a.protocol.read_text())
    if c["schema"]!="neumann.q3.posthoc_complete_original_24_independent_safety_proof_replay.v1" or len(f["cases"])!=24:
        raise RuntimeError("HISTORIC_24_TRUE_ORIGINAL_SHA_COHORT_OR_PROTOCOL_CHANGED")
    bmc.BMC_MAX_DEPTH=5
    bmc.SAT_TIMEOUT_MS=4000
    bmc.INDEPENDENT_SAT_TIMEOUT_S=6
    expert.classical.PDR_MS=6000
    expert.classical.DUAL_S=5
    t=time.perf_counter_ns()
    rows=[evaluate_one(a.root,item) for item in f["cases"]]
    safes=sum(x["source_safe_original_full_3VC"] for x in rows)
    unsafe=sum(x["source_unsafe_original_full_grounded_path"] for x in rows)
    statuses={"SAFE":safes,"UNSAFE":unsafe,"UNKNOWN":len(rows)-safes-unsafe}
    routes={k:sum(x["route"]==k for x in rows) for k in sorted({x["route"] for x in rows})}
    report={
      "schema":"neumann.q3.source_original24_independently_classified_posthoc.v1",
      "source_original_git_blob_pre_open_sha_manifest_commit":FIRST_SOURCE_GIT_FREEZE,
      "posthoc_protocol_before_final_composed_CI_commit":BEFORE_REPLAY,
      "all_true_original_files_previously_OPENED_from_first_expert_screen":True,
      "all_original24_source_rows_retained":len(rows)==24,
      "exact_original_git_blob_verified_count":sum(x["source_native_git_sha_authenticated"] for x in rows),
      "complete_source_full_original_independent_results":statuses,
      "source_original_24_certified_safe_plus_unsafe":safes+unsafe,
      "proof_routes":routes,
      "source_specific_manual_parity_NOT_an_automatically_learned_invariant":True,
      "matched_equal_authority_expert_can_use_all_same_source_mathematics":True,
      "strong_generic_pre_parity_original_safe_count":sum(x["original_strong_classical_competing_source_certificate"]["strong_classical_verified_SAFE"] for x in rows),
      "all_actual_original_attacks_and_successes_wall_ms":(time.perf_counter_ns()-t)/1e6,
      "model_weights_updated":0,"neural_forwards":0,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "all_original_sources":rows
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_TRUE_ORIGINAL_24_ALL_AUTHENTIC",report["exact_original_git_blob_verified_count"],"/24")
    print("Q3_TRUE_ORIGINAL_24_INDEPENDENT_COMPLETE_SAFE_UNSAFE_UNKNOWN",statuses)
    print("Q3_TRUE_ORIGINAL_24_DISPOSITION_ROUTING",routes)
    print("Q3_TRUE_ORIGINAL_24_GLOBAL_LEARNED_Q3_OPEN",report["global_Q3"])
if __name__=="__main__":
    main()
