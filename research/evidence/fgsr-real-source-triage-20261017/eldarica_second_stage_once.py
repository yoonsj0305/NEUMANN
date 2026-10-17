"""Frozen second-stage specialist classical screen; *not* a learned result.
Preregistered before Eldarica use: a2ec0ba4e4506da5b2e67dc675ce1130cf3578bb
"""
from __future__ import annotations
import hashlib, importlib.util, json, pathlib, platform, subprocess, sys, time

HERE=pathlib.Path(__file__).resolve().parent
EXISTING=HERE.parent/"fgsr-q3-single-independent-family"/"eldarica_once.py"
ORIGINAL_REV="e5a86a1ad252fe1df75e06814769ec1d14540032"
TAG="v2.3"
LIMIT_S=30
PREREG="a2ec0ba4e4506da5b2e67dc675ce1130cf3578bb"
CASES=(
 ("lists-4-inc-some2-safe.smt2","a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db","5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9"),
 ("prusti-3-pass-paper_examples-points-compress.smt2","4221e1ba907a2055d6a61e2b3ae6eecadca307716d651dd11414576fc2a45c20","21f2938c47d8c3bcdacc99fae09d6ffb671a9a75"),
)

def load_existing():
    spec=importlib.util.spec_from_file_location("neumann_existing_eldarica", EXISTING)
    if spec is None or spec.loader is None:raise RuntimeError("Missing existing Eldarica tool")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def source_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def run():
    m=load_existing()
    result={
        "study":"FGSR specialist classical second-stage bounded screen",
        "preregistered_commit":PREREG,
        "upstream":"chc-comp/rust-horn",
        "revision":ORIGINAL_REV,
        "solver":"Eldarica",
        "solver_tag":TAG,
        "solver_cap_seconds_per_original":LIMIT_S,
        "sources_now_opened":True,
        "model_calls":0, "gpu_calls":0,
        "Q1_Q7":"OPEN",
        "outcome":"INCOMPLETE",
        "machine":{"python":sys.version.split()[0],"platform":platform.platform()},
        "original_first_Z3_results":["TIMEOUT_OR_ERROR","TIMEOUT_OR_ERROR"],
        "records":[]
    }
    # Freeze the release selection policy independent of the benchmark answers.
    try:
        meta=json.loads(m.fetch(f"https://api.github.com/repos/uuverifiers/eldarica/releases/tags/{TAG}"))
        choices=m.compatible_assets(meta.get("assets",[]))
        if not choices:raise ValueError("NO_SUITABLE_RELEASE_ASSET")
        asset=choices[0]
        content=m.fetch(asset["browser_download_url"],timeout=120)
        result["solver_binary_sha256"]=hashlib.sha256(content).hexdigest()
        result["solver_binary_bytes"]=len(content)
        result["solver_asset_name"]=asset["name"]
        command,cwd=m.unpack_payload(asset["name"],content)
        result["solver_command_prefix"]=command[:2]
    except Exception as e:
        result["outcome"]="BLOCKED_SOLVER_INSTALL"
        result["error"]=f"{type(e).__name__}: {str(e)[:350]}"
        return result
    for idx,(name,sha,blob) in enumerate(CASES):
        start=time.monotonic_ns()
        rec={"source":name,"pinned_sha256":sha,"pinned_git_blob_sha1":blob,
             "original_unchanged":False,"status":"NOT_RUN","solver_verdict":None}
        try:
            url=f"https://raw.githubusercontent.com/chc-comp/rust-horn/{ORIGINAL_REV}/{name}"
            raw=m.fetch(url)
            if hashlib.sha256(raw).hexdigest()!=sha or source_blob(raw)!=blob:
                raise ValueError("PINNED_SOURCE_HASH_MISMATCH")
            rec["original_unchanged"]=True
            path=pathlib.Path(f"/tmp/fgsr_real_chc_case_{idx}.smt2")
            path.write_bytes(raw)
            start_solver=time.monotonic_ns()
            try:
                cp=subprocess.run(command+[str(path)],cwd=cwd,text=True,capture_output=True,
                                  stdin=subprocess.DEVNULL,timeout=LIMIT_S,check=False)
                rec["solver_wall_ms"]=round((time.monotonic_ns()-start_solver)/1e6,3)
                rec["returncode"]=cp.returncode
                rec["stdout_prefix"]=cp.stdout[:1600]
                rec["stderr_prefix"]=cp.stderr[:600]
                verdicts=[line.strip() for line in cp.stdout.splitlines()
                          if line.strip() in ("sat","unsat","unknown")]
                rec["solver_verdict"]=verdicts[-1] if len(verdicts)==1 else None
                rec["status"]=("DECIDED" if cp.returncode==0 and len(verdicts)==1
                                and verdicts[0] in ("sat","unsat")
                               else "UNKNOWN" if cp.returncode==0 and verdicts==["unknown"]
                               else "ERROR")
            except subprocess.TimeoutExpired as e:
                rec["solver_wall_ms"]=round((time.monotonic_ns()-start_solver)/1e6,3)
                rec["status"]="TIMEOUT"
                rec["stderr_prefix"]=str(e.stderr)[:600]
        except Exception as e:
            rec["status"]="BLOCKED_SOURCE_OR_RUNTIME"
            rec["error"]=f"{type(e).__name__}: {str(e)[:350]}"
        rec["whole_original_wall_ms"]=round((time.monotonic_ns()-start)/1e6,3)
        result["records"].append(rec)
    statuses=[x["status"] for x in result["records"]]
    if any(x.startswith("BLOCKED") or x=="ERROR" for x in statuses):
        result["outcome"]="ABSTAIN_BLOCKED"
    elif any(x=="DECIDED" for x in statuses):
        result["outcome"]="CLASSICAL_SPECIALIST_DECIDES_AT_LEAST_ONE"
    elif len(statuses)==2 and all(x in ("TIMEOUT","UNKNOWN") for x in statuses):
        result["outcome"]="CLASSICAL_HEADROOM_CANDIDATE_ONLY"
    else:
        result["outcome"]="ABSTAIN"
    result["interpretation"]=(
        "This is not strongest-classical impossibility, a learned result, "
        "or a frontier recovery. An initial Z3 timeout and an Eldarica timeout "
        "do not prove a model is needed. The sources are opened development cases."
    )
    return result

if __name__=="__main__":
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True,type=pathlib.Path)
    args=a.parse_args()
    receipt=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({k:v for k,v in receipt.items() if k!="records"},indent=2))
    print("ORIGINALS",[(r["source"],r["status"],r["solver_verdict"],r.get("solver_wall_ms")) for r in receipt["records"]])
    if receipt["outcome"] in ("INCOMPLETE","BLOCKED_SOLVER_INSTALL","ABSTAIN_BLOCKED"):
        raise SystemExit(2)
