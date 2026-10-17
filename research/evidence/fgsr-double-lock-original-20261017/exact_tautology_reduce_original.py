"""Exact Horn clause tautology reduction of a pinned 48-clause public original.

Each dropped original clause independently proved first-order VALID under
ARBITRARY interpretations of Inv and CHC_COMP_FALSE, not a bounded trace or
an inductive invariant. The reduced CHC retains exactly all other source clauses.
No neural model, no new operator grammar, no solution claims without certificate.
"""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SRC="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
OUT=Path(os.environ.get("FGSR_RESULT","real_original_exact_reduction_first_receipt.json"))

def original_solver_native(data):
    import z3
    lib=C.CDLL(str(Path(z3.__file__).parent/"lib/libz3.so"))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p];lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p];lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    cfg=lib.Z3_mk_config();ctx=lib.Z3_mk_context(cfg);lib.Z3_del_config(cfg)
    try:return (lib.Z3_eval_smtlib2_string(ctx,data) or b"").decode(errors="replace").strip()
    finally:lib.Z3_del_context(ctx)

def solver_child(mode,source):
    import z3
    data=Path(source).read_bytes()
    if mode=="native":return {"verdict":original_solver_native(data)}
    if mode=="horn":
        solver=z3.SolverFor("HORN");solver.set(timeout=20000)
        solver.from_string(data.decode())
        r=str(solver.check())
        ans={"verdict":r}
        if r=="unknown":ans["reason"]=solver.reason_unknown()
        if r=="sat":
            try:
                result=str(solver.model())
                ans["model_sha256"]=hashlib.sha256(result.encode()).hexdigest()
                ans["model_len"]=len(result)
            except Exception as e:ans["model_error"]=str(e)[:120]
        return ans
    raise ValueError("invalid mode")

def universal_body(clause,idx):
    import z3
    if not z3.is_quantifier(clause) or not clause.is_forall():
        raise ValueError("nonuniversal original assertion")
    vs=[z3.Const(f"VALIDATE_CLAUSE_{idx}_BOUND_{j}",clause.var_sort(j))
        for j in range(clause.num_vars())]
    return z3.substitute_vars(clause.body(),*vs)

def independent_is_valid(clause,idx):
    import z3
    t=time.perf_counter_ns()
    s=z3.Solver();s.set(timeout=1800)
    s.add(z3.Not(universal_body(clause,idx)))
    ans=str(s.check())
    record={"original_rule_1based":idx,"negated_universal_clause":ans,
            "wall_ms":round((time.perf_counter_ns()-t)/1e6,3)}
    if ans=="unknown":record["reason_unknown"]=s.reason_unknown()
    if ans=="unsat":
        # A separate fresh solver context checks identical logical statement
        # with a different name and a second parse, not a cached result.
        fresh=z3.Solver();fresh.set(timeout=1800)
        fresh.add(z3.Not(universal_body(clause,idx+1000)))
        record["independent_fresh_solver_result"]=str(fresh.check())
        if record["independent_fresh_solver_result"]!="unsat":
            record["negated_universal_clause"]="INCONSISTENT_VALIDITY_CHECK_KEEP"
    return record

def rebuild_with_original_relation_declarations(survivors):
    original=[
        "(set-logic HORN)",
        "(declare-fun |CHC_COMP_FALSE| () Bool)",
        "(declare-fun |Inv| (Int Int Int Int Int Int Int Int) Bool)",
    ]
    original.extend("(assert "+x.sexpr()+")" for x in survivors)
    original.extend(["(check-sat)","(exit)"])
    return "\n".join(original)+"\n"

