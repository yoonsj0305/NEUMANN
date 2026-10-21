"""First source SHA-frozen generic 0..3 bounded unsafe + validated safe portfolio.

BMC SAT never counts alone: ground EVERY time-indexed source state, replay
entire unmodified Pre, Trans*, and NotPost in Z3 and independent cvc5 SAT.
Safety only via actual native original 3VC UNSAT in BOTH independent solvers.
No target-specific formulas, no learned or frontier/Q3/Q4 claims.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    blob,sha,sexprs,compile_typed_original,compile_independent_native,dual,elapsed
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,original_syguS,native_pdr,negative_control
)

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FREEZE="8d31c884c45cac8b5955b1ff548f8c4305f3ae8e"
BMC_MAX_DEPTH=3
SAT_TIMEOUT_MS=2000
INDEPENDENT_SAT_TIMEOUT_S=10
FAST_SYGUS_BUDGET_S=0.75

def concrete_value(value,sort):
    if sort.kind()==z3.Z3_INT_SORT:
        return z3.IntVal(value.as_long())
    if sort.kind()==z3.Z3_BOOL_SORT:
        return z3.BoolVal(z3.is_true(value))
    raise RuntimeError("UNSUPPORTED_ORIGINAL_VARIABLE_SORT_FOR_TRACE")

def display_value(v):
    if z3.is_true(v):return True
    if z3.is_false(v):return False
    return int(v.as_long())

def construct_original_bmc(src,native,depth):
    curr,nxt=src["now"],src["next"]
    perstep=[
        [z3.Const(f"check_depth{depth}_t{t}_state{j}",v.sort())
         for j,v in enumerate(curr)]
        for t in range(depth+1)
    ]
    original_symbols=z3.z3util.get_vars(z3.And(native["pre"],native["trans"],native["post"]))
    member_names={str(x) for x in curr+nxt}
    extras=[v for v in original_symbols if str(v) not in member_names]
    def at(expression,step,has_next=False):
        replacements=list(zip(curr,perstep[step]))
        if has_next:replacements+=list(zip(nxt,perstep[step+1]))
        replacements +=[(v,z3.Const(f"check_depth{depth}_step{step}_aux{j}",v.sort()))
                        for j,v in enumerate(extras)]
        return z3.substitute(expression,*replacements)
    path=[at(native["pre"],0)]
    for t in range(depth):
        path.append(at(native["trans"],t,True))
    path.append(z3.Not(at(native["post"],depth)))
    return z3.And(*path),perstep

def bounded_original_bad_path(src,native):
    receipts=[]
    for depth in range(BMC_MAX_DEPTH+1):
        start=time.perf_counter_ns()
        formula,states=construct_original_bmc(src,native,depth)
        solver=z3.Solver()
        solver.set(timeout=SAT_TIMEOUT_MS,random_seed=0)
        solver.add(formula)
        ans=solver.check()
        row={"depth":depth,"original_source_BMC_result":str(ans)}
        if ans==z3.unknown:
            row["reason"]=solver.reason_unknown()
        if ans==z3.sat:
            m=solver.model()
            witness=tuple(tuple(concrete_value(m.eval(v,model_completion=True),v.sort())
                                for v in state) for state in states)
            grounded=z3.And(*[
                v==value for state,tuple_values in zip(states,witness)
                for v,value in zip(state,tuple_values)
            ])
            proof=dual(z3.And(formula,grounded),"sat",INDEPENDENT_SAT_TIMEOUT_S)
            row["actual_original_fully_grounded_trace_sat_Z3_cvc5"]=proof
            row["all_original_state_values_each_time"]=[
                [display_value(v) for v in vals] for vals in witness
            ]
            row["original_source_first_bad_trace_independently_proved"]=proof["dual_pass"]
            row["wall_ms"]=elapsed(start)
            receipts.append(row)
            if proof["dual_pass"]:
                return {"status":"UNSAFE_ORIGINAL_GROUND_SOURCE_PATH_DUAL",
                        "true_bounded_original_safety_refuted":True,
                        "witness_depth":depth,
                        "checked_depth_receipts":receipts}
        else:
            row["wall_ms"]=elapsed(start)
            receipts.append(row)
    return {"status":"NO_INDEPENDENT_UNSAFE_WITNESS_WITHIN_DEPTH3",
            "true_bounded_original_safety_refuted":False,
            "checked_depth_receipts":receipts,
            "important":"No unsafe trace within <=3 does NOT certify source SAFE."}

def study(root,item):
    started=time.perf_counter_ns()
    result={"source":item["path"],"status":"UNKNOWN",
            "original_git_blob":item["git_blob"],"neural_forwards":0}
    try:
        raw,src,native,evidence=prepare(root,item)
        result["original_source_provenance_and_nonvacuity"]=evidence
        result["original_safety_BMC"]=bounded_original_bad_path(src,native)
        if result["original_safety_BMC"]["true_bounded_original_safety_refuted"]:
            result["status"]="PROVED_ORIGINAL_UNSAFE_WITH_REPLAYABLE_TRACE"
            result["source_scientific_classification"]="UNSAFE"
            return result
        first=original_syguS(raw,src,native,FAST_SYGUS_BUDGET_S)
        result["first_fast_original_SyGuS"]=first
        if first["certified"]:
            result["status"]="PROVED_ORIGINAL_SAFE_FAST_SYGUS_NATIVE_DUAL3VC"
            result["source_scientific_classification"]="SAFE"
            return result
        fallback=native_pdr(src,native)
        result["full_original_PDR_fallback"]=fallback
        if fallback["certified"]:
            result["status"]="PROVED_ORIGINAL_SAFE_PDR_NATIVE_DUAL3VC"
            result["source_scientific_classification"]="SAFE"
        else:
            result["status"]="UNKNOWN_BMC_SYGUS_AND_PDR_NOT_CERTIFIED"
            result["source_scientific_classification"]="UNKNOWN"
    except Exception as e:
        result["status"]="UNKNOWN_SOURCE_OR_PROOF_EXCEPTION"
        result["source_scientific_classification"]="UNKNOWN"
        result["exception"]=type(e).__name__+":"+str(e)[:340]
    finally:
        result["total_true_automated_work_wall_ms"]=elapsed(started)
        print("SECOND_UNOPENED_SIX",result["source"],result["status"],
              "WALL",round(result["total_true_automated_work_wall_ms"],3),
              "ERROR",result.get("exception"),flush=True)
    return result

def control_prior_fib07(root):
    item={"path":"lib/Inv_Track/from_2018/fib_07.sl",
          "git_blob":"d078734e83a870d7b95a68bc7a947cf85ff944d8",
          "bytes":658}
    raw,src,native,evidence=prepare(root,item)
    trial=bounded_original_bad_path(src,native)
    if not trial["true_bounded_original_safety_refuted"] or trial["witness_depth"]!=1:
        raise RuntimeError("GENERIC_BMC_MISSED_HISTORICALLY_SOURCE_CERTIFIED_FIB07")
    return {"status":"PASS_GROUNDED_TRUE_SOURCE_UNSAFE_ONE_STEP_REDISCOVERED",
            "first_certified_trace":trial}

def control_prior_safe(root):
    item={"path":"lib/Inv_Track/from_2018/fib_05_x.sl",
          "git_blob":"c722739a4917aa1a358bc1b9fc3d9f2c171fe856",
          "bytes":522}
    raw,src,native,evidence=prepare(root,item)
    trial=bounded_original_bad_path(src,native)
    if trial["true_bounded_original_safety_refuted"]:
        raise RuntimeError("GENERIC_BMC_FALSE_UNSAFE_ON_PREVIOUSLY_PROVED_SAFE_SOURCE")
    return {"status":"PASS_NO_FALSE_UNSAFE_ON_CERTIFIED_SAFE_SOURCE",
            "bounded_check":trial}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    metadata=json.loads(opts.freeze.read_text())
    if len(metadata["targets"])!=6 or UPSTREAM not in metadata["immutable_upstream"]:
        raise RuntimeError("PREGISTERED_FRESH_SOURCE_COHORT_CHANGED")
    controls={"historic_original_fib07_UNSAFE":control_prior_fib07(opts.root),
              "historic_original_fib05_SAFE":control_prior_safe(opts.root)}
    outcomes=[]
    for item in metadata["targets"]:
        outcomes.append(study(opts.root,item))
    counts={key:sum(x.get("source_scientific_classification") == key for x in outcomes)
            for key in ("SAFE","UNSAFE","UNKNOWN")}
    result={
        "schema":"neumann.q34.second_new_six_first_source_safe_unsafe_triage.v1",
        "first_presource_git_freeze_commit":FREEZE,
        "immutable_source_revision":UPSTREAM,
        "first_true_original_six_outcomes_all_retained":len(outcomes)==6,
        "positive_AND_negative_historic_control":controls,
        "original_source_authenticated_count":sum(
            "original_source_provenance_and_nonvacuity" in x for x in outcomes),
        "original_SAFE_independent_Z3_cvc5_3VC":counts["SAFE"],
        "original_UNSAFE_independent_grounded_Z3_cvc5":counts["UNSAFE"],
        "original_UNKNOWN_count":counts["UNKNOWN"],
        "complete_proof_based_disposition_count":counts["SAFE"]+counts["UNSAFE"],
        "do_not_extrapolate_or_claim_neural_novelty":True,
        "no_model_training_or_forward":True,
        "global_Q3":"OPEN","global_Q4":"OPEN",
        "first_cases":outcomes,
    }
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("SECOND_SIX_EXACT_PRESOURCE_SAFETY_DISPOSITION",counts)
    print("SECOND_SIX_COMPLETE_PROOF_DISPOSITION",result["complete_proof_based_disposition_count"],"/6")
    print("GLOBAL_Q3_Q4",result["global_Q3"],result["global_Q4"])
if __name__=="__main__":
    main()
