"""NEUMANN Q3 POSTHOC classical hypothesis learner: source-generic
bounded affine atom grammar + Houdini counterexample elimination, full
independent genuine original Z3/cvc5 Pre/Trans/Post 3VC.

All 12 originals have been opened in prior studies. No filename-specific
coefficients, no manually inserted gold invariant; no neural computation.
This known classical Houdini mechanism is not a new ML discovery or theorem.
The 3 primary original source variables, coefficient {-1,0,+1} and
threshold {-1,0,+1} grammar is preregistered BEFORE running experiments.
"""
from __future__ import annotations
import argparse,itertools,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    verified_3vc,dual,DUAL_S,prepare
)
def millis(t):return (time.perf_counter_ns()-t)/1e6
def atoms(src):
    var=src["now"][:min(3,len(src["now"]))]
    coeffs=[c for c in itertools.product((-1,0,1),repeat=len(var))
            if 1<=sum(x!=0 for x in c)<=2]
    result={}
    for a in coeffs:
        term=z3.Sum(*[x*y for x,y in zip(a,var) if x])
        for b in (-1,0,1):
            f=z3.simplify(term>=b)
            result.setdefault(f.sexpr(),f)
    return list(result.values())
def sat_info(formula,timeout=1800):
    s=z3.Solver();s.set(timeout=timeout);s.add(formula)
    v=s.check()
    if v==z3.unknown:raise RuntimeError("BOUND_TIMEOUT_OR_UNKNOWN:"+s.reason_unknown())
    return str(v),(s.model() if v==z3.sat else None)
def quick(src,native,inv,timeout=1400):
    iv_next=z3.substitute(inv,*list(zip(src["now"],src["next"])))
    vcs=[
        z3.And(native["pre"],z3.Not(inv)),
        z3.And(inv,native["trans"],z3.Not(iv_next)),
        z3.And(inv,z3.Not(native["post"]))]
    for query in vcs:
        res,_=sat_info(query,timeout=timeout)
        if res!="unsat":return False
    return True
def houdini(src,native):
    started=time.perf_counter_ns()
    pool=atoms(src);created=len(pool)
    history=[];loops=0
    while loops<=created+3:
        loops+=1
        if not pool:
            return None,{"status":"EMPTY_NO_NONTRIVIAL_INVARIANT",
                         "generated":created,"iterations":loops,"history":history}
        cur=z3.And(*pool)
        prebad,zmodel=sat_info(z3.And(native["pre"],z3.Not(cur)))
        if prebad=="sat":
            removed=[p for p in pool if not z3.is_true(zmodel.eval(p,model_completion=True))]
            if not removed:raise RuntimeError("NO_REMOVABLE_COUNTEREXAMPLE_INIT")
            keys={p.sexpr() for p in removed}
            pool=[p for p in pool if p.sexpr() not in keys]
            history.append({"phase":"init","removed":len(removed),"retained":len(pool)})
            continue
        nxt=z3.substitute(cur,*list(zip(src["now"],src["next"])))
        stepbad,zmodel=sat_info(z3.And(cur,native["trans"],z3.Not(nxt)))
        if stepbad=="sat":
            removed=[]
            for p in pool:
                pnext=z3.substitute(p,*list(zip(src["now"],src["next"])))
                if not z3.is_true(zmodel.eval(pnext,model_completion=True)):removed.append(p)
            if not removed:raise RuntimeError("NO_REMOVABLE_COUNTEREXAMPLE_TRANS")
            keys={p.sexpr() for p in removed}
            pool=[p for p in pool if p.sexpr() not in keys]
            history.append({"phase":"transition","removed":len(removed),"retained":len(pool)})
            continue
        # Every constituent really inductive collectively, but final goal
        # may not be implied; do not fabricate a complete task proof.
        raw_pass=quick(src,native,cur)
        minimization_trials=0
        if raw_pass:
            # Greedy proof-preserving deletion is source generic; no manual rule
            # injection and independently re-prove the final smaller invariant.
            i=0
            while i<len(pool):
                rest=pool[:i]+pool[i+1:]
                candidate=z3.And(*rest) if rest else z3.BoolVal(True)
                minimization_trials+=1
                if quick(src,native,candidate):
                    pool=rest
                else:i+=1
        final=z3.And(*pool) if pool else z3.BoolVal(True)
        return final,{
            "status":"COMPLETE_GLOBAL_INDUCTIVE_HYPOTHESES_FOUND",
            "generated":created,"retained_conjunct_count":len(pool),
            "removed_total":created-len(pool),"iterations":loops,
            "sample_counterexample_feedback":history,
            "goal_can_be_proved_by_full_template":raw_pass,
            "greedy_minimization_trials":minimization_trials,
            "retained_original_typed_conjuncts":[p.sexpr() for p in pool],
            "actual_candidate_generation_pruning_wall_ms":millis(started)}
    raise RuntimeError("HOUDINI_BOUND_VIOLATION")
