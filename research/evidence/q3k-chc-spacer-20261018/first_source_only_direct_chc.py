"""Q3K: original C source -> direct variable-arity CHC/SPACER reachability.

This is an independently specialized CLASSICAL algorithm, without any human
invariant, learned model or published answer label. Safety is PROVEN only if
all original exit, step-overflow and prelude-overflow checks are UNSAT.
"""
from __future__ import annotations
import argparse,hashlib,io,json,sys,time,zipfile
from pathlib import Path
import z3,z3.z3util

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
from replay_real_c_loop_invariants import (
    model_original,signed_domain,MIN_INT,MAX_INT,Unsupported
)
SOURCE="dataset/loop_invariants/LinearArbitrary-SeaHorn/loops/loops/sum04_true-unreach-call_true-termination.i.annot.c"
SOURCE_SHA="7b1ed83d1a2e80a1e5aa97e27a23c7ac1a53bd734cc95808ecce4aa868c41a23"
DATASET_BLOB="17cac0f6734a39f0fe73558199cc2ad8d5c1a810"
MAX_BMC=64
QUERY_MS=15000

def substitute(e,heads,new):
    return z3.substitute(e,*[(heads[n],new[n]) for n in heads])

def signed_bad(exprs):
    return z3.Or(*[z3.Or(x<MIN_INT,x>MAX_INT) for x in exprs]) if exprs else z3.BoolVal(False)

def partition_arithmetic(model):
    pre,step=[],[]
    # Exact original Q3H C AST frontend collects both prelude and loop
    # expressions; separate them based on distinct variable namespaces.
    heads={v.decl().name() for v in model["loop_state"].values()}
    for term in model["arithmetic_expressions"]:
        syms={v.decl().name() for v in z3.z3util.get_vars(term)}
        if syms&heads:step.append(term)
        else:pre.append(term)
    return pre,step

def model_semantics(original):
    m=model_original(original,"1")
    names=tuple(sorted(m["loop_state"]))
    head=m["loop_state"]
    ini=m["after_prelude"]
    preexpr,step=partition_arithmetic(m)
    assumptions=z3.And(*signed_domain(m["initial"]),*m["init_assumptions"])
    pre_bad=signed_bad(preexpr)
    init_signed=z3.And(*signed_domain(ini))
    s=z3.Solver();s.set(timeout=5000)
    s.add(assumptions,z3.Or(pre_bad,z3.Not(init_signed)))
    prelude_status=str(s.check())
    # Never obscure prelude errors by restricting the initial reach relation.
    base=z3.And(assumptions,z3.Not(pre_bad),init_signed)
    return m,names,base,prelude_status,step

