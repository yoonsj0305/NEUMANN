#!/usr/bin/env python3
"""Separate POST-FIRST efficient original evaluator of SEALED SGI12 source-only policy.
This script does NOT participate in first predictions, original cvc5 search or query
decisions. Source correctness checked in one fresh independent Z3 obligation per arm.
"""
import hashlib,json,pathlib,subprocess,sys,time,os
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import (
  ROOT,FIRST,SCORED,PIN,source_pick,sha256,top_level_forms,get_cmd,
  io_form,source_without_forms,helpers_for,proposal_function,bounded_cvc5,model_eval
)

FIRST_HASH=os.environ.get("SEALED_FIRST_SHA256")
def source_verified(z3,helper,candidate,bodies):
    z3script=helper+"\n"+candidate+"\n(assert (not (and "+" ".join(bodies)+")))\n"
    ctx=z3.Context()
    try:
        s=z3.Solver(ctx=ctx);s.set(timeout=5000)
        s.add(*z3.parse_smt2_string(z3script,ctx=ctx))
        return str(s.check())=="unsat"
    finally:
        ctx=None

def body(original):
    import re
    m=re.fullmatch(r"\(\s*constraint\s+(.*)\s*\)",original,re.S)
    if not m:raise ValueError("Not simple constraint")
    return m.group(1)

def grade_one(r,z3):
    o={"index":r["index"],"path":r["path"],"first_decision":r["query_decision"],
       "first_prediction_sha256":r["proposals"][0].get("stdout_sha256") if r["proposals"] else None}
    if r["status"]!="ELIGIBLE":
        o["status"]="INELIGIBLE";return o
    p=ROOT/r["path"];original=p.read_bytes()
    if sha256(original)!=r["original_sha256"]:raise ValueError("ORIGINAL_SHA_MISMATCH")
    forms=top_level_forms(original.decode("utf-8"))
    cs=[f for f in forms if get_cmd(f[2])=="constraint"]
    assert len(cs)==r["n_constraints"]
    vals=[io_form(f[2]) for f in cs]
    assert vals[-2][0]==r["probe_input"] and vals[-1][0]==r["future_input"]
    assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
    assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
    source=source_without_forms(original.decode("utf-8"),cs[-2:])
    assert sha256(source.encode())==r["source_only_sha256"]
    helper=helpers_for(source)
    out=(FIRST/f"{r['index']:02d}_0.stdout").read_bytes()
    assert sha256(out)==r["proposals"][0]["stdout_sha256"]
    o["original_constraint_count"]=len(cs)
    o["probe_input_new"]=vals[-2][0] not in {v[0] for v in vals[:-2]}
    o["future_input_new"]=vals[-1][0] not in {v[0] for v in vals[:-1]}
    try:
        c0=proposal_function(out.decode("utf8","replace"))
        o["c0_source_verified"]=source_verified(z3,helper,c0,[body(f[2]) for f in cs[:-2]])
        y0=model_eval(helper,c0,vals[-1][0])
        o["c0"]="EXACT" if o["c0_source_verified"] and y0==vals[-1][1] else "WRONG"
        o["c0_pred"]=y0
    except Exception as e:
        o["c0"]="HOLD";o["c0_error"]=type(e).__name__+":"+str(e)[:100]
    # C1 comparator always permitted one extra original probe label, on all cases;
    # C_active pays that label+refit only if the PRE-GRADE frozen decision said so.
    source_probe=source_without_forms(original.decode("utf8"),[cs[-1]])
    path=SCORED/f"source+probe_{r['index']:02d}.sl"
    path.write_text(source_probe)
    try:
        a,b,cost=bounded_cvc5(path,["--seed=0"])
    finally:
        path.unlink()
    o["c1_refit_cost"]=cost
    try:
        if cost["exit_code"]!=0 or cost["forced"]:raise ValueError("CVC5_C1_REFIT_FAIL")
        c1=proposal_function(a)
        h1=helpers_for(source_probe)
        o["c1_source_verified"]=source_verified(z3,h1,c1,[body(f[2]) for f in cs[:-1]])
        y1=model_eval(h1,c1,vals[-1][0])
        o["c1_pred"]=y1
        o["c1"]="EXACT" if o["c1_source_verified"] and y1==vals[-1][1] else "WRONG"
    except Exception as e:
        o["c1"]="HOLD";o["c1_error"]=type(e).__name__+":"+str(e)[:100]
    if r["query_decision"]=="SKIP_UNANIMOUS_THREE":
        o["active"]=o["c0"];o["active_queries"]=0
    elif r["query_decision"]=="REQUEST_ONE_DIVERGENCE_OR_UNCERTAIN":
        o["active"]=o["c1"];o["active_queries"]=1
    else:
        o["active"]="HOLD";o["active_queries"]=0
    o["status"]="GRADED";return o

