"""Opened authentic CHC portfolio extension: Eldarica v2.3, one original, one cold attempt.

This tests a specialist capable of interpolant/CEGAR predicate discovery.
Do NOT treat solver timeout as neural proof. Do NOT modify external source.
"""
import hashlib,io,json,os,platform,re,subprocess,sys,tarfile,time,urllib.request,zipfile
from pathlib import Path

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SOURCE_SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
ASSET_TAG="v2.3"
LIMIT_S=60
OUT=Path(os.environ.get("FGSR_RESULT","eldarica_receipt.json"))

def fetch(url,timeout=50):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-Q3-Research/0.1","Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(req,timeout=timeout) as f:return f.read()

def compatible_assets(assets):
    # Exactly one first suitable archive, ranked independent of task content.
    def rank(a):
        name=a["name"].lower()
        if ("linux" in name and ("x86_64" in name or "amd64" in name)):return 0
        if "linux" in name:return 1
        if "assembly" in name and name.endswith(".jar"):return 2
        if name.endswith(".zip"):return 3
        if name.endswith((".tar.gz",".tgz")):return 4
        return 8
    return [x for x in sorted(assets,key=lambda a:(rank(a),a["name"])) if rank(x)<8]

def unpack_payload(name,archive):
    base=Path("/tmp/fgsr_eldarica_release")
    base.mkdir(parents=True,exist_ok=True)
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as z:z.extractall(base)
    elif name.endswith((".tar.gz",".tgz")):
        with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as t:
            # Asset from official tagged GitHub release; still reject traversal paths.
            for m in t.getmembers():
                if Path(m.name).is_absolute() or ".." in Path(m.name).parts:raise ValueError("UNSAFE_RELEASE_ARCHIVE_PATH")
            t.extractall(base,filter="data")
    elif name.endswith(".jar"):
        p=base/name;p.write_bytes(archive)
    else:raise ValueError("UNSUPPORTED_ASSET_FORMAT")
    jars=sorted(base.rglob("*assembly*.jar"))
    elds=[p for p in base.rglob("eld") if p.is_file()]
    if elds:
        exe=elds[0]
        exe.chmod(exe.stat().st_mode | 0o111)
        return [str(exe)],str(exe.parent)
    if jars:return ["java","-jar",str(jars[0])],str(jars[0].parent)
    raise ValueError("ARCHIVE_LACKS_RUNNABLE_ELDARICA")

def main():
    t0=time.perf_counter_ns()
    rec={"study":"FGSR-Q3 first strong specialist CHC predicate synthesizer",
         "source_sha256":SOURCE_SHA,"model_training":False,"neural_calls":0,
         "Q1_Q7":"OPEN","opened_original":True,"external_source_modified":False,
         "solver":"Eldarica","tag":ASSET_TAG,"cap_seconds":LIMIT_S,
         "status":"BLOCKED_INSTALL","category":"LIA nonlinear CHC 8-state concurrency",
         "machine":{"python":sys.version.split()[0],"platform":platform.platform()}}
    try:
        remote=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{SOURCE}"
        data=fetch(remote)
        if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:raise ValueError("ORIGINAL_SHA256_MISMATCH")
        original=Path("/tmp/fgsr_original_eldarica.smt2")
        original.write_bytes(data)
        meta=json.loads(fetch(f"https://api.github.com/repos/uuverifiers/eldarica/releases/tags/{ASSET_TAG}"))
        choices=compatible_assets(meta.get("assets",[]))
        rec["release_tag_id"]=meta.get("tag_name")
        rec["release_assets_seen"]=[{"name":x["name"],"size":x.get("size")} for x in meta.get("assets",[])]
        if not choices:raise ValueError("RELEASE_HAS_NO_SUPPORTED_ASSET")
        asset=choices[0] # do not choose based on task outcome
        rec["asset_name"]=asset["name"]
        rec["asset_url"]=asset.get("browser_download_url")
        blob=fetch(asset["browser_download_url"],timeout=120)
        rec["asset_sha256"]=hashlib.sha256(blob).hexdigest()
        rec["asset_bytes"]=len(blob)
        command,cwd=unpack_payload(asset["name"],blob)
        rec["solver_command"]=command[:2]
        start=time.perf_counter_ns()
        try:
            proc=subprocess.run(command+[str(original)],cwd=cwd,text=True,capture_output=True,
                                stdin=subprocess.DEVNULL,timeout=LIMIT_S,check=False)
            rec["solver_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
            stdout=proc.stdout[:2800];stderr=proc.stderr[:1100]
            rec["stdout_prefix"]=stdout
            rec["stderr_prefix"]=stderr
            rec["returncode"]=proc.returncode
            found=[x.strip() for x in stdout.splitlines() if x.strip() in ("sat","unsat","unknown")]
            rec["status"]=(
                "DECIDED_"+found[-1].upper() if len(found)==1 and found[0]!="unknown" and proc.returncode==0
                else "UNKNOWN" if found==["unknown"] and proc.returncode==0
                else "ERROR"
            )
        except subprocess.TimeoutExpired as exc:
            rec["solver_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
            rec["status"]="TIMEOUT"
            rec["stdout_prefix"]=str(exc.stdout)[:1000]
    except Exception as exc:
        rec["status"]="BLOCKED_INSTALL_OR_RUNTIME"
        rec["error"]=type(exc).__name__+": "+str(exc)[:950]
    rec["total_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n")
    print("ELDARICA_SCIENTIFIC",rec["status"])
    print("ELDARICA_RUN_MS",rec.get("solver_wall_ms"))
    print("GLOBAL_Q1_Q7",rec["Q1_Q7"])

if __name__=="__main__":main()
