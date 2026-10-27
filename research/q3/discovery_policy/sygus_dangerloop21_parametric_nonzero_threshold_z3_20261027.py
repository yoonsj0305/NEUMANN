#!/usr/bin/env python3
"""POST-FIRST parametric theorem test for the exact official danger-loop21 schema.

No new hidden third-party task was used. Replace just original literal guard
threshold by a symbolic 32-bit N; adapt ranking R to N-x; D and S unchanged.
Check FOR ALL nonzero N and all 32-bit x,y via negated logical obligations.
This is symbolic template generalization, NOT neural transfer.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_dangerloop21_analytic_z3_exact_original_20261027 import (
    UPSTREAM,ORIGINAL,SOURCE_SHA,PROGRAMS,ROOT,query_z3
)

DEST=pathlib.Path("official_danger21_parameterized_template")
OLD_THRESHOLD="#x00010003"

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    b=(ROOT/ORIGINAL).read_bytes()
    assert sha256(b)==SOURCE_SHA
    forms=top_level_forms(b.decode("utf8"))
    constraints=[]
    statements=[]
    guard_count=0
    for _,__,form in forms:
        cmd=get_cmd(form)
        if cmd=="constraint":
            m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",form,re.S)
            assert m
            constraints.append(m.group(1))
        elif cmd=="declare-var":
            statements.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
        elif cmd=="set-logic":
            statements.append(form)
        elif cmd=="define-fun":
            if re.match(r"^\(\s*define-fun\s+G(?=\s)",form):
                guard_count+=1
                assert form.count(OLD_THRESHOLD)==1
                form=form.replace(OLD_THRESHOLD,"N")
            statements.append(form)
    assert guard_count==1 and len(constraints)==3
    R=PROGRAMS[1].replace(OLD_THRESHOLD,"N")
    assert R!=PROGRAMS[1] and "bvsub N x" in R
    model=PROGRAMS[0]+"\n"+R+"\n"+PROGRAMS[2]
    assert statements and get_cmd(statements[0])=="set-logic"
    statements.insert(1,"(declare-const N (_ BitVec 32))")
    header="\n".join(statements)+"\n"+model+"\n"
    DEST.mkdir(exist_ok=True)
    proofs=[]
    for i in range(5):
        expr=constraints[i] if i<3 else "(and "+" ".join(constraints)+")"
        assume_N="(assert (not (= N #x00000000)))\n" if i<=3 else "(assert (= N #x00000000))\n"
        query=header+assume_N+"(assert (not "+expr+"))\n(check-sat)\n"
        tag=("parametric_constraint_"+str(i+1)) if i<3 else (
             "parametric_all_nonzero_N" if i==3 else "excluded_N_zero_expected_SAT")
        (DEST/(tag+".smt2")).write_text(query)
        try:
            proof=query_z3(query)
            # First 4: UNSAT for arbitrary nonzero threshold.
            # Last: SAT expected because N=0 breaks exit on initial (0,1).
            expect="unsat" if i<4 else "sat"
            proof.update(obligation=tag,
                expected=expect,status=("PASS" if proof["result"]==expect else "HOLD_OR_FALSIFIED"))
        except Exception as e:
            proof={"obligation":tag,"status":"HOLD_SOLVER_EXCEPTION",
                   "error":type(e).__name__+":"+str(e)[:230]}
        proofs.append(proof)
        print("PARAMETRIC_G0",tag,proof["status"],proof.get("result"),flush=True)
    success=all(p["status"]=="PASS" for p in proofs)
    record={
      "research_scope":"POSTFIRST_MANUALLY_PARAMETERIZED_SYNTHESIS_TEMPLATE_NO_LEARNED_WEIGHTS",
      "source_exact_upstream_commit":UPSTREAM,"source_sha256":SOURCE_SHA,
      "width":32,"threshold_universally_quantified_by_counterexample_UNSAT":"N != 0",
      "threshold_count_representable":2**32-1,
      "normal_conclusion":"All 3 constraints valid for every nonzero BV32 N, all x/y BV32",
      "normal_template_found_in":"one already opened and validated original task",
      "domain_D_and_control_S":PROGRAMS[0]+"\n"+PROGRAMS[2],
      "symbolic_ranking_R":R,
      "independent_z3_version":z3.get_version_string(),
      "status":"VERIFIED_SYMBOLIC_ALL_NONZERO_32BIT_THRESHOLDS" if success else "HOLD",
      "ownweight_training":False,"global_Q1_Q7":"OPEN","G1":"HOLD",
      "original_task_author_independence":"ONE_OPENED_ORIGINAL_ONLY",
      "proof":proofs}
    p=DEST/"DANGER_LOOP21_ALL_32BIT_NONZERO_THRESHOLDS_SYMBOLIC_Z3.json"
    p.write_text(json.dumps(record,indent=2,sort_keys=True))
    print("RESULT_SHA256",sha256(p.read_bytes()),flush=True)
if __name__=="__main__":main()
