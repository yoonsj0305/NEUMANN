"""Q3 v3.2 POSTHOC: add the actual ORIGINAL source Post as a proof target
to already empirically fitted PCA source-native invariant candidates.

This is NOT a pre-registered first source body complete-safety experiment:
PR401 opened all twelve. It does not use manually copied gold invariants.
Original native unchanged Pre/Trans/Post verified independently Z3 & cvc5.
Same-data exact classical nullspace and simple nofit baselines have equal
source parser, Post access and 3VC verification.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from research.evidence.q3_v3_PCA_conservation_20261021.actual_native_source_PCA_conservation import (
    learned_pca_candidates,exact_classical_nullspace_candidates
)
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import (
    source_samples,candidate_generator,houdini,millis
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare
def one(root,item):
    start=time.perf_counter_ns()
    record={"source":item["path"],"true_original_git_blob":item["git_blob"],
            "already_opened_before_method_added":True,"status":"ABSTAIN"}
    try:
        raw,src,native,identity=prepare(root,item)
        samples,edges,observation=source_samples(src,native)
        record["actual_original_pre_trans_post_native_parity"]=identity
        record["actual_original_source_transition_data"]=observation
        if len(samples)<3 or not edges:raise RuntimeError("NOT_ENOUGH_REAL_NATIVE_SOURCE_TRAJECTORIES")
        nofit,_=candidate_generator(src,samples,edges,False)
        learned,L=learned_pca_candidates(src,samples)
        exact,E=exact_classical_nullspace_candidates(src,samples)
        record["actual_CPU_fitted_model"]=L
        record["equal_data_exact_classical_model"]=E
        original_post=(native["post"],{"ORIGINAL_FULL_SOURCE_POST_AVAILABLE_TO_ALL"})
        # Identical proof engine, source data and original Post, only
        # candidate-generating learning method differs.
        record["POST_only_already_exact_original_dual"]=houdini(src,native,[original_post])
        record["simple_NOLEARN_plus_original_POST"]=houdini(src,native,nofit+[original_post])
        record["TRAINED_PCA_plus_original_POST"]=houdini(src,native,nofit+learned+[original_post])
        record["EXACT_CLASSICAL_plus_original_POST"]=houdini(src,native,nofit+exact+[original_post])
        record["trained_full_3VC_success_not_no_learn"]=bool(
            record["TRAINED_PCA_plus_original_POST"]["fully_verified_complete_original_3VC"] and
            not record["simple_NOLEARN_plus_original_POST"]["fully_verified_complete_original_3VC"])
        record["trained_full_3VC_success_not_exact_classical"]=bool(
            record["TRAINED_PCA_plus_original_POST"]["fully_verified_complete_original_3VC"] and
            not record["EXACT_CLASSICAL_plus_original_POST"]["fully_verified_complete_original_3VC"])
        record["status"]="EXECUTED_POSTHOC_REAL_NATIVE_FULL_3VC_COMPARE"
    except Exception as e:
        record["status"]="ABSTAIN_REAL_SOURCE_OR_PROOF"
        record["error"]=type(e).__name__+":"+str(e)[:350]
    record["full_original_source_preflight_fit_propose_and_3VC_wall_ms"]=millis(start)
    print("Q3_V32_ORIGINAL_COMPLETE",
          item["path"].rsplit("/",1)[-1],record["status"],
          "POST",record.get("POST_only_already_exact_original_dual",{}).get("fully_verified_complete_original_3VC"),
          "NOFIT",record.get("simple_NOLEARN_plus_original_POST",{}).get("fully_verified_complete_original_3VC"),
          "TRAINED",record.get("TRAINED_PCA_plus_original_POST",{}).get("fully_verified_complete_original_3VC"),
          "EXACT",record.get("EXACT_CLASSICAL_plus_original_POST",{}).get("fully_verified_complete_original_3VC"),
          "ERROR",record.get("error"),flush=True)
    return record
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    freeze=json.loads(Path(a.freeze).read_text())
    if freeze["schema"]!="neumann.q3.v31_twelve_new_source_body_unopened_actual_PCA_inductive_conservation.v1":
        raise RuntimeError("HISTORIC_FIRST_SHA_SOURCE_LOCK_CHANGED")
    originals=freeze["cases"]
    assert len(originals)==12
    rows=[one(Path(a.root),item) for item in originals]
    count=lambda key:sum(q.get(key,{}).get("fully_verified_complete_original_3VC",False) for q in rows)
    report={
      "schema":"neumann.q3.v32_true_original_posthoc_actual_learned_conservation_to_full_safety.v1",
      "original_source_count":len(rows),
      "all_program_source_bodies_ALREADY_OPENED_by_PR401":True,
      "original_correctness_only_Z3_cvc5_complete_native_three_VCs":True,
      "post_only_3VC":count("POST_only_already_exact_original_dual"),
      "basic_no_learn_Post_3VC":count("simple_NOLEARN_plus_original_POST"),
      "trained_PCA_plus_Post_3VC":count("TRAINED_PCA_plus_original_POST"),
      "classical_exact_nullspace_plus_Post_3VC":count("EXACT_CLASSICAL_plus_original_POST"),
      "bounded_gain_vs_basic_nofit":sum(q.get("trained_full_3VC_success_not_no_learn",False) for q in rows),
      "bounded_gain_vs_equal_classical_exact":sum(q.get("trained_full_3VC_success_not_exact_classical",False) for q in rows),
      "no_claim_of_firstblind_complete_post_experiment":True,
      "no_machine_learning_unique_versus_strongest_classical_claim":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "real_originals":rows
    }
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("post_only_3VC","basic_no_learn_Post_3VC","trained_PCA_plus_Post_3VC",
              "classical_exact_nullspace_plus_Post_3VC","bounded_gain_vs_basic_nofit",
              "bounded_gain_vs_equal_classical_exact"):
        print("LEARNED_ORIGINAL_FULL_POST_3VC",k,report[k])
    print("GLOBAL_Q3_OPEN")
if __name__=="__main__":main()
