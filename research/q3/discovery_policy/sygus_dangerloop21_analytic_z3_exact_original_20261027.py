#!/usr/bin/env python3
"""Exact original pinned official danger-loop21 analytic three-function candidate.

The candidate D/R/S was constructed *post-first after fully exposing the task*,
NOT via learned weights. Four fresh independent Z3 obligations ensure entire
formal original constraint set, not a hand-transcribed approximation.
"""
import hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
ORIGINAL="lib/General_Track/cegist-cav18/inv/danger-loop21.sl"
SOURCE_SHA="8b3fa6aa436f67ec10b1112c3f7e8ffb1eb0e920b0268bcae5d3adf8cced539c"
ORIGINAL_FIRST="a648346b162b3c76d4c60283f339c1a3c54016ad374128c1b4135453c27a5ba5"
MODERN_FIRST="7f7f57f960508b21db406880949f4567cce010c37393b9f503f9bb719887dec2"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_danger21_z3_proof")

PROGRAMS=[
"""(define-fun D ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool
  (or (= x y) (and (= x #x00000000) (= y #x00000001))))""",
"""(define-fun R ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
  (bvsub #x00010003 x))""",
"""(define-fun S ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
  (ite (and (= x #x00000000) (= y #x00000001))
       #x00000001 #x00000000))"""
]

def query_z3(script):
    import z3
    t=time.monotonic()
    solver=z3.Solver()
    solver.set(timeout=10000)
    solver.add(*z3.parse_smt2_string(script))
    result=str(solver.check())
    return {"result":result,"wall_seconds":round(time.monotonic()-t,6),
            "original_unsat_semantics_witness":result=="unsat",
            "script_sha256":sha256(script.encode())}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    data=(ROOT/ORIGINAL).read_bytes()
    assert sha256(data)==SOURCE_SHA
    source=data.decode("utf8")
    forms=top_level_forms(source)
    commands=[get_cmd(f[2]) for f in forms]
    assert commands.count("synth-fun")==3,commands
    assert commands.count("constraint")==3,commands
    assert commands.count("check-synth")==1
    assert set(commands)<=set(("set-logic","declare-var","define-fun","synth-fun","constraint","check-synth"))
    declared=[]
    other=[]
    constraints=[]
    for _,__,form in forms:
        cmd=get_cmd(form)
        if cmd=="declare-var":
            declared.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
        elif cmd in ("set-logic","define-fun"):
            other.append(form)
        elif cmd=="constraint":
            m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",form,re.S)
            assert m,"NOT_SIMPLE_CONSTRAINT"
            constraints.append(m.group(1))
    assert len(declared)==2 and len(constraints)==3
    pre="\n".join(other+declared+PROGRAMS)+"\n"
    OUT.mkdir(exist_ok=True)
    proof=[]
    for j in range(4):
        part=constraints[j] if j<3 else "(and "+" ".join(constraints)+")"
        query=pre+"(assert (not "+part+"))\n(check-sat)\n"
        name="original_constraint_"+str(j+1) if j<3 else "original_all_three_conjunction"
        qpath=OUT/(name+".smt2")
        qpath.write_text(query)
        try:
            out=query_z3(query)
            status="Z3_UNSAT_FORMALLY_VALID" if out["result"]=="unsat" else (
                "Z3_SAT_FALSIFIED" if out["result"]=="sat" else "HOLD_Z3_UNKNOWN_OR_TIMEOUT")
            out.update(status=status,obligation=name)
        except Exception as e:
            out={"obligation":name,"status":"HOLD_PARSER_OR_SOLVER_EXCEPTION",
                 "error":type(e).__name__+":"+str(e)[:220],
                 "script_sha256":sha256(query.encode())}
        proof.append(out)
        print("DANGER_LOOP21_Z3",name,out["status"],out.get("wall_seconds"),flush=True)
    success=all(p["status"]=="Z3_UNSAT_FORMALLY_VALID" for p in proof)
    candidate="\n".join(PROGRAMS)+"\n"
    (OUT/"candidate_D_R_S_define_fun.smt2").write_text(candidate)
    record={
        "classification":"RETROSPECTIVE_ASSISTANT_AUTHORED_SYMBOLIC_CONSTRUCTION_NOT_OWNWEIGHT",
        "status":"SCOPED_EXACT_ORIGINAL_FORMAL_SOLUTION" if success else "HOLD_OR_FALSIFIED",
        "official_source_sha":UPSTREAM,"official_source_path":ORIGINAL,
        "exact_original_sha256":SOURCE_SHA,
        "historic_native_cvc5_112_FIRST":ORIGINAL_FIRST,
        "historic_native_cvc5_142_modern_retest":MODERN_FIRST,
        "z3_version":z3.get_version_string(),
        "original_sygus_synth_funs":3,"original_constraints":3,
        "candidate_program_sha256":sha256(candidate.encode()),
        "candidate_program_chars":len(candidate),
        "all_query_scripts_derived_automatically_from_exact_original":True,
        "all_three_original_constraints_semantic_proof":success,
        "future_original_test_golds":"NOT_APPLICABLE_FULL_FORMAL_SPEC",
        "native_original_source_grammar_restriction":"NONE_EXPLICIT",
        "ownweight_model_trained":False,
        "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
        "proof":proof}
    rpath=OUT/"DANGER_LOOP21_ORIGINAL_EXACT_Z3_3FUNCTION_FORMAL_PROOF.json"
    rpath.write_text(json.dumps(record,indent=2,sort_keys=True))
    print("RESULT_SHA256",sha256(rpath.read_bytes()),flush=True)
    print("FORMAL_RESULT",record["status"],flush=True)
if __name__=="__main__":main()
