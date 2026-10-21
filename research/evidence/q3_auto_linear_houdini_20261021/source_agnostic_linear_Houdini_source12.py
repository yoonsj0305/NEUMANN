"""Universal posthoc classic Houdini-style linear invariant discovery on genuine sources.

NO source-specific named vars, no manual candidate from PR390, no trained ML.
The bounded grammar was designed AFTER these original source bodies had been
opened by previous PR389, so this is NOT a new blind problem-generalization.
Only independently native Z3+cvc5 full ORIGINAL 3VC counts as a proof.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc
)

def millis(ns):return (time.perf_counter_ns()-ns)/1e6
def source_literals(formulas):
    result={0,1,2}
    for k in ("pre","trans","post"):
        stack=[formulas[k]]
        while stack:
            q=stack.pop()
            if z3.is_int_value(q):
                n=q.as_long()
                if 0<=n<=10000:result.add(n)
            if z3.is_app(q):stack.extend(q.children())
    return sorted(result)
def generate(src,native,cap):
    state=src["now"]
    if not(2<=len(state)<=7) or any(v.sort().kind()!=z3.Z3_INT_SORT for v in state):
        raise ValueError("BOUNDED_ONLY_2_TO_7_INTEGER_SOURCE_VARIABLES")
    constants=source_literals(native)
    scalars=[c for c in constants if c>=2]
    candidates={};names=[]
    def add(q):
        q=z3.simplify(q)
        if z3.is_true(q) or z3.is_false(q):return
        key=q.sexpr()
        if key not in candidates:candidates[key]=q
    for x in state:
        for c in constants:
            add(x>=c);add(x<=c);add(x==c)
    for i,x in enumerate(state):
        for j,y in enumerate(state):
            if i==j:continue
            for delta in (-1,0,1):
                add(x>=y+delta)
                add(x<=y+delta)
                add(x==y+delta)
            for mult in scalars:
                add(x>=mult*y)
                add(x<=mult*y)
    if len(candidates)>cap:raise RuntimeError("CANDIDATE_GRAMMAR_CAP_EXCEEDED")
    return list(candidates.values()),constants

def initialization_filter(all_candidates,native,timeout):
    solver=z3.Solver();solver.set(timeout=timeout);solver.add(native["pre"])
    admitted=[];disqualified=0;unknown=0
    for cand in all_candidates:
        solver.push();solver.add(z3.Not(cand));status=solver.check();solver.pop()
        if status==z3.unsat:admitted.append(cand)
        elif status==z3.sat:disqualified+=1
        else:unknown+=1
    return admitted,disqualified,unknown

def houdini(src,native,initial,cap,timeout):
    now=src["now"];nxt=src["next"]
    subst=list(zip(now,nxt))
    active=list(initial)
    history=[]
    for step in range(cap):
        if not active:return active,history,"HOLD_EMPTY"
        primed=[z3.substitute(q,*subst) for q in active]
        s=z3.Solver();s.set(timeout=timeout)
        s.add(z3.And(*active),native["trans"],z3.Not(z3.And(*primed)))
        status=s.check()
        if status==z3.unsat:return active,history,"PROVED_INDUCTIVE_FIXED_POINT"
        if status!=z3.sat:return active,history,"HOLD_Z3_UNKNOWN"
        m=s.model()
        invalid=[idx for idx,c in enumerate(primed) if z3.is_false(m.eval(c,model_completion=True))]
        if not invalid:raise RuntimeError("SOURCE_HOUDINI_SAT_WITNESS_FAILED_TO_ELIMINATE")
        removed=set(invalid)
        history.append({"iter":step,"active_before":len(active),"invalid_next_state_candidates":len(removed)})
        active=[q for i,q in enumerate(active) if i not in removed]
    return active,history,"HOLD_ITERATION_CAP"

def original(root,item,contract,i):
    start=time.perf_counter_ns()
    row={"source":item["path"],"original_git_blob":item["git_blob"],
         "automatic_source_agnostic_finite_linear_Houdini_verified":False,
         "status":"HOLD"}
    try:
        raw,src,native,identity=prepare(root,item)
        row["true_original_source_authentic_native_3_formula_parity"]=identity
        t=time.perf_counter_ns()
        atoms,constants=generate(src,native,contract["max_candidate_count"])
        row["source_native_integer_constants"]=constants
        row["actual_generated_source_name_free_arithmetic_candidate_count"]=len(atoms)
        possible,discarded,unknown=initialization_filter(
            atoms,native,contract["per_Z3_check_timeout_ms"])
        row["actual_initial_Pre_entailed_atom_count"]=len(possible)
        row["initial_source_refuted_atom_count"]=discarded
        row["initial_UNKNOWN_solver_candidate_count"]=unknown
        candidate,steps,fixed=houdini(
            src,native,possible,contract["max_houdini_iterations"],contract["per_Z3_check_timeout_ms"])
        row["Houdini_held_actual_transition_models"]=steps
        row["Houdini_fixed_point_verdict"]=fixed
        row["automatic_candidate_generation_and_Houdini_Z3_wall_ms"]=millis(t)
        row["automatic_invariant_conjunct_count"]=len(candidate)
        if fixed=="PROVED_INDUCTIVE_FIXED_POINT":
            t=time.perf_counter_ns()
            inv=z3.And(*candidate)
            certified,three=verified_3vc(src,native,inv)
            row["source_actual_original_full_Z3_cvc5_3VC_receipts"]=three
            row["source_actual_original_dual_3VC_wall_ms"]=millis(t)
            row["automatic_invariant_SHA256"]=hashlib.sha256(inv.sexpr().encode()).hexdigest()
            row["automatic_source_agnostic_finite_linear_Houdini_verified"]=bool(certified)
            row["status"]="CLASSICAL_AUTOMATIC_FULL_ORIGINAL_SOURCE_INDUCTIVE_PROVEN" if certified else "HOLD_FINAL_SOURCE_DUAL_3VC_FAILED"
        else:
            row["status"]="HOLD_BOUNDED_HOUDINI_NOT_COMPLETED"
    except Exception as e:
        row["status"]="HOLD_SOURCE_UNSUPPORTED_OR_RUNTIME"
        row["error"]=type(e).__name__+":"+str(e)[:440]
    row["entire_actual_source_auth_candidate_houdini_full_dual_wall_ms"]=millis(start)
    print("CLASSIC_Q3_TRUE_SOURCE",i+1,item["path"],
          "STATUS",row["status"],
          "GENERATED",row.get("actual_generated_source_name_free_arithmetic_candidate_count"),
          "INIT",row.get("actual_initial_Pre_entailed_atom_count"),
          "FIXED",row.get("Houdini_fixed_point_verdict"),
          "REMAIN",row.get("automatic_invariant_conjunct_count"),
          "PROVED",row["automatic_source_agnostic_finite_linear_Houdini_verified"],
          "ERROR",row.get("error"),flush=True)
    return row

def main():
    p=argparse.ArgumentParser()
    for a in ("root","freeze","contract","out"):p.add_argument("--"+a,required=True)
    a=p.parse_args()
    freeze=json.loads(Path(a.freeze).read_text())
    contract=json.loads(Path(a.contract).read_text())
    if contract["schema"]!="neumann.q3.posthoc_generic_linear_Houdini_original12_20261021.v1":
        raise RuntimeError("PRE_REGISTERED_GENERIC_HOUDINI_GRAMMAR_CHANGED")
    if freeze["schema"]!="neumann.q4q6_first12_heldout_original_source_metadata_LOCK_v1":
        raise RuntimeError("ORIGINAL_12_SOURCE_IDENTITY_CHANGED")
    assert len(freeze["new_originals"])==12
    results=[original(Path(a.root),item,contract,i) for i,item in enumerate(freeze["new_originals"])]
    proofs=[q for q in results if q["automatic_source_agnostic_finite_linear_Houdini_verified"]]
    twonames={"fib_21.sl","jmbl_hola.41.sl"}
    known=[r for r in results if r["source"].rsplit("/",1)[-1] in twonames]
    assert len(known)==2
    report={
        "schema":"neumann.q3.houdini_generic_linear_program12_auto_classical_20261021.v1",
        "original_source_programs":results,
        "real_original_sha_authenticated_and_pre_trans_post_preflight_count":sum(
            "true_original_source_authentic_native_3_formula_parity" in r for r in results),
        "actual_source_auto_inductive_dual_Z3_cvc5_proof_count":len(proofs),
        "original_2_previous_TIMEOUT_posthoc_auto_success_count":sum(
            r["automatic_source_agnostic_finite_linear_Houdini_verified"] for r in known),
        "source_agnostic_candidate_generation_no_original_specific_cases":True,
        "original_source_bodies_were_previously_opened":True,
        "original_positive_and_negative_method_failures_preserved":True,
        "classical_existing_Houdini_concept_not_novel_neural_structure":True,
        "full_frontier_cost_energy_gap_unproven":True,
        "neural_training_updates":0,"model_inference_calls":0,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"
    }
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("CLASSIC_Q3_AUTHENTIC12",report["real_original_sha_authenticated_and_pre_trans_post_preflight_count"])
    print("CLASSIC_Q3_AUTO_FULL_NATIVE_INDUCTIVE_PROOFS",report["actual_source_auto_inductive_dual_Z3_cvc5_proof_count"])
    print("CLASSIC_Q3_PREVIOUS_TWO_AUTO_RECOVERED",report["original_2_previous_TIMEOUT_posthoc_auto_success_count"])
    print("CLASSIC_Q3_GLOBAL_LEARNED_MODEL","OPEN")
if __name__=="__main__":main()
