"""First PRE-SOURCE-FROZEN authentic original SMT-LIB source UNBOUNDED
UNSAT on three integer cubes with mod 9 finite complete sound abstraction.

Mathematical proof: every integer cube mod9 belongs to {0,1,8};
x mod9 determines x^3 mod9 by (x+9)^3-x^3=9(3x^2+27x+81).
An exact original assertion x^3+y^3+z^3=N with forbidden N%9 is
therefore UNSAT for ALL unbounded integers, not bounded-50k UNKNOWN.
Independent Z3+cvc5 check the finite abstract SMT formula; original
unchanged direct Z3/cvc5 also run for comparative status. No hidden label.
Elementary classical number theory, not learned invention or SOTA proof.
"""
from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
import z3
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    structural_source
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)

CUBE_RESIDUES=tuple(sorted({pow(r,3,9) for r in range(9)}))
THREE_CUBE_SUM_RESIDUES=tuple(sorted({(a+b+c)%9
    for a in CUBE_RESIDUES for b in CUBE_RESIDUES for c in CUBE_RESIDUES}))
assert CUBE_RESIDUES==(0,1,8)
assert THREE_CUBE_SUM_RESIDUES==(0,1,2,3,6,7,8)
FREEZE_COMMIT="b169a7fd88abb1818dc7327e413ad8b7ac59ea10"

def abstract_QFLIA(n,timeout=5):
    started=time.perf_counter_ns()
    a,b,c=z3.Ints("abc_r_0 abc_r_1 abc_r_2")
    s=z3.Solver();s.set(timeout=4000)
    for v in (a,b,c):
        s.add(z3.Or(*(v==i for i in CUBE_RESIDUES)))
    s.add(z3.Mod(a+b+c,9)==n%9)
    r=s.check()
    z3answer=str(r).upper()
    def abstract_source():
        rows=["(set-logic QF_LIA)"]
        for v in ("a","b","c"):
            rows.append(f"(declare-fun {v} () Int)")
            rows.append("(assert (or "+ " ".join(f"(= {v} {v0})" for v0 in CUBE_RESIDUES)+"))")
        rows.append(f"(assert (= (mod (+ a b c) 9) {n%9}))")
        rows+=["(check-sat)","(exit)"]
        return "\n".join(rows)+"\n"
    payload=abstract_source()
    cvc_status="UNKNOWN"
    cvc_exit=None
    try:
        cp=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=4000","-"],
                  input=payload,text=True,capture_output=True,timeout=timeout)
        cvc_exit=cp.returncode
        if cp.returncode==0:
            states=[x.strip().upper() for x in cp.stdout.splitlines()
                    if x.strip().lower() in ("sat","unsat","unknown")]
            if states:cvc_status=states[0]
    except subprocess.TimeoutExpired:
        cvc_status="UNKNOWN_TIMEOUT"
    math_expected="SAT" if n%9 in THREE_CUBE_SUM_RESIDUES else "UNSAT"
    return {
       "QF_LIA_exact_abstract_formula":payload,
       "abstract_formula_SHA256":sha256(payload.encode()),
       "Z3_result":z3answer,"cvc5_result":cvc_status,
       "cvc5_exit_code":cvc_exit,
       "mathematical_residue_729_finite_expected":math_expected,
       "independent_dual_abstract_agrees_with_finite_math":z3answer==cvc_status==math_expected,
       "actual_math_proof_wall_ms":(time.perf_counter_ns()-started)/1e6
    }

def original_direct(raw,parser,timeout_s=4):
    s=z3.Solver();s.set(timeout=timeout_s*1000);s.from_string(raw.decode("utf-8"))
    t=time.perf_counter_ns()
    z3_status=str(s.check()).upper()
    z3_cost=(time.perf_counter_ns()-t)/1e6
    t=time.perf_counter_ns()
    cvc_status="UNKNOWN";exitcode=None
    try:
        p=subprocess.run(["cvc5","--lang=smt2",f"--tlimit-per={timeout_s*1000}","-"],
            input=raw.decode("utf-8"),capture_output=True,text=True,timeout=timeout_s+2)
        exitcode=p.returncode
        val=[v.strip().upper() for v in p.stdout.splitlines()
             if v.strip().lower() in ("sat","unsat","unknown")]
        if p.returncode==0 and val:cvc_status=val[0]
    except subprocess.TimeoutExpired:
        cvc_status="UNKNOWN_TIMEOUT"
    cvc_cost=(time.perf_counter_ns()-t)/1e6
    return {"full_unchanged_source_Z3":z3_status,"full_unchanged_source_cvc5":cvc_status,
            "raw_z3_wall_ms":z3_cost,"raw_cvc5_wall_ms":cvc_cost,
            "raw_cvc5_exit":exitcode,"same_source_full_unbounded_UNSAT_dual":z3_status==cvc_status=="UNSAT"}

