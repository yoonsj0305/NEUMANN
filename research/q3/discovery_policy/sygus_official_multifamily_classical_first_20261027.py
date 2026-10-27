#!/usr/bin/env python3
"""FIRST external official multi-family SyGuS CVC5 headroom only.

Original source files stay pinned by exact Git SHA and immutable filename-only
selection before content is read. A solver stdout containing define-fun is NOT
an independently verified correct solution. All 16 programs are reported.
"""
import collections, hashlib, json, pathlib, re, resource, subprocess, time

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
NAMES_SHA="9cdc403f8515900c72605d674dd96a7cacb57af1355153e93a7df4b66968584e"
PREFIX="neumann1-official-headroom-v1/"
FAMILIES=[
  "lib/General_Track/bv-conditional-inverses/",
  "lib/General_Track/cegist-cav18/",
  "lib/PBE_SLIA_Track/euphony/",
  "lib/Inv_Track/xujie_code2inv/",
]
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_c16_first")

def hash_data(value):
    return hashlib.sha256(value).hexdigest()

def selected_paths():
    names=subprocess.check_output(["git","-C",str(ROOT),"ls-tree","-r","--name-only","HEAD"],text=True).splitlines()
    files=sorted(p for p in names if p.endswith((".sl",".sl2",".sy",".sl3")))
    # exactly the immutable prior filename inventory JSON artifact's schema
    sample={}
    for group in FAMILIES:
        candidates=[p for p in files if p.startswith(group)]
        if len(candidates)<4:raise RuntimeError("INSUFFICIENT_FAMILY"+group)
        candidates.sort(key=lambda p:(hash_data((PREFIX+p).encode()),p))
        sample[group]=candidates[:4]
    return sample

def run_solver(filename):
    def cap():
        resource.setrlimit(resource.RLIMIT_CPU,(12,13))
    start=time.monotonic()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    p=subprocess.Popen(["cvc5","--lang=sygus2",str(filename)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
        errors="replace",preexec_fn=cap)
    rss=0;forced=None
    while p.poll() is None:
        try:
            data=pathlib.Path(f"/proc/{p.pid}/status").read_text(errors="replace")
            m=re.search(r"^VmRSS:\s+(\d+)\s+kB",data,re.M)
            if m:
                rss=max(rss,int(m.group(1)))
                if rss>800*1024:
                    forced="RSS_CAP";p.kill()
        except (ProcessLookupError,FileNotFoundError):pass
        if time.monotonic()-start>15:
            forced="WALL_CAP";p.kill()
        time.sleep(.015)
    stdout,stderr=p.communicate(timeout=2)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    cost={
        "returncode":p.returncode,"forced":forced,
        "wall_seconds":round(time.monotonic()-start,6),
        "cpu_user_seconds":round(after.ru_utime-before.ru_utime,6),
        "cpu_system_seconds":round(after.ru_stime-before.ru_stime,6),
        "sampled_max_rss_kib":rss or None,
        "stdout_sha256":hash_data(stdout.encode()),
        "stderr_sha256":hash_data(stderr.encode()),
        "stdout_bytes":len(stdout.encode()),
        "stderr_bytes":len(stderr.encode()),
    }
    return stdout,stderr,cost

def main():
    head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    assert head==PIN,(head,PIN)
    ver=subprocess.check_output(["cvc5","--version"],text=True,stderr=subprocess.STDOUT).strip()
    selection=selected_paths()
    assert len(selection)==4 and sum(len(v) for v in selection.values())==16
    OUT.mkdir(exist_ok=True)
    rows=[]
    for fam,names in selection.items():
        for filename in names:
            raw=(ROOT/filename).read_bytes()
            row={
                "family":fam,"path":filename,"original_source_sha256":hash_data(raw),
                "original_git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest(),
                "bytes":len(raw),
                "native_candidate_independently_verified":False,
                "native_cvc5_cost_excludes_install_and_harness":True,
            }
            try:
                stdout,stderr,cost=run_solver(ROOT/filename)
                row.update(cost)
                tag=filename.replace("/","__")
                (OUT/(tag+".stdout")).write_text(stdout)
                (OUT/(tag+".stderr")).write_text(stderr)
                m=re.findall(r"\(\s*define-fun\s+",stdout)
                row["define_fun_count"]=len(m)
                error_text=(stdout+"\n"+stderr).lower()
                if cost["forced"] or cost["returncode"] in (-24,-9,-6):
                    status="C_BUDGET_HOLD"
                elif cost["returncode"]!=0 or re.search(
                    r"error:|exception|unsupported|\(error",error_text):
                    status="HOLD_SOLVER_ERROR_OR_UNSUPPORTED"
                elif m:
                    status="C_PROGRAM_CANDIDATE_UNVERIFIED"
                else:
                    status="HOLD_NO_EXECUTABLE_PROGRAM_RETURNED"
                row["status"]=status
            except Exception as e:
                row.update(status="HOLD_EXECUTOR_EXCEPTION",error_type=type(e).__name__,
                           error_detail=str(e)[:140])
            rows.append(row)
            print("OFFICIAL_C_FIRST",len(rows),filename,row["status"],
                  row.get("wall_seconds"),flush=True)
    cnt=dict(collections.Counter(r["status"] for r in rows))
    result={
       "original_repository":"SyGuS-Org/benchmarks","original_exact_commit":head,
       "preregistered_names_inventory_sha256":NAMES_SHA,
       "status":"FIRST_UNGRADED_C_HEADROOM_SCREEN",
       "native_version":ver,"fixed_groups":FAMILIES,"selection":selection,
       "task_denominator":16,"results":rows,"counts":cnt,
       "no_neural_training":True,"candidate_solution_independent_grade":"NOT_RUN",
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
    }
    filename=OUT/"OFFICIAL_C16_FIRST_UNGRADED_CLASSICAL_HEADROOM.json"
    filename.write_text(json.dumps(result,sort_keys=True,indent=2))
    print("FIRST_SHA256",hash_data(filename.read_bytes()),flush=True)
    print("COUNTS",json.dumps(cnt,sort_keys=True),flush=True)
    print("CHILD_CPU_TOTAL",round(sum(
        r.get("cpu_user_seconds",0)+r.get("cpu_system_seconds",0) for r in rows),6),flush=True)

if __name__=="__main__":main()
