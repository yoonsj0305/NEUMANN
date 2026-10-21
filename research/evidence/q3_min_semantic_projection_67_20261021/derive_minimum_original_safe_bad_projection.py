"""Exact minimal extension of a 2-slot semantic interface on authentic original 67.

Goal: avoid a false learned-model success when FIRST TWO declared state
variables lose information about safe 1-step reachable states and arbitrary
violations of the original Post. Exhaustively enumerate additional ORIGINAL
state-variable slots in increasing cardinality. For each projection S ask:
  exists original init s0, original transition s0 -> s1, Post(s1) true,
  arbitrary bad state b with NotPost(b), and projected(s1,S)=projected(b,S)?
SAT = impossible for any classifier over projection S to separate these
classes. UNSAT = the projection does separate THESE two universally quantified
sets, not a guarantee of full inductive safe invariants.
Both Z3 AND cvc5 must agree for every smaller cardinality SAT and winner UNSAT.
No ML fit or hand-supplied original invariant. It is an information interface
certificate and a posthoc original source diagnostic, not a Q3 global closure.
"""
import argparse,hashlib,itertools,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    sexprs,blob,compile_typed_original,compile_independent_native
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import dual,DUAL_S
PATH="lib/Inv_Track/xujie_code2inv/67.c.sl"
SHA="5e1807ee5cbfa43c828fc3f67c3c31d4cb133a88"
def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    f=json.loads(Path(a.freeze).read_text())
    item=next(x for x in f["cases"] if x["path"]==PATH)
    assert item["git_blob"]==SHA
    raw=(Path(a.root)/PATH).read_bytes()
    assert blob(raw)==SHA and len(raw)==item["bytes"]
    src=compile_typed_original(sexprs(raw))
    native=compile_independent_native(sexprs(raw),src)
    parity={k:dual(z3.Xor(src[k],native[k]),"unsat",DUAL_S)
            for k in ("pre","trans","post")}
    if not all(q["dual_pass"] for q in parity.values()):
        raise RuntimeError("FULL_AUTHENTIC_SOURCE_AND_INDEPENDENT_NATIVE_NOT_EQUIVALENT")
    names=[n for n,_ in src["states"]]
    now=list(src["now"]);nexts=list(src["next"])
    bad=[z3.Const("separate_bad_full_state_"+str(j),now[j].sort()) for j in range(len(now))]
    safe_next=z3.substitute(native["post"],*list(zip(now,nexts)))
    bad_post=z3.substitute(native["post"],*list(zip(now,bad)))
    base=z3.And(native["pre"],native["trans"],safe_next,z3.Not(bad_post))
    prior=(0,1)
    assert len(now)>=3
    extra=[i for i in range(len(now)) if i not in prior]
    t=time.perf_counter_ns()
    examined=0;lower_count=0;failed=[];winner=None
    for k in range(len(extra)+1):
        if winner is not None:break
        for chosen in itertools.combinations(extra,k):
            selected=tuple(prior)+chosen
            q=z3.And(base,*[nexts[i]==bad[i] for i in selected])
            solver=z3.Solver();solver.set(timeout=4000);solver.add(q)
            verdict=solver.check()
            if verdict==z3.unknown:raise RuntimeError("UNKNOWN_CANNOT_CERTIFY_PROJECTION_MINIMALITY")
            expected="unsat" if verdict==z3.unsat else "sat"
            external=dual(q,expected,DUAL_S)
            if not external["dual_pass"]:
                raise RuntimeError("INDEPENDENT_SOLVERS_DISAGREE_ON_MINIMALITY_TEST")
            examined+=1
            if verdict==z3.unsat:
                winner={"feature_indices":list(selected),
                        "feature_names": [names[i] for i in selected],
                        "additional_feature_indices":list(chosen),
                        "additional_feature_count":k,
                        "original_full_safestate_badstate_projection_alias_UNSAT_both_solvers":external}
                break
            lower_count+=1
            failed.append({"feature_indices":list(selected),
                           "additional_count":k,"two_original_independent_solver_SAT":external})
    if winner is None:
        raise RuntimeError("EVEN_FULL_ORIGINAL_STATE_PROJECTION_INSEPARABLE_DISAGREES_WITH_POST")
    assert len(failed)==lower_count
    assert all(len(x["feature_indices"])<len(winner["feature_indices"]) for x in failed)
    result={
      "schema":"neumann.q3.genuine_original67_minimum_projection_extension_two_solver.v1",
      "real_original_SHA":SHA,
      "native_full_original_PreTransPost_independent_parity":parity,
      "original_program_state_names":names,
      "initial_current_feature_indices":[0,1],
      "minimum_extra_slots_after_first_two":winner["additional_feature_count"],
      "minimum_proven_projection":winner,
      "strictly_smaller_slot_projections_ALL_independently_SAT":len(failed),
      "independently_verified_enumeration_decisions":examined,
      "all_smaller_projections_rejected":failed,
      "full_original_state_program_SAFE_NOT_implied_by_this_classification_test":True,
      "sample_accuracy_or_supervised_model_training_NOT_USED":True,
      "not_global_machine_learned_Q3":True,
      "posthoc_after_original_PR412":True,
      "wall_ms":(time.perf_counter_ns()-t)/1e6,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN"}
    Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("TRUE_ORIGINAL_SEMANTIC_INTERFACE_FIRST_TWO_INSUFFICIENT",True)
    print("TRUE_ORIGINAL_MINIMAL_EXTRA_FEATURES",winner["additional_feature_count"])
    print("TRUE_ORIGINAL_MINIMUM_PROJECTION_SLOT_NAMES",winner["feature_names"])
    print("STRICTLY_SMALLER_PROJECTIONS_EXACT_DUAL_SAT",len(failed))
    print("TOTAL_CERTIFIED_SOURCE_PROJECTION_SEARCH",examined)
    print("GLOBAL_Q3_OPEN")
if __name__=="__main__":main()
