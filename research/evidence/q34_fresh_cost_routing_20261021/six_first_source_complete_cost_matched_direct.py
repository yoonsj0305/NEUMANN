"""First-source-blind six actual original task full-cost portfolio comparison.

Pre-source pinned Git source. No prior original results exposed to dispatch.
Three complete original native Z3+cvc5 source-safe/unsafe methods share full
original semantics and the same tools; original source parsing, verifier,
failed attempts and source checking INCLUDED per arm wall. Explicitly
not an invention of a better learned structure; strong Direct owns all tools.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path

from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,original_syguS,native_pdr,verified_3vc
)
from research.evidence.q34_safety_triage_six_20261021.first_six_general_reachable_unsafety_and_full_safe_3vc import (
    bounded_original_bad_path,control_prior_fib07,control_prior_safe
)

COMMIT="a4bf2cbf40040636480fb800d5824d8353bac834"
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
BIG_THRESHOLD=8192
FAST_SYGUS_S=0.75

def candidate_sequence(order):
    assert order in ("size_route","uniform_post_first","direct_PDR_first")
    if order=="uniform_post_first":
        return ["post","bmc","sygus","pdr"]
    if order=="direct_PDR_first":
        return ["pdr","bmc","sygus","post"]
    raise RuntimeError("SOURCE_LENGTH_REQUIRED_FOR_SIZE_ROUTE")

def execute_full_path(source_root,entry,order):
    start=time.perf_counter_ns()
    row={
        "source":entry["path"],
        "frozen_git_blob":entry["git_blob"],
        "arm":order,"complete_certified":False,"classification":"UNKNOWN",
        "no_neural_calls":True,"had_exact_source_semantic_parity":False,
        "attempts":[]
    }
    try:
        # Input parsing, independent original semantic parity, source Pre SAT,
        # source Post nontrivial evidence all included in this timer.
        raw,src,native,evidence=prepare(source_root,entry)
        row["had_exact_source_semantic_parity"]=True
        row["original_source_authenticated"]=evidence
        if order=="size_route":
            selected=(candidate_sequence("direct_PDR_first")
                      if entry["bytes"]>BIG_THRESHOLD
                      else candidate_sequence("uniform_post_first"))
        else:
            selected=candidate_sequence(order)
        row["route_precommitted_steps"]=selected
        row["public_metadata_length"]=entry["bytes"]
        row["public_metadata_feature_large"]=entry["bytes"]>BIG_THRESHOLD
        for method in selected:
            t=time.perf_counter_ns()
            attempted={"method":method,"full_original_certified":False}
            if method=="post":
                valid,checks=verified_3vc(src,native,native["post"])
                attempted["dual_Z3_cvc5_original_3VC"]=checks
                attempted["full_original_certified"]=valid
                if valid:
                    row["complete_certified"]=True
                    row["classification"]="SAFE"
            elif method=="bmc":
                trial=bounded_original_bad_path(src,native)
                attempted["real_grounded_source_trace"]=trial
                attempted["full_original_certified"]=trial["true_bounded_original_safety_refuted"]
                if trial["true_bounded_original_safety_refuted"]:
                    row["complete_certified"]=True
                    row["classification"]="UNSAFE"
            elif method=="sygus":
                result=original_syguS(raw,src,native,FAST_SYGUS_S)
                attempted["real_original_sygus_certificate"]=result
                attempted["full_original_certified"]=result["certified"]
                if result["certified"]:
                    row["complete_certified"]=True
                    row["classification"]="SAFE"
            elif method=="pdr":
                result=native_pdr(src,native)
                attempted["real_original_pdr_certificate"]=result
                attempted["full_original_certified"]=result["certified"]
                if result["certified"]:
                    row["complete_certified"]=True
                    row["classification"]="SAFE"
            else:
                raise RuntimeError("UNREGISTERED_METHOD:"+method)
            attempted["paid_attempt_wall_ms"]=(time.perf_counter_ns()-t)/1e6
            row["attempts"].append(attempted)
            if row["complete_certified"]:
                row["accepted_source_original_proof"]=method
                break
    except Exception as e:
        row["error"]=type(e).__name__+":"+str(e)[:340]
        row["classification"]="UNKNOWN"
        row["complete_certified"]=False
    row["complete_path_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return row

def per_source(root,entry):
    # Fixed order, not chosen after viewing source results.
    case={"source":entry["path"],"origin_sha":entry["git_blob"],
          "first_source_pre_content_locked":True}
    for arm in ("direct_PDR_first","uniform_post_first","size_route"):
        case[arm]=execute_full_path(root,entry,arm)
    vals={case[a]["classification"] for a in
          ("direct_PDR_first","uniform_post_first","size_route")
          if case[a]["complete_certified"]}
    case["independently_certified_disposition_agreement"]=len(vals)<=1
    case["any_success"] = bool(vals)
    if not case["independently_certified_disposition_agreement"]:
        case["status"]="FAIL_CONFLICTING_INDEPENDENTLY_CERTIFIED_RESULTS"
    else:
        case["status"]="CERTIFIED_CONSISTENT" if case["any_success"] else "UNKNOWN_NOT_RESOLVED"
    d=case["direct_PDR_first"];u=case["uniform_post_first"];n=case["size_route"]
    case["size_vs_direct_paired_cost_ratio_only_same_certified_result"]=(
        d["complete_path_wall_ms"]/n["complete_path_wall_ms"]
        if d["complete_certified"] and n["complete_certified"]
        and d["classification"]==n["classification"] else None)
    case["size_vs_uniform_paired_cost_ratio_only_same_certified_result"]=(
        u["complete_path_wall_ms"]/n["complete_path_wall_ms"]
        if u["complete_certified"] and n["complete_certified"]
        and u["classification"]==n["classification"] else None)
    print("FROZEN_NEW_SOURCE",entry["path"],case["status"],
          "PDR",d["classification"],round(d["complete_path_wall_ms"],2),
          "UNIFORM",u["classification"],round(u["complete_path_wall_ms"],2),
          "NEW",n["classification"],round(n["complete_path_wall_ms"],2),
          flush=True)
    return case

def aggregate(rows,arm):
    return {
        "certified":sum(x[arm]["complete_certified"] for x in rows),
        "safe":sum(x[arm]["classification"]=="SAFE" and x[arm]["complete_certified"] for x in rows),
        "unsafe":sum(x[arm]["classification"]=="UNSAFE" and x[arm]["complete_certified"] for x in rows),
        "unknown":sum(not x[arm]["complete_certified"] for x in rows),
        "total_paid_full_path_wall_ms":sum(x[arm]["complete_path_wall_ms"] for x in rows),
        "total_paid_attempts":sum(len(x[arm]["attempts"]) for x in rows),
        "full_source_semantic_authentications":sum(x[arm]["had_exact_source_semantic_parity"] for x in rows)
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    frozen=json.loads(a.freeze.read_text())
    if frozen["rev"]!=UPSTREAM or len(frozen["sources"])!=6:
        raise RuntimeError("PRE_CONTENT_ORIGINAL_SOURCE_COHORT_CHANGED")
    # Real prior source controls, no use in routing any of the six targets.
    controls={"original_fib07_independent_UNSAFE":control_prior_fib07(a.root),
              "original_fib05_independent_SAFE":control_prior_safe(a.root)}
    studies=[per_source(a.root,item) for item in frozen["sources"]]
    arms=["direct_PDR_first","uniform_post_first","size_route"]
    metrics={arm:aggregate(studies,arm) for arm in arms}
    all_certified=all(x["independently_certified_disposition_agreement"] for x in studies)
    baseline=metrics["direct_PDR_first"];fixed=metrics["size_route"]
    same_capability=(all_certified and
        fixed["certified"]==baseline["certified"]==6 and
        all(x["size_route"]["classification"]==x["direct_PDR_first"]["classification"] for x in studies))
    report={
        "schema":"neumann.q34.prospective_six_true_originals_conditional_computation.v1",
        "pre_content_source_freeze_commit":COMMIT,
        "source_all_six_preserved":len(studies)==6,
        "source_all_six_programs_nonduplicate":len({x["source"] for x in studies})==6,
        "positive_and_negative_source_controls":controls,
        "arms":metrics,
        "per_original_case":studies,
        "no_neural_model_forwards":True,
        "source_case_all_certificates_agree":all_certified,
        "same_capability_full_certificate_new_vs_direct":same_capability,
        "candidate_total_wall_over_direct_total_wall_ratio":(
            fixed["total_paid_full_path_wall_ms"]/baseline["total_paid_full_path_wall_ms"]
            if same_capability else None),
        "candidate_full_cost_below_direct_at_iso_capability":(
            fixed["total_paid_full_path_wall_ms"]<baseline["total_paid_full_path_wall_ms"]
            if same_capability else False),
        "candidate_10x_faster_at_iso_capability":(
            fixed["total_paid_full_path_wall_ms"]*10<=baseline["total_paid_full_path_wall_ms"]
            if same_capability else False),
        "same_run_sequential_hardware_noise":True,
        "strong_direct_can_execute_identical_source_size_dispatch":True,
        "evidence_domain":"real original source safety only; three benchmark directories; no new authors established",
        "not_neural_unique_structure_discovery":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q34_SIX_SOURCE_TOTAL_COUNTS",json.dumps(metrics))
    print("Q34_SIX_SCOPED_MATCHED_COST_POSSIBLE",same_capability,
          "CANDIDATE_OVER_DIRECT",report["candidate_total_wall_over_direct_total_wall_ratio"])
    print("Q34_SIX_SCOPED_MATCHED_COST_BETTER",report["candidate_full_cost_below_direct_at_iso_capability"])
    print("Q34_SIX_SCOPED_10X",report["candidate_10x_faster_at_iso_capability"])
    print("Q34_GLOBAL_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
