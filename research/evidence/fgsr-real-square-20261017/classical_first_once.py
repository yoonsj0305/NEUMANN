"""One preregistered true external original CHC classical headroom screen.

Never edit the public original. No model calls and no post-selection of source.
A checked SAT/UNSAT is a Z3 native original verdict, NOT a reusable proof object.
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
FILE="eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2"
LIMIT=15
OUT=Path(os.getenv("FGSR_RESULT","actual_square_original_classical.json"))

def original_native(p):
    import z3
    lib=C.CDLL(str(Path(z3.__file__).parent/"lib/libz3.so"))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p];lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p];lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    cfg=lib.Z3_mk_config()
    ctx=lib.Z3_mk_context(cfg)
    lib.Z3_del_config(cfg)
    try:
        data=p.read_bytes()
        result=lib.Z3_eval_smtlib2_string(ctx,data)
        print((result or b"").decode(errors="replace").strip())
    finally:
        lib.Z3_del_context(ctx)

def main():
    started=time.perf_counter_ns()
    report={
        "study":"NEUMANN Q3 real external llreve quadratic transfer classical-first",
        "preregistered":"research/evidence/fgsr-real-square-20261017/PREREG_BEFORE_SOURCE.md",
        "source_repo":"chc-comp/chc-comp26-benchmarks",
        "source_commit":REV,"source_path":FILE,"model_calls":0,
        "q1_q7":"OPEN","original_modified":False,
        "cap_s":LIMIT,"status":"BLOCKED",
    }
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{FILE}"
        with urllib.request.urlopen(url,timeout=25) as f:data=f.read()
        report["original_sha256"]=hashlib.sha256(data).hexdigest()
        report["original_bytes"]=len(data)
        report["assertions_count"]=data.count(b"(assert")
        report["z3_version"]=__import__("z3").get_version_string()
        p=Path("/tmp/neumann_real_square_original.smt2")
        p.write_bytes(data)
        start=time.perf_counter_ns()
        try:
            done=subprocess.run([sys.executable,__file__,"--native",str(p)],timeout=LIMIT,
                 check=False,capture_output=True,text=True)
            report["stdout"]=done.stdout.strip()[:1000]
            report["stderr"]=done.stderr.strip()[:1000]
            report["exit_code"]=done.returncode
            ans=report["stdout"]
            report["status"]=(
                "ORIGINAL_CLASSICAL_SOLVED_"+ans.upper()
                if ans in ("sat","unsat") and done.returncode==0 else
                "ORIGINAL_CLASSICAL_UNKNOWN"
                if ans=="unknown" and done.returncode==0 else "CLASSICAL_RUNTIME_ERROR"
            )
        except subprocess.TimeoutExpired:
            report["status"]="CLASSICAL_TIMEOUT"
        report["z3_original_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    except Exception as exc:
        report["status"]="SOURCE_OR_RUNTIME_BLOCKED"
        report["error"]=type(exc).__name__+": "+str(exc)[:850]
    report["complete_wall_ms"]=round((time.perf_counter_ns()-started)/1e6,3)
    report["learned_head_domain_test"]="NOT_ENTERED_CLASSICAL_FIRST" if report["status"].startswith("ORIGINAL_CLASSICAL_SOLVED") else "REQUIRES_FROZEN_AST_DOMAIN_CHECK_NO_MODEL_CALL"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("EXTERNAL_SQUARE_ORIGINAL",report["status"])
    print("ORIGINAL_SHA",report.get("original_sha256"))
    print("NO_Q_PROMOTION",report["q1_q7"])

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--native":
        original_native(Path(sys.argv[2]))
    else:
        main()
