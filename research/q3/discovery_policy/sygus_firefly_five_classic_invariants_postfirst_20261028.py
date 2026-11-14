#!/usr/bin/env python3
"""POST-FIRST fixed five candidate classical invariant hypotheses for official
FIREFLY. Each is verified against 3 full original inductive Z3 verification
conditions, not tested with neural weights. No adaptive candidate selection.
"""
import hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import (
    form_name, parameter_signature, independent_grade
)

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/Inv_Track/andrew_lustre/FIREFLY_luke_1b_e1_1139_e2_2893.lus.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_firefly_classic_five")

def candidate_bodies():
    sum4="(+ (+ (+ top.res.abs_0 top.res.abs_1) top.res.abs_2) top.res.abs_3)"
    equal="(= top.res.abs_7 "+sum4+")"
    ok="top.usr.OK"
    relation="(= top.res.abs_5 (and top.res.abs_4 (>= top.usr.i_invalid 0)))"
    return [
        ("A_OK_ONLY",ok),
        ("B_OK_AND_STORED_SUM","(and "+ok+" "+equal+")"),
        ("C_OK_SUM_NOT_INIT","(and "+ok+" "+equal+" (not top.res.init_flag))"),
        ("D_OK_IF_EVENT_THEN_SUM","(and "+ok+" (=> top.res.abs_6 "+equal+"))"),
        ("E_OK_SUM_AUX_RELATION","(and "+ok+" "+equal+" "+relation+")"),
    ]

def main():
    import z3
    sha=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    assert sha==PIN
    original=(ROOT/PATH).read_bytes()
    src=original.decode("utf8")
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(src)]
    sy=[form for command,form in forms if command=="synth-inv"]
    inv=[form for command,form in forms if command=="inv-constraint"]
    assert len(sy)==1 and len(inv)==1
    assert form_name(sy[0],"synth-inv")=="str_invariant"
    params=parameter_signature(sy[0],"synth-inv","str_invariant")
    assert len(params)==23
    assert all(sort in ("Bool","Int") for _,sort in params)
    names={x for x,_ in params}
    assert all(x in names for x in (
        "top.usr.OK","top.res.abs_0","top.res.abs_1",
        "top.res.abs_2","top.res.abs_3","top.res.abs_7",
        "top.res.abs_6","top.res.init_flag","top.res.abs_4",
        "top.res.abs_5","top.usr.i_invalid"))
    assert "str_invariant init trans prop" in inv[0]
    OUT.mkdir(exist_ok=True)
    cases=[]
    for name,expr in candidate_bodies():
        t=time.process_time()
        code="(define-fun str_invariant ("+" ".join(
            "("+var+" "+sort+")" for var,sort in params)+") Bool "+expr+")"
        (OUT/(name+".smt2")).write_text(code+"\n")
        entry={"candidate":name,"candidate_program_sha256":sha256((code+"\n").encode()),
               "candidate_expression":expr,
               "proposed_directly_after_opening_original":True}
        try:
            # Fully reused independently verified original semantics evaluator:
            # check INIT→I, I∧TRANS→I', I→PROP, no truncated original clauses.
            grade=independent_grade({},src,code)
            entry.update(grade)
            entry["status"]="PASS_ALL_THREE_INDUCTIVE_VCS" if (
                grade["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS"
                and len(grade["original_formal_proof_obligations"])==3
                and all(q["proof_counterexample_unsat"] for q in
                        grade["original_formal_proof_obligations"])
            ) else "HOLD_SAT_COUNTEREXAMPLE_OR_UNKNOWN"
        except Exception as ex:
            entry["status"]="HOLD_EXECUTOR_OR_UNSUPPORTED"
            entry["error"]=type(ex).__name__+":"+str(ex)[:320]
        entry["full_process_cpu_seconds"]=round(time.process_time()-t,6)
        cases.append(entry)
        print("FIREFLY_CLASSICAL_FIVE",name,entry["status"],
              [(x["obligation"],x["z3_answer"]) for x in
               entry.get("original_formal_proof_obligations",[])],flush=True)
    report={
        "experiment":"POSTFIRST_5_FIXED_CLASSICAL_INVARIANT_ORIGINAL_3VC",
        "source_upstream":"SyGuS-Org/benchmarks","original_commit":PIN,
        "original_path":PATH,"original_source_sha256":sha256(original),
        "n_original_state_vars":len(params),
        "original_inv_constraints":1,
        "source_closed_formulas":True,
        "Z3_version":z3.get_version_string(),
        "original_modern_CVC5_142_12CPU":"TIMEOUT",
        "total_classical_5_candidates_process_cpu_seconds":round(
            sum(t["full_process_cpu_seconds"] for t in cases),6),
        "no_adaptive_changes_from_results":True,
        "n_verified_full_inductive":sum(t["status"]=="PASS_ALL_THREE_INDUCTIVE_VCS" for t in cases),
        "ownweight_model":False,"G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
        "cases":cases}
    path=OUT/"FIREFLY_ORIGINAL_5_CLASSIC_INVARIANTS_3VC_POSTFIRST.json"
    path.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("REPORT_SHA256",sha256(path.read_bytes()),flush=True)
    print("NUM_VERIFIED",report["n_verified_full_inductive"],flush=True)
if __name__=="__main__":main()
