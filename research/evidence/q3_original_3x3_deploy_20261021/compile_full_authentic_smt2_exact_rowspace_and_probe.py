"""Executable original QF_NIA structural compression, not SAT oracle.

Each authentic published original 3x3 source retains ALL original assertions
except the original power-sum equations independently proved linearly
redundant over arbitrary formal power-feature values. In particular the
original nonlinear x**k, positivity, distinct constraints remain untouched.
The entire reduced source is equivalent to the original conjunction because
both source equality subsystems have the same exact Z3+cvc5-certified rowspace
and every other original native AST assertion is identical.
"""
from __future__ import annotations
import argparse,json,subprocess,sys,time
from pathlib import Path
import z3
from sympy import Matrix
from research.evidence.q3_original_3x3_rank_20261021.exact_true_original_magic_power_rowspace_dual import (
  parse_true_source_linear_skeleton,frac_rank_exact,independent_source_rowspace_dual
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

SOURCE_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
WALL_PROCESS_CAP=4.5
MODEL_INTERNAL_CAP_MS=3000

def original_source_vars(assertions):
    declared={}
    pending=list(assertions)
    while pending:
        term=pending.pop()
        if term.num_args()==0 and term.decl().kind()==z3.Z3_OP_UNINTERPRETED:
            if term.sort().kind()!=z3.Z3_INT_SORT:
                raise RuntimeError("NON_INT_SOURCE_SYMBOL_NOT_DEPLOYABLE")
            declared[str(term)]=term
        else:
            pending.extend(term.children())
    return sorted(declared)

def original_semantics_smt2(assertions):
    symbols=original_source_vars(assertions)
    parts=["(set-logic QF_NIA)"]
    parts.extend(f"(declare-fun {v} () Int)" for v in symbols)
    parts.extend(f"(assert {a.sexpr()})" for a in assertions)
    parts.append("(check-sat)")
    parts.append("(exit)")
    return "\n".join(parts)+"\n"

def status_run(name,payload):
    begin=time.perf_counter_ns()
    state="UNKNOWN";error=None;out=""
    try:
        if name=="z3":
            code="""import sys,z3
s=z3.Solver()
s.set(timeout=3000)
s.from_string(sys.stdin.read())
print(s.check())"""
            cmd=[sys.executable,"-c",code]
        elif name=="cvc5":
            cmd=["cvc5","--lang=smt2","--tlimit-per=3000","-"]
        else:raise ValueError("UNKNOWN_RAW_BACKEND")
        p=subprocess.run(cmd,input=payload,text=True,capture_output=True,
                         timeout=WALL_PROCESS_CAP)
        matches=[t.strip().upper() for t in p.stdout.splitlines()
                 if t.strip().lower() in ("sat","unsat","unknown")]
        if p.returncode==0 and matches:state=matches[0]
        elif p.returncode!=0:
            error=f"PROCESS_EXIT_{p.returncode}:STDERR:{p.stderr[:250]}"
        out=p.stdout[:250]
    except subprocess.TimeoutExpired:
        state="UNKNOWN_HARD_PROCESS_CAP"
    except Exception as e:
        state="ABSTAIN_PROCESS_ERROR"
        error=type(e).__name__+":"+str(e)[:240]
    return {"engine":name,"source_status":state,
            "external_OS_hard_timeout_sec":WALL_PROCESS_CAP,
            "whole_raw_source_backend_wall_ms":(time.perf_counter_ns()-begin)/1e6,
            "error":error,"stdout_excerpt":out}

def original_to_reduced(root,item):
    start=time.perf_counter_ns()
    row={"source":item["path"],"original_sha":item["sha1_git_blob"],
         "source_Git_blob_authenticated":False,
         "status":"ABSTAIN",
         "actual_original_full_formula_equivalence_certified":False}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("ACTUAL_TRUE_SOURCE_FILE_BLOB_MISMATCH")
        row["source_Git_blob_authenticated"]=True
        row["original_source_SHA256"]=sha256(raw)
        orig=z3.Solver();orig.from_string(raw.decode("utf-8"))
        actual=list(orig.assertions())
        spec,rows=parse_true_source_linear_skeleton(orig)
        mx=Matrix(rows);rank=int(mx.rank())
        assert frac_rank_exact(rows)==rank
        indep=list(mx.T.rref()[1])
        cert=independent_source_rowspace_dual(rows,indep)
        row["linear_feature_skeleton_independent_original_dual_proof"]=cert
        if not cert["both_actual_independent_skeleton_equivalence"]:
            row["status"]="ABSTAIN_ORIGINAL_LINEAR_SKELETON_FAILED"
            return row
        special_hashes=[q["source_ast_sha256"] for q in spec["source_rows"]]
        assert len(set(special_hashes))==len(special_hashes)
        kept_hashes=set(special_hashes[i] for i in indep)
        dropped_hashes=set(special_hashes)-kept_hashes
        retained=[q for q in actual if sha256(q.sexpr().encode()) not in dropped_hashes]
        assert len(actual)-len(retained)==len(rows)-rank
        before=sorted(sha256(q.sexpr().encode()) for q in actual
                      if sha256(q.sexpr().encode()) not in special_hashes)
        after=sorted(sha256(q.sexpr().encode()) for q in retained
                     if sha256(q.sexpr().encode()) not in special_hashes)
        assert before==after
        assert set(sha256(q.sexpr().encode()) for q in retained)==(
            set(sha256(q.sexpr().encode()) for q in actual)-dropped_hashes)
        full=original_semantics_smt2(actual)
        reduced=original_semantics_smt2(retained)
        # Independent correctness guards on the TWO exact generated full
        # native QF_NIA SMT-LIB programs, not checker-only abstraction.
        for script in (full,reduced):
            s=z3.Solver()
            s.from_string(script)
            assert len(s.assertions())==(
                len(actual) if script==full else len(retained))
        row["all_unchanged_true_original_nonlinear_positive_distinct_AST_sha_verified"]=True
        row["original_full_AST_assertion_count"]=len(actual)
        row["reduced_full_AST_assertion_count"]=len(retained)
        row["actually_redundant_original_power_sum_assertions_removed"]=len(dropped_hashes)
        row["original_full_source_generated_canonical_SHA256"]=sha256(full.encode())
        row["reduced_full_original_equivalent_QFNIA_SHA256"]=sha256(reduced.encode())
        row["source_linear_feature_rank"]=rank
        row["source_original_necessary_power_feature_dimensions"]=len(rows[0])-rank
        row["actual_original_full_formula_equivalence_certified"]=True
        row["full_compiler_parser_rank_two_solver_certificate_wall_ms"]=(time.perf_counter_ns()-start)/1e6
        row["original_direct_on_FULL_true_source"]={
            engine:status_run(engine,full) for engine in ("z3","cvc5")}
        row["source_equivalent_compiled_reduce_FULL"]={
            engine:status_run(engine,reduced) for engine in ("z3","cvc5")}
        before_status=set(x["source_status"] for x in row["original_direct_on_FULL_true_source"].values())
        after_status=set(x["source_status"] for x in row["source_equivalent_compiled_reduce_FULL"].values())
        definitive=lambda x:set(x)&{"SAT","UNSAT"}
        row["backend_observed_original_positive_success"]=bool(definitive(before_status))
        row["backend_observed_reduced_positive_success"]=bool(definitive(after_status))
        row["no_conflicting_actual_full_QFNIA_solver_answer"]=not (
            ("SAT" in before_status|after_status) and ("UNSAT" in before_status|after_status))
        row["status"]="CERTIFIED_EQUIVALENT_FULL_QFNIA_SOURCE_REWRITE" if row[
           "no_conflicting_actual_full_QFNIA_solver_answer"] else "FAIL_CONFLICT_SOLVER_ANSWERS"
        row["original_full_two_solver_wall_ms"]=sum(x["whole_raw_source_backend_wall_ms"] for x in row["original_direct_on_FULL_true_source"].values())
        row["reduced_full_two_solver_wall_ms"]=sum(x["whole_raw_source_backend_wall_ms"] for x in row["source_equivalent_compiled_reduce_FULL"].values())
        row["reduced_FULL_plus_initial_compiler_certificate_paid_ms"]=(
            row["reduced_full_two_solver_wall_ms"]+row["full_compiler_parser_rank_two_solver_certificate_wall_ms"])
        row["source_full_task_iso_positive_correctness"]=(
            row["backend_observed_original_positive_success"] and row["backend_observed_reduced_positive_success"]
            and row["no_conflicting_actual_full_QFNIA_solver_answer"])
        row["compiled_original_is_NOT_new_true_source_sat_unsat_result"]=True
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_GENERATOR_OR_SOLVER_EXCEPTION"
        row["error"]=type(e).__name__+":"+str(e)[:360]
    row["whole_experiment_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_3X3_FULL_QFNIA_REDUCED_ACTUAL_SOURCE",item["path"].split("/")[-1],
          "ORIGINAL_EQ",row["actual_original_full_formula_equivalence_certified"],
          "DROP",row.get("actually_redundant_original_power_sum_assertions_removed"),
          "RAW",[x["source_status"] for x in row.get("original_direct_on_FULL_true_source",{}).values()],
          "REDUCED",[x["source_status"] for x in row.get("source_equivalent_compiled_reduce_FULL",{}).values()],
          "ISO",row.get("source_full_task_iso_positive_correctness"),
          "STATUS",row["status"],"ERROR",row.get("error"),flush=True)
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    z=ap.parse_args()
    c=json.loads(z.contract.read_text());q=json.loads(z.freeze.read_text())
    if c["schema"]!="neumann.q3.posthoc.deploy_source_native_full_QFNIA_equivalent_magic_3x3.v1":
        raise RuntimeError("ACTUAL_SOURCE_COMPILER_PROTOCOL_CHANGED")
    if q["source"].split("@")[-1]!=SOURCE_COMMIT or len(q["five_original_3x3_controls"])!=5:
        raise RuntimeError("SOURCE_FROZEN_IDENTITY_MISMATCH")
    rows=[original_to_reduced(z.root,s) for s in q["five_original_3x3_controls"]]
    original=sum(x.get("backend_observed_original_positive_success",False) for x in rows)
    reduced=sum(x.get("backend_observed_reduced_positive_success",False) for x in rows)
    valid=sum(x["actual_original_full_formula_equivalence_certified"] for x in rows)
    report={
       "schema":"neumann.q3.real3x3_deploy_original_QFNIA_equivalent_compiler_matched.v1",
       "posthoc_after_frozen_source_original_open":True,
       "all_five_original_rows_preserved":len(rows)==5,
       "original_source_equivalent_full_native_compilation_dual_certificates":valid,
       "raw_generic_full_QFNIA_positive_solver_success_count":original,
       "reduced_generic_full_QFNIA_positive_solver_success_count":reduced,
       "no_false_solver_answer_conflicts":all(x.get("no_conflicting_actual_full_QFNIA_solver_answer",False) for x in rows),
       "no_asymptotic_10x_based_on_UNRESOLVED_both_unsolved":True,
       "is_source_linear_skeleton_only_NOT_original_total_problem_solved":True,
       "same_compiler_available_to_strong_direct":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "originals":rows,
    }
    z.out.parent.mkdir(parents=True,exist_ok=True)
    z.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_DEPLOY_REAL3X3_SOURCE_FULL_EQUIVALENCE",valid,"/5")
    print("Q3_DEPLOY_REAL3X3_RAW_SOURCE_TRUE_SOLVED",original,"/5")
    print("Q3_DEPLOY_REAL3X3_REDUCED_SOURCE_TRUE_SOLVED",reduced,"/5")
    print("Q3_DEPLOY_GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
