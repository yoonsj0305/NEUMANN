"""Q3 bounded finite grammar information theorem + zero-gradient proof-first actual original8.

For fixed feature functions phi_i(s), a source conditioned affine state
representation h(s)=s_anchor + sum_i c_i phi_i(s), and genuine source
transition observations (s,s') and original pre-state fiber p_j, exact
constraints are:
  sum_i c_i (phi_i(s')-phi_i(s)) = -(s'_anchor-s_anchor)
  sum_i c_i (phi_i(p_j)-phi_i(p_0)) = -(p_j_anchor-p_0_anchor).
So the ENTIRE zero-training-error candidate set is the rational affine
solution space A*c=b. Complete exact rational elimination characterizes ALL
such coefficient representations; numeric gradient cannot invent a primitive
outside supplied phi_i. This DOES NOT guarantee fastest synthesis or
global-source safety. Only original dual 3VC proves safety.

POSTHOC original eight already exposed in PR432/433. Matched same
source initial and transition samples and exact polynomial feature basis.
Run zero ML, attempt source-exact rational small grammar first; only on miss
run original native Z3-SPACER (and original cvc5 SyGuS if SPACER abstains).
All source identities, full native Z3+cvc5 original proofs, and wall costs
preserved. No claims of novel learned structure or superior frontier AI.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
import sympy as sp
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    original_syguS,native_pdr,DUAL_S
)
from research.evidence.q3_precondition_transition_joint_20261021.actual_model_precondition_conditioned_structure import (
    original_samples,operator_basis,numeric_poly,same_math_classical,evaluate_candidate
)
REV="13c8deb68a873635879c9a69bc78caebd340f646"
def ms(t):return (time.perf_counter_ns()-t)/1e6
def certify_exact_solution_space(A,bs,returned):
    t=time.perf_counter_ns()
    if A.shape[1]==0:raise RuntimeError("NO_NONTRIVIAL_GRAMMAR")
    if np.any(np.abs(A)>1e9) or np.any(np.abs(bs)>1e9):
        raise RuntimeError("GRAMMAR_INTEGER_OVERFLOW_CAP")
    ints=np.rint(A).astype(np.int64)
    vals=np.rint(bs).astype(np.int64)
    if not np.array_equal(A,ints) or not np.array_equal(bs,vals):
        raise RuntimeError("NOT_EXACT_INTEGER_SOURCE_SAMPLES")
    M=sp.Matrix(ints.tolist());v=sp.Matrix(vals.tolist())
    rank=M.rank()
    aug=M.row_join(v).rank()
    feasible=rank==aug
    dimension=M.cols-rank if feasible else None
    if returned is None:
        if feasible:raise RuntimeError("EXACT_SOLVER_MISSED_FEASIBLE_GRAMMAR")
    else:
        if not feasible:raise RuntimeError("EXACT_SOLVER_RETURNED_IMPOSSIBLE_GRAMMAR")
        c=sp.Matrix(list(returned))
        if M*c!=v:raise RuntimeError("CLASSICAL_COEFFICIENT_NOT_EXACT_SOURCE_MATCH")
    null=M.nullspace()
    if len(null)!=(dimension if feasible else M.cols-rank):
        raise RuntimeError("SOURCE_GRAMMAR_LINEAR_BASIS_DIMENSION_MISMATCH")
    if any(M*q!=sp.zeros(M.rows,1) for q in null):
        raise RuntimeError("EXACT_RATIONAL_NULLSPACE_INVALID")
    return dict(
       exact_source_constraint_equations=M.rows,
       feature_operator_count=M.cols,
       exact_rational_rank=rank,
       exact_rational_augmented_rank=aug,
       finite_grammar_sample_constraints_feasible=feasible,
       affine_rational_coefficient_solution_dimension=dimension,
       affine_nullspace_generators=len(null),
       exact_solution_space_basis_verified=True,
       returned_particular_solution_source_exact=(returned is not None),
       rank_and_membership_certificate_ms=ms(t))
def one(root,item):
    start=time.perf_counter_ns()
    result={"source":item["path"],"original_git_blob":item["git_blob"],
            "status":"ABSTAIN","neural_forwards":0,"ML_fit_count":0,"full_SAFE":False,
            "source_methods":[]}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or blob(raw)!=item["git_blob"]:
            raise RuntimeError("SOURCE_PREBODY_GIT_SHA_CHANGED")
        forms=sexprs(raw)
        primed=[x for x in forms if isinstance(x,list) and x and x[0]=="declare-primed-var"]
        clean=[x for x in forms if not (isinstance(x,list) and x and x[0]=="declare-primed-var")]
        if any(len(x)!=3 or x[2] not in ("Int","Bool") for x in primed):
            raise RuntimeError("ORIGINAL_PRIMED_DECLARATIONS_UNSUPPORTED")
        src=compile_typed_original(clean)
        native=compile_independent_native(clean,src)
        parity={key:dual(z3.Xor(src[key],native[key]),"unsat",DUAL_S)
                for key in ("pre","trans","post")}
        if not all(x["dual_pass"] for x in parity.values()):
            raise RuntimeError("TYPED_SOURCE_NATIVE_INDEPENDENT_PARSER_MISMATCH")
        result["native_original_PreTransPost_parity"]=parity
        t=time.perf_counter_ns()
        if any(q.sort().kind()!=z3.Z3_INT_SORT for q in src["now"]) or len(src["now"])>8:
            raise RuntimeError("UNSUPPORTED_STATE_SORT_OR_COUNT")
        vals,init,pres=original_samples(src,native)
        result["actual_original_transition_examples"]=len(vals)
        result["actual_original_initial_conditions"]=len(pres)
        result["original_sampling_ms"]=ms(t)
        if len(vals)<16:raise RuntimeError("INSUFFICIENT_SOURCE_SAMPLES")
        n=len(src["now"])
        X=np.asarray([z[:n] for z in vals],dtype=object)
        Y=np.asarray([z[n:] for z in vals],dtype=object)
        trials=[];certified=False
        t=time.perf_counter_ns()
        for anchor in range(min(n,3)):
            if certified:break
            for degree in (1,2,3):
                B=operator_basis(n,anchor,degree)
                if not B or len(B)>20:continue
                D=np.asarray([[numeric_poly(y,b)-numeric_poly(x,b) for b in B]
                              for x,y in zip(X,Y)],dtype=np.float64)
                dy=np.asarray([int(y[anchor])-int(x[anchor]) for x,y in zip(X,Y)],dtype=np.float64)
                Dpre=np.asarray([[numeric_poly(x,b)-numeric_poly(init,b) for b in B]
                                  for x in pres],dtype=np.float64)
                dypre=np.asarray([int(x[anchor])-int(init[anchor]) for x in pres],dtype=np.float64)
                A=np.vstack([D,Dpre]);rhs=-np.concatenate([dy,dypre])
                if max(np.max(np.abs(A)),np.max(np.abs(rhs)))>1e9:
                    trials.append(dict(anchor=anchor,degree=degree,status="SKIP_CAP"))
                    continue
                t0=time.perf_counter_ns()
                c,solver_ms=same_math_classical(A,rhs)
                exact=certify_exact_solution_space(A,rhs,c)
                original_proof=evaluate_candidate(src,native,anchor,B,c,init) if c is not None else None
                valid=bool(original_proof and original_proof["exactly_full_source_3VC_proved"])
                trials.append(dict(anchor=anchor,degree=degree,
                    exact_math_coefficient_solution_space=exact,
                    original_program_cvc5_Z3_full_3VC=original_proof,
                    candidate_exact_rational_coefficients=c,
                    classical_exact_solver_ms=solver_ms,
                    exact_synthesis_and_proof_wall_ms=ms(t0),
                    certified_full_source_SAFE=valid))
                if valid:
                    certified=True;result["winner"]="exact_rational_Pre_Trans_relation"
                    result["full_SAFE"]=True;break
        result["grammar_search_and_independent_original_proof_ms"]=ms(t)
        result["source_generic_grammar_analysis"]=trials
        result["candidate_basis_feasible_count"]=sum(q.get("exact_math_coefficient_solution_space",{}).get("finite_grammar_sample_constraints_feasible",False) for q in trials)
        result["candidate_exact_3VC_certified"]=sum(q.get("certified_full_source_SAFE",False) for q in trials)
        result["source_methods"].append(dict(route="source_exact_rational_grammar_no_ML",
                     wall_ms=result["grammar_search_and_independent_original_proof_ms"],
                     certified=result["full_SAFE"]))
        if not result["full_SAFE"]:
            t=time.perf_counter_ns()
            pdr=native_pdr(src,native)
            result["original_Z3_SPACER"]=pdr
            result["source_methods"].append(dict(route="original_Z3_SPACER",
                  wall_ms=ms(t),certified=pdr["certified"]))
            if pdr["certified"]:
                result["winner"]="original_Z3_SPACER";result["full_SAFE"]=True
            else:
                t=time.perf_counter_ns()
                sygus=original_syguS(raw,src,native,2.0)
                result["original_cvc5_SyGuS_2s"]=sygus
                result["source_methods"].append(dict(route="original_cvc5_SyGuS_2s",
                      wall_ms=ms(t),certified=sygus["certified"]))
                if sygus["certified"]:
                    result["winner"]="original_cvc5_SyGuS_2s";result["full_SAFE"]=True
        result["status"]="ORIGINAL_SAFE_COMPLETE_3VC" if result["full_SAFE"] else "ORIGINAL_UNKNOWN_NOT_CERTIFIED"
    except Exception as e:
        result["status"]="ABSTAIN_AUTHENTIC_SOURCE_OR_PARSER_OR_SOLVER"
        result["error"]=type(e).__name__+":"+str(e)[:350]
    finally:
        result["total_original_source_CPU_wall_ms"]=ms(start)
        print("Q3_ACTUAL_ZERO_GRADIENT_SOURCE_PROOF",result["source"],
              result["status"],"WINNER",result.get("winner"),
              "WALL",round(result["total_original_source_CPU_wall_ms"],3),
              "ERROR",result.get("error"),flush=True)
    return result
def main():
    ap=argparse.ArgumentParser()
    for k in ("root","freeze","out"):ap.add_argument("--"+k,required=True)
    args=ap.parse_args()
    frozen=json.loads(Path(args.freeze).read_text())
    if frozen["schema"]!="neumann.q3.external_real_8_PREBODY_SHA_V1":
        raise RuntimeError("ORIGINAL_PREBODY_SOURCE_FREEZE_CHANGED")
    originals=frozen["cases"]
    if len(originals)!=8 or len({o["git_blob"] for o in originals})!=8:
        raise RuntimeError("ORIGINAL_EIGHT_IDENTITY_NOT_FROZEN")
    rows=[one(Path(args.root),entry) for entry in originals]
    winners={route:sum(x.get("winner")==route for x in rows) for route in (
        "exact_rational_Pre_Trans_relation","original_Z3_SPACER","original_cvc5_SyGuS_2s")}
    report=dict(schema="neumann.q3.exact_span_dominance_8_originals_zero_neural_controller.v1",
      mathematical_contract="Fixed finite feature map and fixed anchor generate exact affine coefficient system A*c=b from original Pre and Trans samples. Exact rational particular plus nullspace completely characterizes the entire exact-fit coefficient set. This limits representational novelty of gradient coefficients, NOT relative global goal-solving time.",
      original_first_body_precommitted_git_SHA_manifest=True,
      present_experiment_posthoc_on_previously_opened_eight_originals=True,
      original_programs=len(rows),
      all_8_source_identity_independently_audited=sum("native_original_PreTransPost_parity" in q for q in rows),
      true_original_full_SAFE_independent_dual_Z3_cvc5=sum(q["full_SAFE"] for q in rows),
      true_original_UNKNOWN_or_abstained=sum(not q["full_SAFE"] for q in rows),
      winner_breakdown=winners,
      measured_source_to_proof_wall_ms_sum=sum(q["total_original_source_CPU_wall_ms"] for q in rows),
      measured_exact_grammar_synthesis_and_proof_wall_ms_sum=sum(q.get("grammar_search_and_independent_original_proof_ms",0) for q in rows),
      all_exact_nullspace_basis_memberships_proved=all(
          t["exact_math_coefficient_solution_space"]["exact_solution_space_basis_verified"]
          for q in rows for t in q.get("source_generic_grammar_analysis",[])
          if "exact_math_coefficient_solution_space" in t),
      source_exact_constraint_rank_audit_count=sum(
          "exact_math_coefficient_solution_space" in t
          for q in rows for t in q.get("source_generic_grammar_analysis",[])),
      all_originals_zero_neural_forwards=sum(q["neural_forwards"] for q in rows),
      all_originals_zero_model_fit=sum(q["ML_fit_count"] for q in rows),
      complete_online_controller_actually_executed=True,
      full_zero_neural_computation_is_not_a_learned_new_architecture=True,
      exact_linear_operator_span_cannot_be_exceeded_by_coefficient_fitting=True,
      amortized_learning_comparison_and_strongest_frontier_speed_10x_UNPROVEN=True,
      global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",all_source_receipts=rows)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("true_original_full_SAFE_independent_dual_Z3_cvc5","true_original_UNKNOWN_or_abstained",
              "winner_breakdown","source_exact_constraint_rank_audit_count",
              "measured_source_to_proof_wall_ms_sum"):
        print("Q3_EXACT_SPAN_DOMINANCE_RESULT",k,report[k],flush=True)
    print("GLOBAL_Q3_OPEN")
if __name__=="__main__":main()
