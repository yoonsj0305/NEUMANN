"""First source-body-unopened twelve ORIGINAL program transfer of preexisting PCA
affine conservation learning and full original inductive 2VC dual checker.

Frozen source names, Git blobs, sizes at commit 9133aa8 BEFORE any of these
12 program bodies were opened. This file does not modify the previously
executed PCA fit, sampling, exact comparator, or independent verifier.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.evidence.q3_v31_proof_learned_conservation_20261021.verify_individual_PCA_learned_original_source_2VC import one

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE_LOCK="9133aa8909d051c9a1b33964d674877b049c4662"
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    frozen=json.loads(Path(a.freeze).read_text())
    if frozen["schema"]!="neumann.q3.v31_twelve_new_source_body_unopened_actual_PCA_inductive_conservation.v1":
        raise RuntimeError("ORIGINAL_SOURCE_SHA_FREEZE_SCHEMA_CHANGED")
    if frozen["upstream"].split("@")[-1]!=UPSTREAM or len(frozen["cases"])!=12:
        raise RuntimeError("ORIGINAL_UPSTREAM_REVISION_OR_SOURCE_COUNT_CHANGED")
    if not frozen["source_body_NOT_OPENED_before_original_Git_SHA_registration"]:
        raise RuntimeError("NOT_BLIND_SOURCE_COHORT")
    cases=frozen["cases"]
    if len({q["git_blob"] for q in cases})!=12:
        raise RuntimeError("DUPLICATE_NEW_ORIGINAL_GIT_BLOBS")
    # FIRST source body access, only after metadata freeze:
    for q in cases:
        raw=(Path(a.root)/q["path"]).read_bytes()
        if len(raw)!=q["bytes"] or blob(raw)!=q["git_blob"]:
            raise RuntimeError("NEW_ORIGINAL_GIT_BLOB_SHA_OR_BYTES_NOT_MATCHING_FROZEN:"+q["path"])
    result=[one(Path(a.root),q) for q in cases]
    report={
      "schema":"neumann.q3.first_unopened12_true_originals_actually_fitted_PCA_inductive_2VC.v1",
      "true_original_Git_SHA_before_source_body_commit":SOURCE_LOCK,
      "new_source_originals_SHA_verified":12,
      "native_source_pre_trans_post_authentically_loaded":sum("source_native_independently_authenticated" in r for r in result),
      "actually_fitted_CPU_PCA_originals":sum(r.get("actual_fitted_model",{}).get("real_CPU_PCA_model_fits",0)>0 for r in result),
      "first_unopened_originals_with_independent_learned_conservation_2VC":sum(r.get("actually_trained_model_found_true_original_conservation",False) for r in result),
      "individually_original_Z3_cvc5_proven_trained_conservation_expressions":sum(r.get("trained_true_conservation_count",0) for r in result),
      "first_unopened_originals_with_exact_classical_nullspace_2VC":sum(r.get("classical_exact_true_conservation_count",0)>0 for r in result),
      "invalid_or_abstain_count":sum(r["status"]!="COMPLETE_FITTED_CONSERVATION_REAL_ORIGINAL_2VC" for r in result),
      "SOURCE_FIRST_true_originals_and_bounded_generalization_only":True,
      "same_original_source_upstream_not_independent_author_claim":True,
      "per_program_fit_not_transfer_of_trained_model_weights":True,
      "same_data_exact_classical_comparator_has_equal_authority":True,
      "no_full_original_postcondition_3VC_claim":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "originals":result
    }
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    for k in ("new_source_originals_SHA_verified",
              "native_source_pre_trans_post_authentically_loaded",
              "actually_fitted_CPU_PCA_originals",
              "first_unopened_originals_with_independent_learned_conservation_2VC",
              "individually_original_Z3_cvc5_proven_trained_conservation_expressions",
              "first_unopened_originals_with_exact_classical_nullspace_2VC",
              "invalid_or_abstain_count"):
        print("FIRST_REAL_UNOPENED_PCA_SOURCE_DISCOVERY",k,report[k])
    print("Q3_GLOBAL_OPEN")
if __name__=="__main__":main()
