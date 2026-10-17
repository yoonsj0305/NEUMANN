"""CHC-COMP exact original 48 Horn strong classical status FIRST preregistered run.

Do NOT equate heuristic success or bounded trace absence with proof of global
SAT/UNSAT. All four arms use original unchanged SMT bytes and independent process.
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

UPSTREAM="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
PATH="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
SPECS=[("spacer",16),("original_native",12),("bmc",8),("horn_solver",12)]
OUT=Path(os.environ.get("FGSR_RESULT","double_lock_original_one_shot_receipt.json"))

def native_check(source):
    import z3
    so=Path(z3.__file__).parent/"lib/libz3.so"
    lib=C.CDLL(str(so))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p]
    lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p]
    lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    config=lib.Z3_mk_config()
    ctx=lib.Z3_mk_context(config)
    lib.Z3_del_config(config)
    try:
        return (lib.Z3_eval_smtlib2_string(ctx,source) or b"").decode(errors="replace").strip()
    finally:
        lib.Z3_del_context(ctx)

def fixedpoint(source,engine,limit_ms):
    import z3
    context=z3.Fixedpoint()
    context.set(engine=engine,timeout=limit_ms)
    # Full unchanged original declarations and exact assertions are added by the parser.
    parsed=z3.parse_smt2_string(source)
    if len(parsed)!=48:
        raise ValueError(f"not 48 source assertions ({len(parsed)})")
    if any(not z3.is_quantifier(x) for x in parsed):
        raise ValueError("original unsupported quantified rule")
    named_false=z3.Bool("CHC_COMP_FALSE")
    # Original clause 48 is exactly (CHC_COMP_FALSE => false), equivalent
    # to querying CHC_COMP_FALSE for reachability. Independently prove this
    # normalization and register each of the preceding 47 rules unchanged.
    qc=z3.Solver()
    qc.add(z3.Xor(parsed[-1],z3.Not(named_false)))
    if qc.check()!=z3.unsat:
        raise ValueError("original last rule not equivalent to query false")
    inv_decl=z3.Function("Inv",*([z3.IntSort()]*8),z3.BoolSort())
    context.register_relation(inv_decl,named_false.decl())
    for original in parsed[:-1]:
        context.add_rule(original)
    rule_count=len(context.get_rules())
    if rule_count!=47:
        raise ValueError(f"expected 47 original rules plus exact final false query, got {rule_count}")
    result=str(context.query(named_false))
    extra={"original_rule_count":rule_count,"fixedpoint_query":result}
    try:
        extra["solver_reason_unknown"]=context.reason_unknown() if result=="unknown" else None
    except Exception:pass
    if result in ("sat","unsat"):
        try:
            ans=context.get_answer()
            rendered=ans.sexpr()
            extra["solver_answer_sha256"]=hashlib.sha256(rendered.encode()).hexdigest()
            extra["solver_answer_size"]=len(rendered)
            extra["solver_answer_head"]=rendered[:1200]
        except Exception as exc:
            extra["solver_answer_error"]=type(exc).__name__+":"+str(exc)[:300]
    return extra

def horn_solver(source,limit_ms):
    import z3
    solver=z3.SolverFor("HORN")
    solver.set(timeout=limit_ms)
    solver.from_string(source)
    result=str(solver.check())
    info={"result":result}
    if result=="unknown":info["reason"]=solver.reason_unknown()
    if result=="sat":
        try:
            model=solver.model()
            m=str(model)
            info["model_chars"]=len(m)
            info["model_sha256"]=hashlib.sha256(m.encode()).hexdigest()
        except Exception as exc:
            info["model_error"]=str(exc)[:100]
    return info

def child(mode,src):
    import z3
    path=Path(src)
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError("pinned original source SHA mismatch")
    if mode=="original_native":
        ans=native_check(raw)
        return {"result":ans}
    if mode in ("spacer","bmc"):
        return fixedpoint(raw.decode(),mode,{"spacer":16000,"bmc":8000}[mode])
    if mode=="horn_solver":
        return horn_solver(raw.decode(),12000)
    raise ValueError("unexpected mode")

def main():
    started=time.perf_counter()
    import z3
    out={"experiment":"Authentic full 48-original Horn unbounded status disambiguation",
         "pre_registration":"research/evidence/fgsr-double-lock-original-20261017/PREREG_ONE_SHOT_STRONGER_ORIGINAL_STATUS.md",
         "source_upstream_sha":UPSTREAM,
         "source_path":PATH,"expected_source_sha256":SHA,
         "z3_version":z3.get_version_string(),
         "learned_model_calls":0,"full_original_modified":False,
         "global_q1_q7":"OPEN","arms":[]}
    try:
        link=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{UPSTREAM}/{PATH}"
        with urllib.request.urlopen(link,timeout=25) as f:data=f.read()
        if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("wrong upstream source")
        if data.count(b"(assert")!=48:raise ValueError("not 48 original Horn rules")
        out["pinned_original_verified"]=True
        out["original_bytes"]=len(data)
        path=Path("/tmp/neumann_double_lock_48_exact_original.smt2")
        path.write_bytes(data)
        for name,lim in SPECS:
            t=time.perf_counter()
            x={"solver_arm":name,"subprocess_cap_s":lim}
            try:
                done=subprocess.run([sys.executable,__file__,"--child",name,str(path)],
                    check=False,text=True,capture_output=True,timeout=lim+2)
                if done.returncode==0:
                    try:
                        payload=json.loads(done.stdout)
                        x["status"]="SOLVER_RETURNED"
                        x["payload"]=payload
                    except json.JSONDecodeError:
                        x["status"]="TOOL_OUTPUT_UNPARSEABLE"
                        x["stdout_head"]=done.stdout[:200]
                else:
                    x["status"]="SOLVER_ERROR"
                    x["error"]=done.stderr[-1800:]
            except subprocess.TimeoutExpired:
                x["status"]="TIMEOUT"
            x["wall_ms"]=round((time.perf_counter()-t)*1000,3)
            out["arms"].append(x)
            print(name,x["status"],x.get("payload",{}).get("result",x.get("payload",{}).get("fixedpoint_query","")),flush=True)
        answers=[
            arm["payload"].get("result",arm["payload"].get("fixedpoint_query"))
            for arm in out["arms"] if arm["status"]=="SOLVER_RETURNED"]
        out["strong_original_classical_status"]=(
            "RAW_SOLVER_SAT_OR_UNSAT_NEEDS_CERTIFICATE"
            if any(x in ("sat","unsat") for x in answers)
            else "UNRESOLVED_UNBOUNDED_ORIGINAL")
    except Exception as e:
        out["strong_original_classical_status"]="INFRA_BLOCKED"
        out["error"]=type(e).__name__+":"+str(e)[:300]
    out["elapsed_ms"]=round((time.perf_counter()-started)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2)+"\n")
    print("FINAL",out["strong_original_classical_status"])
    print("Q1_Q7",out["global_q1_q7"])
    return out

if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--child":
        try:
            value=child(sys.argv[2],sys.argv[3])
            print(json.dumps(value))
        except Exception as e:
            print(type(e).__name__+":"+str(e),file=sys.stderr)
            sys.exit(2)
    else:
        main()
