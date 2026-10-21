"""FIRST source-body-unopened transfer of PREVIOUSLY FIXED H→S→D hybrid.

Actual source bodies were not read before metadata SHA lock 311db2c.
Core source parser, generic linear-Houdini and all fallbacks imported
UNCHANGED from preceding PR392. No per-file tuning. Real new source proofs
only on original native 3VC Z3+cvc5; all unsafe/unknown ABSTAIN.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.evidence.q3_complete_houdini_portfolio_20261021.full_original12_same_source_hybrid_vs_strong_classical import per_source
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as base
LOCK="311db2c777d01de80fe7a323d67386732b3ff16c"
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for n in ("root","freeze","out"):p.add_argument("--"+n,required=True)
    a=p.parse_args()
    manifest=json.loads(Path(a.freeze).read_text())
    if manifest["schema"]!="neumann.q3q6_second12_genuinely_unopened_original_source_hybrid_transfer_v1":
        raise RuntimeError("SOURCE_SECOND_12_PRECOMMITTED_METADATA_DIFFERENT")
    if manifest["upstream"].split("@")[-1]!=UPSTREAM or len(manifest["new_originals"])!=12:
        raise RuntimeError("SOURCE_UPSTREAM_OR_SOURCE_COUNT_DRIFT")
    candidates=manifest["new_originals"]
    assert len({x["git_blob"] for x in candidates})==12
    assert len([x for x in candidates if x["family"]=="fib"])==2
    assert len([x for x in candidates if x["family"]=="other"])==10
    root=Path(a.root)
    # Before any true body is parsed by the already frozen source-agnostic
    # method, independently check all native original bytes and Git SHA.
    for c in candidates:
        raw=(root/c["path"]).read_bytes()
        if len(raw)!=c["bytes"] or sha(raw)!=c["git_blob"]:
            raise RuntimeError("SECOND_NEW_SOURCE_ORIGINAL_SHA_OR_SIZE_MISMATCH:"+c["path"])
    base.PDR_MS=5000
    records=[per_source(root,c,i) for i,c in enumerate(candidates)]
    valid=[q for q in records if q["status"]=="COMPLETE_ALL_THREE_TRUE_ORIGINAL_SOURCE_PROGRAMS"]
    proven=lambda arm:sum(q["all_matched_originals_full_inductive_success"][arm] for q in valid)
    matched=[r for r in valid if all(r["all_matched_originals_full_inductive_success"].values())]
    measured={route:sum(r["individual_deploy_source_wall_including_prep_ms"][route] for r in matched)
              for route in ("hybrid","S_then_D","D_then_S")}
    result={
      "schema":"neumann.q3q6.second12_first_unopened_true_original_fixed_classical_hybrid_proof_v1",
      "first_meta_only_original_git_SHA_commit":LOCK,
      "original_source_revision":UPSTREAM,
      "new_original_cohort_git_SHA_authenticated":12,
      "actual_three_routes_source_native_executed":len(valid),
      "first_source_body_new_12_originals":True,
      "previously_FIXED_Houdini_SyGuS_SPACER_core_reused_without_code_changes":True,
      "actual_source_full_dual_3VC_Hybrid_success":proven("hybrid"),
      "actual_source_full_dual_3VC_classical_SyGuS_then_SPACER_success":proven("S_then_D"),
      "actual_source_full_dual_3VC_classical_SPACER_then_SyGuS_success":proven("D_then_S"),
      "fully_verified_originals_for_matched_three_method_cost":len(matched),
      "costs_on_identical_originals_with_same_true_proof":measured,
      "genuine_new_originals_uncertified_as_SAFE_in_hybrid":12-proven("hybrid"),
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "no_trained_structure_or_unique_frontier_speed_claim":True,
      "fresh_programs":records
    }
    result["bounded_hybrid_extra_safe_over_best_matched_static_under_caps"]=(
       result["actual_source_full_dual_3VC_Hybrid_success"]-
       max(result["actual_source_full_dual_3VC_classical_SyGuS_then_SPACER_success"],
           result["actual_source_full_dual_3VC_classical_SPACER_then_SyGuS_success"]))
    if measured["hybrid"]:
        result["matched_static_best_posthoc_wall_over_hybrid_ratio"]=min(
            measured["S_then_D"],measured["D_then_S"])/measured["hybrid"]
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for key in ("new_original_cohort_git_SHA_authenticated","actual_three_routes_source_native_executed",
                "actual_source_full_dual_3VC_Hybrid_success",
                "actual_source_full_dual_3VC_classical_SyGuS_then_SPACER_success",
                "actual_source_full_dual_3VC_classical_SPACER_then_SyGuS_success",
                "fully_verified_originals_for_matched_three_method_cost",
                "bounded_hybrid_extra_safe_over_best_matched_static_under_caps",
                "matched_static_best_posthoc_wall_over_hybrid_ratio"):
        print("FIRST_NEW_SECOND12_TRUE_SOURCE",key,result.get(key))
    print("NO_GLOBAL_LEARNED_STRUCTURE_PASS",result["global_Q3"])
if __name__=="__main__":main()
