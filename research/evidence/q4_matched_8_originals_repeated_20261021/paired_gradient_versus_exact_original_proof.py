"""Q4 paired controlled 3-repeat same-source cost comparison.

Actual previously opened 8 SyGuS originals, fixed exact source SHA,
same source Pre+Trans sampling, polynomial basis, original Z3/cvc5 3VC and
Z3-SPACER fallback. Only difference: gradient 6500 steps vs exact rational
equation solve for coefficients, with identical source and certificates.
Both method routes REALLY EXECUTE, not an offline union; AB/BA alternating.
Per-route costs include identical original preprocessing allocated to each.
Results are scoped to prior-opened sources and chosen bounded grammar.
"""
from __future__ import annotations
import argparse,hashlib,json,statistics,time
from pathlib import Path
import numpy as np
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native,dual)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    native_pdr,DUAL_S)
from research.evidence.q3_precondition_transition_joint_20261021.actual_model_precondition_conditioned_structure import (
    original_samples,operator_basis,numeric_poly,same_math_classical,evaluate_candidate)
from research.evidence.q3_raw_transition_nonlinear_20261021.learned_original_source_nonlinear_AST import fit
def ms(t):return (time.perf_counter_ns()-t)/1e6
def candidate_arrays(n,anchor,degree,X,Y,pres,init):
    B=operator_basis(n,anchor,degree)
    if not B or len(B)>20:return None
    D=np.asarray([[numeric_poly(y,b)-numeric_poly(x,b) for b in B]
                  for x,y in zip(X,Y)],dtype=float)
    d=np.asarray([int(y[anchor])-int(x[anchor]) for x,y in zip(X,Y)],dtype=float)
    P=np.asarray([[numeric_poly(q,b)-numeric_poly(init,b) for b in B]
                   for q in pres],dtype=float)
    p=np.asarray([int(q[anchor])-int(init[anchor]) for q in pres],dtype=float)
    A=np.vstack([D,P]);rhs=-np.concatenate([d,p])
    if max(np.max(np.abs(A)),np.max(np.abs(rhs)))>1e9:return None
    return B,A,rhs
def route(kind,src,native,vals,init,pres,seed):
    t=time.perf_counter_ns()
    n=len(src["now"]);X=[q[:n] for q in vals];Y=[q[n:] for q in vals]
    count=0;fit_ms=0;verify_ms=0;mat_ms=0
    result={"route":kind,"certified":False,"winner":None,"zero_neural":kind=="exact","methods":[]}
    for anchor in range(min(n,3)):
        if result["certified"]:break
        for degree in (1,2,3):
            st=time.perf_counter_ns()
            arrays=candidate_arrays(n,anchor,degree,X,Y,pres,init)
            mat_ms+=ms(st)
            if arrays is None:continue
            B,A,rhs=arrays;count+=1
            t0=time.perf_counter_ns()
            if kind=="learned":
                # Fit from same A*c=rhs; fit() expects differences ending
                # with fixed anchor delta, so last column is -rhs.
                params,_,residual=fit(np.column_stack([A,-rhs]),seed+anchor*17+degree)
                co=np.rint(params[:-1]).astype(int)
                admissible=(np.max(np.abs(params[:-1]-co))<.075
                           and np.max(np.abs(co))<=20)
                c=co.tolist() if admissible else None
            elif kind=="exact":
                c,_=same_math_classical(A,rhs)
                residual=0 if c is not None else None
            else:raise AssertionError("METHOD_NOT_ALLOWED")
            fit_ms+=ms(t0)
            proof=None
            if c is not None:
                t1=time.perf_counter_ns()
                proof=evaluate_candidate(src,native,anchor,B,c,init)
                verify_ms+=ms(t1)
            certified=bool(proof and proof["exactly_full_source_3VC_proved"])
            result["methods"].append(dict(anchor=anchor,degree=degree,coefficients=c,
                  source_exact_original_3VC=proof,
                  candidate_certified=certified,learner_numeric_residual=residual))
            if certified:
                result["certified"]=True;result["winner"]=kind
                break
    result["coefficient_trials"]=count
    result["matrix_construction_ms"]=mat_ms
    result["coefficient_fit_or_exact_solve_ms"]=fit_ms
    result["independent_original_candidate_proof_ms"]=verify_ms
    if not result["certified"]:
        t2=time.perf_counter_ns()
        pdr=native_pdr(src,native)
        result["Z3_SPACER_native_source"]=pdr
        result["PDR_ms"]=ms(t2)
        if pdr["certified"]:
            result["certified"]=True;result["winner"]="Z3_SPACER"
    result["post_preprocessing_route_wall_ms"]=ms(t)
    return result
