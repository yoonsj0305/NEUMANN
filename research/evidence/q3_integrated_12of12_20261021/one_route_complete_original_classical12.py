"""NEUMANN Q3 integrated empirical program proof portfolio on EXACT 12 source
originals. Invoke previously already executed independent native Z3+cvc5
proof-first no-ML classical route; only when original remains UNKNOWN
invoke independently proven general affine conjunction + Houdini source
proof. No model fits, manually supplied invariants, or unsound assumed SAFE.
Source SHA locked before PR412 body, method is posthoc.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from research.evidence.q3_proof_first_baseline_20261021.cheap_safe_verified_original12_no_neural import case as cheap_first
from research.evidence.q3_original12_sourcegeneric_houdini_20261021.auto_affine_houdini_actual_original12 import one as affine_fallback
def ms(t):return (time.perf_counter_ns()-t)/1e6
def run(root,items):
    out=[]
    for item in items:
        started=time.perf_counter_ns()
        first=cheap_first(root,item)
        row={"source":item["path"],"original_git_blob":item["git_blob"],
             "source_original_first_proof":first,
             "final_original_complete_safe":False,
             "neural_forwards":0,"machine_learning_fits":0}
        if first.get("certified_SAFE"):
            row["final_original_complete_safe"]=True
            row["winner"]=first["winner"]
            row["fallback_attempted"]=False
        elif first.get("status")=="ORIGINAL_UNSAFE_DUAL_SAT_NOT_POSSIBLE_SAFE":
            row["winner"]=None
            row["source_original_UNSAFE"]=True
            row["fallback_attempted"]=False
        else:
            proof=affine_fallback(root,item)
            row["source_generic_affine_Houdini_fallback"]=proof
            row["fallback_attempted"]=True
            if proof.get("certified_full_original_SAFE"):
                cert=proof.get("actual_genuine_original_Z3_cvc5_induction_3VC",{})
                if set(cert)!={"init","consecution","goal"} or not all(
                        q.get("dual_pass") for q in cert.values()):
                    raise RuntimeError("FALLBACK_FALSE_SOURCE_NATIVE_DUAL_3VC")
                row["winner"]="generic_conjunctive_affine_Houdini"
                row["final_original_complete_safe"]=True
            else:
                row["winner"]=None
        row["actual_original_full_routed_end_to_end_wall_ms"]=ms(started)
        out.append(row)
        print("Q3_REAL_ORIGINAL_PROOF_FIRST_INTEGRATED",item["path"].rsplit("/",1)[-1],
              "DUAL_CERTIFIED",row["final_original_complete_safe"],
              "ROUTE",row.get("winner"),"WALL_MS",round(row["actual_original_full_routed_end_to_end_wall_ms"],3),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    args=p.parse_args()
    freeze=json.loads(Path(args.freeze).read_text())
    assert freeze["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    cases=freeze["cases"]
    assert len(cases)==12 and len({x["git_blob"] for x in cases})==12
    rows=run(Path(args.root),cases)
    wins={k:sum(r.get("winner")==k for r in rows) for k in
          ("tautology_delete","exact_no_fit_OR_with_min_info","original_cvc5_SyGuS",
           "original_Z3_SPACER","generic_conjunctive_affine_Houdini")}
    report={
        "schema":"neumann.q3.12_originals_full_source_proof_first_integrated_no_neural.v1",
        "same_prebody_sha_frozen_real_originals":12,
        "originals_already_opened_before_THIS_posthoc_implementation":True,
        "fully_independent_source_Z3_cvc5_native_three_VC_safe":sum(r["final_original_complete_safe"] for r in rows),
        "winner_breakdown":wins,
        "fallback_attempts":sum(r["fallback_attempted"] for r in rows),
        "actually_observed_whole_routed_end_to_end_wall_ms":
            sum(r["actual_original_full_routed_end_to_end_wall_ms"] for r in rows),
        "genuine_original_UNSAFE_count":sum(r.get("source_original_UNSAFE",False) for r in rows),
        "global_unsafe_or_unproven_count":
            sum(not r["final_original_complete_safe"] for r in rows),
        "neural_forward_count":0,"trained_model_fit_count":0,
        "same_original_all_12_independent_SHA_verifier_3VC_authority":True,
        "source_family_is_one_small_existing_benchmark_cohort":True,
        "not_frontier_or_end_to_end_10x_or_original_ML_discovery":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "all_originals_and_all_attempted_fallbacks":rows}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for key in ("fully_independent_source_Z3_cvc5_native_three_VC_safe",
                "winner_breakdown","fallback_attempts",
                "actually_observed_whole_routed_end_to_end_wall_ms",
                "global_unsafe_or_unproven_count","trained_model_fit_count"):
        print("Q3_INTEGRATED_EXACT_PROOF_FIRST",key,report[key],flush=True)
    print("GLOBAL_Q3_Q4_Q6_OPEN",flush=True)
if __name__=="__main__":main()
