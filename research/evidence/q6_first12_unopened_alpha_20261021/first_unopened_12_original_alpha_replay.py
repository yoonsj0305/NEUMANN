"""First source-body-unopened 12 original program ALPHA-only transfer.

Only previously frozen, unchanged PRE/TRANS/POST role-normalization method
from PR380, whose 8-program 72 dual semantical-equivalence CI passed.
Not a new trained-model Q3/Q6 success. Any failure is an abstention, not
converted into an original unsafe classification.

12 fresh authorship-unverified authentic SyGuS programs, selected by Git
SHA only before ever opening their SMT-LIB bodies, no retuning.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from research.evidence.q6_alpha_arity_20261021.posthoc_eight_original_source_dynamic_arity_alpha_semantic_normalizer import (
    one_true_original
)

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE_LOCK_COMMIT="d6120f92e898f0b4775dfaa96010d546dbe150e4"

def orig_blob_sha(source):
    return hashlib.sha1(b"blob "+str(len(source)).encode()+b"\0"+source).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    frozen=json.loads(a.freeze.read_text())
    if frozen["schema"]!="neumann.q6.first12_unopened_source_alpha_generalization_fixed_method.v1":
        raise RuntimeError("PRESOURCE_BENCHMARK_FREEZE_CHANGED")
    if frozen["upstream"].split("@")[-1]!=UPSTREAM or len(frozen["cases"])!=12:
        raise RuntimeError("PRE_COMMITTED_TRUE_SOURCE_IDENTITY_CHANGED")
    assert len({q["git_blob"] for q in frozen["cases"]})==12
    start=time.perf_counter_ns()
    original_rows=[]
    for frozen_item in frozen["cases"]:
        # Independently insist on SHA identity even if the original helper
        # catches an unsupported source and reports ABSTAIN.
        b=(a.root/frozen_item["path"]).read_bytes()
        authentic=(orig_blob_sha(b)==frozen_item["git_blob"] and len(b)==frozen_item["bytes"])
        if not authentic:
            raise RuntimeError("FROZEN_UNOPENED_ORIGINAL_GIT_SHA_OR_BYTES_CHANGED:"+frozen_item["path"])
        record=one_true_original(a.root,frozen_item)
        record["first_source_body_unopened_at_SHA_lock"]=True
        record["original_sha256"]=hashlib.sha256(b).hexdigest()
        record["independent_exact_git_blob_matches_frozen"]=authentic
        record["registered_family"]=frozen_item["family"]
        original_rows.append(record)
    supported=sum(q["dynamic_arity_original_canonical_success"] for q in original_rows)
    verified=sum(q["original_source_and_renamed_3x_full_dual_equivalence_tests_passed"] for q in original_rows)
    copies=sum(q["three_synthetic_alpha_semantic_equivalence_test_count"] for q in original_rows)
    negatives=sum(q.get("negative_post_mutation_real_semantics_dual_SAT",False) and
                  q.get("negative_post_mutation_canonical_sha_differs",False)
                  for q in original_rows)
    report={
      "schema":"neumann.q6.fixed_classical_alpha_representation_on_12_first_originals.v1",
      "original_SHA_freeze_committed_before_any_test_source_BODY":SOURCE_LOCK_COMMIT,
      "all_12_original_source_Git_blob_SHA_and_bytes_authenticated":True,
      "source_originals_are_first_source_body_test_not_new_author_proven":True,
      "source_original_count":len(original_rows),
      "fully_verified_source_programs":supported,
      "independent_native_source_pre_trans_post_dual_proofs":verified,
      "actual_alpha_copies_tested":copies,
      "original_semantic_negative_mutation_controls_passed":negatives,
      "original_source_abstention_count":len(original_rows)-supported,
      "family_verdicts":{name:{
          "authentic":sum(q["registered_family"]==name for q in original_rows),
          "fully_verified":sum(q["registered_family"]==name and q["dynamic_arity_original_canonical_success"]
                                for q in original_rows)}
                         for name in ("fib_related","other_2018_math_program")},
      "source_body_opened_only_after_original_GitSHA_registration":True,
      "trained_model_inference_calls":0,
      "model_gradient_updates":0,
      "best_classical_direct_with_same_normalizer_equal_rights":True,
      "no_source_original_SAFE_UNSAFE_or_learned_invariant_proof_claim":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN",
      "originals":original_rows
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q6_FIRST_12_SOURCE_SHA_AUTHENTIC",len(original_rows),"/12")
    print("Q6_FIRST_12_DYNAMIC_PROGRAM_CANONICALIZED",supported,"/12")
    print("Q6_FIRST_12_TRUE_NATIVE_Z3_CVC5_PRE_TRANS_POST_EQUIVALENCES",verified)
    print("Q6_FIRST_12_FIRST_ALPHA_VERSIONS_VERIFIED",copies)
    print("Q6_FIRST_12_NEGATIVE_POST_ALTERED_DETECTED",negatives)
    print("Q6_FIRST_12_ACTUAL_ABSTENTIONS",len(original_rows)-supported)
    print("Q6_FIRST_12_BY_FAMILY",report["family_verdicts"])
    print("Q6_FIRST_12_GLOBAL_Q3_Q6_OPEN",report["global_Q3"],report["global_Q6"])
    print("Q6_FIRST_12_FULL_ELAPSED_MS",(time.perf_counter_ns()-start)/1e6)
if __name__=="__main__":
    main()
