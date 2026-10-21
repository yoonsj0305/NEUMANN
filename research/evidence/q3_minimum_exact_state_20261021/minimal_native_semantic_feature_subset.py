"""Find the exact minimum NUMBER of original source features needed for a
0/1-step Pre/reachable-successor vs NotPost symbolic separator in 67.c.sl.

This proves a bounded representation lower bound, NOT global program safety
or a trained ML contribution. Evaluate ALL subsets strictly smaller than the
first successful size, certify ALL SAT counterexamples and the final UNSAT
in independent source-native Z3+cvc5. No name-based variable selection.
"""
from __future__ import annotations
import argparse,itertools,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,dual,DUAL_S

TARGET="lib/Inv_Track/xujie_code2inv/67.c.sl"
SHA="5e1807ee5cbfa43c828fc3f67c3c31d4cb133a88"
def now_ms(t):return (time.perf_counter_ns()-t)/1e6
def run(root,manifest):
    it=next(q for q in manifest["cases"] if q["path"]==TARGET)
    if it["git_blob"]!=SHA:raise RuntimeError("ORIGINAL_SOURCE_SHA_MISMATCH")
    _,src,native,identity=prepare(root,it)
    n=len(src["now"])
    cloned=[z3.Const("independent_Bad_state_"+str(i),s.sort())
            for i,s in enumerate(src["now"])]
    bad=z3.substitute(z3.Not(native["post"]),*list(zip(src["now"],cloned)))
    def formula(sub):
        equalpre=[src["now"][i]==cloned[i] for i in sub]
        equalstep=[src["next"][i]==cloned[i] for i in sub]
        return z3.Or(z3.And(native["pre"],bad,*equalpre),
                     z3.And(native["pre"],native["trans"],bad,*equalstep))
    def cheap(sub):
        s=z3.Solver();s.set(timeout=4000);s.add(formula(sub))
        r=s.check()
        if r==z3.unknown:raise RuntimeError("UNKNOWN_ORIGINAL_SUBSET:"+str(sub))
        return str(r)
    t=time.perf_counter_ns()
    attempted=[];winner=None
    for size in range(0,min(n,5)+1):
        for sub in itertools.combinations(range(n),size):
            outcome=cheap(sub)
            attempted.append({"subset":list(sub),"size":size,"original_Z3_collision":outcome})
            if outcome=="unsat":
                winner=sub;break
        if winner is not None:break
    if winner is None:
        return {"status":"HOLD_NOT_FOUND_UNDER_5_FEATURES","all_results":attempted,
                "global_Q3":"OPEN","original_identity":identity}
    # Verify each smaller-cardinality set is inadequate (SAT) with BOTH
    # independent solvers, and a winning set is sufficient (UNSAT) for the
    # bounded original source projection task.
    tested=[a for a in attempted if a["size"]<len(winner)]
    if len(tested)!=sum(__import__("math").comb(n,i) for i in range(len(winner))):
        raise RuntimeError("NOT_EXHAUSTIVE_BELOW_OPTIMUM")
    validated=[]
    for item in tested:
        if item["original_Z3_collision"]!="sat":
            raise RuntimeError("SMALLER_SUBSET_NO_ALIAS_CONTRADICTION")
        evidence=dual(formula(tuple(item["subset"])),"sat",DUAL_S)
        if evidence.get("dual_pass") is not True:
            raise RuntimeError("INDEPENDENT_SOLVERS_DID_NOT_CONFIRM_SMALLER_COLLISION")
        validated.append({"subset":item["subset"],"native_original_sat_both_solvers":evidence})
    good=dual(formula(winner),"unsat",DUAL_S)
    if good.get("dual_pass") is not True:
        raise RuntimeError("INDEPENDENT_SOLVERS_DID_NOT_CONFIRM_WINNER_SEPARATES")
    pre_bad=dual(z3.And(native["pre"],z3.Not(native["post"])),"unsat",DUAL_S)
    next_post=z3.substitute(z3.Not(native["post"]),
                            *list(zip(src["now"],src["next"])))
    step_bad=dual(z3.And(native["pre"],native["trans"],next_post),"unsat",DUAL_S)
    if not pre_bad.get("dual_pass") or not step_bad.get("dual_pass"):
        raise RuntimeError("REAL_ORIGINAL_UNSAFE_OR_ORIGINAL_CERTIFICATE_UNKNOWN")
    return {
        "schema":"neumann.q3.minimum_original_source_projection_cardinality_for_zero_one_step_separation.v1",
        "status":"PROVED_FINITE_FEATURE_MINIMUM_ORIGINAL_NATIVE_Z3_CVC5",
        "target_original":TARGET,"original_git_blob":SHA,
        "original_PreTransPost_parity":identity,
        "original_variable_count":n,
        "minimum_required_feature_count":len(winner),
        "one_minimal_feature_indices":list(winner),
        "one_minimal_feature_names":[src["states"][i][0] for i in winner],
        "strictly_smaller_subset_counterexamples_independently_certified":len(validated),
        "all_strictly_smaller_combinations_have_real_SAT_witness":True,
        "minimum_sufficient_zero_one_projection_independent_original_UNSAT":good,
        "all_smaller_independent_original_SAT_receipts":validated,
        "original_not_UNSAFE_zero_or_one_step":[pre_bad,step_bad],
        "only_necessary_and_sufficient_to_separate_initial_and_one_step_from_arbitrary_bad_states":True,
        "NOT_sufficient_for_global_inductive_safety":True,
        "no_trained_model":True,
        "experiment_wall_ms":now_ms(t),
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"}
def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    report=run(Path(a.root),json.loads(Path(a.freeze).read_text()))
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_ORIGINAL_67_MINIMUM_FEATURE_STATUS",report["status"],flush=True)
    if "minimum_required_feature_count" in report:
        for k in ("original_variable_count","minimum_required_feature_count",
                  "one_minimal_feature_indices","one_minimal_feature_names",
                  "strictly_smaller_subset_counterexamples_independently_certified",
                  "experiment_wall_ms"):
            print("Q3_EXACT_MINIMUM_REAL_ORIGINAL",k,report[k],flush=True)
    print("GLOBAL_Q3_OPEN",flush=True)
if __name__=="__main__":main()
