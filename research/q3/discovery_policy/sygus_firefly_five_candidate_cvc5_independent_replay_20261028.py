#!/usr/bin/env python3
"""FIREFLY postfirst: independent actual CVC5 1.4.2 on 15 original full VCs.

Compare against exact frozen Z3 five-candidate FIRST, no new synthesis.
No Z3 import, no candidate modification; all 15 original init/trans/prop
obligations checked by a DIFFERENT published SMT backend.
"""
import hashlib,json,pathlib,re,resource,subprocess,sys,time,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    parameter_signature,form_name
)

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/Inv_Track/andrew_lustre/FIREFLY_luke_1b_e1_1139_e2_2893.lus.sl"
SOURCE_DIR=pathlib.Path("official_repo")
FROZEN=pathlib.Path("official_frozen_firefly_five")
OUT=pathlib.Path("official_firefly_2solver_recheck")
FROZEN_JSON_SHA="fb98bc250e57131cb671c613616796373a5f5ff2a93acd4ebb0472cd28f810c4"
EXPECTED={
    "A_OK_ONLY":("unsat","sat","unsat"),
    "B_OK_AND_STORED_SUM":("unsat","unsat","unsat"),
    "C_OK_SUM_NOT_INIT":("sat","unsat","unsat"),
    "D_OK_IF_EVENT_THEN_SUM":("unsat","unsat","unsat"),
    "E_OK_SUM_AUX_RELATION":("unsat","unsat","unsat"),
}
OBLIGATIONS=("INIT_IMPLIES_INVARIANT","INDUCTIVE_CONSECUTION","INVARIANT_IMPLIES_POST")

def call(f,vs):
    return "("+f+(" "+" ".join(vs) if vs else "")+")"

