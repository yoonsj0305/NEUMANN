#!/usr/bin/env python3
"""POST-FIRST independently prove original SyGuS universal constraint formulas.

For ordinary (constraint ...), original universal declare-var variables become
free SMT constants; negate all constraints and require Z3 UNSAT.
For inv-constraint/synth-inv report HOLD (no unverified proof invention).
"""
import hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_SHA="a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5"
ORIG=pathlib.Path("official_repo")
FIRST=pathlib.Path("official_original_first")
OUT=pathlib.Path("official_z3_semantic_grade")

def extract_define_fun(s):
    start=s.find("(define-fun")
    if start<0 or s.find("(define-fun",start+1)>=0:raise ValueError("UNIQUE_PROGRAM_REQUIRED")
    depth=0;quoted=False
    for i in range(start,len(s)):
        ch=s[i]
        if ch=='"':quoted=not quoted
        if quoted:continue
        if ch=='(':depth+=1
        elif ch==')':
            depth-=1
            if depth==0:
                return s[start:i+1]
    raise ValueError("UNBALANCED_NATIVE_CANDIDATE")

def z3_full_check(script):
    import z3
    t=time.monotonic()
    solver=z3.Solver()
    solver.set(timeout=10000)
    solver.add(*z3.parse_smt2_string(script))
    chk=solver.check()
    return {"z3_result":str(chk),"wall_seconds":round(time.monotonic()-t,6),
            "script_sha256":sha256(script.encode()),
            "model_counterexample_exists":str(chk)=="sat"}

def grade_one(r):
    out={"path":r["path"],"first_status":r["status"],
         "original_sha256":r["original_source_sha256"],
         "native_first_stdout_sha256":r["stdout_sha256"],
         "status":"HOLD"}
    b=(ORIG/r["path"]).read_bytes()
    assert sha256(b)==r["original_source_sha256"]
    forms=top_level_forms(b.decode("utf8"))
    roles=[get_cmd(f[2]) for f in forms]
    if "synth-inv" in roles or "inv-constraint" in roles:
        out["status"]="HOLD_REQUIRES_INVARIANT_VERIFICATION_CONDITIONS"
        return out
    ss=[f[2] for f in forms if get_cmd(f[2])=="synth-fun"]
    cs=[f[2] for f in forms if get_cmd(f[2])=="constraint"]
    if len(ss)!=1 or not cs:
        out["status"]="HOLD_NOT_SINGLE_ORDINARY_CONSTRAINTS"
        return out
    program_bytes=(FIRST/(r["path"].replace("/","__")+".stdout")).read_bytes()
    assert sha256(program_bytes)==r["stdout_sha256"]
    program=extract_define_fun(program_bytes.decode("utf8","replace"))
    out["candidate_program_sha256"]=sha256(program.encode())
    asserts=[]
    for c in cs:
        m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",c,re.S)
        if m is None:raise ValueError("UNEXPECTED_CONSTRAINT_SYNTAX")
        asserts.append(m.group(1))
    # Native synthesizer grammar is irrelevant to independent semantic proof.
    # Free original universally interpreted variables, negate all constraints.
    declarations=[]
    helpers=[]
    for (_,_,form) in forms:
        command=get_cmd(form)
        if command=="declare-var":
            declarations.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
        elif command=="define-fun":
            helpers.append(form)
    # candidate may refer to helper functions: place primitive helpers first,
    # then candidate, then helpers that use candidate. Test both valid orders.
    # Some original benchmarks refer to the candidate in a later helper
    # (e.g. l); hence keep only helpers defined before its first reference.
    split_at=next((j for j,h in enumerate(helpers) if re.search(r"\(\s*inv\b",h)),len(helpers))
    ordered=helpers[:split_at]+[program]+helpers[split_at:]
    script="\n".join(["(set-logic ALL)"]+declarations+ordered)+\
           "\n(assert (not (and "+" ".join(asserts)+")))\n"
    try:
        proof=z3_full_check(script)
        out.update(proof)
        out["status"]=(
            "Z3_UNSAT_ALL_ORIGINAL_CONSTRAINTS_SEMANTIC_VALID"
            if proof["z3_result"]=="unsat" else
            "Z3_SAT_ORIGINAL_CONSTRAINTS_COUNTEREXAMPLE"
            if proof["z3_result"]=="sat" else "HOLD_Z3_UNKNOWN_OR_TIMEOUT")
    except Exception as exc:
        out["status"]="HOLD_Z3_PARSER_OR_EXECUTION"
        out["error"]=type(exc).__name__+":"+str(exc)[:240]
    return out

def main():
    assert subprocess.check_output(["git","-C",str(ORIG),"rev-parse","HEAD"],text=True).strip()==PIN
    original=(FIRST/"OFFICIAL_C16_FIRST_UNGRADED_CLASSICAL_HEADROOM.json").read_bytes()
    assert sha256(original)==FIRST_SHA,"IMMUTABLE_FIRST_HASH_MISMATCH"
    first=json.loads(original)
    selected=[r for r in first["results"] if r["status"]=="C_PROGRAM_CANDIDATE_UNVERIFIED"]
    assert len(first["results"])==16 and len(selected)==9
    OUT.mkdir(exist_ok=True)
    result=[]
    for r in selected:
        try:record=grade_one(r)
        except Exception as e:
            record={"path":r["path"],"status":"HOLD_INDEPENDENT_VERIFIER_EXCEPTION",
                    "error":type(e).__name__+":"+str(e)[:200]}
        result.append(record)
        print("INDEPENDENT_Z3",record["path"],record["status"],
              record.get("wall_seconds"),flush=True)
    report={
      "original_repo_commit":PIN,"original_c16_first_json_sha256":FIRST_SHA,
      "original_task_denominator":16,"native_candidate_subset_denominator":9,
      "only_full_source_semantic_verification_of_ordinary_constraints":True,
      "native_candidate_grammar_membership_independently_verified":False,
      "invariant_constraints_not_falsely_verified":True,
      "independent_z3_version":__import__("z3").get_version_string(),
      "global_Q1_Q7":"OPEN","G1":"HOLD","results":result,
    }
    p=OUT/"OFFICIAL_9_CANDIDATES_ORDINARY_Z3_GRADE_POSTFIRST.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("GRADE_SHA256",sha256(p.read_bytes()),flush=True)
if __name__=="__main__":main()
