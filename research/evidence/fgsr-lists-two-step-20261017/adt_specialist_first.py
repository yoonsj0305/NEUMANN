"""Single preregistered ADT-specialist classical check of already-opened RustHorn source.

If build or solver is unsupported, classify honestly. Do NOT patch source or
rerun with chosen flags: would contaminate the first frozen comparator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import platform
import re
import subprocess
import time
import urllib.request

UPSTREAM="e5a86a1ad252fe1df75e06814769ec1d14540032"
CATALIA="5ee6493e996863c8ec22c42d786822d6af39c7f6"
SOURCE_NAME="lists-4-inc-some2-safe.smt2"
SOURCE_SHA256="a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db"
SOURCE_BLOB="5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9"
PROTOCOL_COMMIT="4b888d9911b5306d4d25b4bf094a1790356462cc"
BUILD_TIMEOUT=480
SOLVE_TIMEOUT=30

def execute(argv, seconds, *, cwd=None):
    start=time.monotonic_ns()
    try:
        cp=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,
                          stdin=subprocess.DEVNULL,timeout=seconds,check=False)
        return {"wall_ms":round((time.monotonic_ns()-start)/1e6,3),
                "status":"EXIT", "returncode":cp.returncode,
                "stdout_tail":cp.stdout[-3500:],
                "stderr_tail":cp.stderr[-4500:]}
    except subprocess.TimeoutExpired as exc:
        return {"wall_ms":round((time.monotonic_ns()-start)/1e6,3),
                "status":"TIMEOUT", "returncode":None,
                "stdout_tail":str(exc.stdout)[-2000:] if exc.stdout else "",
                "stderr_tail":str(exc.stderr)[-2000:] if exc.stderr else ""}

def source():
    url=f"https://raw.githubusercontent.com/chc-comp/rust-horn/{UPSTREAM}/{SOURCE_NAME}"
    with urllib.request.urlopen(url,timeout=30) as response:
        raw=response.read()
    sha=hashlib.sha256(raw).hexdigest()
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    if sha!=SOURCE_SHA256 or blob!=SOURCE_BLOB:
        raise ValueError("PINNED_EXTERNAL_SOURCE_IDENTITY_MISMATCH")
    if raw.count(b"(check-sat)")!=1:
        raise ValueError("ORIGINAL_CHECK_SAT_MISSING")
    return raw

def run(out):
    result={
      "study":"FGSR ADT specialist classical necessity test",
      "protocol_commit":PROTOCOL_COMMIT,
      "original_upstream":UPSTREAM, "original_filename":SOURCE_NAME,
      "source_sha256":SOURCE_SHA256, "source_git_blob":SOURCE_BLOB,
      "catalia_git_commit":CATALIA,
      "build_timeout_seconds":BUILD_TIMEOUT,
      "solver_timeout_seconds":SOLVE_TIMEOUT,
      "started_at_utc":None,
      "platform":platform.platform(),
      "global_q1_q7":"OPEN","model_calls":0,
      "science_status":"BLOCKED_NOT_EXECUTED",
      "original_source_unmodified":False,
      "notes":"One opened original; exact source only. Strong solver report is not independent certificate."
    }
    try:
        original=source()
        result["source_bytes"]=len(original)
        result["original_source_unmodified"]=True
        src=out.with_name("frozen_original_only.smt2")
        src.write_bytes(original)
        # Official Catalia README documents binary name hoice.
        install=["cargo","install","--git","https://github.com/hopv/catalia",
                 "--rev",CATALIA,"--locked","--root",str(out.parent/"catalia")]
        result["cargo_version"]=execute(["cargo","--version"],20)
        result["z3_binary_version"]=execute(["z3","--version"],20)
        if result["cargo_version"]["returncode"]!=0 or result["z3_binary_version"]["returncode"]!=0:
            result["science_status"]="BLOCKED_MISSING_REQUIRED_BUILD_TOOL"
            return result
        result["build"]=execute(install,BUILD_TIMEOUT)
        if result["build"]["status"]!="EXIT" or result["build"]["returncode"]!=0:
            result["science_status"]="BLOCKED_CATALIA_BUILD"
            return result
        binary=out.parent/"catalia"/"bin"/"hoice"
        if not binary.is_file():
            result["science_status"]="BLOCKED_MISSING_BUILT_BINARY"
            return result
        result["binary_sha256"]=hashlib.sha256(binary.read_bytes()).hexdigest()
        command=[str(binary),str(src)]
        result["solver_command"]=command
        solver=execute(command,SOLVE_TIMEOUT)
        result["solver"]=solver
        if solver["status"]=="TIMEOUT":
            result["science_status"]="SPECIALIST_TIMEOUT_NOT_GAP"
        elif solver["returncode"]!=0:
            result["science_status"]="SPECIALIST_ERROR_OR_UNSUPPORTED"
        else:
            reported=re.findall(r"(?m)^\s*(sat|unsat|unknown)\s*$",solver["stdout_tail"])
            result["status_lines"]=reported
            if reported==["sat"] or reported==["unsat"]:
                result["science_status"]="SPECIALIST_SOLVER_REPORTED_DECISION"
                result["solver_answer"]=reported[0]
            elif reported==["unknown"]:
                result["science_status"]="SPECIALIST_UNKNOWN"
            else:
                result["science_status"]="SPECIALIST_UNCLASSIFIED_OUTPUT"
    except Exception as exc:
        result["science_status"]="BLOCKED_EXCEPTION"
        result["exception"]=f"{type(exc).__name__}: {str(exc)[:900]}"
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=pathlib.Path,required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    result=run(args.output)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("ADT_SPECIALIST",result["science_status"])
    print("SOURCE",result["original_source_unmodified"])
    print("BUILT",result.get("build",{}).get("status"))
    print("SOLVER",result.get("solver_answer"))
    print("Q1_Q7",result["global_q1_q7"])

if __name__=="__main__":
    main()