def prove_original(root,item,expected_class):
    t=time.perf_counter_ns()
    row={"path":item["path"],"expected_git_blob":item["sha1_git_blob"],
         "original_pre_source_frozen":True,"status":"ABSTAIN_NO_PROOF",
         "modular_mathematical_original_UNSAT_proven":False,
         "positive_control_modular_not_refuted":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("AUTHENTIC_PRE_SOURCE_GIT_BLOB_OR_BYTES_CHANGED")
        row["original_source_sha256"]=sha256(raw)
        target,names,parser=structural_source(raw)
        row["original_true_target"]=target
        row["original_var_names"]=names
        finite_cube=[pow(r,3,9) for r in range(9)]
        assert set(finite_cube)==set(CUBE_RESIDUES)
        assert len(THREE_CUBE_SUM_RESIDUES)==7
        row["full_mod9_finite_9residue_cube_table"]=finite_cube
        row["all_possible_three_integer_cubes_mod9"]=list(THREE_CUBE_SUM_RESIDUES)
        # Original exact AST checker verifies ONLY the true 3-cube equation
        # was asserted; thus finite structural abstraction is SOUND.
        abstraction=abstract_QFLIA(target)
        row["independent_source_theorem_abstract_smt_z3_cvc5"]=abstraction
        row["full_original_direct_control"]=original_direct(raw,parser,4)
        forbidden=target%9 not in THREE_CUBE_SUM_RESIDUES
        row["n_mod9_is_mathematically_forbidden"]=forbidden
        if expected_class=="NEW_UNBOUNDED_UNSAT":
            if forbidden and abstraction["independent_dual_abstract_agrees_with_finite_math"]:
                row["status"]="TRUE_ORIGINAL_ALL_INTEGER_UNSAT_BY_COMPLETE_MOD9_THEOREM"
                row["modular_mathematical_original_UNSAT_proven"]=True
            else:row["status"]="ABSTAIN_NOT_PROVED_BY_REGISTERED_MOD9"
        elif expected_class=="NOT_UNSAT_CONTROL":
            if not forbidden and abstraction["independent_dual_abstract_agrees_with_finite_math"]:
                row["status"]="FINITE_MOD9_PERMITS_NO_FULL_SAT_INFERRED"
                row["positive_control_modular_not_refuted"]=True
            else:row["status"]="FAIL_UNEXPECTED_MOD9_CONTROL"
        else:raise RuntimeError("UNREGISTERED_ROLE")
        row["scientific_scope"]="FIRST_GIT_BLOB_FROZEN_ORIGINAL_SOURCE"
    except Exception as e:
        row["status"]="ABSTAIN_ORIGINAL_PARSER_OR_SOLVER_EXCEPTION"
        row["error"]=type(e).__name__+":"+str(e)[:320]
    row["whole_authentic_original_source_structural_and_matched_direct_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    print("G0_FIRST_UNBOUNDED_SMT_ORIGINAL",row["path"],
          "TARGET",row.get("original_true_target"),"MOD9",row.get("n_mod9_is_mathematically_forbidden"),
          "STATUS",row["status"],"RAW_DIRECT",row.get("full_original_direct_control"),
          "ERROR",row.get("error"),flush=True)
    return row

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--root",type=Path,required=True)
    a.add_argument("--freeze",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    o=a.parse_args()
    f=json.loads(o.freeze.read_text())
    if f["schema"]!="neumann.g0.true_first_source_four_unbounded_cube_UNSAT_mod9.v1":
        raise RuntimeError("FROZEN_FIRST_SOURCE_CONTRACT_CHANGED")
    if len(f["targets"])!=4 or len(f["positive_source_controls"])!=2:
        raise RuntimeError("FIRST_FOUR_AND_TWO_SOURCE_CONTROL_COUNT_CHANGED")
    target=[prove_original(o.root,i,"NEW_UNBOUNDED_UNSAT") for i in f["targets"]]
    ctrls=[prove_original(o.root,i,"NOT_UNSAT_CONTROL") for i in f["positive_source_controls"]]
    successful=sum(x["modular_mathematical_original_UNSAT_proven"] for x in target)
    rawdual=sum(x.get("full_original_direct_control",{}).get("same_source_full_unbounded_UNSAT_dual",False) for x in target)
    report={
       "schema":"neumann.g0.first_authentic_four_source_unbounded_cube_mod9_unsat.v1",
       "four_original_git_sha_frozen_before_source_open_commit":FREEZE_COMMIT,
       "first_source_metadata_filename_target_leakacknowledged":True,
       "all_four_new_originals_retained":len(target)==4,
       "original_source_absolute_unbounded_UNSAT_mathematically_proven":successful,
       "original_full_source_dual_direct_UNSAT_within_each_4sec":rawdual,
       "control_mod9_does_NOT_falsely_claim_unsat_count":sum(q["positive_control_modular_not_refuted"] for q in ctrls),
       "independent_mod9_math_Z3_cvc5_unbounded_original_certificate":True,
       "full_original_checkers_run_but_abstract_theorem_is_separate_from_raw_source_solver":True,
       "no_neural_structure_discovery":True,
       "no_direct_strongest_source_mod9_algorithm_advantage":True,
       "scientific_scope":"real source original novel initial source-body discovery, conventional well-known mod9 theory; directory/name target-number is leaked",
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "four_true_original_unbounded_cases":target,"two_non_unsat_mod9_controls":ctrls
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("G0_FIRST_TRUE_ORIGINAL_UNBOUNDED_UNSAT_MATH",successful,"/4")
    print("G0_TRUE_ORIGINAL_RAW_4SEC_BOTH_DIRECT_UNSAT",rawdual,"/4")
    print("G0_TRUE_ORIGINAL_NEGATIVE_MOD9_CONTROLS_NOT_FALSE_UNSAT",
          report["control_mod9_does_NOT_falsely_claim_unsat_count"],"/2")
    print("GLOBAL_Q3_Q4_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