def run_one(root,item,repeat,index):
    st=time.perf_counter_ns()
    raw=(root/item["path"]).read_bytes()
    if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
        raise RuntimeError("SOURCE_IDENTITY_DRIFT")
    forms=sexprs(raw)
    forms=[x for x in forms if not(isinstance(x,list) and x and x[0]=="declare-primed-var")]
    src=compile_typed_original(forms);native=compile_independent_native(forms,src)
    parity={k:dual(z3.Xor(src[k],native[k]),"unsat",DUAL_S) for k in ("pre","trans","post")}
    if not all(x["dual_pass"] for x in parity.values()):
        raise RuntimeError("ORIGINAL_NATIVE_SOURCE_MISMATCH")
    vals,init,pres=original_samples(src,native)
    prep_ms=ms(st)
    if len(vals)<16:raise RuntimeError("ORIGINAL_TRANS_SAMPLES_TOO_FEW")
    order=["learned","exact"] if (repeat+index)%2==0 else ["exact","learned"]
    r={}
    for kind in order:r[kind]=route(kind,src,native,vals,init,pres,20261021+index)
    for key in r:
        r[key]["preprocess_ms_charged"]=prep_ms
        r[key]["full_original_source_processing_ms"]=prep_ms+r[key]["post_preprocessing_route_wall_ms"]
    if not all(v["certified"] for v in r.values()):
        raise RuntimeError("A_METHOD_LACKS_FULL_NATIVE_CERTIFICATE")
    return {"original":item["path"],"git_blob":item["git_blob"],"repeat":repeat,
            "same_source_preparation_ms":prep_ms,"alternating_method_order":order,
            "learned":r["learned"],"exact":r["exact"]}
def main():
    ap=argparse.ArgumentParser()
    for n in ("root","freeze","out"):ap.add_argument("--"+n,required=True)
    args=ap.parse_args();f=json.loads(Path(args.freeze).read_text())
    assert f["schema"]=="neumann.q3.external_real_8_PREBODY_SHA_V1"
    cases=f["cases"];assert len(cases)==8
    rows=[]
    for repeat in range(3):
        for index,item in enumerate(cases):
            row=run_one(Path(args.root),item,repeat,index)
            rows.append(row)
            print("PAIRED_TRUE_ORIGINAL_Q4",repeat,item["path"],"ORDER",
                  row["alternating_method_order"],"LEARNED_MS",
                  round(row["learned"]["full_original_source_processing_ms"],3),
                  "EXACT_MS",round(row["exact"]["full_original_source_processing_ms"],3),
                  "WINNERS",row["learned"]["winner"],row["exact"]["winner"],flush=True)
    groups=[]
    for rep in range(3):
        subset=[q for q in rows if q["repeat"]==rep]
        l=sum(q["learned"]["full_original_source_processing_ms"] for q in subset)
        e=sum(q["exact"]["full_original_source_processing_ms"] for q in subset)
        groups.append(dict(repetition=rep,full_learned_route_ms=l,
                           full_exact_route_ms=e,
                           learned_divided_by_exact=l/e))
    report=dict(schema="neumann.q4.three_repeat_original8_matched_learner_vs_exact_pretrans_portfolio.v1",
      original_prebody_sha_frozen=True,
      scope="POSTHOC SAME TWO SOURCE CORPORA, PAIRED WITHIN ORIGINAL AND ALTERNATING ORDER",
      source_originals_per_repeat=8,paired_repetitions=3,total_paired_method_trials=len(rows),
      learned_certified_full_original_3vc=sum(z["learned"]["certified"] for z in rows),
      exact_certified_full_original_3vc=sum(z["exact"]["certified"] for z in rows),
      unchanged_original_source_preprocess_charged_to_each_route=True,
      same_observed_original_pre_and_trans_data_for_both_routes=True,
      identical_independent_native_Z3_and_cvc5_original_goal_proof_for_both=True,
      same_original_Z3_SPACER_fallback_for_both=True,
      real_method_repeated_experiments=groups,
      ratio_of_three_repeat_wall_sums=sum(z["full_learned_route_ms"] for z in groups)/
          sum(z["full_exact_route_ms"] for z in groups),
      learned_over_exact_ratio_median_repetition=statistics.median(
          z["learned_divided_by_exact"] for z in groups),
      original_fit_coefficient_only_same_fixed_operator_vocabulary=True,
      learning_not_unique_vs_strong_exact_classical=True,
      does_not_include_pretraining_shared_across_future_tasks=True,
      total_hardware_energy_gpu_10x_claim_not_proven=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",source_runs=rows)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PAIRED_REAL_Q4_COMPLETE",len(rows),flush=True)
    print("PAIRED_REAL_Q4_SCOPED_SPEED_RATIO",report["ratio_of_three_repeat_wall_sums"],flush=True)
    print("PAIRED_REAL_Q4_NO_LEARNED_UNIQUE_Q3",flush=True)
if __name__=="__main__":main()
