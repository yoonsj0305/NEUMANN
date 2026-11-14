#!/usr/bin/env python3
"""POSTFIRST independent ORIGINAL 106.c finite unsafe path certificate.

Never rely on cvc5's 'infeasible' textual claim. Reachable original unsafe
path from exact original pre/trans/post proves NO inductive invariant can exist.
Depths 1→2→3 fixed before examining solver response.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import form_name,parameter_signature

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/Inv_Track/xujie_code2inv/106.c.sl"
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_4track16_FROZEN_FIRST")
OUT=pathlib.Path("official_106_reachable_unsafety")

def call(n,vs):
    return "("+n+" "+" ".join(vs)+")"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    first_raw=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(first_raw)==FIRST_SHA
    first=json.loads(first_raw)
    row=first["rows"][4]
    assert row["original"]==SOURCE and row["status"]=="HOLD_NATIVE_INFEASIBLE_CLAIM_UNPROVED"
    source=(ROOT/SOURCE).read_bytes()
    assert sha256(source)==row["source_sha256"]
    forms=[(get_cmd(x[2]),x[2]) for x in top_level_forms(source.decode("utf8"))]
    synth=[f for c,f in forms if c=="synth-inv"]
    invcon=[f for c,f in forms if c=="inv-constraint"]
    assert len(synth)==len(invcon)==1
    assert form_name(synth[0],"synth-inv")=="inv-f"
    assert invcon[0]=="(inv-constraint inv-f pre-f trans-f post-f)"
    sig=parameter_signature(synth[0],"synth-inv","inv-f")
    assert len(sig)==14 and all(sort=="Int" for _,sort in sig)
    define={form_name(f,"define-fun"):f for c,f in forms if c=="define-fun"}
    assert all(k in define for k in ("pre-f","trans-f","post-f"))
    for name,size in (("pre-f",14),("trans-f",28),("post-f",14)):
        check=parameter_signature(define[name],"define-fun",name)
        assert len(check)==size and all(t=="Int" for _,t in check)
    original_defs=[f for c,f in forms if c=="define-fun"]
    OUT.mkdir(exist_ok=True)
    results=[]
    for depth in (1,2,3):
        states=[[f"__x_{j}_{i}" for i in range(14)] for j in range(depth+1)]
        typed="\n".join(f"(declare-const {v} Int)" for step in states for v in step)
        conditions=[call("pre-f",states[0])]
        conditions += [call("trans-f",states[i]+states[i+1]) for i in range(depth)]
        conditions += ["(not "+call("post-f",states[-1])+")"]
        query="(set-logic ALL)\n"+"\n".join(original_defs)+"\n"+typed+"\n"
        query+="(assert (and "+" ".join(conditions)+"))\n(check-sat)\n"
        fn=OUT/f"official_original_106_reachable_unsafe_depth{depth}.smt2"
        fn.write_text(query)
        t0=time.process_time()
        sol=z3.Solver();sol.set(timeout=15000)
        sol.add(*z3.parse_smt2_string(query))
        answer=str(sol.check())
        witness=sol.model().sexpr() if answer=="sat" else None
        (OUT/f"z3_depth{depth}_model.txt").write_text(witness or "")
        cpu=round(time.process_time()-t0,6)
        cp=subprocess.run(["cvc5","--lang=smt2",str(fn)],text=True,
                          capture_output=True,timeout=18)
        native=[x.strip() for x in cp.stdout.splitlines() if x.strip()]
        nr=native[0] if native else "NO_OUTPUT"
        r={"depth":depth,"z3_result":answer,"native_cvc5_result":nr,
           "native_cvc5_exit_code":cp.returncode,"original_full_SMT_sha256":sha256(query.encode()),
           "real_reachable_unsafe":"CONFIRMED" if answer==nr=="sat" else "NOT_CONFIRMED",
           "z3_witness_model_sha256":sha256((witness or "").encode()),
           "z3_witness_model_saved":answer=="sat",
           "z3_process_cpu_seconds":cpu,
           "native_stderr_tail":cp.stderr[-300:]}
        results.append(r)
        print("ORIGINAL_106_REACHABLE_UNSAFE",depth,answer,nr,flush=True)
        if answer=="sat" and nr=="sat":break
    proven=any(r["real_reachable_unsafe"]=="CONFIRMED" for r in results)
    report={
       "status":"ORIGINAL_SYNTHESIS_UNREALIZABLE_BY_SOURCE_REACHABILITY"
          if proven else "HOLD_ORIGINAL_SYNTHESIS_INFEASIBILITY_NOT_PROVEN",
       "original_source_repository":"SyGuS-Org/benchmarks",
       "original_source_commit":PIN,"original_source":SOURCE,
       "original_sha256":sha256(source),"original_first_sha256":FIRST_SHA,
       "witness_depth":next((r["depth"] for r in results if r["real_reachable_unsafe"]=="CONFIRMED"),None),
       "proof_scope":"SAT original pre(s0) AND transitions AND not post(sh) excludes every possible inductive invariant",
       "original_source_pre_trans_post_unmodified":True,
       "z3_version":z3.get_version_string(),
       "cvc5_version":subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0],
       "model_trained":False,
       "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
       "all_fixed_order_depth_results":results}
    p=OUT/"ORIGINAL106_SOURCE_REACHABLE_UNSAFE_Z3_CVC5.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("ORIGINAL_106_REPORT_SHA",sha256(p.read_bytes()))
    print("ORIGINAL_106_VERDICT",report["status"],flush=True)
if __name__=="__main__":main()
