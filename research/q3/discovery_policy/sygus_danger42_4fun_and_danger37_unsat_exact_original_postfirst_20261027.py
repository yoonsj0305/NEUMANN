#!/usr/bin/env python3
"""POST-FIRST formal exact original SyGuS 4-function danger42 analytic solution
and 3-function danger37 finite original-ground-instance UNSAT certificate.

Both task bodies were opened after filename-only prospective 8-task FIRST.
This is **classical symbolic reasoning**, no trained NEUMANN ownweights.
"""
import hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
ROOT=pathlib.Path("official_repo")
P42="lib/General_Track/cegist-cav18/inv/danger-loop42.sl"
P37="lib/General_Track/cegist-cav18/inv/danger-loop37.sl"
SHA42="47a78c4a3d6bd715ee57db8044bb140858d8809bbd3b6522af46793d5905ee5e"
SHA37="11f19d4bab4f637492dee2bee9e8d6fadf8d2de04eaa5aa2ef2b0fa9c1485c31"
OUT=pathlib.Path("official_danger42_37_semantic_proofs")
BIT32="(_ BitVec 32)"
D42=[
"""(define-fun D ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool
     (= y (bvadd x #x00000001)))""",
"""(define-fun R ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
     (bvsub #x00010003 x))""",
"""(define-fun S1 ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
     #x00000001)""",
"""(define-fun S2 ((x (_ BitVec 32)) (y (_ BitVec 32))) (_ BitVec 32)
     #x00000001)"""
]

def original(path,sha):
    content=(ROOT/path).read_bytes()
    assert sha256(content)==sha
    fs=top_level_forms(content.decode())
    parts=[(get_cmd(f[2]),f[2]) for f in fs]
    assert parts[0][0]=="set-logic"
    return parts

def extract_body(form,role):
    m=re.fullmatch(r"\(\s*"+role+r"\s+(.+)\s*\)",form,re.S)
    assert m,"CANNOT_PARSE_ORIGINAL_"+role
    return m.group(1)

def name(form):
    m=re.match(r"\(\s*(?:define-fun|synth-fun)\s+([^\s()]+)",form)
    assert m
    return m.group(1)

def check_one_z3(text,timeout=20000):
    import z3
    tick=time.monotonic()
    solver=z3.Solver()
    solver.set(timeout=timeout)
    solver.add(*z3.parse_smt2_string(text))
    res=str(solver.check())
    return {
      "status":"UNSAT" if res=="unsat" else ("SAT" if res=="sat" else "UNKNOWN"),
      "wall_seconds":round(time.monotonic()-tick,6),
      "query_sha256":sha256(text.encode()),
    }

def solve42():
    parts=original(P42,SHA42)
    source_synth={name(p):p for op,p in parts if op=="synth-fun"}
    assert sorted(source_synth)==sorted(("D","R","S1","S2"))
    assert len([x for op,x in parts if op=="constraint"])==3
    assertions=[]
    for op,form in parts:
        if op=="constraint":
            assertions.append(extract_body(form,"constraint"))
    prefix=[]
    for op,form in parts:
        if op=="declare-var":
            prefix.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
        elif op=="define-fun":
            prefix.append(form)
    prefix.extend(D42)
    records=[]
    for i in range(4):
        body=assertions[i] if i<3 else "(and "+" ".join(assertions)+")"
        query="(set-logic ALL)\n"+"\n".join(prefix)+"\n(assert (not "+body+"))\n"
        p=OUT/(f"danger42_obligation_{i+1}.smt2")
        p.write_text(query)
        try:
            out=check_one_z3(query)
            out["pass"]=out["status"]=="UNSAT"
        except Exception as e:
            out={"status":"HOLD_EXCEPTION","error":type(e).__name__+":"+str(e)[:240],"pass":False}
        out["obligation"]=i+1
        records.append(out)
        print("OFFICIAL_42_Z3",i+1,out["status"],flush=True)
    (OUT/"danger42_4_function_candidate.smt2").write_text("\n".join(D42)+"\n")
    return {
      "path":P42,"original_sha256":SHA42,
      "candidate_count":4,"candidate_program_sha256":sha256("\n".join(D42).encode()),
      "original_individual_constraints":3,"proof_obligations":records,
      "result":"POSTFIRST_CLASSICAL_4FUNCTION_SEMANTIC_SOLUTION"
         if all(x["pass"] for x in records) else "HOLD_OR_FALSIFIED",
      "global_Q":"OPEN","G1":"HOLD"}

