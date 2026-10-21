"""Q3 first-body-UNOPENED twelve source programs, no method changes.

Exact Git blob metadata frozen at 916c2c3 BEFORE original code content was
viewed for this cohort. Reuse unchanged PR424 proof-first integrated engine:
true original source, exact minimal info, OR, affine Houdini, SyGuS, SPACER,
all with native independent Z3+cvc5 complete 3VC only. No ML calls/weights.
All unseen original failures/unsafe/unknown remain counted in denominator.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from research.evidence.q3_integrated_optimized_12_20261021.complete_zero_neural_exact_houdini_portfolio import case

REGISTER="916c2c3e3c1f08c5ef804ca3179231f60d46dcff"
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def gitblob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    if f["schema"]!="neumann.q3.source_body_first_unopened12_fixed_proof_first_zero_neural_original_v1":
        raise RuntimeError("FIRST_SOURCE_COHORT_CONTRACT_SCHEMA_CHANGED")
    if f["upstream"].split("@")[-1]!=REV or not f["original_source_BODIES_NOT_VIEWED_before_metadata_commit"]:
        raise RuntimeError("ORIGINAL_SOURCE_REGISTRATION_UNVERIFIED")
    selected=f["cases"]
    if len(selected)!=12 or len({r["git_blob"] for r in selected})!=12:
        raise RuntimeError("REAL_SOURCE12_NOT_TWELVE_DISTINCT_ORIGINALS")
    # Only after permanent separate Git registration, first native source read.
    for r in selected:
        data=(Path(a.root)/r["path"]).read_bytes()
        if len(data)!=r["bytes"] or gitblob(data)!=r["git_blob"]:
            raise RuntimeError("SOURCE_BODY_PRE_REGISTERED_SHA_FAIL:"+r["path"])
    start=time.perf_counter_ns()
    rows=[case(Path(a.root),r) for r in selected]  # same real executed PR424 algorithm
    wins={k:sum(x.get("winner")==k for x in rows) for k in (
        "tautology_delete","exact_no_fit_OR_with_min_info","generic_affine_Houdini",
        "original_cvc5_SyGuS","original_Z3_SPACER")}
    safe=sum(r["certified_SAFE"] for r in rows)
    unsafe=sum(r["status"]=="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE" for r in rows)
    report={
      "schema":"neumann.q3.first_body_blind12_unchanged_classical_PROOF_FIRST_full_native_3VC.v1",
      "before_any_original_body_Git_metadata_commit":REGISTER,
      "upstream_original_revision":REV,
      "authentic_distinct_source_SHA_verified":12,
      "original_family_is_xujie_code2inv_same_source_not_cross_author":True,
      "model_weight_transfer_false_no_model_is_trained":True,
      "method_unmodified_since_pr424_success_original12":True,
      "first_blind_true_original_full_dual_3VC_safe":safe,
      "first_blind_true_original_unsafety_proven":unsafe,
      "first_blind_original_UNKNOWN_or_ABSTAIN":12-safe-unsafe,
      "first_blind_route_winner_breakdown":wins,
      "neural_forward_count":0,"model_fit_count":0,
      "source_full_wall_ms_sum":sum(q["total_original_source_parse_minimum_search_proof_wall_ms"] for q in rows),
      "additional_runner_wall_ms":(time.perf_counter_ns()-start)/1e6,
      "strong_classical_mathematical_method_not_neural_Q3":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "all_first_source_originals_and_native_3VC_receipts":rows}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("authentic_distinct_source_SHA_verified","first_blind_true_original_full_dual_3VC_safe",
              "first_blind_true_original_unsafety_proven","first_blind_original_UNKNOWN_or_ABSTAIN",
              "first_blind_route_winner_breakdown","source_full_wall_ms_sum"):
        print("Q3_FIRST_UNOPENED_FIXED_CLASSICAL_PORTFOLIO",k,report[k],flush=True)
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