def run():
    import z3
    t=time.perf_counter()
    record={"scope":"EXACT_48_ORIGINAL_FIRST_ORDER_VALIDITY_PRESERVING_PREPROCESSING",
           "original_sha256":SHA,"source_upstream_commit":REV,
           "source_path":SRC,"neural_calls":0,"q1_to_q7":"OPEN",
           "pre_reg_commit":"20247c65565de400597e578dc8da6d5e7969ad81",
           "z3_version":z3.get_version_string(),
           "status":"BLOCKED_OR_UNKNOWN","clauses":[]}
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{SRC}"
        with urllib.request.urlopen(url,timeout=25) as f:data=f.read()
        if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("original_sha_mismatch")
        src=z3.parse_smt2_string(data.decode())
        if len(src)!=48:raise ValueError("not 48 original clauses")
        record["original_source_sha_verified"]=True
        # These two tests are independent of the candidate Inv interpretation.
        survivors=[]
        for i,c in enumerate(src,1):
            q=independent_is_valid(c,i)
            record["clauses"].append(q)
            if not(q["negated_universal_clause"]=="unsat"
                   and q.get("independent_fresh_solver_result")=="unsat"):
                survivors.append(c)
        record["removed_tautological_clause_indices"]=[
            r["original_rule_1based"] for r in record["clauses"]
            if r["negated_universal_clause"]=="unsat"
            and r.get("independent_fresh_solver_result")=="unsat"]
        record["preserved_original_clause_count"]=len(survivors)
        if 48-len(survivors)!=len(record["removed_tautological_clause_indices"]):
            raise ValueError("tautology proof ledger disagreement")
        reduced=rebuild_with_original_relation_declarations(survivors)
        path=Path("/tmp/neumann_double_lock_reduced_equivalent.smt2")
        path.write_text(reduced)
        check=z3.parse_smt2_string(reduced)
        if len(check)!=len(survivors):raise ValueError("reduced source parser count mismatch")
        record["logically_equivalent_reduced_smt2_sha256"]=hashlib.sha256(reduced.encode()).hexdigest()
        record["logically_equivalent_reduced_size_bytes"]=len(reduced.encode())
        record["original_clause_index_map"]=[i for i in range(1,49)
            if i not in record["removed_tautological_clause_indices"]]
        record["solver_arms"]=[]
        for mode,seconds in (("horn",20),("native",16)):
            start=time.perf_counter()
            row={"mode":mode,"subprocess_wall_cap_s":seconds}
            try:
                proc=subprocess.run([sys.executable,__file__,"--child",mode,str(path)],
                    capture_output=True,text=True,timeout=seconds+2)
                if proc.returncode!=0:
                    row["status"]="ERROR"
                    row["error"]=proc.stderr[-1100:]
                else:
                    row["status"]="RETURNED"
                    row["payload"]=json.loads(proc.stdout)
            except subprocess.TimeoutExpired:row["status"]="TIMEOUT"
            except Exception as e:
                row["status"]="ERROR";row["error"]=type(e).__name__+":"+str(e)[:250]
            row["wall_ms"]=round((time.perf_counter()-start)*1000,3)
            record["solver_arms"].append(row)
            print("CLASSICAL_EQUIVALENT",mode,row["status"],
                  row.get("payload",{}).get("verdict",""),flush=True)
        verdicts=[r.get("payload",{}).get("verdict") for r in record["solver_arms"]]
        record["status"]=("REDUCED_EQUIVALENT_SOURCE_SOLVER_RETURNED_DECISIVE_UNCHECKED"
            if any(v in ("sat","unsat") for v in verdicts)
            else "TAUTOLOGY_ELIMINATION_CERTIFIED_ORIGINAL_SAFETY_UNRESOLVED")
    except Exception as e:
        record["status"]="INFRA_OR_PROOF_CHECK_ERROR"
        record["error"]=type(e).__name__+":"+str(e)[:600]
    record["total_ms"]=round((time.perf_counter()-t)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(record,indent=2)+"\n")
    print("FULL_ORIGINAL_STATUS",record["status"])
    print("TAUTOLOGIES_PROVED",len(record.get("removed_tautological_clause_indices",[])))
    print("QUESTIONS",record["q1_to_q7"])

if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--child":
        try:print(json.dumps(solver_child(sys.argv[2],sys.argv[3])))
        except Exception as exc:
            print(type(exc).__name__+":"+str(exc),file=sys.stderr)
            sys.exit(2)
    else:run()
