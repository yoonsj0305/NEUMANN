"""Frozen first P1.10 opened-development Kaggle bootstrap."""
from __future__ import annotations
import argparse, hashlib, json, math, os, signal, subprocess, sys, time, zipfile
from pathlib import Path

RUNTIME_HEAD=os.environ.get("NEUMANN_P110_FROZEN_HEAD","")
REPOSITORY_URL="https://github.com/yoonsj0305/NEUMANN.git"
SETUP="neumann_p110_first_setup.json"; OUTPUT="neumann_p110_first"; CHECKOUT="NEUMANN_P110_FROZEN"
ARCHIVE="NEUMANN_P110_FIRST_EVIDENCE.zip"; HASH_RECEIPT="NEUMANN_P110_FIRST_EVIDENCE.sha256.json"
LOG="neumann_p110_bootstrap.log"; REPLAY="neumann_p110_replay_stdout.txt"; CONSTRAINTS="neumann_p110_runtime_constraints.txt"
PREFLIGHT='''import json
from importlib.metadata import version
import torch
assert version("torch") == "2.11.0+cu128"
assert version("torchvision") == "0.26.0+cu128"
assert torch.cuda.is_available()
assert torch.cuda.get_device_name(0) == "Tesla T4"
print(json.dumps({"torch":version("torch"),"torchvision":version("torchvision"),"device":torch.cuda.get_device_name(0)},sort_keys=True))
'''

def write_json(path,value,exclusive=False):
    with Path(path).open("x" if exclusive else "w",encoding="utf-8") as f: json.dump(value,f,sort_keys=True,indent=2,allow_nan=False); f.write("\n")
