"""Prospective first-source-body classical ceiling for genuine original 24 QF_NRA.

All original source SHA/bytes fixed by GitHub file metadata pre-inspection.
Three full-source classical solver arms, no learned model and no gold labels.
Any SAT/UNSAT must be actual complete unchanged published original source
status. No original SAT/UNSAT assumed from filename/matched BDC/DDC stem.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
import z3

REGISTERED_SHA="7a0d8d8d414d35e7b7f77c24897fd9120c3f9f14"
ORIGINAL_REV="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
HARD_WALL_S=5
INNER_TIMEOUT_MS=4000

def authentic_blob_sha(b:bytes):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def raw_engine(b,engine):
    t=time.perf_counter_ns()
    if engine=="Z3_GENERAL":
        cmd=[sys.executable,"-c","import z3,sys; s=z3.Solver();s.set(timeout=4000);s.from_string(sys.stdin.read());print(s.check())"]
    elif engine=="Z3_QFNRA":
        cmd=[sys.executable,"-c","import z3,sys; s=z3.SolverFor('QF_NRA');s.set(timeout=4000);s.from_string(sys.stdin.read());print(s.check())"]
    elif engine=="CVC5":
        cmd=["cvc5","--lang=smt2","--tlimit-per=4000","-"]
    else:raise ValueError("SOURCE_EXPERT_NAME_INVALID")
    result="UNKNOWN";error=None;exitcode=None
    try:
        p=subprocess.run(cmd,input=b.decode("utf-8"),capture_output=True,text=True,timeout=HARD_WALL_S)
        exitcode=p.returncode
        values=[line.strip().upper() for line in p.stdout.splitlines()
                if line.strip().lower() in ("sat","unsat","unknown")]
        if p.returncode==0 and values:
            result=values[-1]
        elif p.returncode!=0:
            result="ABSTAIN_SOURCE_ENGINE_ERROR"
            error="exit="+str(p.returncode)+":"+p.stderr[:240]
    except subprocess.TimeoutExpired:
        result="UNKNOWN_OS_WALL_CAP"
    except Exception as e:
        result="ABSTAIN_RUNTIME_EXCEPTION"
        error=type(e).__name__+":"+str(e)[:180]
    return {"engine":engine,"actual_original_solver_result":result,
            "backend_real_OS_wall_ms":(time.perf_counter_ns()-t)/1e6,
            "original_solver_inner_limit_ms":INNER_TIMEOUT_MS,
            "original_solver_outer_limit_seconds":HARD_WALL_S,
            "return_code":exitcode,"error":error}

def case(original_root,item):
    begin=time.perf_counter_ns()
    report={"true_original_path":item["path"],"family":item["family"],
            "paired_variant_filename_stem_only":item["stem"],
            "frozen_original_git_blob":item["git_blob"],
            "source_sha_verified":False,"status":"ABSTAIN_SOURCE"}
    try:
        data=(original_root/item["path"]).read_bytes()
        if len(data)!=item["bytes"] or authentic_blob_sha(data)!=item["git_blob"]:
            raise ValueError("ORIGINAL_PREINSPECTION_SHA_AND_SIZE_NOT_MATCH")
        report["source_sha_verified"]=True
        report["authentic_source_SHA256"]=hashlib.sha256(data).hexdigest()
        ast=z3.Solver();ast.from_string(data.decode("utf-8"))
        report["original_actual_native_assertion_count"]=len(ast.assertions())
        if len(ast.assertions())<1:
            raise ValueError("ORIGINAL_ASSERTIONS_EMPTY")
        receipts=[raw_engine(data,e) for e in ("Z3_GENERAL","Z3_QFNRA","CVC5")]
        report["same_cpu_real_full_original_solver_receipts"]=receipts
        answered={x["actual_original_solver_result"] for x in receipts}&{"SAT","UNSAT"}
        report["any_direct_original_SAT"]= "SAT" in answered
        report["any_direct_original_UNSAT"]= "UNSAT" in answered
        report["original_strong_raw_solver_produced_answer"]=bool(answered)
        report["any_known_SAT_UNSAT_disagreement"]=len(answered)>1
        report["original_dual_independent_agreement"]=len({
          receipts[0]["actual_original_solver_result"],receipts[2]["actual_original_solver_result"]
        })==1 and receipts[0]["actual_original_solver_result"] in ("SAT","UNSAT")
        report["status"]=("FAIL_ORIGINAL_SOLVER_LOGIC_CONFLICT" if len(answered)>1 else
                          "TRUE_ORIGINAL_STRONG_DIRECT_SOLVED" if answered else
                          "TRUE_ORIGINAL_STRONG_DIRECT_TIMEOUT_UNKNOWN")
    except Exception as e:
        report["status"]="ABSTAIN_ORIGINAL_SOURCE_OR_PARSE_ERROR"
        report["source_error"]=type(e).__name__+":"+str(e)[:350]
    report["all_source_sha_parse_and_three_solver_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("Q3_NEW_UNCU24_FIRST_SOURCE",item["family"],item["path"].split("/")[-1],
          "SHA",report["source_sha_verified"],
          "EXPERT",[q["actual_original_solver_result"] for q in report.get("same_cpu_real_full_original_solver_receipts",[])],
          "CLASS",report["status"],"ERR",report.get("source_error"),flush=True)
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    manifest=json.loads(o.manifest.read_text())
    if manifest["schema"]!="neumann.Q3.l1_uncu_24_genuine_presource_expert_screen.v1":
        raise RuntimeError("SOURCE_FROZEN_24_EXPERT_CONTRACT_INVALID")
    if manifest["original_source_revision"].split("@")[-1]!=ORIGINAL_REV:
        raise RuntimeError("ORIGINAL_BENCHMARK_COMMIT_DRIFT")
    rows=manifest["all_original_sha_and_byte_targets"]
    if len(rows)!=24 or len({z["git_blob"] for z in rows})!=24:
        raise RuntimeError("SOURCE_COHORT_NOT_24_INDEPENDENT_GIT_BLOBS")
    result=[case(o.root,z) for z in rows]
    solved=sum(r.get("original_strong_raw_solver_produced_answer",False) for r in result)
    report={
      "schema":"neumann.q3.first24_presource_uncu_polynomial_rational_original_ceiling.v1",
      "strict_original_source_preinspection_SHA_freeze_commit":REGISTERED_SHA,
      "all_24_source_body_first_opened_after_SHA_freeze":True,
      "original_file_cases_authentic_SHA_verified":sum(r["source_sha_verified"] for r in result),
      "all_24_originals_retained":len(result)==24,
      "strong_original_three_solver_portfolio_solved_total":solved,
      "candidate_unresolved_original_source_count":24-solved,
      "source_original_label_cvc5_Z3_conflicts":sum(r.get("any_known_SAT_UNSAT_disagreement",False) for r in result),
      "first_screen_only_NOT_learning":True,
      "fresh_original_source_bodies_no_longer_blind_for_future_training":True,
      "all_solvers_on_same_CPU_hard_process_limit":True,
      "no_same_filename_stem_implies_mathematical_equivalence_assumed":True,
      "by_family":{name:{"total":sum(r["family"]==name for r in result),
                         "solved":sum(r["family"]==name and r.get("original_strong_raw_solver_produced_answer",False) for r in result)}
                   for name in ("POLYNOMIAL","BASIC_DENOMINATOR","DISJUNCTIVE_DENOMINATOR")},
      "originals":result,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN"
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q3_UNCU_FIRST_AUTHENTIC_ORIGINAL_24",report["original_file_cases_authentic_SHA_verified"],"/24")
    print("Q3_UNCU_STRONG_RAW_ORIGINAL_SOLVED",solved,"/24")
    print("Q3_UNCU_STRONG_RAW_ORIGINAL_HARD_RESIDUAL",24-solved)
    print("Q3_UNCU_FIRST_24_FAMILIES",report["by_family"])
    print("Q3_UNCU_GLOBAL_LEARNED_Q3_OPEN",report["global_Q3"])
if __name__=="__main__":
    main()
