"""One independent stronger cold Z3 4.13.3 baseline on a previously OPENED, pinned source.
No solver tactics or source modifications selected by observed task content.
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

REPO="chc-comp/chc-comp26-benchmarks"
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
PATH="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
DIGEST="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
BLOB="9c6f22f32de6c32dce69394e38c7a1cf2368e65c"
OUT=Path(os.environ.get("FGSR_RESULT","modern_z3_receipt.json"))

def new_lib():
    import z3
    root=Path(z3.__file__).parent
    paths=list(root.glob("lib/libz3.so*"))
    if not paths:raise FileNotFoundError(f"Z3 shared object absent in wheel: {root}")
    return C.CDLL(str(paths[0])),z3.get_version_string()

def evaluate(text):
    lib,version=new_lib()
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p]
    lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p]
    lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    lib.Z3_get_error_code.argtypes=[C.c_void_p]
    lib.Z3_get_error_code.restype=C.c_int
    HANDLER=C.CFUNCTYPE(None,C.c_void_p,C.c_int)
    handler=HANDLER(lambda ctx,code:None)
    lib.Z3_set_error_handler.argtypes=[C.c_void_p,HANDLER]
    config=lib.Z3_mk_config()
    context=lib.Z3_mk_context(config)
    lib.Z3_del_config(config)
    lib.Z3_set_error_handler(context,handler)
    try:
        raw=lib.Z3_eval_smtlib2_string(context,text)
        answer=(raw or b"").decode("utf8",errors="replace").strip()
        error=lib.Z3_get_error_code(context)
    finally:
        lib.Z3_del_context(context)
    return answer,error,version

def main():
    start=time.perf_counter_ns()
    receipt={"study":"FGSR-Q3 next strongest classical after prereg original screen",
        "original_sha256":DIGEST,"original_git_blob":BLOB,
        "source_revision":REV, "model_calls":0,"Q1_Q7":"OPEN",
        "original_modified":False,"run_type":"opened further classical audit",
        "cap_seconds":20,"status":"BLOCKED"}
    try:
        url=f"https://raw.githubusercontent.com/{REPO}/{REV}/{PATH}"
        raw=urllib.request.urlopen(url,timeout=30).read()
        actual=hashlib.sha256(raw).hexdigest()
        blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if actual!=DIGEST or blob!=BLOB:raise ValueError("SOURCE_HASH_MISMATCH")
        p=Path("/tmp/fgsr_external_modern_original.smt2")
        p.write_bytes(raw)
        child=subprocess.run([sys.executable,__file__,"--native",str(p)],
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                            text=True,timeout=20,check=False)
        answer=child.stdout.strip()
        receipt["raw_response"]=answer[:2000]
        receipt["stderr"]=child.stderr[:1000]
        receipt["exit_code"]=child.returncode
        receipt["status"]= (
            "SAT" if answer=="sat" and child.returncode==0 else
            "UNSAT" if answer=="unsat" and child.returncode==0 else
            "UNKNOWN" if answer=="unknown" and child.returncode==0 else
            "ERROR"
        )
    except subprocess.TimeoutExpired:
        receipt["status"]="TIMEOUT"
    except Exception as exc:
        receipt["status"]="BLOCKED"
        receipt["error"]=type(exc).__name__+": "+str(exc)[:800]
    receipt["wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2)+"\n")
    print("MODERN_Z3_ACTUAL",receipt["status"],receipt["wall_ms"],"ms")

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--native":
        from pathlib import Path
        original=Path(sys.argv[2]).read_bytes()
        answer,error,version=evaluate(original)
        if error:raise RuntimeError(f"Z3_PARSE_ERROR {error} {answer[:200]}")
        print(answer)
    else:
        main()
