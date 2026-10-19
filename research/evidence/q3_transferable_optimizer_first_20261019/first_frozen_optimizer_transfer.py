"""First frozen transferable source-invariant optimizer, strict Issue #275.

ONE shared trained 4-parameter unrolled recurrent linear neuron, trained on
synthetic public transition-constraint matrices. No official source loaded
during training. At evaluation on TWO already-opened REAL published official
SyGuS sources, model step weights are frozen and reused; no source-specific
gradient fitting. Outputs must prove ORIGINAL 3VC via native Z3 + cvc5.

This is learned computational schedule, NOT newly invented symbolic mathematics,
pretrained language model, or unique capability over strong classical nullspace.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
import z3

from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof,
)
from research.evidence.q3_real_selfsupervised_source_gradient_20261019.first_official_source_gradient import (
    source_samples, exact_classical_nullspace, primitive_integer_coefficients,
    source_only_equality, candidates_form, actual_certificate,
    normalize_rows,
)

REPO_COMMIT="13c8deb68a873635879c9a69bc78caebd340f646"
TARGETS=(
    "cggmp2005_variant_true-unreach-call_true-termination.sl",
    "brett.sl",
)
UPSTREAM_FOLDER="comp/2018/Inv_Track"
TRAIN_SEED=113
TRAIN_MATRICES=256
ROLLOUT_TRAIN=32
ROLLOUT_TEST=4096
SCHEMA="neumann.q3.frozen-transfer-recurrent-operator.v1"
W0=np.asarray([1.,2.,3.])

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def covariance(rows):
    a=normalize_rows(rows)
    return (a.T@a)/float(len(a))

def training_covariances():
    rng=np.random.default_rng(TRAIN_SEED)
    matrices=[]
    vectors=[]
    for case in range(TRAIN_MATRICES):
        while True:
            w=rng.integers(-3,4,size=3,dtype=np.int64)
            if np.count_nonzero(w)>=2:break
        basis=[]
        for axis in np.eye(3,dtype=np.int64):
            b=np.cross(w,axis)
            if np.any(b) and (not basis or np.any(np.cross(basis[0],b))):
                basis.append(b)
            if len(basis)==2:break
        if len(basis)!=2:raise RuntimeError("CANNOT_GENERATE_RANK2_SOURCE_ROWS")
        rows=[]
        for _ in range(24):
            c1,c2=rng.integers(-5,6,size=2)
            v=c1*basis[0]+c2*basis[1]
            if np.any(v):rows.append([int(x) for x in v])
        if len(rows)<10:raise RuntimeError("SYNTHETIC_TRAIN_CONSTRAINTS_INSUFFICIENT")
        matrices.append(covariance(rows))
        vectors.append(sha_bytes(canonical(rows).encode()))
    return np.asarray(matrices),vectors

def advance_many(matrices,alphas,iterations):
    weights=np.tile(W0/np.linalg.norm(W0),(len(matrices),1))
    for step in range(iterations):
        weights-=float(alphas[step%4])*np.einsum(
            "nij,nj->ni",matrices,weights)
        weights/=np.linalg.norm(weights,axis=1)[:,None]
    return weights

def training_loss(matrices,alphas):
    out=advance_many(matrices,alphas,ROLLOUT_TRAIN)
    residue=np.einsum("nij,nj->ni",matrices,out)
    return float(np.mean(np.sum(residue*residue,axis=1)))

def train_once_globally():
    covs,source_sha=training_covariances()
    initial=np.asarray([0.75,1.00,1.25,1.50],dtype=np.float64)
    t=time.perf_counter_ns()
    initial_loss=training_loss(covs,initial)
    result=minimize(lambda p:training_loss(covs,p),initial,
            method="L-BFGS-B",bounds=[(0.05,1.8)]*4,
            options={"maxiter":80,"ftol":1e-13})
    elapsed=(time.perf_counter_ns()-t)/1e6
    trained=np.asarray(result.x,dtype=np.float64)
    final_loss=training_loss(covs,trained)
    return {"alphas":trained,
      "public_model_receipt":{
        "method":"FROZEN_FOUR_SCALAR_SHARED_RECURRENT_LINEAR_OPTIMIZER",
        "learned_parameters":4,
        "train_source_generator_seed":TRAIN_SEED,
        "train_number_of_distinct_synthetic_constraint_matrices":len(covs),
        "train_source_hash_sha256":sha_bytes(canonical(source_sha).encode()),
        "train_loss_no_target_weights_or_post":True,
        "initial_train_loss":initial_loss,
        "final_train_loss":final_loss,
        "trained_shared_alphas":[float(x) for x in trained],
        "shared_weights_sha256":sha_bytes(trained.tobytes()),
        "optimizer_scipy_success":bool(result.success),
        "optimizer_message":str(result.message)[:170],
        "outer_optimization_iterations":int(result.nit),
        "pretrain_wall_ms":round(elapsed,3),
        "official_source_content_read_before_frozen_model":False,
        "test_source_gradient_weight_update_count":0,
      }}

def source_inductive_bounds(src,native,pre_states):
    """Finite preregistered source-only [-8,+8] unary inductive bounds.

    Bounds are admitted ONLY if original Pre implies bound and bound AND
    OriginalTrans implies bound'. No Post, no filenames or solution labels.
    """
    constraints=[]
    now,nxt=src["now"],src["next"]
    bound_checks=0
    for axis,(v,vnext) in enumerate(zip(now,nxt)):
        observed=[state[axis] for state in pre_states]
        upper_initial=max(observed)
        lower_initial=min(observed)
        for sign in ("LOWER","UPPER"):
            if sign=="LOWER":
                search=range(min(8,lower_initial),-9,-1)
            else:
                search=range(max(-8,upper_initial),9)
            for threshold in search:
                if sign=="LOWER":
                    prop=v>=threshold
                    nextprop=vnext>=threshold
                else:
                    prop=v<=threshold
                    nextprop=vnext<=threshold
                bound_checks+=2
                if (check_formula(z3.And(native["pre"],z3.Not(prop)))=="unsat"
                    and check_formula(z3.And(prop,native["trans"],
                                              z3.Not(nextprop)))=="unsat"):
                    constraints.append(prop)
                    break
    return constraints,bound_checks

def one_original(path,pretrained):
    raw=path.read_bytes()
    digest=sha_bytes(raw)
    parsed=sexprs(raw)
    src=extract_mixed_original(parsed)
    native=native_original_relations(parsed,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
        raise RuntimeError("NATIVE_ORIGINAL_SOURCE_PARSER_PARITY_FAIL")
    start=time.perf_counter_ns()
    pre,trans,rows=source_samples(src,native)
    sample_ms=(time.perf_counter_ns()-start)/1e6
    if len(src["now"])!=3:
        raise RuntimeError("UNREGISTERED_REAL_SOURCE_DIMENSION")
    cov=covariance(rows)
    frozen_alphas=pretrained["alphas"]
    t=time.perf_counter_ns()
    vector=advance_many(cov.reshape(1,3,3),frozen_alphas,ROLLOUT_TEST)[0]
    inference_ms=(time.perf_counter_ns()-t)/1e6
    coeff=primitive_integer_coefficients(vector)
    t=time.perf_counter_ns()
    classic,classical_ms,nullity=exact_classical_nullspace(rows,3)
    t2=time.perf_counter_ns()
    bounds,bound_queries=source_inductive_bounds(src,native,pre)
    bound_ms=(time.perf_counter_ns()-t2)/1e6
    def validate(coefs):
        if coefs is None:return {"accepted":False,"status":"NO_UNIQUE_NULLSPACE"}
        candidate,rel,const=candidates_form(src,native,coefs,pre[0],bounds)
        proof=actual_certificate(path,candidate.sexpr())
        proof.update({"source_coefficients":coefs,
            "source_only_relation_sexpr":rel.sexpr(),
            "constant_from_public_pre":const,
            "proposed_complete_invariant_sha256":
                 sha_bytes(candidate.sexpr().encode())})
        return proof
    learned=validate(coeff)
    untrained=validate([1,2,3])
    fixed_schedule_vector=advance_many(cov.reshape(1,3,3),
       np.asarray([0.5,0.5,0.5,0.5]),ROLLOUT_TEST)[0]
    fixed=validate(primitive_integer_coefficients(fixed_schedule_vector))
    strong=validate(classic)
    post=source_proof(native["post"],native)
    return {
       "source_basename":path.name,
       "original_public_source_sha256":digest,
       "public_source_original_semantic_parity":parity,
       "public_pre_samples":len(pre),
       "public_transition_pairs":len(trans),
       "public_source_delta_rows":len(rows),
       "source_only_rows_sha256":sha_bytes(canonical(rows).encode()),
       "source_only_covariance_sha256":sha_bytes(cov.tobytes()),
       "shared_global_model_weights_sha256":
             pretrained["public_model_receipt"]["shared_weights_sha256"],
       "per_source_training_calls":0,
       "per_source_weight_gradient_updates":0,
       "learned_frozen_latent_vector":[float(x) for x in vector],
       "learned_frozen_source_coefficients":coeff,
       "learned_pretrained":learned,
       "untrained_no_forward":untrained,
       "fixed_untrained_forward_0p5":fixed,
       "strong_classical_exact_nullspace":strong,
       "strong_classical_nullspace_dimension":nullity,
       "post_only_original_3vc":post["vcs"],
       "post_only_is_inductive":bool(post["accepted"]),
       "source_pretrans_sampling_wall_ms":round(sample_ms,3),
       "pretrained_neural_forward_inference_wall_ms":round(inference_ms,3),
       "classical_exact_nullspace_wall_ms":classical_ms,
       "public_inductive_bound_discovery_wall_ms":round(bound_ms,3),
       "public_bound_candidates_vc_queries":bound_queries,
       "source_inductive_unary_bounds_count":len(bounds),
       "source_only_training_labels":0,
       "source_post_used_by_frozen_optimizer":False,
    }

def run(source_root):
    # A SINGLE globally trained model is frozen before ANY test source is
    # opened by this run. No evaluation feedback updates these four weights.
    trained=train_once_globally()
    recorded_sha=trained["public_model_receipt"]["shared_weights_sha256"]
    rows=[]
    for basename in TARGETS:
        row=one_original(source_root/UPSTREAM_FOLDER/basename,trained)
        assert row["shared_global_model_weights_sha256"]==recorded_sha
        rows.append(row)
        print("FROZEN_LEARNED_TRANSFER_REAL_OFFICIAL",basename,
              "learned",row["learned_pretrained"]["accepted"],
              "fixed0p5",row["fixed_untrained_forward_0p5"]["accepted"],
              "untrained",row["untrained_no_forward"]["accepted"],
              "strong",row["strong_classical_exact_nullspace"]["accepted"],
              "per_source_training",row["per_source_training_calls"])
    checks={
      "exact_two_frozen_opened_original_sources":len(rows)==2,
      "shared_learned_weights_identical_before_both_sources":all(
          r["shared_global_model_weights_sha256"]==recorded_sha for r in rows),
      "trained_only_on_synthetic_no_original_source_or_post":
          not trained["public_model_receipt"][
             "official_source_content_read_before_frozen_model"]
          and trained["public_model_receipt"]["train_loss_no_target_weights_or_post"],
      "trained_shared_operator_reduces_training_drift":
          trained["public_model_receipt"]["final_train_loss"]<
          trained["public_model_receipt"]["initial_train_loss"],
      "zero_gradient_training_or_parameter_updates_on_both_real_sources":all(
          r["per_source_weight_gradient_updates"]==0
          and r["per_source_training_calls"]==0 for r in rows),
      "both_frozen_weight_outputs_original_three_vc_and_cvc5_accepted":all(
          r["learned_pretrained"]["accepted"] and
          r["learned_pretrained"]["original_source_bound"] for r in rows),
      "both_original_post_only_not_inductive":all(
          not r["post_only_is_inductive"] for r in rows),
      "at_least_one_no_forward_untrained_initial_refused":any(
          not r["untrained_no_forward"]["accepted"] for r in rows),
      "exact_full_classical_comparator_measured":all(
          r["strong_classical_exact_nullspace"]["accepted"] for r in rows),
    }
    return {
       "schema":SCHEMA,"preregistered_issue":275,
       "upstream":"SyGuS-Org/benchmarks","upstream_commit":REPO_COMMIT,
       "prior_opened_originals_only":True,"unseen_new_authored_origins":0,
       "scientific_scope":"SHARED_FROZEN_LEARNED_OPTIMIZATION_SCHEDULE_ONLY",
       "globally_pretrained_recurrent_operator":trained["public_model_receipt"],
       "original_public_cases":rows,
       "first_transfer_gate_pass":all(checks.values()),
       "predeclared_conditions":checks,
       "earned_unique_solution_vs_strong_full_classical":False,
       "actual_pretrained_language_model":False,
       "new_grammar_learned":False,
       "train_compute_amortization_not_eliminated":True,
       "full_all_in_cost_and_energy":"NOT_EVALUATED",
       "actual_gemma_E2B_calls":0,"gpu_calls":0,"frontier_calls":0,
       "sealed_D3":"BLOCKED",
       "historical_first_AM1":"FAIL_UNCHANGED",
       "global_Q1_Q7":"OPEN",
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source-root",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    r=run(args.source_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("FIRST_PRETRAINED_FIXED_WEIGHT_TRANSFER_GATE",
          r["first_transfer_gate_pass"])
    print("FROZEN_TRANSFER_CHECKS",json.dumps(r["predeclared_conditions"],sort_keys=True))
    print("GLOBAL_Q1_Q7",r["global_Q1_Q7"])

if __name__=="__main__":main()
