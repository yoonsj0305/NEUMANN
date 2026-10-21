"""Prospectively SHA frozen ORIGINAL QF_NRA / NRA expert ceiling screen.

NO learned model, no oracle answer; all 18 originals previously not read at
freeze commit 5412a4f. Actual Z3, cvc5 original SMT-LIB and specialized Z3
QF_NRA with OS process caps. If the strongest equally-authorized classical
experts solve ALL cases, these sources have NO capability gap to beat.

A true SAT/UNSAT outcome is only the actually reported solver response to
the complete original unchanged SMT-LIB. UNKNOWN/ERROR is never SAT/UNSAT.
No clever source-based routing after reading any task.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path
import z3

MANIFEST_COMMIT="5412a4fb16c96694ab2bf629c34f6e41737f7a7f"
ORIGINAL_SHA="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
HARD_CAP_S=7.0
INNER_MS=5000

def sha1_git_blob(source:bytes):
    import hashlib
    return hashlib.sha1(b"blob "+str(len(source)).encode()+b"\0"+source).hexdigest()

def sha256(source:bytes):
    import hashlib
    return hashlib.sha256(source).hexdigest()

SOLVER_PROGRAM=r"""
import sys,z3
raw=sys.stdin.read()
mode=sys.argv[1]
if mode=="special":
    p=z3.SolverFor("QF_NRA")
else:
    p=z3.Solver()
