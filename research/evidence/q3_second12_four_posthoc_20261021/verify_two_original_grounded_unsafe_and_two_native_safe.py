"""True SOURCE-NATIVE exact dual Z3+cvc5 original SAFE/UNSAFE original12 triage.

After first-source OPENED original PR394: two actual depth-one UNSAFE paths,
one exact affine inductive SAFE, one genuine Post tautology. No neural or
algorithm first-blind claim; previous 8/12 history immutable. Never promote
unknown from a solver timeout without exact native original certificates.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import z3
from research.evidence.q3_gater_relational_mixed_20261020.first_actual_nondet_and_branch_originals import (
    sexprs,compile_typed_original,compile_independent_native,dual
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import verified_3vc

PREVIOUS_SHA="3ae631a1defdd1119d1f35f7fdfcc6ede84d44e5a51bdac908b37cf5b7be6523"
DUAL_TIMEOUT_S=8
def sha_git(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def ms(t):return (time.perf_counter_ns()-t)/1e6

def compile_authentic(root,item):
    b=(root/item["path"]).read_bytes()
    if sha_git(b)!=item["git_blob"] or len(b)!=item["bytes"]:
        raise RuntimeError("TRUE_ORIGINAL_FIRST_METADATA_GIT_SHA_OR_BYTES_CHANGED")
    expr=sexprs(b);src=compile_typed_original(expr);native=compile_independent_native(expr,src)
    checks={k:dual(z3.Xor(src[k],native[k]),"unsat",DUAL_TIMEOUT_S) for k in ("pre","trans","post")}
    if not all(q["dual_pass"] for q in checks.values()):
        raise RuntimeError("SOURCE_EXACT_TYPED_PARSER_NATIVE_PARITY_NOT_INDEPENDENTLY_PROVED")
    pre=dual(native["pre"],"sat",DUAL_TIMEOUT_S)
    if not pre["dual_pass"]:raise RuntimeError("ORIGINAL_PRE_NOT_INDEPENDENT_SAT")
    return src,native,{"original_source_git_sha":item["git_blob"],
                       "original_source_SHA256":hashlib.sha256(b).hexdigest(),
                       "native_pre_trans_post_XOR_independent_Z3_cvc5":checks,
                       "original_Pre_satisfiable_original_Z3_cvc5":pre}

def unsafe_bmc_one(src,native):
    now=src["now"];nxt=src["next"]
    s0=[z3.Int("SOURCE_BMC_TIME0_"+str(i)) for i in range(len(now))]
    s1=[z3.Int("SOURCE_BMC_TIME1_"+str(i)) for i in range(len(now))]
    if any(q.sort().kind()!=z3.Z3_INT_SORT for q in list(now)+list(nxt)):
        raise RuntimeError("BOUNDED_ONLY_ORIGINAL_INT_STATES")
    p=z3.substitute(native["pre"],*zip(now,s0))
    t=z3.substitute(native["trans"],*(list(zip(now,s0))+list(zip(nxt,s1))))
    q=z3.substitute(z3.Not(native["post"]),*zip(now,s1))
    whole=z3.And(p,t,q)
    first=dual(whole,"sat",DUAL_TIMEOUT_S)
    out={"actual_original_Pre_Trans_NotPost_dual_Z3_cvc5_SAT":first,
         "verified_concrete_full_original_BMC_witness":False}
    if not first["dual_pass"]:return out
    sol=z3.Solver();sol.add(whole)
    if sol.check()!=z3.sat:raise RuntimeError("Z3_CONTRADICTS_FIRST_INDEPENDENT_REAL_BMC_SAT")
    model=sol.model()
    grounded_vars=s0+s1
    vals=[model.eval(x,model_completion=True).as_long() for x in grounded_vars]
    concrete=z3.substitute(whole,*[(x,z3.IntVal(v)) for x,v in zip(grounded_vars,vals)])
    complete=dual(concrete,"sat",DUAL_TIMEOUT_S)
    out["actual_original_grounded_full_source_Pre_Trans_NotPost_independent_Z3_cvc5_SAT"]=complete
    out["actual_original_state0_exact_integers"]=vals[:len(now)]
    out["actual_original_state1_exact_integers"]=vals[len(now):]
    out["verified_concrete_full_original_BMC_witness"]=bool(complete["dual_pass"])
    return out

def safe_invariant(src,native,name):
    names=[n for n,sort in src["states"]]
    v={name:state for name,state in zip(names,src["now"])}
    if name=="jm2006_variant_true-unreach-call_true-termination.sl":
        if names!=["i","j","x","y","z"]:raise RuntimeError("JMM2006_ORIGINAL_VARIABLE_SIGNATURE_CHANGED")
        inv=z3.And(v["x"]+v["z"]==v["i"],v["y"]+2*v["z"]==v["j"])
        label="POSTHOC_EXACT_SOURCE_MANUAL_TWO_AFFINE_CONSERVATION_RELATIONS"
    elif name=="terminator_03_true-unreach-call_true-termination.sl":
        if names!=["x","y"]:raise RuntimeError("TERMINATOR03_ORIGINAL_SIGNATURE_CHANGED")
        inv=z3.BoolVal(True)
        label="SOURCE_POSTCONDITION_IS_LOGICAL_TAUTOLOGY_NOT_AN_UNSAFE_ORIGINAL"
    else:raise RuntimeError("UNKNOWN_MANUALLY_PRE_REGISTERED_TRUE_SAFE_CASE")
    accepted,three=verified_3vc(src,native,inv)
    return {
       "candidate_label":label,
       "source_exact_posthoc_invariant_AST_SHA256":hashlib.sha256(inv.sexpr().encode()).hexdigest(),
       "independent_original_full_native_source_Z3_cvc5_three_VCs":three,
       "actual_original_SAFE_dual_3VC_proven":bool(accepted),
       "candidate_expression_was_posthoc_NOT_learned":True}

def one(root,item,claim):
    start=time.perf_counter_ns()
    report={"source":item["path"],"original_git_blob":item["git_blob"],
            "status":"UNKNOWN","no_falsification_hidden":True}
    try:
        if claim["path"]!=item["path"] or claim["git_blob"]!=item["git_blob"]:
            raise RuntimeError("ORIGINAL_POSTHOC_HYPOTHESIS_NOT_IDENTICAL_SOURCE")
        src,native,auth=compile_authentic(root,item)
        report["true_actual_original_independent_compilation"]=auth
        if claim["hypothesis"]=="ACTUAL_UNSAFE_DEPTH_1":
            rec=unsafe_bmc_one(src,native)
            report["complete_actual_original_1transition_path"]=rec
            report["status"]="TRUE_ORIGINAL_INDEPENDENTLY_DUAL_GROUNDED_UNSAFE" if rec[
                "verified_concrete_full_original_BMC_witness"] else "UNKNOWN_ORIGINAL_BMC_UNPROVEN"
        else:
            rec=safe_invariant(src,native,item["path"].split("/")[-1])
            report["true_original_posthoc_full_inductive_proof"]=rec
            report["status"]="TRUE_ORIGINAL_INDEPENDENTLY_DUAL_INDUCTIVE_SAFE" if rec[
                "actual_original_SAFE_dual_3VC_proven"] else "UNKNOWN_ORIGINAL_3VC_UNPROVEN"
    except Exception as e:
        report["status"]="UNKNOWN_ORIGINAL_ERROR"
        report["error"]=type(e).__name__+":"+str(e)[:450]
    report["whole_original_source_and_independent_dual_wall_ms"]=ms(start)
    print("Q3_FRESH_SECOND12_PREVIOUS_UNKNOWN",item["path"],"STATUS",report["status"],
          "ERROR",report.get("error"),flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    for k in ("root","freeze","hypotheses","prior","out"):p.add_argument("--"+k,required=True)
    a=p.parse_args()
    prior_raw=Path(a.prior).read_bytes()
    if hashlib.sha256(prior_raw).hexdigest()!=PREVIOUS_SHA:
        raise RuntimeError("IMMUTABLE_FIRST_NEW_ORIGINAL12_RUN_RESULTS_CHANGED")
    original=json.loads(prior_raw)
    manifest=json.loads(Path(a.freeze).read_text())
    hypotheses=json.loads(Path(a.hypotheses).read_text())
    assert len(manifest["new_originals"])==12
    assert len(original["fresh_programs"])==12 and hypotheses["schema"]==(
        "neumann.q3.second_firstsource12_four_POSTHOC_original_unknown_source_native_triage_v1")
    first={z["source"]:z for z in original["fresh_programs"]}
    frozen={z["path"]:z for z in manifest["new_originals"]}
    assert set(first)==set(frozen)
    prior_SAFE={name for name,z in first.items() if z.get(
         "all_matched_originals_full_inductive_success",{}).get("hybrid") is True}
    remain=set(first)-prior_SAFE
    if len(prior_SAFE)!=8 or len(remain)!=4:
        raise RuntimeError("FIRST_OBSERVATION_EIGHT_SAFE_FOUR_UNKNOWN_NOT_PRESERVED")
    fixed=hypotheses["four_unchanged_source_posthoc_hypotheses"]
    if {z["path"] for z in fixed}!=remain:raise RuntimeError("NEW_CLAIMS_NOT_EXACT_PREVIOUSLY_UNKNOWN")
    rows=[one(Path(a.root),frozen[q["path"]],q) for q in fixed]
    s=sum(r["status"]=="TRUE_ORIGINAL_INDEPENDENTLY_DUAL_INDUCTIVE_SAFE" for r in rows)
    u=sum(r["status"]=="TRUE_ORIGINAL_INDEPENDENTLY_DUAL_GROUNDED_UNSAFE" for r in rows)
    report={
        "schema":"neumann.q3.second_12_first_source_original_complete_true_SAFE_UNSAFE_partition_v1",
        "original_git_SHA_frozen_before_first_source_BODIES":True,
        "first_original_source_historical_run":39582778316,
        "unchanged_historical_first_run_eight_certified_safe":len(prior_SAFE),
        "four_genuine_original_previous_UNKNOWN":len(remain),
        "new_posthoc_original_safe_native_3VC":s,
        "new_posthoc_original_unsafe_grounded_full_native_paths":u,
        "all_original_twelve_truly_certified_SAFE_or_UNSAFE":len(prior_SAFE)+s+u,
        "remaining_original_12_UNRESOLVED":12-(len(prior_SAFE)+s+u),
        "no_neural_trained_structure_or_unique_math":True,
        "external_published_theorem_premises":0,
        "source_first_blind_cohort_but_followup_posthoc_manual_source_inspected":True,
        "original_previous_history_never_rewritten":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "four_posthoc_original_source_proof_records":rows
    }
    Path(a.out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for key in ("unchanged_historical_first_run_eight_certified_safe",
                "new_posthoc_original_safe_native_3VC",
                "new_posthoc_original_unsafe_grounded_full_native_paths",
                "all_original_twelve_truly_certified_SAFE_or_UNSAFE",
                "remaining_original_12_UNRESOLVED"):
        print("Q3_SECOND12_GENUINE_ORIGINAL",key,report[key])
    print("GLOBAL_LEARNED_Q3_STILL",report["global_Q3"])
if __name__=="__main__":main()
