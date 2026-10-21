"""Historical PUBLIC externally found SAT witness for genuine original STC_0367.

This is a manually retrieved published witness, NOT learner discovery or
source-body-blind new NEUMANN Q3. Independently ground the complete actual
raw original SMT2 and require both native Z3 and cvc5 SAT. A known source
UNKNOWN under radius10000 is a search-bound miss, NEVER original UNSAT.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    structural_source,independent_original_grounded_certificate
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)
WITNESS=(-117360,-857002,857735)
SOURCE="non-incremental/QF_NIA/20220315-MathProblems/STC_0367.smt2"
SHA="01a8e86521634d522ee0a6b62024dc26e7ee5ac7"
SOURCE_BYTES=623
PUBLIC_REFERENCE="https://www.kaynet.or.jp/~kay/misc/aa3-1000.html"
COMMIT_BEFORE_SOURCE_VALIDATION="26eb550ea5afc51e7c700bbada63d1146fb5533b"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text())
    if c["schema"]!="neumann.q3.true_original_367_EXTERNAL_PUBLIC_SAT_oracle_reference_positive_v1":
        raise RuntimeError("EXTERNAL_REFERENCE_PROVENANCE_CONTRACT_CHANGED")
    if c["external_source_witness_minus_plus"]!=list(WITNESS) or c["true_original_file_git_blob"]!=SHA:
        raise RuntimeError("MANUALLY_CURATED_PUBLIC_WITNESS_OR_SOURCE_CHANGED")
    start=time.perf_counter_ns()
    record={"genuine_source_SHA_authenticated":False,
            "original_full_SMT2_independent_Z3_cvc5_SAT":False,
            "not_NEUMANN_learned_or_autonomous_discovery":True,
            "external_reference_URL":PUBLIC_REFERENCE,
            "external_reference_witness_inference_has_privileged_answer":True,
            "prior_mathematical_search_bound_10000_did_not_find_witness":True,
            "prior_bounded_UNKNOWN_remains_historically_unchanged":True,
            "status":"ABSTAIN"}
    try:
        b=(a.root/SOURCE).read_bytes()
        if len(b)!=SOURCE_BYTES or git_blob_sha1(b)!=SHA:
            raise RuntimeError("REAL_ORIGINAL_GIT_SHA_OR_SIZE_MISMATCH")
        record["genuine_source_SHA_authenticated"]=True
        record["real_source_SHA256"]=sha256(b)
        original_n,names,parsed=structural_source(b)
        record["true_original_integer_rhs"]=original_n
        exact=sum(v**3 for v in WITNESS)
        record["arbitrary_precision_integer_cubic_sum"]=exact
        record["witness_max_absolute_integer"]=max(abs(v) for v in WITNESS)
        if original_n!=367 or exact!=original_n:raise RuntimeError("PUBLIC_WITNESS_MATH_WRONG")
        # Independent original complete SMT2 actual source dual proof:
        proof=independent_original_grounded_certificate(
            b.decode("utf-8"),names,WITNESS,parsed,"SAT")
        record["complete_real_original_source_independent_Z3_cvc5_ground_proof"]=proof
        record["original_full_SMT2_independent_Z3_cvc5_SAT"]=proof["independent_dual_result"]
        record["status"]="KNOWN_PUBLISHED_PRIOR_WITNESS_TRUE_ORIGINAL_SAT_DUAL" if proof["independent_dual_result"] else "ABSTAIN_INCOMPLETE_ORIGINAL_DUAL_PROOF"
    except Exception as e:
        record["status"]="ABSTAIN_SOURCE_OR_CVC5_Z3_EXCEPTION"
        record["error"]=type(e).__name__+":"+str(e)[:380]
    record["full_external_witness_true_source_check_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    result={
       "schema":"neumann.q3.real_original_STC367_external_prior_reference_genuine_full_smt_sat.v1",
       "registered_prior_to_dual_original_verification_commit":COMMIT_BEFORE_SOURCE_VALIDATION,
       "externally_retrieved_existing_public_witness_NOT_NEUMANN_created":True,
       "original_first_source_previously_opened":True,
       "not_authenticated_as_learner_hidden_structure_discovery":True,
       "source_genuine_original_checked":record,
       "public_reference_not_a_new_math_result":PUBLIC_REFERENCE,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "no_auto_26_broker_backfill_without_second_combined_explicit_ablation":True
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("SOURCE367_ORIGINAL_SMT2_VERIFIED_EXTERNAL_PRIOR_SAT",record["original_full_SMT2_independent_Z3_cvc5_SAT"])
    print("SOURCE367_PUBLIC_ARBITRARY_INTEGER_CUBES_EXACT",record.get("arbitrary_precision_integer_cubic_sum"))
    print("SOURCE367_PUBLIC_EXTERNAL_IS_NOT_LEARNED_Q3",result["not_authenticated_as_learner_hidden_structure_discovery"])
    print("SOURCE367_STATUS",record["status"])
if __name__=="__main__":
    main()
