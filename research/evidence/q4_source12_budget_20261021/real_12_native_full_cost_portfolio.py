"""PREREG posthoc Q4 equal-source CPU portfolio with complete original dual proof.

All twelve original SyGuS sources already OPENED in prior PR385. Their original
SHA freeze predates *that* first source look, but this NEW cost strategy is
posthoc. No learned feature, new mathematical theorem, or frontier advantage.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import z3
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as base

REVISION="13c8deb68a873635879c9a69bc78caebd340f646"
LOCK_BLOB="cd2110c6c8a68451b7c5bd9f6acbf81b70f9709b"
SCHEMA="neumann.q4.preregistered_posthoc_source12_same_answer_cost_three_routes.v1"
FAST_SYGUS_S=.55
FULL_SYGUS_S=3.0
PDR_MS=5000
def ms(t):return (time.perf_counter_ns()-t)/1e6
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def post_only(src,native):
    t=time.perf_counter_ns()
    proved,receipts=base.verified_3vc(src,native,native["post"])
    return {"certified":bool(proved),"wall_ms":ms(t),
            "original_dual_native_pre_trans_post_3VC":receipts,
            "candidate":"native Post exactly, no train, no solver-extracted candidate"}
def per_case(root,item,idx):
    t=time.perf_counter_ns()
    output={"source":item["path"],"git_blob":item["git_blob"],"source_valid":False,
            "cost_strategy":"fixed_post_then_fast_SyGuS_then_PDR_no_train",
            "status":"ABSTAIN_ORIGINAL"}
    try:
        pre=time.perf_counter_ns()
        raw,src,native,parity=base.prepare(root,item)
        output["source_valid"]=True
        output["source_SHA_authenticated"]=True
        output["source_pre_trans_post_full_native_independent_parity"]=parity
        output["common_source_prep_wall_ms"]=ms(pre)
        if idx==0:
            control,tests=base.verified_3vc(src,native,z3.BoolVal(False))
            output["negative_Post_false_rejected"]=not control
            output["negative_Post_false_independent_original_dual_receipts"]=tests
            if control:raise RuntimeError("FALSE_POST_NEGATIVE_MUTATION_SHOULD_NOT_PROVE_SAFE")
        # all three arms are evaluated on every same original, including failures.
        # Alternate expensive arm order by source index to expose order effects.
        if idx%2:
            standalone_pdr=base.native_pdr(src,native)
            standalone_syguS=base.original_syguS(raw,src,native,FULL_SYGUS_S)
        else:
            standalone_syguS=base.original_syguS(raw,src,native,FULL_SYGUS_S)
            standalone_pdr=base.native_pdr(src,native)
        output["standalone_cvc5_SyGuS"]=standalone_syguS
        output["standalone_Z3_SPACER"]=standalone_pdr
        cstart=time.perf_counter_ns()
        post=post_only(src,native)
        short=None;fallback=None
        if not post["certified"]:
            short=base.original_syguS(raw,src,native,FAST_SYGUS_S)
            if not short["certified"]:
                fallback=base.native_pdr(src,native)
        cheap={"original_Post_dual3VC":post,
              "short_original_cvc5_SyGuS":short,
              "fallback_Z3_SPACER_if_needed":fallback,
              "actual_wall_ms":ms(cstart)}
        cheap["certified"]=bool(post["certified"] or
                                (short and short["certified"]) or
                                (fallback and fallback["certified"]))
        output["fixed_post_first_cheapest_safe"]=cheap
        ssuccess=bool(standalone_syguS["certified"])
        psuccess=bool(standalone_pdr["certified"])
        output["strong_original_reference_any_route_certified"]=ssuccess or psuccess
        reference_times=[v["total_route_wall_ms"] for v in
                         (standalone_syguS,standalone_pdr) if v["certified"]]
        if cheap["certified"] and reference_times:
            output["comparable_same_certified_original_task"]=True
            output["best_hindsight_expert_reference_wall_ms"]=min(reference_times)
            output["ratio_hindsight_expert_over_strategy_including_common_prep"]=(
                (min(reference_times)+output["common_source_prep_wall_ms"])/
                (cheap["actual_wall_ms"]+output["common_source_prep_wall_ms"]))
        else:
            output["comparable_same_certified_original_task"]=False
            output["ratio_hindsight_expert_over_strategy_including_common_prep"]=None
        output["status"]="COMPLETE_THREE_ACTUAL_ORIGINAL_ROUTES"
    except Exception as e:
        output["status"]="FAIL_CLOSED_UNSUPPORTED_OR_RUNTIME"
        output["failure"]=type(e).__name__+":"+str(e)[:400]
    finally:
        output["full_three_route_research_wall_ms"]=ms(t)
    print("Q4_ACTUAL_ORIGINAL",idx+1,output["source"],
          "PRE",output.get("source_valid"),"POST",output.get("fixed_post_first_cheapest_safe",{}).get("original_Post_dual3VC",{}).get("certified"),
          "STRATEGY",output.get("fixed_post_first_cheapest_safe",{}).get("certified"),
          "SYGUS",output.get("standalone_cvc5_SyGuS",{}).get("certified"),
          "PDR",output.get("standalone_Z3_SPACER",{}).get("certified"),
          "MATCHED_RATIO",output.get("ratio_hindsight_expert_over_strategy_including_common_prep"),
          "STATUS",output["status"],flush=True)
    return output

def run(root,manifest,contract):
    if contract["schema"]!=SCHEMA or contract["input_git_blob_of_lock"]!=LOCK_BLOB:
        raise RuntimeError("PREEXECUTION_FIXED_PROTOCOL_ORIGINAL_MANIFEST_CHANGED")
    if contract["global_Q4"]!="OPEN" or contract["training_updates"]!=0:
        raise RuntimeError("FALSE_GLOBAL_Q4_CLOSURE_OR_TRAINING")
    if manifest["upstream"].split("@")[-1]!=REVISION or len(manifest["cases"])!=12:
        raise RuntimeError("UNMODIFIED_TWELVE_ORIGINAL_SOURCE_SHA_INVALID")
    for item in manifest["cases"]:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_PREOPEN_GIT_BLOB_MISMATCH")
    base.PDR_MS=PDR_MS
    rows=[per_case(root,item,i) for i,item in enumerate(manifest["cases"])]
    valid=[r for r in rows if r["status"]=="COMPLETE_THREE_ACTUAL_ORIGINAL_ROUTES"]
    matched=[r for r in valid if r["comparable_same_certified_original_task"]]
    denominator=sum(r["fixed_post_first_cheapest_safe"]["actual_wall_ms"]+r["common_source_prep_wall_ms"] for r in matched)
    numerator=sum(r["best_hindsight_expert_reference_wall_ms"]+r["common_source_prep_wall_ms"] for r in matched)
    report={
      "schema":"neumann.q4.genuine_prior_opened_original12_CPU_proof_matched_cost_v1",
      "originals":rows,"true_original_genuine_git_SHA_count":12,
      "actually_executed_full_three_route_cases":len(valid),
      "post_only_actual_original_dual_3VC_count":sum(r["fixed_post_first_cheapest_safe"]["original_Post_dual3VC"]["certified"] for r in valid),
      "fixed_cheap_portfolio_native_dual_3VC_count":sum(r["fixed_post_first_cheapest_safe"]["certified"] for r in valid),
      "standalone_full_cvc5_original_certified":sum(r["standalone_cvc5_SyGuS"]["certified"] for r in valid),
      "standalone_Z3_SPACER_original_certified":sum(r["standalone_Z3_SPACER"]["certified"] for r in valid),
      "matched_original_both_certified_count":len(matched),
      "matched_hindsight_STRONGEST_lower_bound_ratio_with_common_parsing":numerator/denominator if denominator>0 else None,
      "matched_portfolio_10x_vs_hindsight_best_same_task_COUNT":sum(
          r["ratio_hindsight_expert_over_strategy_including_common_prep"]>=10 for r in matched),
      "per_source_hindsight_selection_is_nonimplementable_oracle":True,
      "real_source_body_already_opened_before_this_NEW_protocol":True,
      "all_original_statuses_including_failures_retained":True,
      "synthetic_false_Post_safety_refuted":rows[0].get("negative_Post_false_rejected",False),
      "source_invariant_learner_used":False,"neural_forwards":0,
      "equal_authority_classical_direct_can_use_same_strategy":True,
      "not_global_Q4_frontier_efficiency":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN",
      "overall":"OBSERVATION_ONLY_NEVER_AUTOPASS_GLOBAL_GATES"
    }
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=run(a.root,json.loads(a.freeze.read_text()),json.loads(a.contract.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for label in ("actually_executed_full_three_route_cases","post_only_actual_original_dual_3VC_count",
                  "fixed_cheap_portfolio_native_dual_3VC_count","standalone_full_cvc5_original_certified",
                  "standalone_Z3_SPACER_original_certified","matched_original_both_certified_count",
                  "matched_hindsight_STRONGEST_lower_bound_ratio_with_common_parsing",
                  "matched_portfolio_10x_vs_hindsight_best_same_task_COUNT"):
        print("Q4_TRUE_ORIGINAL",label,report[label])
    print("Q4_GLOBAL",report["global_Q4"])
if __name__=="__main__":main()
