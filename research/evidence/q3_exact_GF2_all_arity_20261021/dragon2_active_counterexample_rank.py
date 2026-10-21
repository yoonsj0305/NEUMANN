"""Q3 DRAGON_2: active, source-authentic counterexample-guided GF(2) rank closure.

Scientific scope: an already OPENED SyGuS original and an already proved rank-3
low-arity inductive basis. This can close that program's affine XOR *upper
bound* by finding genuine source Pre/Pre+Trans states, NOT by assuming samples
are inductive. No model learning, no new author-family transfer, no global Q3.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import z3

from research.evidence.q3_exact_GF2_all_arity_20261021.first_source_64_observation_exact_nullspace import (
    ORIGINS, UPSTREAM, blob, sha, sexprs, compile_typed_original,
    compile_independent_native, dual, samples, nullspace_matrix,
    add_pivot, gf2_in_span, candidate_original_native,
    independent_original_2vc, elapsed,
)

PRIOR_SHA = "a9a3481c04a6cd5bbdcb310bcc416482ae29a5cde2cbc17de636b1ce7884fe43"
EXPECTED_PREVIOUS_FULL_NULLITY = 6
MAX_WITNESSES = 24

def proof_vector(cert, eligible):
    idx = [eligible.index(i) for i in cert["original_state_bool_coordinates"]]
    mask = sum(1 << i for i in idx)
    offset = int(cert["xor_equals"])
    if not mask or offset not in (0, 1):
        raise RuntimeError("INVALID_AUTHENTIC_CERTIFICATE_VECTOR")
    return mask | (offset << len(eligible))

def vector_parts(vector, n):
    return vector & ((1 << n) - 1), (vector >> n) & 1

def witness(original, eligible, vec, depth):
    """Find an actual length-depth native-original path refuting a parity.

    A single set of source auxiliary/nondet inputs is SHARED across all steps:
    this intentionally under-approximates potentially fresher per-step inputs.
    Thus a SAT path is authentic, while UNSAT is never taken as full unbounded
    reachability proof. Only SAT witnesses can shrink the GF2 upper bound.
    """
    mask, off = vector_parts(vec, len(eligible))
    candidate = candidate_original_native(original, eligible, mask, off)
    states = [original["now"], original["next"]]
    for d in range(2, depth + 1):
        states.append([z3.Const("_neumann_q3_depth_%d_state_%d" % (d, i), v.sort())
                       for i, v in enumerate(original["now"])])
    constraints = [original["native_pre"]]
    for d in range(depth):
        sub = list(zip(original["now"], states[d]))
        sub += list(zip(original["next"], states[d + 1]))
        constraints.append(z3.substitute(original["native_trans"], *sub))
    target = z3.substitute(candidate, *list(zip(original["now"], states[depth])))
    formula = z3.And(*(constraints + [z3.Not(target)]))
    s = z3.Solver()
    s.set(timeout=10000)
    s.add(formula)
    verdict = s.check()
    if verdict == z3.unknown:
        return {"status": "UNKNOWN", "reason":s.reason_unknown(), "depth":depth}
    if verdict == z3.unsat:
        return {"status": "UNSAT", "depth":depth}
    model = s.model()
    observed_states = states[depth]
    bits = [int(z3.is_true(model.eval(observed_states[i], model_completion=True))) for i in eligible]
    if ((mask & sum(int(b) << j for j,b in enumerate(bits))).bit_count() % 2) == off:
        raise RuntimeError("RETURNED_MODEL_DOES_NOT_REFUTE_FORMULA")
    replay = z3.Solver()
    replay.set(timeout=10000)
    replay.add(*constraints)
    for i,b in zip(eligible,bits):
        replay.add(observed_states[i] == z3.BoolVal(bool(b)))
    rv = replay.check()
    if rv != z3.sat:
        raise RuntimeError("ORIGINAL_NATIVE_MULTISTEP_WITNESS_NOT_REPLAYABLE_" + str(rv))
    return {"status":"SAT_AUTHENTIC", "depth":depth, "bits":bits,
            "observed_sha256":sha(bytes(bits))}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--prior",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    started=time.perf_counter_ns()
    raw_previous=args.prior.read_bytes()
    if sha(raw_previous)!=PRIOR_SHA:
        raise RuntimeError("IMMUTABLE_PREVIOUS_SOURCE_CERTIFICATE_SHA_MISMATCH")
    prev=json.loads(raw_previous)
    if prev["original_first_learned_2VC"]!="0/2_PRESERVED" or prev["global_Q3"]!="OPEN":
        raise RuntimeError("PRIOR_FAILURE_OR_Q3_SCOPE_WAS_REWRITTEN")
    prior_case=next(x for x in prev["actual_original_sources"] if "DRAGON_2.lus.sl" in x["source"])
    if prior_case["source_original_certified_2VC_low_arity_rank"]!=3:
        raise RuntimeError("PRIOR_TRUE_INDUCTIVE_RANK3_NOT_CERTIFIED")
    if prior_case["previous_actual_source_sample_full_GF2_nullity"]!=EXPECTED_PREVIOUS_FULL_NULLITY:
        raise RuntimeError("HISTORICAL_ACTUAL_64_STATE_GF2_DIMENSION_MISMATCH")
    source_path,expected_blob=next(o for o in ORIGINS if "DRAGON_2.lus.sl" in o[0])
    source_data=(args.root/source_path).read_bytes()
    if blob(source_data)!=expected_blob:
        raise RuntimeError("AUTHENTIC_ORIGINAL_GIT_BLOB_MISMATCH")
    parsed=compile_typed_original(sexprs(source_data))
    native=compile_independent_native(sexprs(source_data),parsed)
    checks={field:dual(z3.Xor(parsed[field],native[field]),"unsat",10)
            for field in ("pre","trans","post")}
    if not all(c["dual_pass"] for c in checks.values()):
        raise RuntimeError("SOURCE_NATIVE_TYPED_3_PREDICATE_DUAL_PARITY_FAILED")
    original={**parsed,**native,
              "native_pre":native["pre"],"native_trans":native["trans"]}
    post_vars={str(v) for v in z3.z3util.get_vars(native["post"])}
    eligible=[i for i,(_,sort) in enumerate(parsed["states"])
              if sort=="Bool" and str(parsed["now"][i]) not in post_vars]
    if eligible!=prior_case["original_boolean_eligible_indices"]:
        raise RuntimeError("ELIGIBLE_STATE_SCOPE_CHANGED")
    n=len(eligible)
    proof_basis={}
    certificates=[]
    for cert in prior_case["every_observed_consistent_low_arity_source_certificate"]:
        if not cert["individually_inductive_source_program"]:
            continue
        if not cert["native_original_dual_2VC"]["full_two_vc_dual_original"]:
            raise RuntimeError("PREVIOUS_CERTIFICATE_IS_NOT_DUAL_ORIGINAL")
        vec=proof_vector(cert,eligible)
        if add_pivot(proof_basis,vec):
            candidates=vector_parts(vec,n)
            fresh=independent_original_2vc(original,candidate_original_native(original,eligible,*candidates))
            if not fresh["full_two_vc_dual_original"]:
                raise RuntimeError("REPLAY_INDUCTIVE_ORIGINAL_CERTIFICATE_FAILED")
            certificates.append({"source_state_indices":cert["original_state_bool_coordinates"],
                                 "xor_equals":cert["xor_equals"],
                                 "fresh_original_z3_cvc5_2VC":fresh})
    if len(proof_basis)!=3:
        raise RuntimeError("INDEPENDENT_ORIGINAL_PROVED_RANK3_NOT_REPLAYED")
    rows,source_sample_receipts=samples(original,eligible)
    if len(rows)!=64:
        raise RuntimeError("AUTHENTIC_INITIAL_SOURCE_SAMPLE_NOT_64")
    if not all(
        (sum(bits[i] for i in range(n) if (vec>>i)&1)%2)==((vec>>n)&1)
        for bits in rows for vec in proof_basis.values()
    ):
        raise RuntimeError("ACTUAL_SOURCE_OBSERVATION_CONTRADICTS_PROVEN_2VC")
    events=[]
    seen={tuple(v) for v in rows}
    initial_distinct_count=len(seen)
    initial_nullity=len(nullspace_matrix(rows,n)[1])
    status="ABSTAIN_NOT_CONVERGED"
    for it in range(MAX_WITNESSES+1):
        _,kernel=nullspace_matrix(rows,n)
        if len(kernel)<len(proof_basis):
            raise RuntimeError("ORIGINAL_PROVED_RANK_EXCEEDS_SOURCE_OBSERVATION_NULLITY")
        if len(kernel)==len(proof_basis):
            if not all(gf2_in_span(proof_basis,v) for v in kernel):
                raise RuntimeError("EQUAL_RANK_BUT_NOT_SAME_SPAN")
            status="PASS_ACTUAL_PROGRAM_ALL_ARITY_AFFINE_GF2_CLOSURE"
            break
        if it>=MAX_WITNESSES:
            status="ABSTAIN_WITNESS_CAP"
            break
        residual=next((v for v in kernel if not gf2_in_span(proof_basis,v)),None)
        if residual is None:
            raise RuntimeError("UNEXPLAINED_NULLITY_WITH_NO_RESIDUAL")
        results=[]
        hit=None
        for depth in range(5):
            result=witness(original,eligible,residual,depth)
            results.append({k:v for k,v in result.items() if k!="bits"})
            if result["status"]=="SAT_AUTHENTIC":
                hit=result
                break
        if hit is None:
            status="ABSTAIN_NO_AUTHENTIC_COUNTEREXAMPLE_UP_TO_DEPTH4"
            events.append({"iteration":it,"kernel_nullity":len(kernel),
                           "residual_vector_hex":hex(residual),"solver_results":results})
            break
        if tuple(hit["bits"]) in seen:
            raise RuntimeError("WITNESS_ALREADY_IN_SPAN_SAMPLES")
        seen.add(tuple(hit["bits"]))
        rows.append(hit["bits"])
        new_nullity=len(nullspace_matrix(rows,n)[1])
        if new_nullity>=len(kernel):
            raise RuntimeError("NEW_SOURCE_WITNESS_DID_NOT_REDUCE_GF2_NULLITY")
        events.append({"iteration":it,"nullity_before":len(kernel),
                       "nullity_after":new_nullity,"refuted_residual_hex":hex(residual),
                       "witness_depth":hit["depth"],"witness_sha256":hit["observed_sha256"],
                       "solver_results":results})
    final_nullity=len(nullspace_matrix(rows,n)[1])
    out={"schema":"neumann.q3.original.DRAGON2.active_GF2_counterexample_rank.v1",
         "status":status,"source":source_path,"upstream":UPSTREAM,"git_blob":expected_blob,
         "previous_receipt_sha256":PRIOR_SHA,
         "previous_first_learned_original_2VC":"0/2_PRESERVED",
         "previous_original_observation_nullity":EXPECTED_PREVIOUS_FULL_NULLITY,
         "fresh_verified_inductive_basis_rank":len(proof_basis),
         "fresh_initial_source_64_sample_nullity":initial_nullity,
         "final_source_counterexample_enriched_nullity":final_nullity,
         "all_arity_affine_original_closed":status.startswith("PASS_"),
         "source_authentic_observations":len(rows),
         "new_independent_counterexample_witnesses":len(seen)-initial_distinct_count,\n         "native_bounded_reachability_depth_cap":4,
         "iterations":events,"fresh_proven_low_arity_certificates":certificates,
         "native_typed_original_semantics_z3_cvc5":checks,
         "sampling_receipts":source_sample_receipts,
         "source_specific_posthoc":True,"learned_unique_operator":"NOT_DEMONSTRATED",
         "full_original_safety_3VC":"NOT_CLAIMED",
         "global_Q3":"OPEN","Q4_global":"OPEN","Q7":"OPEN",
         "GPU_calls":0,"paid_API_calls":0,"wall_ms":elapsed(started)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("DRAGON2_ACTIVE_COUNTEREXAMPLE_CLOSURE",out["status"],
          "rank",initial_nullity,"=>",final_nullity,"proved_low",len(proof_basis),
          "counterexamples",out["new_independent_counterexample_witnesses"],
          "GLOBAL_Q3",out["global_Q3"],flush=True)

if __name__=="__main__":
    main()