p.set(timeout=5000)
p.from_string(raw)
print(p.check())
"""
def status_engine(raw,engine,source_logic):
    clock=time.perf_counter_ns()
    if engine=="cvc5":
        cmd=["cvc5","--lang=smt2","--tlimit-per=5000","-"]
    elif engine=="Z3_GENERAL":
        cmd=[sys.executable,"-c",SOLVER_PROGRAM,"general"]
    elif engine=="Z3_QFNRA":
        if source_logic!="QF_NRA":
            return {"solver":"Z3_QFNRA","status":"NOT_APPLICABLE_NON_QF_LOGIC",
                    "total_elapsed_ms":0.0,"not_counted_unknown":True}
        cmd=[sys.executable,"-c",SOLVER_PROGRAM,"special"]
    else:raise ValueError("UNEXPECTED_CLASSICAL_EXPERT")
    state="UNKNOWN";err=None;rc=None
    try:
        p=subprocess.run(cmd,input=raw.decode("utf-8"),capture_output=True,
                         text=True,timeout=HARD_CAP_S)
        rc=p.returncode
        statuses=[x.strip().upper() for x in p.stdout.splitlines()
                  if x.strip().lower() in ("sat","unsat","unknown")]
        if rc==0 and len(statuses)>=1:
            state=statuses[-1]
        else:
            state="ABSTAIN_ENGINE_ERROR"
            err=f"exit={rc}, stderr="+p.stderr[:350]
    except subprocess.TimeoutExpired:
        state="UNKNOWN_HARD_OS_WALL_CAP"
    except Exception as e:
        state="ABSTAIN_ENGINE_EXCEPTION"
        err=type(e).__name__+":"+str(e)[:250]
    return {"solver":engine,"status":state,"return_code":rc,
            "total_elapsed_ms":(time.perf_counter_ns()-clock)/1e6,
            "OS_process_wall_cap_seconds":HARD_CAP_S,
            "solver_internal_wall_cap_ms":INNER_MS,"error":err}

def source_original(root,item):
    t=time.perf_counter_ns()
    rec={"family":item["family"],"path":item["path"],
         "first_source_body_study_split":item["split"],
         "registered_original_git_blob":item["git_blob"],
         "original_Git_blob_authenticated":False,
         "status":"ABSTAIN_ORIGINAL"}
    try:
        b=(root/item["path"]).read_bytes()
        if len(b)!=item["bytes"] or sha1_git_blob(b)!=item["git_blob"]:
            raise ValueError("FIRST_OPENED_ORIGINAL_SOURCE_SHA_OR_SIZE_CHANGED")
        rec["original_Git_blob_authenticated"]=True
        rec["true_original_source_sha256"]=sha256(b)
        # BOTH parser and solver accept the original untouched source.
        native=z3.Solver()
        native.from_string(b.decode("utf-8"))
        rec["exact_native_original_assertion_count"]=len(native.assertions())
        logic="QF_NRA" if item["family"]=="GEOGEBRA" else "NRA"
        rec["source_native_mathematical_logic"]=logic
        rec["source_solver_execution_receipts"]=[
            status_engine(b,"Z3_GENERAL",logic),
            status_engine(b,"cvc5",logic),
            status_engine(b,"Z3_QFNRA",logic)]
        results={r["status"] for r in rec["source_solver_execution_receipts"]}
        rec["actually_observed_complete_original_SAT"]= "SAT" in results
        rec["actually_observed_complete_original_UNSAT"]= "UNSAT" in results
        rec["original_dual_Z3_cvc5_direct_status_agreement"]=(
             rec["source_solver_execution_receipts"][0]["status"]==
             rec["source_solver_execution_receipts"][1]["status"] and
             rec["source_solver_execution_receipts"][0]["status"] in ("SAT","UNSAT"))
        rec["strong_classical_original_task_resolved"]=bool(results&{"SAT","UNSAT"})
        rec["source_solver_possibly_contradictory_original_status"]="SAT" in results and "UNSAT" in results
        rec["status"]="FAIL_ORIGINAL_DIFFERENT_SOLVERS_CONTRADICT" if rec[
          "source_solver_possibly_contradictory_original_status"] else (
            "STRONG_CLASSICAL_SOLVED_ORIGINAL" if rec["strong_classical_original_task_resolved"]
            else "EXPERT_PORTFOLIO_ORIGINAL_UNKNOWN")
    except Exception as e:
        rec["status"]="ABSTAIN_SOURCE_OR_PARSER_EXCEPTION"
        rec["source_error"]=type(e).__name__+":"+str(e)[:310]
    rec["all_full_original_source_parse_three_solver_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    print("Q3_FIRST_NEW_NRA_AUTHENTIC_SOURCE",rec["path"].split("/")[-1],
          "FAMILY",rec["family"],"AUTHENTIC",rec["original_Git_blob_authenticated"],
          "EXPERT_STATUSES",[r["status"] for r in rec.get("source_solver_execution_receipts",[])],
          "STRONG_EXPERT_SOLVED",rec.get("strong_classical_original_task_resolved"),
          "STATUS",rec["status"],flush=True)
    return rec

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    contract=json.loads(a.freeze.read_text())
    if contract["schema"]!="neumann.q3.new_author_nra_original_18_before_source_body.v1":
        raise RuntimeError("PRE_BENCH_SOURCE_18_MANIFEST_CHANGED")
    if contract["original_upstream"].split("@")[-1]!=ORIGINAL_SHA or len(contract["cases"])!=18:
        raise RuntimeError("FROZEN_ORIGINAL_GIT_SHA_18_CHANGED")
    rows=[source_original(a.root,item) for item in contract["cases"]]
    strong=sum(r.get("strong_classical_original_task_resolved",False) for r in rows)
    unknown=sum(not r.get("strong_classical_original_task_resolved",False) for r in rows)
    report={
      "schema":"neumann.q3.first_open_18_NRA_other_author_expert_ceiling_original.v1",
      "first_source_body_opened_only_after_original_git_metadata_freeze_commit":MANIFEST_COMMIT,
      "all_eighteen_original_ids_retained":len(rows)==18,
      "authenticated_native_original_source_sha_count":sum(r["original_Git_blob_authenticated"] for r in rows),
      "strongest_three_original_solver_arms_resolved_total":strong,
      "original_source_remaining_candidate_hard_unsolved_total":unknown,
      "individual_expert_results_are_NOT_dual_certified_if_only_one_solver_reported_answer":True,
      "no_hidden_original_label_used_for_routing":True,
      "no_CPU_or_GPU_learned_model_ever_trained_in_this_expert_screen":True,
      "cannot_reuse_read_source_bodies_as_first_blind_future_learned_holdout":True,
      "actual_original_classification_conflicts":sum(r.get("source_solver_possibly_contradictory_original_status",False) for r in rows),
      "existing_equal_rights_STRONG_DIRECT_includes_Z3_cvc5_and_QFNRA":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "family_counts":{f:{"authentic":sum(r["family"]==f and r["original_Git_blob_authenticated"] for r in rows),
                          "solved":sum(r["family"]==f and r.get("strong_classical_original_task_resolved",False) for r in rows)}
                       for f in ("GEOGEBRA","STRASSEN","THREE_CIRCLES")},
      "all_exact_original_sources":rows
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_FIRST_NEW_AUTHENTIC_ORIGINAL_18",report["authenticated_native_original_source_sha_count"],"/18")
    print("Q3_NEW_ORIGINAL_STRONG_EXPERT_CEILING",strong,"/18")
    print("Q3_NEW_ORIGINAL_POTENTIAL_UNSOLVED_RESIDUAL",unknown,"/18")
    print("Q3_NEW_ORIGINAL_BY_FAMILY",report["family_counts"])
    print("Q3_GATES_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