def main():
    import z3
    if FIRST_HASH is None:raise RuntimeError("PRE_GRADE_FIRST_NOT_SEALED")
    raw=(FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json").read_bytes()
    assert sha256(raw)==FIRST_HASH
    frozen=json.loads(raw)
    assert frozen["upstream"]==PIN and frozen["graded_final"]=="NOT_RUN"
    assert subprocess.check_output(["git","-C","upstream","rev-parse","HEAD"],text=True).strip()==PIN
    names=[p.relative_to(ROOT).as_posix() for p in source_pick()]
    assert names==[r["path"] for r in frozen["rows"]] and len(names)==12
    SCORED.mkdir(exist_ok=True)
    result=[]
    for r in frozen["rows"]:
        try:
            o=grade_one(r,z3)
        except Exception as e:
            o={"index":r["index"],"path":r["path"],"status":"HOLD_GRADE_EXCEPTION",
               "error_type":type(e).__name__,"error_detail":str(e)[:200]}
        result.append(o)
        print("ORIGINAL_GRADE",o["index"],o["path"],o.get("c0"),o.get("c1"),o.get("active"),o.get("active_queries"),o["status"],flush=True)
    def counts(name):return dict(Counter(o.get(name,"INELIGIBLE") for o in result))
    spent=sum(o.get("active_queries",0) for o in result)
    full=sum(o["status"]=="GRADED" for o in result)
    c0_cpu=sum(sum(p.get("cpu_user_s",0)+p.get("cpu_sys_s",0) for p in r["proposals"][:1]) for r in frozen["rows"])
    active_initial_cpu=sum(sum(p.get("cpu_user_s",0)+p.get("cpu_sys_s",0) for p in r["proposals"]) for r in frozen["rows"])
    full_refit_cpu=sum(o.get("c1_refit_cost",{}).get("cpu_user_s",0)+o.get("c1_refit_cost",{}).get("cpu_sys_s",0) for o in result)
    active_refit_cpu=sum((o.get("c1_refit_cost",{}).get("cpu_user_s",0)+o.get("c1_refit_cost",{}).get("cpu_sys_s",0)) for o in result if o.get("active_queries")==1)
    report={
     "description":"Original unseen-after-prereg SGI12 hard classical source-only versions and conditional original oracle, no NEUMANN weights",
     "source_commit":PIN,"sealed_first_sha256":FIRST_HASH,"denominator":12,
     "c0":counts("c0"),"c1":counts("c1"),"active":counts("active"),
     "queries_active":spent,"queries_full":full,
     "c0_process_cpu_s":round(c0_cpu,6),
     "c1_incremental_refit_cpu_s":round(full_refit_cpu,6),
     "active_3arm_initial_process_cpu_s":round(active_initial_cpu,6),
     "active_additional_refit_cpu_s":round(active_refit_cpu,6),
     "cpu_excludes_input_setup_z3_verification_runner_overhead_energy_and_cost":True,
     "scope":"PROJECT_FAMILY_ONLY_NOT_NEURAL_OR_FRONTIER",
     "neural_training":False,"global_Q1_Q7":"OPEN","G1":"HOLD","rows":result
    }
    p=SCORED/"POSTFIRST_ORIGINAL_ACTIVE_ORACLE_GRADE.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("GRADE_SHA256",sha256(p.read_bytes()))
    print("SUMMARY",json.dumps({k:report[k] for k in ("c0","c1","active","queries_active","queries_full","c0_process_cpu_s","c1_incremental_refit_cpu_s","active_3arm_initial_process_cpu_s","active_additional_refit_cpu_s")},sort_keys=True),flush=True)
if __name__=="__main__":main()