def native_smt(script):
    def cpu_cap():
        resource.setrlimit(resource.RLIMIT_CPU,(7,8))
    p=OUT/"current_query.smt2"
    p.write_text(script)
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    t=time.monotonic()
    try:
        r=subprocess.run(["cvc5","--lang=smt2",str(p)],capture_output=True,text=True,
                         timeout=8.2,preexec_fn=cpu_cap,errors="replace")
        stdout,stderr,ret=r.stdout,r.stderr,r.returncode
        forced=None
    except subprocess.TimeoutExpired as e:
        stdout=(e.stdout or b"").decode(errors="replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
        stderr=(e.stderr or b"").decode(errors="replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
        ret=None
        forced="WALL_TIMEOUT"
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    lines=[x.strip() for x in stdout.splitlines() if x.strip()]
    verdict=lines[-1] if lines else "HOLD_NO_OUTPUT"
    if ret!=0 or forced or verdict not in ("sat","unsat","unknown"):
        verdict="HOLD_NATIVE_ERROR_OR_TIMEOUT"
    return {"verdict":verdict,"returncode":ret,"forced":forced,
            "stdout_sha256":sha256(stdout.encode()),"stderr_sha256":sha256(stderr.encode()),
            "stdout_last_line":lines[-1][:160] if lines else None,
            "stderr_excerpt":stderr[-350:],
            "wall_seconds":round(time.monotonic()-t,6),
            "child_user_cpu_seconds":round(after.ru_utime-before.ru_utime,6),
            "child_system_cpu_seconds":round(after.ru_stime-before.ru_stime,6),
            "script_sha256":sha256(script.encode())}

def main():
    assert subprocess.check_output(["git","-C",str(SOURCE_DIR),"rev-parse","HEAD"],text=True).strip()==PIN
    ver=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert ver.startswith("cvc5 1.4.2 ")
    b=(SOURCE_DIR/SOURCE).read_bytes()
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(b.decode())]
    inv=[f for c,f in forms if c=="synth-inv"]
    link=[f for c,f in forms if c=="inv-constraint"]
    assert len(inv)==1 and len(link)==1
    assert link[0]=="(inv-constraint str_invariant init trans prop)"
    assert form_name(inv[0],"synth-inv")=="str_invariant"
    sig=parameter_signature(inv[0],"synth-inv","str_invariant")
    assert len(sig)==23
    helpers={form_name(f,"define-fun"):f for c,f in forms if c=="define-fun"}
    assert all(x in helpers for x in ("init","trans","prop"))
    sorts=[q for _,q in sig]
    assert sorts==[q for _,q in parameter_signature(helpers["init"],"define-fun","init")]
    assert sorts+sorts==[q for _,q in parameter_signature(helpers["trans"],"define-fun","trans")]
    assert sorts==[q for _,q in parameter_signature(helpers["prop"],"define-fun","prop")]
    frozen=(FROZEN/"FIREFLY_ORIGINAL_5_CLASSIC_INVARIANTS_3VC_POSTFIRST.json").read_bytes()
    assert sha256(frozen)==FROZEN_JSON_SHA
    old=json.loads(frozen)
    assert len(old["cases"])==5
    assert [x["candidate"] for x in old["cases"]]==list(EXPECTED)
    OUT.mkdir(exist_ok=True)
    a=["__n1bc_v"+str(i) for i in range(len(sig))]
    a1=["__n1bc_w"+str(i) for i in range(len(sig))]
    decls=["(declare-const "+n+" "+sort+")" for n,sort in zip(a+a1,sorts+sorts)]
    results=[]
    for past in old["cases"]:
        name=past["candidate"]
        candidate_bytes=(FROZEN/(name+".smt2")).read_bytes()
        assert sha256(candidate_bytes)==past["candidate_program_sha256"]
        candidate=candidate_bytes.decode().strip()
        assert form_name(candidate,"define-fun")=="str_invariant"
        assert parameter_signature(candidate,"define-fun","str_invariant")==sig
        pre=["(set-logic ALL)"]+[f for c,f in forms if c=="define-fun"]+[candidate]+decls
        clauses=[
            "(and "+call("init",a)+" (not "+call("str_invariant",a)+"))",
            "(and "+call("str_invariant",a)+" "+call("trans",a+a1)+
                       " (not "+call("str_invariant",a1)+"))",
            "(and "+call("str_invariant",a)+" (not "+call("prop",a)+"))",
        ]
        checks=[]
        for idx,(kind,neg) in enumerate(zip(OBLIGATIONS,clauses)):
            query="\n".join(pre)+"\n(assert "+neg+")\n(check-sat)\n"
            (OUT/(name+"__"+kind+".smt2")).write_text(query)
            check=native_smt(query)
            expected=EXPECTED[name][idx]
            check.update({"obligation":kind,"expected_prior_Z3":expected,
                          "agrees_with_frozen_independent_Z3":check["verdict"]==expected})
            checks.append(check)
            print("FIREFLY_SECOND_SOLVER",name,kind,check["verdict"],
                  "expected",expected,flush=True)
        results.append({"candidate":name,"prior_source_candidate_sha256":past["candidate_program_sha256"],
                        "second_engine_checks":checks,
                        "parity_all_three":all(x["agrees_with_frozen_independent_Z3"] for x in checks)})
    all_match=all(x["parity_all_three"] for x in results)
    report={
      "experiment":"POSTFIRST_INDEPENDENT_OFFICIAL_CVC5_142_ALL_FIVE_FIREFLY_ORIGINAL_3VC",
      "upstream_source_git_sha":PIN,"source_exact_sha256":sha256(b),
      "prior_five_original_Z3_json_sha256":FROZEN_JSON_SHA,
      "native_backend":ver,"fixed_candidates":list(EXPECTED),
      "source_3vc_per_candidate":3,"actual_backend_calls":15,
      "second_engine_parity_all_15":all_match,
      "num_inductively_valid":sum(all(x["verdict"]=="unsat" for x in r["second_engine_checks"]) for r in results),
      "total_child_CPU_seconds":round(sum(sum(x["child_user_cpu_seconds"]+x["child_system_cpu_seconds"] for x in r["second_engine_checks"]) for r in results),6),
      "result":"SECOND_SOLVER_15_OF_15_PARITY" if all_match else "HOLD_SOLVER_DISAGREEMENT_OR_TIMEOUT",
      "not_ownweight_neural":True,"Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "cases":results}
    p=OUT/"FIREFLY_5_ORIGINAL_INVARIANTS_TWO_PROVERS_15_VCS.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("REPLAY_SHA256",sha256(p.read_bytes()),flush=True)
    print("REPLAY_RESULT",report["result"],"valid",report["num_inductively_valid"],flush=True)
if __name__=="__main__":main()
