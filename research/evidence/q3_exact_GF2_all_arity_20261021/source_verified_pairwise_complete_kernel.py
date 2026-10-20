"""Upgrade previously proven source-sample GF2 kernel closure to a stronger
actual ORIGINAL-program full inductive-2VC basis closure, *iff* rank matches.

Do not call sample-consistent pairwise equations program invariants without
independent native Z3 and pinned cvc5, 2 VCs each. First original 0/2 result
and earlier all-arity kernel proof raw SHA immutable. Pure classical audit.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import z3
from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    ORIGINS, UPSTREAM, sha, blob, sexprs, compile_typed_original,
    compile_independent_native, dual, samples, nullspace_matrix,
    sample_pairwise_basis, gf2_in_span, add_pivot,
    independent_original_2vc, candidate_original_native, elapsed
)
PREVIOUS_EXACT_ORIGINAL_JSON_SHA="e5764b1815947b0c4092be96e2ef0eebca7b81dfc3c65ff9da8e581175127fab"
SOURCE_ORIGINAL_FIRST_NEURAL_RUN=39514997383
SOURCE_ORIGINAL_ALL_ARITY_RUN=39515983812

def exact_source(root,path,sha1,previous):
    t=time.perf_counter_ns()
    rec={
      "source":path,"pinned_git_blob":sha1,
      "source_original_certified_2VC_low_arity_rank":0,
      "full_all_arity_inductive_GF2_covered_by_proved_low_arity":False,
      "status":"NOT_TESTED"
    }
    try:
        data=(root/path).read_bytes()
        if blob(data)!=sha1:raise RuntimeError("AUTHENTIC_GIT_BLOB_CHANGED")
        rec["real_source_sha256"]=sha(data)
        parsed=compile_typed_original(sexprs(data))
        native=compile_independent_native(sexprs(data),parsed)
        rec["actual_original_native_typed_parity"]= {
            k:dual(z3.Xor(parsed[k],native[k]),"unsat",8)
            for k in ("pre","trans","post")
        }
        if not all(x["dual_pass"] for x in rec["actual_original_native_typed_parity"].values()):
            raise RuntimeError("NATIVE_ORIGINAL_PREDICATE_PARITY_NOT_DUAL_CERTIFIED")
        original={**parsed,**native}
        post_used={str(v) for v in z3.z3util.get_vars(native["post"])}
        eligible=[i for i,(_,sort) in enumerate(parsed["states"])
                  if sort=="Bool" and str(parsed["now"][i]) not in post_used]
        if eligible!=previous["eligible_original_boolean_indices"]:
            raise RuntimeError("PREVIOUS_SOURCE_ELIGIBLE_VARIABLES_CHANGED")
        rec["original_boolean_eligible_indices"]=eligible
        rows,replay=samples(original,eligible)
        rec["source_sample_count"]=len(rows)
        rec["source_sampling"]=replay
        if len(rows)!=previous["observed_source_state_count"] or len(rows)!=64:
            raise RuntimeError("NOT_HISTORICAL_64_ORIGINAL_SAMPLES")
        n=len(eligible)
        observed_row_basis,fullnull=nullspace_matrix(rows,n)
        pair_basis,pair_report=sample_pairwise_basis(rows,n)
        if len(fullnull)!=previous["GF2_complete_affine_nullity"] or len(pair_basis)!=previous["observed_source_singleton_pairwise_span"]["GF2_pairwise_span_rank"]:
            raise RuntimeError("HISTORICAL_GF2_ORIGINAL_KERNEL_RANK_CHANGED")
        if len(fullnull)!=len(pair_basis) or not all(gf2_in_span(pair_basis,v) for v in fullnull):
            raise RuntimeError("EARLIER_EXACT_ALL_ARITY_CLOSURE_NO_LONGER_HOLDS")
        rec["complete_observed_source_GF2_nullity"]=len(fullnull)
        rec["source_observed_singleton_pairwise_span_rank"]=len(pair_basis)
        verified_basis={}
        outcomes=[]
        for width in (1,2):
            for columns in itertools.combinations(range(n),width):
                first=sum(rows[0][i] for i in columns)%2
                if any(sum(row[i] for i in columns)%2 != first for row in rows):
                    continue
                vector=sum(1<<i for i in columns)|(first<<n)
                expr=candidate_original_native(original,eligible,vector&((1<<n)-1),first)
                proof=independent_original_2vc(original,expr)
                certified=proof["full_two_vc_dual_original"]
                was_independent=add_pivot(verified_basis,vector) if certified else False
                outcomes.append({
                    "original_state_bool_coordinates":[eligible[i] for i in columns],
                    "arity":width,"xor_equals":first,"source_formula_SMT":expr.sexpr(),
                    "native_original_dual_2VC":proof,
                    "individually_inductive_source_program":certified,
                    "new_independently_proved_GF2_basis_direction":was_independent
                })
        rec["every_observed_consistent_low_arity_source_certificate"]=outcomes
        rec["source_original_certified_2VC_low_arity_rank"]=len(verified_basis)
        rec["number_of_source_checked_candidates"]=len(outcomes)
        rec["number_of_source_inductive_independently_dual_proved_low_arity"]=sum(
             v["individually_inductive_source_program"] for v in outcomes)
        rec["all_independently_source_proved_low_arity_in_nullspace"]=all(
             gf2_in_span(pair_basis,v) for v in verified_basis.values())
        rec["full_all_arity_inductive_GF2_covered_by_proved_low_arity"]=(
          len(verified_basis)==len(fullnull)
          and rec["all_independently_source_proved_low_arity_in_nullspace"]
          and all(gf2_in_span(verified_basis,v) for v in fullnull)
        )
        rec["status"]=(
            "ORIGINAL_INDUCTIVE_GF2_ALL_ARITY_FULLY_GENERATED_BY_INDEPENDENTLY_PROVED_LOW_ARITY_RELATIONS"
            if rec["full_all_arity_inductive_GF2_covered_by_proved_low_arity"]
            else "SOURCE_SAMPLED_GF2_COMPLETE_BUT_PROVED_LOW_ARITY_BASIS_INCOMPLETE"
        )
    except Exception as exc:
        rec["status"]="ABSTAIN_ORIGINAL_2VC_OR_BASIS_CHECK_ERROR"
        rec["error"]=type(exc).__name__+":"+str(exc)[:320]
    rec["case_wall_ms"]=elapsed(t)
    print("ORIGINAL_TRUE_LOW_ARITY_GF2",rec["source"],rec["status"],
          "CERTIFIED_BASIS_RANK",rec["source_original_certified_2VC_low_arity_rank"],
          "OBSERVED_FULL_NULLITY",rec.get("complete_observed_source_GF2_nullity"),
          "ERROR",rec.get("error"),flush=True)
    return rec

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    start=time.perf_counter_ns()
    historical=args.previous.read_bytes()
    if sha(historical)!=PREVIOUS_EXACT_ORIGINAL_JSON_SHA:
        raise RuntimeError("PREVIOUS_GF2_ORIGINAL_IMMUTABLE_RECEIPT_CHANGED")
    previous=json.loads(historical)
    assert previous["original_first_source_run"]==SOURCE_ORIGINAL_FIRST_NEURAL_RUN
    assert previous["source_specific_GF2_complete_closure_count"]==2
    assert previous["first_source_model_XOR4_2VC"]=="0/2_PRESERVED"
    cases=[exact_source(args.root,path,git,old)
           for (path,git),old in zip(ORIGINS,previous["original_sources"])]
    out={
        "schema":"neumann.q3.all_arity_affine_GF2_true_inductive_low_arity_original_basis.v1",
        "original_first_learned_run":SOURCE_ORIGINAL_FIRST_NEURAL_RUN,
        "original_first_learned_2VC":"0/2_PRESERVED",
        "first_source_all_arity_GF2_run":SOURCE_ORIGINAL_ALL_ARITY_RUN,
        "pinned_previous_raw_JSON_SHA256":PREVIOUS_EXACT_ORIGINAL_JSON_SHA,
        "source_already_opened_posthoc":True,
        "source_Git_revision":UPSTREAM,
        "two_real_original_source_git_blobs_authenticated":all("real_source_sha256" in r for r in cases),
        "full_actual_program_inductive_all_arity_GF2_basis_coverage_count":sum(
          r["full_all_arity_inductive_GF2_covered_by_proved_low_arity"] for r in cases),
        "first_neural_new_operator_exclusive":"NOT_DEMONSTRATED",
        "global_Q3":"OPEN","gate_R_full":"OPEN","gate_V":"OPEN","global_Q1_Q7":"OPEN",
        "source_original_published_safety_3VC_from_learned":"NOT_CLAIMED",
        "GPU_calls":0,"paid_API_calls":0,
        "whole_study_wall_ms":elapsed(start),"actual_original_sources":cases
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("TRUE_PROGRAM_GF2_ALL_ARITY_CLOSED",
          out["full_actual_program_inductive_all_arity_GF2_basis_coverage_count"],"/2")
    print("GLOBAL_Q3",out["global_Q3"])


if __name__=="__main__":
    main()
