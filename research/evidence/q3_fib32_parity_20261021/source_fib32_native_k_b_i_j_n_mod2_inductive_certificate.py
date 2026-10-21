"""The exact true original fib32 program proof with parity and branch phase.

Original contents were already opened in prior source-authenticated PR371.
This invariant was designed by *classical manual source inspection*, NOT by
NEUMANN neural learning, and is checked against UNCHANGED original Pre,
Trans and Post via independent Z3+cvc5 inductive 3VC.

If 3VC fails, preserve FAIL/UNKNOWN, don't weaken original.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,verified_3vc
)
SOURCE="lib/Inv_Track/from_2018/fib_32.sl"
ORIGINAL_BLOB="4fb129488bee3e1e0cdae899b318d6503ae23c12"
ORIGINAL_SIZE=824
PREREGISTER="bfbfa969b38041118b2ca6dea4188ab1b2b94f5c"

def make_candidate(src,mode):
    assert [x[0] for x in src["states"]]==["k","b","i","j","n"]
    k,b,i,j,n=src["now"]
    base=z3.And(k>0,n>=0,n<=2*k,z3.Or(b==0,b==1))
    if mode=="exact_full_phase_parity":
        return z3.And(base,z3.Or(
            z3.And(n%2==0,i==j),
            z3.And(n%2==1,b==0,i==j+1),
            z3.And(n%2==1,b==1,j==i+1)))
    if mode=="ablate_phase_relations":
        return z3.And(base,z3.Or(
            z3.And(n%2==0,i==j),
            z3.And(n%2==1,z3.Or(i==j+1,j==i+1))))
    if mode=="ablate_even_odd":
        return z3.And(base,i==j)
    if mode=="ablate_n_upper_bound":
        return z3.And(k>0,n>=0,z3.Or(b==0,b==1),z3.Or(
            z3.And(n%2==0,i==j),
            z3.And(n%2==1,b==0,i==j+1),
            z3.And(n%2==1,b==1,j==i+1)))
    raise ValueError("NOT_PREREGISTERED_CANDIDATE")

def check(root,item):
    start=time.perf_counter_ns()
    record={"true_original_SHA_authenticated":False,"actual_true_original_parity_3VC_Z3_cvc5":False,
            "status":"UNKNOWN","manual_classical_source_hypothesis_not_trained":True}
    try:
        raw,src,native,ids=prepare(root,item)
        record["true_original_SHA_authenticated"]=True
        record["source_original_native_Pre_Trans_Post_independent_parity"]=ids
        proof=make_candidate(src,"exact_full_phase_parity")
        passed,obligations=verified_3vc(src,native,proof)
        record["actual_true_original_parity_3VC_Z3_cvc5"]=bool(passed)
        record["source_native_invariant_SHA256"]=hashlib.sha256(proof.sexpr().encode()).hexdigest()
        record["source_native_invariant_Z3_sexpr"]=proof.sexpr()
        record["original_all_three_independent_proof_obligations"]=obligations
        record["original_verification_true_unmodified_Pre_Trans_Post"]=True
        controls=[]
        for mode in ("ablate_phase_relations","ablate_even_odd","ablate_n_upper_bound"):
            weaker=make_candidate(src,mode)
            okay,details=verified_3vc(src,native,weaker)
            controls.append({"ablation":mode,"still_inductive_3VC_Z3_cvc5":bool(okay),
                             "original_3VC_verifier_receipts":details,
                             "original_candidate_SHA256":hashlib.sha256(weaker.sexpr().encode()).hexdigest()})
        record["all_original_math_ablation_negative_controls"]=controls
        record["status"]="TRUE_ORIGINAL_FIB32_SAFE_PARITY_FULL_3VC_Z3_CVC5_CERTIFIED" if passed else "UNKNOWN_TRUE_ORIGINAL_PARITY_INDUCTIVE_3VC_FAILED"
    except Exception as e:
        record["status"]="UNKNOWN_ORIGINAL_SOURCE_OR_INDUCTION_EXCEPTION"
        record["error"]=type(e).__name__+":"+str(e)[:360]
    record["true_original_source_and_3VC_all_attempts_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_FIB32_FULL_ORIGINAL_PARITY_INDUCTIVE_Z3_CVC5",record["actual_true_original_parity_3VC_Z3_cvc5"])
    print("Q3_FIB32_FULL_ORIGINAL_PARITY_ABLATIONS",[
        {"route":p["ablation"],"is_3VC":p["still_inductive_3VC_Z3_cvc5"]}
        for p in record.get("all_original_math_ablation_negative_controls",[])])
    print("Q3_FIB32_FULL_ORIGINAL_STATUS",record["status"],record.get("error"))
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    m=json.loads(a.freeze.read_text())
    c=json.loads(a.protocol.read_text())
    if c["schema"]!="neumann.q3.posthoc_real_original_fib32_parity_invariant_dual_v1":
        raise RuntimeError("CANNOT_MODIFY_FROZEN_FIB32_CANDIDATE")
    original=next(x for x in m["cases"] if x["path"]==SOURCE)
    if original["git_blob"]!=ORIGINAL_BLOB or original["bytes"]!=ORIGINAL_SIZE:
        raise RuntimeError("ACTUAL_TRUE_ORIGINAL_SOURCE_SHA_CHANGED")
    rec=check(a.root,original)
    out={"schema":"neumann.q3.posthoc_source_fib32_manual_exact_parity_inductive_3VC.v1",
         "manual_parity_candidate_registered_before_original_3VC_commit":PREREGISTER,
         "source_full_original_previously_opened_not_new_first_blind":True,
         "source_true_program_from_24_original_hash_frozen_git":"6a5792e196b2234358dca31ec9dd733f3ffed42d",
         "learned_model_forward_and_training_update":0,
         "source_original_fib32_safe_certified":rec["actual_true_original_parity_3VC_Z3_cvc5"],
         "strongest_matched_classical_with_same_parity_invariant_can_prove_same":True,
         "original":rec,
         "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("Q3_FIB32_POSTHOC_ORIGINAL_SAFE_PROVED",out["source_original_fib32_safe_certified"])
    print("Q3_FIB32_GLOBAL_LEARNED_Q3_OPEN",out["global_Q3"])
if __name__=="__main__":
    main()