def source_fixedpoint(m,names,base,arith,requested=("exit_safety","signed_step_overflow")):
    h=m["loop_state"]
    init=m["after_prelude"]
    vals=[h[n] for n in names]
    nextvals=[m["body_state"][n] for n in names]
    reach=z3.Function("Q3K_Reach",*[z3.IntSort() for _ in names],z3.BoolSort())
    exitbad=z3.Function("Q3K_BadExit",z3.BoolSort())
    overbad=z3.Function("Q3K_BadOverflow",z3.BoolSort())
    fp=z3.Fixedpoint()
    fp.set(engine="spacer",timeout=QUERY_MS)
    fp.register_relation(reach,exitbad,overbad)
    free={v.decl().name():v for t in (
        base,m["loop_test"],m["post_assert"],*nextvals,*arith
    ) for v in z3.z3util.get_vars(t)}
    fp.declare_var(*list(free.values()))
    bodybad=z3.Or(signed_bad(arith),*[
        z3.Or(v<MIN_INT,v>MAX_INT) for v in nextvals])
    rec=reach(*vals)
    fp.rule(reach(*[init[n] for n in names]),base)
    fp.rule(overbad(),z3.And(rec,m["loop_test"],bodybad))
    fp.rule(reach(*nextvals),z3.And(rec,m["loop_test"],z3.Not(bodybad)))
    fp.rule(exitbad(),z3.And(rec,z3.Not(m["loop_test"]),
                              z3.Not(m["post_assert"])))
    result={}
    for title,goal in (("exit_safety",exitbad()),("signed_step_overflow",overbad())):
        if title not in requested:continue
        started=time.perf_counter_ns()
        try:
            q=fp.query(goal)
            status=str(q)
            reason=fp.reason_unknown() if q==z3.unknown else None
        except Exception as e:
            status="error"
            reason=f"{type(e).__name__}: {str(e)[:200]}"
        result[title]={"bad_state_query":status,
                       "reason":reason,
                       "wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}
    result["quantified_original_relation_arity"]=len(names)
    result["original_relation_state_names"]=names
    result["registered_chc_relations"]=3
    return result

def bounded_reachability(m,names,base,arith):
    # Independent exact symbolic unroll of all originally modeled transitions.
    # NO original trace is claimed safe beyond the maximum checked depth.
    h=m["loop_state"]
    solver=z3.Solver();solver.set(timeout=1000)
    at={n:z3.Int(f"q3k_bmc_state_0_{n}") for n in names}
    solver.add(base)
    for n in names:
        solver.add(at[n]==m["after_prelude"][n])
    seen=0
    for depth in range(MAX_BMC+1):
        guard=substitute(m["loop_test"],h,at)
        post=substitute(m["post_assert"],h,at)
        solver.push()
        solver.add(z3.Not(guard),z3.Not(post))
        ans=solver.check()
        if ans==z3.sat:
            mm=solver.model()
            witness={n:int(mm.eval(at[n],model_completion=True).as_long()) for n in names}
            solver.pop()
            return {"classification":"ACTUAL_REACHABLE_BAD_EXIT_WITHIN_BOUND",
                    "checked_exact_depths":depth+1,"earliest_bad_depth":depth,
                    "source_state_at_exit":witness}
        if ans==z3.unknown:
            solver.pop()
            return {"classification":"BMC_SOLVER_UNKNOWN",
                    "checked_exact_depths":depth+1,"reason":solver.reason_unknown()}
        solver.pop()
        seen+=1
        if depth==MAX_BMC:break
        nextstate={n:z3.Int(f"q3k_bmc_state_{depth+1}_{n}") for n in names}
        bad=signed_bad([substitute(v,h,at) for v in arith])
        solver.add(guard,z3.Not(bad))
        for n in names:
            solver.add(nextstate[n]==substitute(m["body_state"][n],h,at))
        solver.add(*signed_domain(nextstate))
        at=nextstate
    return {"classification":"NO_BAD_EXIT_REACHABLE_UP_TO_BOUND_NOT_A_GLOBAL_PROOF",
            "checked_exact_depths":seen,
            "maximum_unrolling_depth":MAX_BMC}

def audit(original,source_sha):
    if hashlib.sha256(original).hexdigest()!=source_sha:
        raise ValueError("ORIGINAL_SOURCE_IDENTITY_MISMATCH")
    m,names,base,prestatus,arith=model_semantics(
        original.decode("utf-8",errors="strict"))
    t0=time.perf_counter_ns()
    chcs=source_fixedpoint(m,names,base,arith)
    bmc=bounded_reachability(m,names,base,arith)
    exitstatus=chcs["exit_safety"]["bad_state_query"]
    overstatus=chcs["signed_step_overflow"]["bad_state_query"]
    if bmc["classification"]=="ACTUAL_REACHABLE_BAD_EXIT_WITHIN_BOUND" and exitstatus=="unsat":
        raise RuntimeError("CLASSICAL_SPACER_DISAGREES_WITH_EXACT_BMC")
    if prestatus=="unsat" and exitstatus=="unsat" and overstatus=="unsat":
        verdict="CLASSICAL_SPECIALIST_FULL_ORIGINAL_PROVEN"
    elif prestatus=="sat" or exitstatus=="sat" or overstatus=="sat":
        verdict="ACTUAL_ERROR_REACHABILITY_REPORTED_NOT_SAFE"
    else:
        verdict="UNKNOWN_OR_BLOCKED_NO_FULL_ORIGINAL_PROOF"
    return {
        "status":verdict,"original_source_sha256":source_sha,
        "original_C_source_bytes_changed":False,
        "source_original_label_read":False,
        "source_state_variables":names,
        "original_c_semantics":"Q3H bounded integer C AST subset; excludes unsupported C, tests signed-int overflow",
        "prelude_bad_query":prestatus,
        "fixedpoint_engine":"Z3_SPACER",
        "direct_chc":chcs,
        "bounded_reachability":bmc,
        "full_audit_wall_ms":round((time.perf_counter_ns()-t0)/1e6,3),
        "zero_neural_calls":True,"all_global_q1_q7":"OPEN"
    }

def controls():
    cases={
       "reachable_wrong_exit":("int main(void){int i=0;while(i<2){i++;}\n//@ assert (i==1);\nreturn 0;}", "sat", "unsat"),
       "safe_correct_exit":("int main(void){int i=0;while(i<2){i++;}\n//@ assert (i==2);\nreturn 0;}", "unsat", "unsat"),
       "genuine_signed_overflow":("int main(void){int i=2147483647;while(i>=0){i++;}\n//@ assert (i<0);\nreturn 0;}", "unsat", "sat"),
    }
    output={}
    for name,(source,expected_exit,expected_overflow) in cases.items():
        m,names,base,prestatus,arith=model_semantics(source)
        report=source_fixedpoint(m,names,base,arith)
        observed=(report["exit_safety"]["bad_state_query"],
                  report["signed_step_overflow"]["bad_state_query"])
        output[name]={"actual":observed,"expected":(expected_exit,expected_overflow),
                      "pass":observed==(expected_exit,expected_overflow)
                      and prestatus=="unsat"}
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    dataset=args.dataset.read_bytes()
    head=b"blob "+str(len(dataset)).encode()+b"\x00"
    if hashlib.sha1(head+dataset).hexdigest()!=DATASET_BLOB:
        raise ValueError("PINNED_LOOPY_DATASET_BLOB_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(dataset)) as archive:
        original=archive.read(SOURCE)
    result={"experiment":"Q3K_DIRECT_SOURCE_ONLY_REACHABILITY_FIRST",
            "source_path":SOURCE,
            "original_sha256":SOURCE_SHA,
            "source_repository_revision":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
            "frozen_before_source_execution":True,
            "source_mathematical_target_invariants_never_read":True,
            "q3f_chc_comp_escrow_targets_remain_unopened":True,
            "model_training_or_inference":0,"all_global_q1_q7":"OPEN"}
    result["control_results"]=controls()
    if not all(x["pass"] for x in result["control_results"].values()):
        result["main"]={"status":"BLOCKED_VERIFIER_CONTROL"}
    else:
        try:result["main"]=audit(original,SOURCE_SHA)
        except Exception as ex:
            result["main"]={"status":"BLOCKED_OR_UNSUPPORTED",
                            "error":f"{type(ex).__name__}: {str(ex)[:500]}"}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3K_CONTROLS",[(k,v["actual"],v["pass"]) for k,v in result["control_results"].items()])
    print("Q3K_ACTUAL_ORIGINAL",result["main"]["status"])
    if "direct_chc" in result["main"]:
        print("Q3K_SPACER",result["main"]["direct_chc"])
        print("Q3K_BMC",result["main"]["bounded_reachability"])
    print("Q1_Q7",result["all_global_q1_q7"])

if __name__=="__main__":main()
