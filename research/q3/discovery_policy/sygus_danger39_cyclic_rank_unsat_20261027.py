#!/usr/bin/env python3
"""Independent exact-source symbolic premise proofs for original danger-loop39.

Finite 2**32 cyclic-rank contradiction is a mathematical finite-descent proof,
NOT a monolithic Z3 proof of second-order synthesis infeasibility.
Original source fully OPENED POST-FIRST; no ownweight/neural learning.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_danger42_4fun_and_danger37_unsat_exact_original_postfirst_20261027 import check_one_z3

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/General_Track/cegist-cav18/inv/danger-loop39.sl"
SHA="c9f45a3e85860f3161fb948a85489777498d64656673364b328162af1d9f2b2d"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_danger39_cyclic_rank_proof")
Z="#x00000000";ONE="#x00000001";BV="(_ BitVec 32)"

def prove(text,key):
    f=OUT/(key+".smt2")
    f.write_text(text)
    try:
        result=check_one_z3(text,10000)
        result.update(obligation=key,passed=result["status"]=="UNSAT")
    except Exception as e:
        result={"obligation":key,"status":"HOLD_EXCEPTION","passed":False,
                "error":type(e).__name__+":"+str(e)[:200],
                "query_sha256":sha256(text.encode())}
    print("DANGER39_SYMBOLIC_PREMISE",key,result["status"],flush=True)
    return result

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(ROOT/PATH).read_bytes()
    assert sha256(raw)==SHA
    parts=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    synth=[x for c,x in parts if c=="synth-fun"]
    names=[]
    for s in synth:
        m=re.match(r"^\(\s*synth-fun\s+(\S+)",s)
        assert m
        names.append(m.group(1))
    assert names==["D","R"]
    source_consts=[re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",x,re.S).group(1)
                   for c,x in parts if c=="constraint"]
    assert len(source_consts)==3
    assert source_consts[2]=="(D x0 y0)"
    helpers=[x for c,x in parts if c=="define-fun"]
    helper_map={}
    for s in helpers:
        m=re.match(r"^\(\s*define-fun\s+(\S+)",s)
        assert m
        helper_map[m.group(1)]=s
    assert all(n in helper_map for n in
               ("if0","expand","implies","G","B_x","B_y","A","x0","y0"))
    assert "(bvult y #x0000000a)" in helper_map["G"]
    assert "#x00000000" in helper_map["B_x"]
    assert "(bvadd y #x00000001)" in helper_map["B_y"]
    assert "#x00000001" in helper_map["x0"]
    assert "#x00000000" in helper_map["y0"]
    assert "(G x)" in source_consts[0]
    assert "bvugt" in source_consts[0]
    assert "(D B_x (B_y y))" in source_consts[0]
    assert "(R B_x (B_y y))" in source_consts[0]

    head="\n".join([
       "(set-logic ALL)",
       "(declare-fun D ((_ BitVec 32) (_ BitVec 32)) Bool)",
       "(declare-fun R ((_ BitVec 32) (_ BitVec 32)) (_ BitVec 32))",
       *helpers,
       "(define-fun STEP ((x (_ BitVec 32)) (y (_ BitVec 32))) Bool "+source_consts[0]+")",
       "(declare-const y (_ BitVec 32))"
    ])+"\n"

    targets=[
      ("G_at_initial_x1",f"(not (G {ONE}))"),
      ("G_at_absorbing_x0",f"(not (G {Z}))"),
      ("Bx_constant_zero",f"(not (= B_x {Z}))"),
      ("By_add_one_mod32",f"(not (= (B_y y) (bvadd y {ONE})))"),
      ("D_initial_to_cycle_start",
          f"(and (STEP {ONE} {Z}) (D {ONE} {Z}) (not (D {Z} {ONE})))"),
      ("D_cycle_successor_closed",
          f"(and (STEP {Z} y) (D {Z} y) (not (D {Z} (bvadd y {ONE}))))"),
      ("rank_cycle_successor_strict_unsigned",
          f"(and (STEP {Z} y) (D {Z} y) (not (bvugt (R {Z} y) (R {Z} (bvadd y {ONE})))))"),
    ]
    OUT.mkdir(exist_ok=True)
    proofs=[]
    for key,bad in targets:
        proofs.append(prove(head+"(assert "+bad+")\n",key))
    all_premises=all(p["passed"] for p in proofs)
    record={
      "research":"RETROSPECTIVE_POSTFIRST_ORIGINAL_SYNTHESIS_IMPOSSIBILITY_FINITE_RANK_CYCLE",
      "original_repo_commit":PIN,"source_path":PATH,"source_sha256":SHA,
      "original_synth_fun_names":names,"original_constraints":3,
      "source_original_full_top_level_parser_checked":True,
      "source_original_step_formula_used_unmodified":True,
      "independent_z3":z3.get_version_string(),
      "all_seven_exact_source_entailment_checks_unsat":all_premises,
      "modulo_bitvector_y_cycle_length":2**32,
      "mathematical_theorem":"D(1,0)→D(0,1); from D(0,y), D(0,y+1) and strict BV32 R descent; 2^32-step y cycle returns to start; strict rank cycle impossible",
      "claim_boundary":"Z3 verifies original source finite-cycle premises; ordinary finite-cycle induction/transitivity is mathematical; not a monolithic 2^32 SMT unrolling",
      "status":"ORIGINAL_SYNTHESIS_INFEASIBLE_BY_PROVEN_FINITE_CYCLIC_RANK" if all_premises else "HOLD_UNVERIFIED_PREMISES",
      "ownweight_model_training":False,
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "premises":proofs}
    p=OUT/"DANGER39_SOURCE_CHECKED_CYCLIC_RANK_UNREALIZABLE.json"
    p.write_text(json.dumps(record,indent=2,sort_keys=True))
    print("RESULT_SHA256",sha256(p.read_bytes()),flush=True)
    print("STATUS",record["status"])
if __name__=="__main__":main()
