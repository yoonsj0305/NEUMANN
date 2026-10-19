"""Source-SHA-bound neural polynomial candidate and independent native Z3/cvc5 proof.

Q3 scientific interpretation: already opened original; generated algebraic relation
outside the old affine-only Gamma, but still within preset quadratic monomial
vocabulary, and a stronger exact classical source specialist solves the same.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from experiments.q3_source_prove import (sexprs,extract_mixed_original,
    native_original_relations,check_parity,check_formula,source_proof)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_learned_polynomial_generator_20261019.neural_generator import (
    train_once,source_example,polynomial)

SOURCE="benchmarks/NIA/2018.CHI_InvGame/gauss_sum-more-rows.auto.sl"
BLOB="a46943a0aacdfc418f5b57788d3b0b0015a815f1"
ACCEPT="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"

def digest(x):return hashlib.sha256(x).hexdigest()
def blob(x):return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def recover_verified_original_updates(native,now,nxt):
    # No gold coeffs: obtain four linearly independent PUBLIC transition models.
    # Source Trans must independently entail each exact inferred affine update.
    rows=[];targets=[]
    for values in itertools.product((-3,-1,0,1,2,4),repeat=len(now)):
        s=z3.Solver();s.set(timeout=3000)
        s.add(native["trans"])
        s.add(*[v==k for v,k in zip(now,values)])
        if s.check()!=z3.sat:continue
        m=s.model()
        delta=[m.eval(b-a,model_completion=True).as_long() for a,b in zip(now,nxt)]
        row=list(values)+[1]
        if sp.Matrix(rows+[row]).rank()>len(rows):
            rows.append(row);targets.append(delta)
        if len(rows)==len(now)+1:break
    if len(rows)!=len(now)+1:raise ValueError("PUBLIC_UPDATE_AFFINE_RANK_UNKNOWN")
    fit=sp.Matrix(rows).inv()*sp.Matrix(targets)
    for j in range(len(now)):
        if any(x.q!=1 for x in fit[:,j]):raise ValueError("NONINTEGER_AFFINE_UPDATE")
        expression=now[j]+sum((int(fit[k,j])*now[k] for k in range(len(now))),
                 z3.IntVal(int(fit[-1,j])))
        if check_formula(z3.And(native["trans"],nxt[j]!=expression))!="unsat":
            raise ValueError("UNVERIFIED_SOURCE_AFFINE_UPDATE")
    A=np.array([[int(fit[k,j]) for k in range(len(now))] for j in range(len(now))])
    b=np.array([int(fit[-1,j]) for j in range(len(now))])
    return A,b

def certify_actual_source(net,root):
    source=root/SOURCE;raw=source.read_bytes()
    if blob(raw)!=BLOB:raise ValueError("ORIGINAL_GIT_BLOB_MISMATCH")
    original=extract_mixed_original(sexprs(raw))
    native=native_original_relations(sexprs(raw),original)
    native.update({"now":original["now"],"next":original["next"]})
    parity=check_parity(original,native)
    if len(parity)!=3 or any(q!="unsat" for q in parity.values()):
        raise ValueError("SOURCE_NATIVE_CUSTOM_SEMANTICS_MISMATCH")
    if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
        raise ValueError("VACUOUS_ORIGINAL")
    now,nxt=original["now"],original["next"]
    if len(now)!=3 or original["num_bool"]!=0:raise ValueError("UNSUPPORTED_3INT_SOURCE")
    A,b=recover_verified_original_updates(native,now,nxt)
    features=np.r_[A.flatten(),b].astype("float64")
    started=time.perf_counter_ns()
    raw_prediction=net.predict(features[None,:])[0]
    coefficients=np.rint(raw_prediction).astype(int)
    inferred_ms=(time.perf_counter_ns()-started)/1e6
    relation=polynomial(coefficients,now,z3)==0

    # Identify small source-only individually inductive bounds without Post.
    # A learned equality alone need not be sufficient for the published safety
    # goal, so we permit the SAME helper for classical and neural candidates.
    bounds=[]
    for i,j in itertools.permutations(range(3),2):
        now_pred=now[i]<=now[j]+1
        next_pred=nxt[i]<=nxt[j]+1
        if (check_formula(z3.And(native["pre"],z3.Not(now_pred)))=="unsat" and
            check_formula(z3.And(now_pred,native["trans"],z3.Not(next_pred)))=="unsat"):
            bounds.append(now_pred)
    helper=z3.And(*bounds)
    candidate=z3.And(relation,helper)
    native_result=source_proof(candidate,native)
    external=check_original_candidate(source,candidate.sexpr(),
             expected_source_sha256=digest(raw))
    helper_only=source_proof(helper,native)
    source_zero=np.rint(net.predict(np.zeros((1,12)))[0]).astype(int)
    source_off=source_proof(z3.And(polynomial(source_zero,now,z3)==0,helper),native)

    # Strong exact source specialist, same public coefficients and helper.
    classical=[]
    for n,acc,counter in itertools.permutations(range(3)):
        if (int(b[counter])==1 and int(b[n])==0 and
            all(A[j,k]==(int(A[acc,counter]) if (j,k)==(acc,counter) else 0)
                for j in range(3) for k in range(3))):
            _,answer=source_example(int(A[acc,counter]),int(b[acc]),(n,acc,counter))
            classical.append((int(A[acc,counter]),int(b[acc]),answer))
    classical_proof=False
    if len(classical)==1:
        classical_proof=source_proof(
          z3.And(polynomial(classical[0][2],now,z3)==0,helper),native)["accepted"]

    cv=external.get("cvc5_original_three_vc") or {}
    gates={
      "original_semantics_three_xor_unsat":True,
      "exact_original_affine_update_independently_proved":True,
      "neural_generates_quadratic_outside_affine_gamma":any(
          int(coefficients[j]) for j in range(4,10)),
      "native_original_three_vc":bool(native_result["accepted"]),
      "external_cvc5_three_original_vc":external["status"]==ACCEPT and
          set(cv)=={"initial","consecution","post"} and
          all(x.get("status")=="unsat" and x.get("returncode")==0 for x in cv.values()),
      "source_only_helper_insufficient":not helper_only["accepted"],
      "strong_classical_expert_also_solves":classical_proof,
    }
    return {
      "source":SOURCE,"source_sha256":digest(raw),"source_git_blob":BLOB,
      "actual_source_original_affine_delta_A":A.tolist(),
      "actual_source_original_affine_delta_b":b.tolist(),
      "neural_predicted_polynomial_coefficients":coefficients.tolist(),
      "neural_raw_output":[round(float(x),6) for x in raw_prediction],
      "model_received_original_post":False,
      "model_trained_on_this_source":False,
      "original_native_bad_conditions":native_result["vcs"],
      "independent_cvc5_bad_conditions":cv,
      "zero_source_features_control":source_off["vcs"],
      "source_only_helper_control":helper_only["vcs"],
      "neural_inference_wall_ms":round(inferred_ms,3),
      "checks":gates,"posthoc_scoped_original_pass":all(gates.values())}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    model,learning=train_once()
    real=certify_actual_source(model,args.source_root)
    result={
      "schema":"neumann.q3.learned-polynomial-external-source-posthoc.v1",
      "posthoc_original_opened_before_architecture":True,
      "first_true_blind_3origin_gate":"FAIL_IMMUTABLE",
      "learning":learning,"external_original":real,
      "trained_neural_computes_new_coefficients":True,
      "novel_mathematical_primitive_absent_training_grammar":False,
      "neural_unique_over_strong_exact_classical":False,
      "independent_authored_source_family_transfer":False,
      "complete_cost_advantage":"NOT_PROVEN",
      "global_Q1_Q7":"OPEN","global_Q3":"OPEN","provider_frontier":"BLOCKED",
      "GPU_calls":0,"paid_model_calls":0}
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("CPU_TRAINED_MODEL",learning["holdout_exact_coefficient_vector"],"/132")
    print("SOURCE_ORIGINAL_NEURAL_POLYNOMIAL_VERIFIED",real["posthoc_scoped_original_pass"])
    print("GATES",json.dumps(real["checks"],sort_keys=True))
    print("Q3_GLOBAL",result["global_Q3"])
if __name__=="__main__":main()
