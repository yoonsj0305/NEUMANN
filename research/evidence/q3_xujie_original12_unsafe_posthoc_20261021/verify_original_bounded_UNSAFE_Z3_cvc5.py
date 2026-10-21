"""Posthoc TRUE original source SAFE/UNSAFE discrimination after OOD PR408.

Not learned, not a new first-blind run, not a full safety decision from
bounded exploration. Original source Init and one-step violating traces are
independently SAT/UNSAT checked by both Z3 and cvc5.
SAFE is never asserted from bounded UNSAT; SAFE only from prior verified full 3VC.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare,dual,DUAL_S

def check_dual(phi):
    s=z3.Solver();s.set(timeout=5000);s.add(phi)
    result=s.check()
    if result==z3.unknown:
        return {"status":"UNKNOWN_CAP","z3_reason":s.reason_unknown(),"independent_dual_agreed":False}
    status="sat" if result==z3.sat else "unsat"
    receipt=dual(phi,status,DUAL_S)
    out={"status":status.upper(),"independent_original_Z3_and_cvc5":receipt,
         "independent_dual_agreed":receipt.get("dual_pass") is True}
    if result==z3.sat:
        out["counterexample_z3_smt_model"]=s.model().sexpr()[:5000]
    return out
def inspect(root,item):
    started=time.perf_counter_ns()
    out={"source":item["path"],"sha":item["git_blob"],"status":"ABSTAIN","full_safety_proven_by_bounded_checks":False}
    try:
        raw,src,native,identity=prepare(root,item)
        out["original_authentic_complete_pretranspost_native_parity"]=identity
        init=check_dual(z3.And(native["pre"],z3.Not(native["post"])))
        next_post=z3.substitute(native["post"],*list(zip(src["now"],src["next"])))
        step=check_dual(z3.And(native["pre"],native["trans"],z3.Not(next_post)))
        out["actual_genuine_original_0_step_unsafe_query"]=init
        out["actual_genuine_original_1_step_unsafe_query"]=step
        if init["status"]=="SAT" and init["independent_dual_agreed"]:
            out["status"]="ORIGINAL_UNSAFE_WITNESSED_INIT_BY_INDEPENDENT_Z3_CVC5"
        elif step["status"]=="SAT" and step["independent_dual_agreed"]:
            out["status"]="ORIGINAL_UNSAFE_WITNESSED_ONE_TRANSITION_BY_INDEPENDENT_Z3_CVC5"
        elif (init["status"]=="UNSAT" and init["independent_dual_agreed"]
              and step["status"]=="UNSAT" and step["independent_dual_agreed"]):
            out["status"]="NO_BOUNDED_ZERO_OR_ONE_TRANSITION_UNSAFE_WITNESS_NOT_GLOBAL_SAFE"
        else:
            out["status"]="UNKNOWN_OR_PROVER_DISAGREEMENT_FAIL_CLOSED"
    except Exception as e:
        out["error"]=type(e).__name__+":"+str(e)[:500]
    out["full_native_original_source_parsing_and_zero_one_bounded_wall_ms"]=(time.perf_counter_ns()-started)/1e6
    print("TRUE_ORIGINAL_NATIVE_SAFETY_STATUS",item["path"].split("/")[-1],out["status"],
          "INIT",out.get("actual_genuine_original_0_step_unsafe_query",{}).get("status"),
          "STEP",out.get("actual_genuine_original_1_step_unsafe_query",{}).get("status"),
          "ERROR",out.get("error"),flush=True)
    return out
def main():
    p=argparse.ArgumentParser()
    for name in ("root","freeze","out"):p.add_argument("--"+name,required=True)
    a=p.parse_args()
    m=json.loads(Path(a.freeze).read_text())
    assert m["schema"]=="neumann.q3.20261021.unseen_cross_family_xujie_code2inv_12_original_SHA_metadata_only.v1"
    cases=m["cases"]
    assert len(cases)==12 and len({q["git_blob"] for q in cases})==12
    rows=[inspect(Path(a.root),q) for q in cases]
    report={
      "schema":"neumann.q3.actual_original_cross_family12_native_Z3_cvc5_bounded_unsafety_not_learned.v1",
      "real_original_sources_in_frozen_earlier_first_blind_cohort":12,
      "these_bodies_opened_by_prior_PR408":True,
      "genuine_original_initial_SAT_unsafe":sum(q["status"]=="ORIGINAL_UNSAFE_WITNESSED_INIT_BY_INDEPENDENT_Z3_CVC5" for q in rows),
      "genuine_original_first_transition_unsafe":sum(q["status"]=="ORIGINAL_UNSAFE_WITNESSED_ONE_TRANSITION_BY_INDEPENDENT_Z3_CVC5" for q in rows),
      "no_short_bounded_unsafe_but_not_global_SAFE":sum(q["status"]=="NO_BOUNDED_ZERO_OR_ONE_TRANSITION_UNSAFE_WITNESS_NOT_GLOBAL_SAFE" for q in rows),
      "unsupported_or_proof_disagreement":sum(q["status"] in ("ABSTAIN","UNKNOWN_OR_PROVER_DISAGREEMENT_FAIL_CLOSED") for q in rows),
      "bounded_unsat_never_interpreted_as_complete_safe":True,
      "positive_counterexample_is_final_original_UNSAFE":True,
      "independent_Z3_cvc5_only_original_full_Pre_Trans_Post_source":True,
      "no_learned_model_inference":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "true_original_cases":rows}
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("genuine_original_initial_SAT_unsafe","genuine_original_first_transition_unsafe",
              "no_short_bounded_unsafe_but_not_global_SAFE","unsupported_or_proof_disagreement"):
        print("Q3_GENUINE_CROSS_FAMILY_UNSAFE_EVIDENCE",k,report[k])
    print("GLOBAL_Q3_Q4_Q6_OPEN")
if __name__=="__main__":main()
