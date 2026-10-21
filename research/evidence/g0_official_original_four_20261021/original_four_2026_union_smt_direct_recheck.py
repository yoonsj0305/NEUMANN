"""Pre-source-blind original QF_NIA G0 classical headroom screen.

No generated NEUMANN solutions. Both strong direct Z3 and independently
pinned cvc5 receive UNCHANGED, SHA-pinned original SMT2. SAT requires a
grounded entire original assertion model re-checked in cvc5. UNSAT
requires both independent solver decisions. Everything else UNKNOWN.
Official 2026 17-configuration historical timeout is separate context,
not comparable full 1200s in this 15sec CPU preflight.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,time
from pathlib import Path
import z3

Z3_TIMEOUT_MS=15000
CVC5_TIMEOUT_MS=15000
SOURCE_REV="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
FREEZE_COMMIT="39ed7c703a922daa4d99e72dfee2e18ea3b77069"

def git_blob_sha1(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode("ascii")+b"\0"+b).hexdigest()

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def z3_original_direct(source):
    start=time.perf_counter_ns()
    record={"raw_original_semantics":True,"status":"UNKNOWN"}
    solver=None
    try:
        solver=z3.Solver()
        solver.set("timeout",Z3_TIMEOUT_MS)
        solver.from_string(source.decode("utf-8"))
        record["original_assertion_count"]=len(solver.assertions())
        if not solver.assertions():
            raise RuntimeError("ZERO_ORIGINAL_ASSERTIONS_NOT_ADMITTED")
        ans=solver.check()
        record["raw_original_z3_result"]=str(ans)
        record["status"]=str(ans).upper()
        if ans==z3.unknown:record["reason_unknown"]=solver.reason_unknown()
    except Exception as exc:
        record["status"]="UNKNOWN_PARSE_OR_EXEC"
        record["error"]=type(exc).__name__+":"+str(exc)[:300]
    record["total_solver_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return record,solver

def cvc5_original_direct(path):
    start=time.perf_counter_ns()
    record={"status":"UNKNOWN","raw_original_path_unchanged":True}
    try:
        call=subprocess.run(
            ["cvc5","--lang=smt2",
             "--tlimit-per="+str(CVC5_TIMEOUT_MS),str(path)],
            capture_output=True,text=True,timeout=CVC5_TIMEOUT_MS/1000+3)
        record["exit_code"]=call.returncode
        record["stdout_sha256"]=sha256(call.stdout.encode())
        record["stderr_excerpt"]=call.stderr[:280]
        tokens=[x.strip() for x in call.stdout.splitlines()
                if x.strip() in ("sat","unsat","unknown")]
        if call.returncode==0 and tokens:
            record["status"]=tokens[0].upper()
        else:
            record["status"]="UNKNOWN_EXIT_OR_NO_SAT_TOKEN"
    except Exception as exc:
        record["status"]="UNKNOWN_EXEC_OR_TIMEOUT"
        record["error"]=type(exc).__name__+":"+str(exc)[:300]
    record["total_solver_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return record

def independent_grounded_model_check(parsed_solver):
    start=time.perf_counter_ns()
    receipt={"status":"UNKNOWN"}
    try:
        model=parsed_solver.model()
        assertions=list(parsed_solver.assertions())
        from z3.z3util import get_vars
        vars_=get_vars(z3.And(*assertions))
        if not vars_:
            raise RuntimeError("NO_FREE_VARS_TO_GROUND")
        equalities=[]
        for v in vars_:
            value=model.eval(v,model_completion=True)
            if z3.is_algebraic_value(value):
                receipt["status"]="UNKNOWN_ALGEBRAIC_GROUNDING_UNSUPPORTED"
                return receipt
            equalities.append(v==value)
        candidate=z3.Solver()
        candidate.add(*assertions,*equalities)
        # Fast preflight before independent cvc5. Original assertion is not
        # weakened; assignments cover every symbolic constant in the formula.
        chk=candidate.check()
        receipt["source_constraints_and_complete_ground_model_z3"]=str(chk)
        if chk!=z3.sat:
            return receipt
        payload=candidate.sexpr()+"\n(check-sat)\n"
        call=subprocess.run(
            ["cvc5","--lang=smt2","--tlimit-per=12000","-"],
            input=payload,capture_output=True,text=True,timeout=14)
        receipt["original_assertion_smt_dump_sha256"]=sha256(payload.encode())
        receipt["original_assertion_vars_grounded_count"]=len(vars_)
        receipt["independent_cvc5_exit"]=call.returncode
        receipt["independent_cvc5_stdout_sha256"]=sha256(call.stdout.encode())
        receipt["independent_original_ground_assertions_cvc5"]=(
            next((line.strip() for line in call.stdout.splitlines()
                  if line.strip() in ("sat","unsat","unknown")),"unknown"))
        if call.returncode==0 and receipt["independent_original_ground_assertions_cvc5"]=="sat":
            receipt["status"]="INDEPENDENT_FULL_ORIGINAL_GROUNDED_SAT"
    except Exception as exc:
        receipt["error"]=type(exc).__name__+":"+str(exc)[:320]
    finally:
        receipt["ground_recheck_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    return receipt

def audit_one(root,meta):
    begin=time.perf_counter_ns()
    path=meta["path"];filename=root/path
    record={"source":path,"frozen_git_blob_sha1":meta["sha1_git_blob"],
            "status":"UNKNOWN_NOT_AUTHENTICATED",
            "original_UNSAT_dual_confirmed":False,
            "original_SAT_grounded_independent_confirmed":False,
            "global_Q3":"OPEN"}
    try:
        raw=filename.read_bytes()
        if len(raw)!=meta["bytes"] or git_blob_sha1(raw)!=meta["sha1_git_blob"]:
            raise RuntimeError("SOURCE_BYTES_OR_GIT_BLOB_MISMATCH")
        record["source_original_sha256"]=sha256(raw)
        record["full_source_authenticated"]=True
        record["source_bytes"]=len(raw)
        z,s=z3_original_direct(raw)
        record["z3_direct"]=z
        c=cvc5_original_direct(filename)
        record["cvc5_direct"]=c
        if z["status"]=="UNSAT" and c["status"]=="UNSAT":
            record["status"]="TRUE_ORIGINAL_UNSAT_IN_TWO_INDEPENDENT_SOLVERS"
            record["original_UNSAT_dual_confirmed"]=True
        elif z["status"]=="SAT":
            cert=independent_grounded_model_check(s)
            record["independent_complete_source_model_proof"]=cert
            if cert.get("status")=="INDEPENDENT_FULL_ORIGINAL_GROUNDED_SAT":
                record["status"]="TRUE_ORIGINAL_SAT_WITH_GROUNDED_Z3_CVC5_PROOF"
                record["original_SAT_grounded_independent_confirmed"]=True
            else:
                record["status"]="UNKNOWN_Z3_SAT_NOT_DUAL_GROUNDED"
        elif (z["status"]=="UNSAT" and c["status"]=="SAT") or (
            z["status"]=="SAT" and c["status"]=="UNSAT"):
            record["status"]="ALARM_INDEPENDENT_SOLVER_CONTRADICTION"
        else:
            record["status"]="OPENED_ORIGINAL_BOUNDED_CLASSICAL_UNKNOWN"
    except Exception as exc:
        record["status"]="ABSTAIN_ORIGINAL_SOURCE_OR_EXEC_ERROR"
        record["error"]=type(exc).__name__+":"+str(exc)[:340]
    record["full_case_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("SMTCOMP_FIRST_ORIGINAL_HARD_G0",path,
          "Z3",record.get("z3_direct",{}).get("status"),
          "CVC5",record.get("cvc5_direct",{}).get("status"),
          "FINAL",record["status"],
          "WALL",round(record["full_case_wall_ms"],2),flush=True)
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    freeze=json.loads(a.freeze.read_text())
    if freeze["original_repo_revision"]!=SOURCE_REV or len(freeze["targets"])!=4:
        raise RuntimeError("PRECONTENT_ORIGINAL_FOUR_IDENTITY_CHANGED")
    first=[audit_one(a.root,t) for t in freeze["targets"]]
    nsolved=sum(x["original_UNSAT_dual_confirmed"] or x["original_SAT_grounded_independent_confirmed"] for x in first)
    nunknown=sum(x["status"]=="OPENED_ORIGINAL_BOUNDED_CLASSICAL_UNKNOWN" for x in first)
    all_auth=sum(x.get("full_source_authenticated",False) for x in first)
    out={
        "schema":"neumann.g0.2026_official_unsolved_four_first_real_direct_recheck.v1",
        "presource_freeze_commit":FREEZE_COMMIT,
        "source_git_revision":SOURCE_REV,
        "source_SHA_and_full_original_verified_count":all_auth,
        "all_frozen_four_rows_preserved":len(first)==4,
        "original_full_sat_or_unsat_independently_dual_certified":nsolved,
        "newly_bounded_CPU_dual_direct_unresolved_count":nunknown,
        "all_original_direct_SMT2_solving_budgets_milliseconds":{
           "Z3":Z3_TIMEOUT_MS,"cvc5":CVC5_TIMEOUT_MS},
        "the_official_2026_17_solver_1200s_result_is_historical_not_replicated":True,
        "this_run_uses_no_neural_model_or_oracle_label_at_inference":True,
        "this_run_never_solves_hard_original_with_NEUMANN":True,
        "new_independent_structure_discovery":"NOT_DEMONSTRATED",
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
        "first_source_cases":first,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("G0_FIRST_OFFICIAL_FOUR_ORIGINAL_SHA_VERIFIED",all_auth,"/4")
    print("G0_FIRST_OFFICIAL_FOUR_ORIGINAL_INDEPENDENT_SAT_OR_UNSAT_CERTIFIED",nsolved,"/4")
    print("G0_FIRST_FOUR_RESIDUAL_CPU_15SEC_BOTH_UNKNOWN",nunknown,"/4")
    print("GLOBAL_Q3",out["global_Q3"])
if __name__=="__main__":
    main()
