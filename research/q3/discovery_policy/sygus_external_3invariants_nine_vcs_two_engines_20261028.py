#!/usr/bin/env python3
"""Post-FIRST replay full original independent xujie inductive VCs ×3×2 engines.

No synthesis in this run. Native candidates/source untouched from prior FIRST.
Both Z3 4.13.3 and cvc5 1.4.2 independently test existential violations.
"""
import hashlib,json,pathlib,re,subprocess,sys,time,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    parameter_signature,form_name,unwrap_native)

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_invariant3_two_provers")
TARGETS=(5,6,7)
OBLIGATIONS=("INITIALIZATION","INDUCTIVE_STEP","SAFETY")

def call(name,terms):
    return "("+name+" "+" ".join(terms)+")"

def prove(query,p):
    import z3
    p.write_text(query)
    zstart=time.monotonic()
    try:
        solver=z3.Solver()
        solver.set(timeout=8000)
        solver.add(*z3.parse_smt2_string(query))
        zans=str(solver.check())
        zerr=None
    except Exception as ex:
        zans="HOLD_EXCEPTION";zerr=type(ex).__name__+":"+str(ex)[:250]
    ztime=round(time.monotonic()-zstart,6)
    cstart=time.monotonic()
    try:
        r=subprocess.run(["cvc5","--lang=smt2",str(p)],capture_output=True,
                         text=True,timeout=8.5,errors="replace")
        lines=[x.strip() for x in r.stdout.splitlines() if x.strip()]
        cans=lines[-1] if r.returncode==0 and lines else "HOLD_NATIVE_ERROR"
        cerr=r.stderr[-400:]
        exitcode=r.returncode
    except subprocess.TimeoutExpired as ex:
        cans="HOLD_TIMEOUT";cerr=str(ex)[:200];exitcode=None
    ctime=round(time.monotonic()-cstart,6)
    return {"source_smt_sha256":sha256(query.encode()),"smt_file":p.name,
            "z3_answer":zans,"z3_elapsed_wall_s":ztime,
            "z3_error":zerr,"cvc5_answer":cans,"cvc5_elapsed_wall_s":ctime,
            "cvc5_returncode":exitcode,"cvc5_stderr_excerpt":cerr,
            "passes_both_solvers":zans==cans=="unsat"}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    data=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(data)==FIRST_SHA
    first=json.loads(data)
    OUT.mkdir(exist_ok=True)
    cases=[]
    for i in TARGETS:
        row=first["rows"][i]
        assert row["status"]=="STRONG_C_CANDIDATE_UNVERIFIED"
        original=(ROOT/row["original"]).read_bytes()
        assert sha256(original)==row["source_sha256"]
        terms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(original.decode())]
        orig_synth=[f for c,f in terms if c=="synth-inv"]
        orig_invcon=[f for c,f in terms if c=="inv-constraint"]
        assert len(orig_synth)==len(orig_invcon)==1
        m=re.fullmatch(r"\(\s*inv-constraint\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",orig_invcon[0])
        assert m
        i_name,pre,trans,post=m.groups()
        assert form_name(orig_synth[0],"synth-inv")==i_name
        sig=parameter_signature(orig_synth[0],"synth-inv",i_name)
        n=len(sig);assert n>0
        defined={form_name(f,"define-fun"):f for c,f in terms if c=="define-fun"}
        assert all(x in defined for x in (pre,trans,post))
        sorts=[t for _,t in sig]
        assert [t for _,t in parameter_signature(defined[pre],"define-fun",pre)]==sorts
        assert [t for _,t in parameter_signature(defined[trans],"define-fun",trans)]==sorts+sorts
        assert [t for _,t in parameter_signature(defined[post],"define-fun",post)]==sorts
        old=(FIRST/(f"{i:02d}_cvc5.stdout")).read_bytes()
        assert sha256(old)==row["native_cost"]["stdout_sha256"]
        defs=unwrap_native(old.decode())
        assert len(defs)==1 and form_name(defs[0],"define-fun")==i_name
        candidate=defs[0]
        assert [s for _,s in parameter_signature(candidate,"define-fun",i_name)]==sorts
        states=["__n1proof_x"+str(k) for k in range(n)]
        states2=["__n1proof_y"+str(k) for k in range(n)]
        decl=["(declare-const "+name+" "+sort+")" for name,sort
              in zip(states+states2,sorts+sorts)]
        additional=[re.sub(r"^\(\s*declare-var\b","(declare-const",f,count=1)
                    for c,f in terms if c=="declare-var"]
        start="\n".join(["(set-logic ALL)"]+additional+[f for c,f in terms if c=="define-fun"]+[candidate]+decl)+"\n"
        violations=[
            "(and "+call(pre,states)+" (not "+call(i_name,states)+"))",
            "(and "+call(i_name,states)+" "+call(trans,states+states2)+" (not "+call(i_name,states2)+"))",
            "(and "+call(i_name,states)+" (not "+call(post,states)+"))",
        ]
        checks=[]
        for kind,formula in zip(OBLIGATIONS,violations):
            script=start+"(assert "+formula+")\n(check-sat)\n"
            path=OUT/(f"{i:02d}_{kind}.smt2")
            result=prove(script,path)
            result["obligation"]=kind
            checks.append(result)
            print("INVARIANT_ORIGINAL_BOTH_ENGINES",i,kind,result["z3_answer"],result["cvc5_answer"],flush=True)
        cases.append({
            "index":i,"original":row["original"],"original_source_sha256":row["source_sha256"],
            "native_program_sha256":sha256(old),
            "original_candidate_definition_sha256":sha256(candidate.encode()),
            "complete_original_three_VCs":checks,
            "three_original_VCs_pass_both_engines":all(x["passes_both_solvers"] for x in checks),
            "original_candidate_grammar_membership_proved":False})
    pass_all=all(c["three_original_VCs_pass_both_engines"] for c in cases)
    report={"research":"POSTFIRST_THREE_OFFICIAL_ORIGINAL_INVARIANTS_SECOND_SMT_BACKEND",
            "source_repository":"SyGuS-Org/benchmarks","original_pin":PIN,
            "immutable_original_first_sha256":FIRST_SHA,"Z3_version":z3.get_version_string(),
            "official_cvc5_version":subprocess.check_output(["cvc5","--version"],text=True).strip().splitlines()[0],
            "original_invariants":3,"total_full_original_inductive_obligations":9,
            "two_engine_concordant_proven_UNSAT":sum(sum(x["passes_both_solvers"] for x in c["complete_original_three_VCs"]) for c in cases),
            "result":"NINE_FULL_ORIGINAL_VCS_UNSAT_BOTH" if pass_all else "HOLD_SOLVER_DISAGREEMENT",
            "no_new_learning":True,"G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
            "cases":cases}
    p=OUT/"THREE_EXTERNAL_ORIGINAL_INVARIANTS_NINE_VCS_CVC5_Z3.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("NINE_ORIGINAL_VCS_RECEIPT_SHA256",sha256(p.read_bytes()))
    print("NINE_ORIGINAL_VCS_VERDICT",report["result"],flush=True)
if __name__=="__main__":main()
