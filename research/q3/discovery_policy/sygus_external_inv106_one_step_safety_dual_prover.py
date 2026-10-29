#!/usr/bin/env python3
"""Formal independent post-first UNREALIZABILITY of original 106.c invariant.

One explicitly preregistered reachable one-step unsafe trace, using original
three source helpers, verified by both Z3 4.13.3 and CVC5 1.4.2.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    form_name,parameter_signature
)

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/Inv_Track/xujie_code2inv/106.c.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_inv106_one_step_unsafety")
S0=[0,0,0,1,0,0,0,0,0,1,1,1,0,1]
S1=[0,0,1,1,0,0,0,0,1,0,1,1,0,0]
NAMES="a j k m a_0 j_0 k_0 k_1 k_2 k_3 m_0 m_1 m_2 m_3".split()

def term(name,args):
    return "("+name+" "+" ".join(args)+")"

def run_z3(script):
    import z3
    start=time.monotonic()
    solver=z3.Solver();solver.set(timeout=12000)
    solver.add(*z3.parse_smt2_string(script))
    return {"verdict":str(solver.check()),
            "backend":"Z3 "+z3.get_version_string(),
            "wall_seconds":round(time.monotonic()-start,6)}

def run_cvc5(script):
    start=time.monotonic()
    r=subprocess.run(["cvc5","--lang=smt2","-"],input=script+"\n(check-sat)\n",
                     text=True,capture_output=True,timeout=15,errors="replace")
    lines=[x.strip() for x in r.stdout.splitlines() if x.strip()]
    return {"verdict":lines[-1] if r.returncode==0 and lines else "HOLD",
            "backend":subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0],
            "returncode":r.returncode,"stderr_excerpt":r.stderr[-220:],
            "wall_seconds":round(time.monotonic()-start,6)}

def main():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).startswith("cvc5 1.4.2 ")
    original=(ROOT/SOURCE).read_bytes()
    terms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(original.decode("utf8"))]
    invs=[f for c,f in terms if c=="synth-inv"]
    links=[f for c,f in terms if c=="inv-constraint"]
    assert len(invs)==1 and len(links)==1
    assert links[0]=="(inv-constraint inv-f pre-f trans-f post-f)"
    assert form_name(invs[0],"synth-inv")=="inv-f"
    sig=parameter_signature(invs[0],"synth-inv","inv-f")
    assert [name for name,sort in sig]==NAMES
    assert len(sig)==len(S0)==len(S1)==14
    assert all(sort=="Int" for _,sort in sig)
    funcs={form_name(f,"define-fun"):f for c,f in terms if c=="define-fun"}
    assert set(funcs)=={"pre-f","trans-f","post-f"}
    assert [sort for _,sort in parameter_signature(funcs["pre-f"],"define-fun","pre-f")]==["Int"]*14
    assert [sort for _,sort in parameter_signature(funcs["trans-f"],"define-fun","trans-f")]==["Int"]*28
    assert [sort for _,sort in parameter_signature(funcs["post-f"],"define-fun","post-f")]==["Int"]*14
    symbols=[f"state0_{i}" for i in range(14)]
    next_symbols=[f"state1_{i}" for i in range(14)]
    allsymbols=symbols+next_symbols
    declarations=["(declare-const "+x+" Int)" for x in allsymbols]
    fixed=["(= "+x+" "+str(v)+")" for x,v in zip(allsymbols,S0+S1)]
    unsafe="(and "+term("pre-f",symbols)+" "+term("trans-f",symbols+next_symbols)+
            " (not "+term("post-f",next_symbols)+"))"
    header="\n".join(["(set-logic ALL)",*funcs.values(),*declarations])
    # Free SAT establishes existential unsafe path. Fixed SAT demonstrates
    # published explicit 28-integer witness. Fixed negation UNSAT is direct
    # ground arithmetic verification of the specified witness.
    scripts={
        "free_one_step_existential_unsafety":(header+"\n(assert "+unsafe+")\n","sat"),
        "fixed_one_step_unsafety":(header+"\n"+"".join("(assert "+x+")\n" for x in fixed)+
                                   "(assert "+unsafe+")\n","sat"),
        "fixed_witness_conjunction_cannot_be_false":(
            header+"\n"+"".join("(assert "+x+")\n" for x in fixed)+
            "(assert (not "+unsafe+"))\n","unsat"),
    }
    OUT.mkdir(exist_ok=True)
    results=[]
    for name,(script,expected) in scripts.items():
        path=OUT/(name+".smt2")
        path.write_text(script+"(check-sat)\n")
        z=run_z3(script);c=run_cvc5(script)
        passed=z["verdict"]==c["verdict"]==expected
        results.append({"name":name,"expected":expected,"z3":z,"cvc5":c,
                        "verified":passed,"source_smt_sha256":sha256(path.read_bytes())})
        print("ORIGINAL_INV106_TWO_SOLVER_TRACE",name,z["verdict"],c["verdict"],
              "PASS" if passed else "HOLD",flush=True)
    valid=all(x["verified"] for x in results)
    report={"kind":"POSTFIRST_CLASSICAL_ORIGINAL_ONE_STEP_SAFETY_COUNTEREXAMPLE",
        "official_original_repo_git":PIN,"original_file":SOURCE,
        "original_source_sha256":sha256(original),
        "original_synth_inv":"inv-f",
        "original_state_signature":NAMES,
        "precommitted_initial":S0,"precommitted_successor":S1,
        "original_helper_bodies_unchanged":True,"both_independent_SMT_backends":True,
        "conclusion":"ORIGINAL_SAFETY_INVARIANT_UNREALIZABLE_BY_ONE_STEP_UNSAFE_TRACE"
                  if valid else "HOLD_NOT_INDEPENDENTLY_PROVED",
        "does_not_count_as_ownweight_neural_discovery":True,
        "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN","checks":results}
    p=OUT/"G1_EXTERNAL_INV106_ORIGINAL_ONE_STEP_UNSAFE_DUAL_SMT.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("INV106_FORMAL_SHA256",sha256(p.read_bytes()))
    print("INV106_FORMAL_STATUS",report["conclusion"])
if __name__=="__main__":main()