def impossible37():
    fs=original(P37,SHA37)
    cmds=[cmd for cmd,_ in fs]
    assert cmds.count("constraint")==3
    synth={name(s):s for cmd,s in fs if cmd=="synth-fun"}
    assert set(synth)=={"D","R","y0"}
    cnt=[extract_body(p,"constraint") for cmd,p in fs if cmd=="constraint"]
    definitions=[s for cmd,s in fs if cmd=="define-fun"]
    def_map={name(s):s for s in definitions}
    assert all(k in def_map for k in ("if0","expand","implies","G","B_x","B_y","A","x0"))
    # Validate fixed original shape before deducting any impossibility.
    assert "(bvult x #x00000063)" in def_map["G"]
    assert "(bvurem y #x00000002)" in def_map["B_x"]
    assert "(bvadd x #x00000002)" in def_map["B_x"]
    assert "(bvadd x #x00000001)" in def_map["B_x"]
    assert re.search(r"\(\s*define-fun\s+B_y\b",def_map["B_y"])
    assert "(= (bvurem x #x00000002) (bvurem y #x00000002))" in def_map["A"]
    assert cnt[2].strip()=="(D x0 (y0 x y))",cnt[2]
    start=[
        "(set-logic ALL)",
        "(declare-fun D ((_ BitVec 32) (_ BitVec 32)) Bool)",
        "(declare-fun R ((_ BitVec 32) (_ BitVec 32)) (_ BitVec 32))",
        "(declare-fun y0 ((_ BitVec 32) (_ BitVec 32)) (_ BitVec 32))",
        *definitions,
        "(define-fun Y () (_ BitVec 32) (y0 #x00000000 #x00000000))",
        "(define-fun STEP ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool "+cnt[0]+")",
        "(define-fun POST ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool "+cnt[1]+")",
        "(define-fun X_0 () (_ BitVec 32) x0)"
    ]
    body=start+["(assert (D x0 Y))"]
    # Reachability grounds. Any universal solution must satisfy these.
    # For k>=50 if even y, guard false after x=100.
    # If odd y, guard false after x=99.
    for k in range(101):
        body.append("(assert (STEP X_"+str(k)+" Y))")
        body.append("(assert (POST X_"+str(k)+" Y))")
        if k<100:
            body.append("(define-fun X_"+str(k+1)+" () (_ BitVec 32) (B_x X_"+str(k)+" Y))")
    query="\n".join(body)+"\n"
    p=OUT/"danger37_uninterpreted_functions_101_step_original_ground_unsat.smt2"
    p.write_text(query)
    try:
        check=check_one_z3(query,30000)
        check["pass"]=check["status"]=="UNSAT"
    except Exception as e:
        check={"status":"HOLD_EXCEPTION","pass":False,
          "error":type(e).__name__+":"+str(e)[:240]}
    print("OFFICIAL_37_FINITE_UNSAT",check["status"],flush=True)
    return {"path":P37,"original_sha256":SHA37,
      "original_formulas_extracted_as_written":True,
      "function_symbols_uninterpreted":list(synth),
      "original_initial_constraint_instance":"x=0, y=0 (thus D(x0,Y) with Y=y0(0,0))",
      "original_transition_and_post_per_step":101,
      "ground_instantiations":203,
      "arbitrary_free_synthesis_functions":True,
      "certificate":check,
      "result":"ORIGINAL_FULL_SYNTHESIS_INFEASIBLE_BY_FINITE_UNSAT"
        if check.get("pass") else "HOLD_UNSAT_NOT_CERTIFIED",
      "global_Q":"OPEN","G1":"HOLD"}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    OUT.mkdir(exist_ok=True)
    a=solve42()
    b=impossible37()
    record={
      "kind":"POSTFIRST_MANUAL_CLASSICAL_EXPLICIT_SOLUTION_AND_INFEASIBILITY_PROOF",
      "official_upstream":UPSTREAM,
      "external_originals_are_opened_dev":True,
      "original_modern_cvc5_142_both_timedout":"YES",
      "z3_version":z3.get_version_string(),
      "not_neumann_ownweight_generated":True,
      "danger42":a,"danger37":b,
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN"}
    p=OUT/"DANGER42_FOUR_FUNCTION_SOLUTION_AND_DANGER37_UNSAT_POSTFIRST.json"
    p.write_text(json.dumps(record,indent=2,sort_keys=True))
    print("PROOF_RESULT_SHA256",sha256(p.read_bytes()))
    print("PROOF_FINAL",a["result"],b["result"])
if __name__=="__main__":main()
