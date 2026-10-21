"""FIRST body-blind transfer of fixed PR393 actual trained relation miner.
Before ANY of eight original source bodies read, immutable original Git
blob metadata and fixed algorithm were committed. No source-specific retune.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import one
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,native_pdr,original_syguS
)
import research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio as classic

METADATA_COMMIT="d712b313d3ffa32b0d1cda20a9b1f9fe693f0901"
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
def sha_git(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def run(root,freeze,contract):
    if freeze["schema"]!="neumann.q3.first_unseen_eight_actual_CPU_invariant_training_benchmark_sha_lock_v1":
        raise RuntimeError("BEFORE_SOURCE_BODY_SHA_FREEZE_CHANGED")
    if contract["schema"]!="neumann.q3.preregistered_eight_source_first_body_CPU_discovery_no_retuning_v1":
        raise RuntimeError("BEFORE_SOURCE_MODEL_AND_BASELINE_CONTRACT_CHANGED")
    if contract["source_SHA_before_body_commit"]!=METADATA_COMMIT:
        raise RuntimeError("NEW_ORIGINAL_SHA_LOCK_COMMIT_CHANGED")
    if freeze["upstream"].split("@")[-1]!=UPSTREAM:raise RuntimeError("SOURCE_REPO_REVISION_CHANGED")
    selected=freeze["originals"]
    assert len(selected)==8 and len({q["git_blob"] for q in selected})==8
    assert sum(x["family"]=="fib" for x in selected)==4
    assert sum(x["family"]=="nonfib" for x in selected)==4
    # THIS IS THE FIRST SOURCE BODY ACCESS; check authentic Git SHA/bytes.
    for q in selected:
        b=(root/q["path"]).read_bytes()
        if len(b)!=q["bytes"] or sha_git(b)!=q["git_blob"]:
            raise RuntimeError("ORIGINAL_SHA_OR_BYTES_CHANGED:"+q["path"])
    classic.PDR_MS=5000
    out=[]
    for q in selected:
        record=one(root,q)
        record["original_Git_SHA_authenticated_prior_to_any_development_model_inference"]=True
        t=time.perf_counter_ns()
        reference={"cvc5_original_SyGuS":[],"Z3_SPACER":[],"status":"ABSTAIN_CLASSICAL_SOURCE"}
        try:
            raw,src,native,receipt=prepare(root,q)
            sygus=original_syguS(raw,src,native,2.0)
            pdr=native_pdr(src,native)
            reference={"cvc5_original_SyGuS":sygus,"Z3_SPACER":pdr,
                       "independent_original_native_identity":receipt,
                       "any_independently_original_dual_inductive_proof":bool(
                           sygus["certified"] or pdr["certified"]),
                       "status":"REAL_FULL_NATIVE_ORIGINAL_CLASSICAL_PORTFOLIO"}
        except Exception as e:
            reference["exception"]=type(e).__name__+":"+str(e)[:250]
        reference["full_source_original_preflight_classical_and_attempts_wall_ms"]=(time.perf_counter_ns()-t)/1e6
        record["strong_same_original_Z3_SPACER_and_cvc5_SyGuS_reference"]=reference
        out.append(record)
        print("Q3_FIRSTBLIND_ACTUAL_TRAINED",q["path"],
              "TRAINED",record.get("TRAINED_model_source_invariant",{}).get("fully_verified_complete_original_3VC"),
              "NOFIT",record.get("ZERO_TRAIN_equal_data_shallow_linear_Houdini",{}).get("fully_verified_complete_original_3VC"),
              "CLASSICAL",reference.get("any_independently_original_dual_inductive_proof"),
              "MODEL_STATUS",record["status"],flush=True)
    accepted=[r for r in out if r["status"]=="EXECUTED_TRAINED_VS_NO_FIT_NATIVE_SOURCE_3VC"]
    return {
      "schema":"neumann.q3.first_source_unopened_eight_actual_learned_affine_original_proofs.v1",
      "metadata_Git_SHA_frozen_before_source_BODY_commit":METADATA_COMMIT,
      "all_eight_original_SHA_authenticated":True,
      "new_genuine_originals":8,
      "actual_trained_learner_executed_count":sum(q.get("actually_trained_learned_numeric_relation_model",False) for q in out),
      "native_full_inductive_dual_trained_source_count":sum(q.get("TRAINED_model_source_invariant",{}).get("fully_verified_complete_original_3VC",False) for q in out),
      "native_full_inductive_dual_no_fit_source_count":sum(q.get("ZERO_TRAIN_equal_data_shallow_linear_Houdini",{}).get("fully_verified_complete_original_3VC",False) for q in out),
      "bounded_train_only_success_ablation":sum(q.get("training_model_unique_bounded_original_discovery",False) for q in out),
      "strong_source_classical_any_dual_certificate":sum(q.get("strong_same_original_Z3_SPACER_and_cvc5_SyGuS_reference",{}).get("any_independently_original_dual_inductive_proof",False) for q in out),
      "source_abstentions_or_caps":8-len(accepted),
      "all_unverified_cases_preserved":True,
      "same_source_benchmark_upstream_not_independent_authors":True,
      "source_specific_self_supervised_training_not_model_weight_generalization":True,
      "strong_equal_authority_learner_unique_vs_best_classical_UNPROVEN":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "all_originals":out
    }
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","contract","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    report=run(Path(a.root),json.loads(Path(a.freeze).read_text()),json.loads(Path(a.contract).read_text()))
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for k in ("new_genuine_originals","actual_trained_learner_executed_count",
              "native_full_inductive_dual_trained_source_count","native_full_inductive_dual_no_fit_source_count",
              "bounded_train_only_success_ablation","strong_source_classical_any_dual_certificate",
              "source_abstentions_or_caps"):
        print("FIRST_UNSEEN_EIGHT_ACTUAL_TRAINED_DISCOVERY",k,report[k])
    print("GLOBAL_Q3_Q4_Q6","OPEN")
if __name__=="__main__":main()
