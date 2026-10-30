#!/usr/bin/env python3
"""Four original external invariant one-sided pre-synthesis viability filter.

Sound YES: there exists pre(s)&trans(s,s')&!post(s') => impossible safety
inductive invariant independent of grammar. NO one-step violation proves only
bounded one-step safety, not invariant existence. Both Z3 and CVC5 agree or HOLD.
"""
import collections,json,pathlib,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    form_name,parameter_signature
)
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_4invariants_one_step_triage")
def call(n,v):
    return "("+n+" "+" ".join(v)+")"
def study(row):
    import z3
    path=row["original"]
    raw=(ROOT/path).read_bytes()
    assert sha256(raw)==row["source_sha256"]
    terms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    synth=[f for c,f in terms if c=="synth-inv"]
    inv=[f for c,f in terms if c=="inv-constraint"]
    assert len(synth)==1 and len(inv)==1
    head=top_level_forms(inv[0][1:-1])
    # inv-constraint is flat; parse the four identifiers from source,
    # never replace the author original helper equations.
    import re
    m=re.fullmatch(r"\(\s*inv-constraint\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",inv[0])
    assert m
    invname,pre,trans,post=m.groups()
    sig=parameter_signature(synth[0],"synth-inv",invname)
    n=len(sig);sorts=[s for _,s in sig]
    source_defs=[f for c,f in terms if c=="define-fun"]
    fun={form_name(f,"define-fun"):f for f in source_defs}
    assert all(k in fun for k in (pre,trans,post))
    for key,correct in [(pre,sorts),(trans,sorts+sorts),(post,sorts)]:
        assert [s for _,s in parameter_signature(fun[key],"define-fun",key)]==correct
    state=["__n1_t0_"+str(i) for i in range(n)]
    next_state=["__n1_t1_"+str(i) for i in range(n)]
    decl=["(declare-const "+v+" "+sort+")" for v,sort in zip(state+next_state,sorts+sorts)]
    query="\n".join(["(set-logic ALL)"]+source_defs+decl+[
        "(assert "+call(pre,state)+")",
        "(assert "+call(trans,state+next_state)+")",
        "(assert (not "+call(post,next_state)+"))",
    ])+"\n"
    tag=row["original"].split("/")[-1].replace(".","_")
    p=OUT/(tag+"__original_pre_trans_not_post.smt2")
    p.write_text(query+"(check-sat)\n")
    t=time.monotonic()
    solver=z3.Solver();solver.set(timeout=10000)
    solver.add(*z3.parse_smt2_string(query))
    zans=str(solver.check())
    zsec=round(time.monotonic()-t,6)
    values=None
    if zans=="sat":
        m=solver.model()
        # Including ALL original state symbols prevents cherry picking a witness
        values={x:str(m.eval(z3.Const(x,z3.IntSort() if ty=="Int" else z3.BoolSort()),model_completion=True))
                for x,ty in zip(state+next_state,sorts+sorts)}
    t=time.monotonic()
    try:
        r=subprocess.run(["cvc5","--lang=smt2",str(p)],
                         capture_output=True,text=True,timeout=10,errors="replace")
        lines=[x.strip() for x in r.stdout.splitlines() if x.strip()]
        cans=lines[-1] if r.returncode==0 and lines else "HOLD_CVC5_EXEC"
        cerr=r.stderr[-400:]
        exitcode=r.returncode
    except subprocess.TimeoutExpired as ex:
        cans="HOLD_CVC5_TIMEOUT";cerr=str(ex);exitcode=None
    csec=round(time.monotonic()-t,6)
    if zans==cans=="sat":verdict="NO_SAFE_INDUCTIVE_INVARIANT_IN_ANY_GRAMMAR"
    elif zans==cans=="unsat":verdict="NO_ONE_STEP_UNSAFE_REACHABLE__LONGER_HORIZONS_UNTESTED"
    else:verdict="HOLD_SOLVER_CONFLICT_OR_UNKNOWN"
    print("INVARIANT_ONE_STEP",tag,zans,cans,verdict,flush=True)
    return {
      "index":row["index"],"source":path,"source_sha256":row["source_sha256"],
      "actual_first_native_status":row["status"],
      "n_original_state_variables":n,
      "full_original_smt_query_sha256":sha256(p.read_bytes()),
      "z3_result":zans,"z3_wall_seconds":zsec,
      "cvc5_result":cans,"cvc5_wall_seconds":csec,
      "cvc5_exitcode":exitcode,"cvc5_stderr":cerr,
      "model_all_source_state_variables":values,
      "verdict":verdict,"source_query_file":p.name,
    }
def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    ver=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert ver.startswith("cvc5 1.4.2 ")
    first=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(first)==FIRST_SHA
    data=json.loads(first)
    assert tuple(r["original"] for r in data["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    results=[study(data["rows"][i]) for i in (4,5,6,7)]
    counts=dict(collections.Counter(x["verdict"] for x in results))
    report={
      "intent":"sound one-step safety impossibility prepass, four FULL ORIGINAL xujie invariants",
      "source_pin":PIN,"original_first_sha256":FIRST_SHA,
      "independent_engines":["Z3 "+z3.get_version_string(),ver],
      "source_native_candidates_replaced":False,
      "SAT_soundness":"any invariant closed under original transition and holding on all original init states would include bad post state: contradiction",
      "UNSAT_nonimplication":"one-step UNSAT does not prove original synthesis realizable or global safety",
      "count":4,"summary":counts,
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "cases":results}
    p=OUT/"EXTERNAL4_ORIGINAL_INVARIANTS_SOUND_ONE_STEP_TRIAGE_TWO_SOLVERS.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("FOUR_INVARIANTS_ONE_STEP_SHA256",sha256(p.read_bytes()))
    print("FOUR_INVARIANTS_ONE_STEP_SUMMARY",json.dumps(counts,sort_keys=True))
if __name__=="__main__":main()