def one(root,item):
    started=time.perf_counter_ns()
    out={"source":item["path"],"original_sha":item["git_blob"],
         "status":"ABSTAIN","neural_calls":0,"learned_weight_updates":0}
    try:
        raw,src,native,parity=prepare(root,item)
        out["real_original_native_PreTransPost_dual_parity"]=parity
        candidate,rec=houdini(src,native)
        out["source_generic_affine_Houdini"]=rec
        if candidate is not None:
            success,cert=verified_3vc(src,native,candidate)
            out["actual_genuine_original_Z3_cvc5_induction_3VC"]=cert
            out["certified_full_original_SAFE"]=bool(success)
            out["final_genuine_original_invariant_AST"]=candidate.sexpr()
            out["final_genuine_original_invariant_SHA256"]=hashlib.sha256(candidate.sexpr().encode()).hexdigest()
        else:out["certified_full_original_SAFE"]=False
        out["status"]="FULL_ORIGINAL_3VC_CERTIFIED" if out["certified_full_original_SAFE"] else "HOLD_NO_SAFE_CERTIFICATE"
    except Exception as e:
        out["status"]="ABSTAIN_AUTHENTIC_ORIGINAL_SOURCE_OR_SOLVER"
        out["error"]=type(e).__name__+":"+str(e)[:430]
    out["full_authenticated_source_and_candidate_original_dual_wall_ms"]=millis(started)
    print("Q3_ACTUAL_GENUINE_ORIGINAL_CONJUNCTIVE",item["path"].split("/")[-1],
          out["status"],"PROVED",out.get("certified_full_original_SAFE"),
          "GEN",out.get("source_generic_affine_Houdini",{}).get("generated"),
          "KEEP",out.get("source_generic_affine_Houdini",{}).get("retained_conjunct_count"),
          "ERROR",out.get("error"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    manifest=json.loads(Path(a.freeze).read_text())
    assert manifest["schema"]=="neumann.q3.train_BOOLEAN_DNF_first12_unopened_xujie_SHA.v1"
    cases=manifest["cases"]
    assert len(cases)==12 and len({x["git_blob"] for x in cases})==12
    rows=[one(Path(a.root),case) for case in cases]
    report={
      "schema":"neumann.q3.real_original12_source_generic_classical_Houdini_linear_conjunction.v1",
      "original_sha_frozen_in_prior_first_unopened_PR412":True,
      "new_method_is_posthoc_after_original_source_was_opened":True,
      "originals":len(rows),
      "genuine_original_full_dual_3VC_SAFE_count":sum(r.get("certified_full_original_SAFE",False) for r in rows),
      "previous_proof_first_classical_11_originals":11,
      "last_original_1_c_sl_independent_complete_3VC":
        next(r.get("certified_full_original_SAFE",False) for r in rows if r["source"].endswith("/1.c.sl")),
      "last_original_1_c_sl_candidate":
        next(r.get("final_genuine_original_invariant_AST") for r in rows if r["source"].endswith("/1.c.sl")),
      "total_auth_and_generator_verifier_wall_ms":sum(r["full_authenticated_source_and_candidate_original_dual_wall_ms"] for r in rows),
      "model_fit_count":0,"neural_forward_count":0,
      "known_classical_Houdini_not_novel_machine_learning_discovery":True,
      "never_claim_global_Q3_or_frontier_or_10x":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "all_original_proof_receipts":rows}
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("genuine_original_full_dual_3VC_SAFE_count",
              "last_original_1_c_sl_independent_complete_3VC",
              "last_original_1_c_sl_candidate",
              "total_auth_and_generator_verifier_wall_ms"):
        print("Q3_GENUINE_CLASSICAL_CONJUNCTIVE_DISCOVERY",k,report[k],flush=True)
    print("Q3_GLOBAL_OPEN")
if __name__=="__main__":main()
