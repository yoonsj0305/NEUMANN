#!/usr/bin/env python3
"""Exact external original 106.c.sl NO INVARIANT via reachable unsafe 1-step.

Original native CVC5 SyGuS first claims infeasible. This independent checker
derives a concrete INIT ∧ TRANS ∧ ¬POST transition from all unmodified source
helper bodies. Existence => no inv function can satisfy all 3 inductive VCs.
Uses separate Z3 4.13.3 AND official CVC5 1.4.2 (on exactly same script).
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    form_name,parameter_signature
)
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
REL="lib/Inv_Track/xujie_code2inv/106.c.sl"
FIRST=pathlib.Path("external_new16_frozen_FIRST")
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_106_unrealizability_proof")

def call(name,args):
    return "("+name+" "+" ".join(args)+")"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    native_version=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert native_version.startswith("cvc5 1.4.2 ")
    first_b=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(first_b)==FIRST_SHA
    first=json.loads(first_b)
    row=first["rows"][4]
    assert row["original"]==REL and row["status"]=="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED"
    original=(ROOT/REL).read_bytes()
    assert sha256(original)==row["source_sha256"]
    fs=[(get_cmd(f[2]),f[2]) for f in top_level_forms(original.decode("utf8"))]
    inv=[f for cmd,f in fs if cmd=="synth-inv"]
    uncon=[f for cmd,f in fs if cmd=="inv-constraint"]
    assert len(inv)==len(uncon)==1
    assert uncon[0]=="(inv-constraint inv-f pre-f trans-f post-f)"
    assert form_name(inv[0],"synth-inv")=="inv-f"
    sig=parameter_signature(inv[0],"synth-inv","inv-f")
    assert len(sig)==14 and all(sort=="Int" for name,sort in sig)
    defs=[f for cmd,f in fs if cmd=="define-fun"]
    helpers={form_name(f,"define-fun"):f for f in defs}
    assert all(k in helpers for k in ("pre-f","trans-f","post-f"))
    sorts=[t for _,t in sig]
    for key,expected in (("pre-f",sorts),("trans-f",sorts+sorts),("post-f",sorts)):
        assert [t for _,t in parameter_signature(helpers[key],"define-fun",key)]==expected
    s=["__n1bad_s"+str(i) for i in range(len(sig))]
    sn=["__n1bad_next"+str(i) for i in range(len(sig))]
    decls=["(declare-const "+n+" "+typ+")" for n,typ in zip(s+sn,sorts+sorts)]
    query="\n".join(["(set-logic ALL)"]+defs+decls+[
        "(assert "+call("pre-f",s)+")",
        "(assert "+call("trans-f",s+sn)+")",
        "(assert (not "+call("post-f",sn)+"))",
    ])+"\n"
    OUT.mkdir(exist_ok=True)
    p=OUT/"EXTERNAL_106_EXACT_ORIGINAL_ONE_STEP_UNSAFE.smt2"
    p.write_text(query+"(check-sat)\n")
    t=time.monotonic()
    parser=z3.parse_smt2_string(query)
    z=z3.Solver();z.set(timeout=15000);z.add(*parser)
    z_res=str(z.check())
    z_wall=round(time.monotonic()-t,6)
    witness={}
    if z_res=="sat":
        m=z.model()
        for symbol in s+sn:
            witness[symbol]=str(m.eval(z3.Int(symbol),model_completion=True))
    t=time.monotonic()
    try:
        cp=subprocess.run(["cvc5","--lang=smt2",str(p)],capture_output=True,
                          text=True,timeout=15,errors="replace")
        cout=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
        c_res=cout[-1] if cp.returncode==0 and cout else "HOLD_NATIVE_EXCEPTION"
        c_stderr=cp.stderr[-500:]
        returncode=cp.returncode
    except subprocess.TimeoutExpired as e:
        c_res="HOLD_TIMEOUT";c_stderr=str(e);returncode=None
    c_wall=round(time.monotonic()-t,6)
    valid=(z_res=="sat" and c_res=="sat" and bool(witness))
    out={
      "study":"ORIGINAL_EXTERNAL106_NO_INDUCTIVE_INVARIANT_BY_ONE_REACHABLE_UNSAFE_STEP",
      "original_pinned_git":UPSTREAM,"original_path":REL,
      "source_sha256":row["source_sha256"],"frozen_first_sha256":FIRST_SHA,
      "first_original_native":"CVC5_RETURNED_INFEASIBLE_UNPROVEN_IN_FIRST",
      "candidate_invariant_constructed":False,
      "one_step_sat_proof_smt_sha256":sha256(p.read_bytes()),
      "state_variables":len(s),"original_full_pre_trans_post_unchanged":True,
      "z3_version":z3.get_version_string(),"z3_sat":z_res,"z3_wall_seconds":z_wall,
      "original_reachable_unsafe_witness":witness if z_res=="sat" else None,
      "cvc5_version":native_version,"cvc5_sat":c_res,"cvc5_wall_seconds":c_wall,
      "cvc5_stderr_excerpt":c_stderr,"cvc5_exitcode":returncode,
      "theorem":"Any invariant must hold in all pre-states and be inductive under all trans; the exhibited reachable state violates post so no invariant exists",
      "verdict":"PROVED_NO_INDUCTIVE_SAFETY_INVARIANT_ANY_GRAMMAR"
          if valid else "HOLD_ONE_STEP_UNSAFE_NOT_BOTH_CERTIFIED",
      "neural_generated":False,
      "G1":"HOLD","Q1_Q7":"OPEN","G2":"NOT_RUN",
    }
    j=OUT/"ORIGINAL106_ONE_STEP_INFEASIBLE_Z3_CVC5_CERTIFICATE.json"
    j.write_text(json.dumps(out,sort_keys=True,indent=2))
    print("ORIGINAL106_Z3",z_res,"CVC5",c_res,"THEOREM",out["verdict"])
    print("ORIGINAL106_REPORT_SHA256",sha256(j.read_bytes()))
if __name__=="__main__":
    main()