def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def command(args,*,cwd,log,timeout,on_started):
    with log.open("ab") as stream:
        p=subprocess.Popen(args,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try:on_started(p.pid); return p.wait(timeout=timeout)
        except BaseException:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait(); raise
def package(working):
    working=Path(working); archive=working/ARCHIVE; receipt=working/HASH_RECEIPT
    if archive.exists() or receipt.exists(): raise RuntimeError("original P1.10 archive exists; preserve it")
    started=time.perf_counter(); paths=[working/n for n in (SETUP,LOG,REPLAY,CONSTRAINTS)]
    output=working/OUTPUT
    if output.is_dir(): paths.extend(sorted(output.rglob("*")))
    members={}
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            if p.is_symlink(): raise ValueError("symlink evidence forbidden")
            if not p.is_file(): continue
            name=p.relative_to(working).as_posix(); raw=p.read_bytes(); z.writestr(name,raw)
            members[name]={"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        raw=Path(__file__).read_bytes(); name="bootstrap/control_plane_p110_kaggle.py"; z.writestr(name,raw)
        members[name]={"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
        z.writestr("archive_manifest.json",json.dumps({"schema":"neumann.control-plane-p110-archive.v1","members":members,
          "runtime_head":RUNTIME_HEAD,"development_only":True,"p19_opened_task_score_reuse":False,
          "p2_registration_admitted":False,"p2_admitted":False,"decision3_admitted":False,"no_replacement":True},sort_keys=True,indent=2)+"\n")
    result={"archive":ARCHIVE,"archive_sha256":digest_file(archive),"archive_bytes":archive.stat().st_size,
            "packaging_ms":(time.perf_counter()-started)*1000,"no_replacement":True,"development_only":True}
    write_json(receipt,result,exclusive=True); print(json.dumps(result,sort_keys=True),flush=True); return result
def package_existing(working):
    working=Path(working); data=json.loads((working/SETUP).read_bytes())
    if data.get("runtime_head")!=RUNTIME_HEAD or data.get("development_only") is not True: raise ValueError("original P1.10 setup identity required")
    if data.get("bootstrap_sha256")!=digest_file(__file__): raise ValueError("exact original bootstrap required")
    pid=data.get("active_child_pid")
    if pid is not None:
        try:os.kill(pid,0)
        except ProcessLookupError:pass
        else:raise RuntimeError("child still exists")
    return package(working)
def run(working=Path("/kaggle/working"),execute=command,*,launcher_wall_ms=None):
    if len(RUNTIME_HEAD)!=40 or any(c not in "0123456789abcdef" for c in RUNTIME_HEAD): raise ValueError("exact P1.10 source head required")
    working=Path(working)
    if not working.is_dir(): raise RuntimeError("Kaggle working directory required")
    names=(SETUP,OUTPUT,CHECKOUT,ARCHIVE,HASH_RECEIPT,LOG,REPLAY,CONSTRAINTS)
    if any((working/n).exists() for n in names): raise RuntimeError("P1.10 first attempt already started")
    if launcher_wall_ms is not None and (not math.isfinite(launcher_wall_ms) or launcher_wall_ms<0): raise ValueError("finite launcher timing required")
    started=time.perf_counter()
    data={"schema":"neumann.control-plane-p110-setup.v1","runtime_head":RUNTIME_HEAD,"bootstrap_sha256":digest_file(__file__),
          "status":"STARTED","stages":[],"launcher_wall_ms":launcher_wall_ms,"development_only":True,"favorable_rerun":False,
          "p19_opened_task_score_reuse":False,"p2_registration_admitted":False,"p2_admitted":False,"decision3_admitted":False,"active_child_pid":None}
    write_json(working/SETUP,data,exclusive=True); checkout=working/CHECKOUT
    def stage(name,args,timeout,cwd=working,required=True,log=None):
        rec={"name":name,"status":"STARTED"}; data["stages"].append(rec); write_json(working/SETUP,data); print("P1.10:",name,flush=True); began=time.perf_counter()
        def on_started(pid):data["active_child_pid"]=pid; write_json(working/SETUP,data)
        try:
            code=execute(args,cwd=cwd,log=log or working/LOG,timeout=timeout,on_started=on_started)
            rec.update(exit_code=code,status="COMPLETE" if code==0 else "NONZERO")
            if required and code!=0: raise RuntimeError(name+" failed")
            return code
        except BaseException as exc: rec.update(status="FAILED_OR_INTERRUPTED",error=type(exc).__name__); raise
        finally:data["active_child_pid"]=None; rec["wall_ms"]=(time.perf_counter()-began)*1000; write_json(working/SETUP,data)
    try:
        stage("CUDA runtime preflight",[sys.executable,"-c",PREFLIGHT],60)
        stage("clone",["git","clone","--no-checkout",REPOSITORY_URL,str(checkout)],180)
        stage("frozen checkout",["git","checkout","--detach",RUNTIME_HEAD],60,checkout)
        (working/CONSTRAINTS).write_text("torch==2.11.0+cu128\ntorchvision==0.26.0+cu128\ntransformers==5.16.1\n",encoding="utf-8")
        stage("dependencies",[sys.executable,"-m","pip","install","--disable-pip-version-check","-c",str(working/CONSTRAINTS),
              "transformers==5.16.1","huggingface_hub","pillow","numpy>=1.26","scipy>=1.11","scikit-learn>=1.4"],600)
        stage("post-install CUDA preflight",[sys.executable,"-c",PREFLIGHT],60)
        stage("package inventory",[sys.executable,"-m","pip","list","--format=json"],60)
        stage("frozen registration",[sys.executable,"-m","experiments.control_plane_p110_registration"],60,checkout)
        runner=stage("first minimal-pairwise semantic development run",[sys.executable,"-u","-m","experiments.control_plane_p110_dev",
                     "--directory",str(working/OUTPUT),"--frozen-head",RUNTIME_HEAD],1800,checkout,required=False)
        data["runner_exit_code"]=runner
        if not (working/OUTPUT/"terminal.json").is_file(): raise RuntimeError("P1.10 runner has no terminal receipt")
        replay=stage("model-free receipt replay",[sys.executable,"-m","experiments.control_plane_p110_replay","--directory",str(working/OUTPUT)],
                     120,checkout,required=False,log=working/REPLAY)
        data["replay_exit_code"]=replay
        if replay!=0: raise RuntimeError("P1.10 receipt replay failed")
        report=json.loads((working/OUTPUT/"report.json").read_bytes()); decision=report["decision"]
        if (report.get("development_only") is not True or report.get("p19_opened_task_score_reuse") is not False
            or decision.get("p2_registration_admitted") is not False or decision.get("p2_admitted") is not False
            or decision.get("decision3_admitted") is not False or runner not in (0,2)
            or (runner==0)!=(decision["verdict"]=="PASS")): raise ValueError("P1.10 exit/decision boundary drift")
        data["development_verdict"]=decision["verdict"]; data["status"]="FINISHED" if runner==0 else "FINISHED_NONPASS"
    except BaseException as exc:data.update(status="FAILED_OR_INTERRUPTED",error=type(exc).__name__+": "+str(exc)); print(data["error"],flush=True)
    finally:
        data["setup_and_runner_wall_ms"]=(time.perf_counter()-started)*1000
        data["launcher_setup_and_runner_wall_ms"]=None if launcher_wall_ms is None else launcher_wall_ms+data["setup_and_runner_wall_ms"]
        write_json(working/SETUP,data); result=package(working); print("Download from the Kaggle Output panel:",ARCHIVE,flush=True)
    return data,result
def display_archive(working):
    try:
        from IPython.display import HTML,display
        if (Path(working)/ARCHIVE).is_file(): display(HTML('<a href="/files/'+ARCHIVE+'" download>'+ARCHIVE+'</a>'))
    except ImportError:pass
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--package-existing",action="store_true"); a=p.parse_args()
    if a.package_existing:package_existing(Path("/kaggle/working"))
    else:
        data,_=run(); display_archive(Path("/kaggle/working")); raise SystemExit(0 if data["status"]=="FINISHED" else 2)
