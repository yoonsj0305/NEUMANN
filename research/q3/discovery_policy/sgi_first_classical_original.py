#!/usr/bin/env python3
"""FIRST original SyGuS-SGI external, source-only CVC5 headroom screen.
Read ONLY source constraints when calling solver; do not compute heldout outputs.
Independent heldout grading MUST be a later, separately frozen step.
"""
import hashlib
import json
import pathlib
import re
import resource
import subprocess
import time

UPSTREAM_SHA = "e7ae840e5546e9243ff94afb1a29064fc050011c"
PREREG_SHA = "a49478b83570447bdc186c0ec849d4253acec956"
SELECTION_SEED = "neumann1-semantic-gap-v1/"
OUT = pathlib.Path("first_receipts")
SRC = pathlib.Path("upstream")

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def top_level_forms(s):
    """Balanced top-level SMT-LIB spans; preserve exact untouched text elsewhere."""
    result = []
    depth = 0
    start = None
    i = 0
    in_string = False
    in_bar = False
    while i < len(s):
        c = s[i]
        if in_string:
            if c == '"':
                if i+1 < len(s) and s[i+1] == '"':
                    i += 2
                    continue
                in_string = False
        elif in_bar:
            if c == '|':
                in_bar = False
        elif c == ';':
            nl = s.find("\n",i)
            if nl < 0:
                break
            i = nl + 1
            continue
        elif c == '"':
            in_string = True
        elif c == '|':
            in_bar = True
        elif c == '(':
            if depth == 0:
                start = i
            depth += 1
        elif c == ')':
            depth -= 1
            if depth < 0:
                raise ValueError("extra-closing")
            if depth == 0:
                result.append((start,i+1,s[start:i+1]))
        i += 1
    if depth != 0 or in_string or in_bar:
        raise ValueError("incomplete-smtlib")
    return result

def get_cmd(form):
    m = re.match(r"^\(\s*([a-zA-Z][a-zA-Z0-9-]*)\b",form)
    return m.group(1) if m else None

def choose_paths(root):
    groups = {}
    for kind in ("easy","hard"):
        entries = sorted(root.glob(kind + "/*/*.sl"))
        choices = sorted(entries, key=lambda p:(sha256((SELECTION_SEED+p.relative_to(SRC).as_posix()).encode()),p.as_posix()))
        requested = 3 if kind == "easy" else 9
        if len(choices) < requested:
            raise RuntimeError("not-enough-"+kind+"-"+str(len(choices))+"-need-"+str(requested))
        groups[kind] = choices[:requested]
    return groups["easy"]+groups["hard"]

def cpu_limit():
    resource.setrlimit(resource.RLIMIT_CPU,(12,13))

def bounded_cvc5(input_file):
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start=time.monotonic()
    proc = subprocess.Popen(["cvc5","--lang=sygus2",str(input_file)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors="replace",preexec_fn=cpu_limit)
    sampled_rss=0
    forced=None
    while proc.poll() is None:
        try:
            status=pathlib.Path("/proc/%s/status" % proc.pid).read_text(errors="replace")
            m=re.search(r"^VmRSS:\s+(\d+)\s+kB",status,re.MULTILINE)
            if m:
                sampled_rss=max(sampled_rss,int(m.group(1)))
                if sampled_rss>800*1024:
                    forced="OVER_800_MIB_SAMPLED_RSS"
                    proc.kill()
        except (ProcessLookupError,FileNotFoundError):
            pass
        if time.monotonic()-start>15:
            forced="OVER_15_S_WALL"
            proc.kill()
        time.sleep(.015)
    stdout,stderr=proc.communicate(timeout=2)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    metrics={
      "exit_code":proc.returncode,
      "forced":forced,
      "wall_seconds":round(time.monotonic()-start,6),
      "cpu_user_seconds":round(after.ru_utime-before.ru_utime,6),
      "cpu_system_seconds":round(after.ru_stime-before.ru_stime,6),
      "sampled_peak_rss_kib_lower_bound":sampled_rss or None,
      "stdout_sha256":sha256(stdout.encode()),
      "stderr_sha256":sha256(stderr.encode()),
      "stdout_bytes":len(stdout.encode()),
      "stderr_bytes":len(stderr.encode()),
    }
    return stdout,stderr,metrics

def main():
    OUT.mkdir(exist_ok=True)
    (OUT/"raw").mkdir(exist_ok=True)
    upstream=subprocess.check_output(["git","-C",str(SRC),"rev-parse","HEAD"],text=True).strip()
    if upstream!=UPSTREAM_SHA:
        raise RuntimeError("upstream sha mismatch")
    version=subprocess.check_output(["cvc5","--version"],text=True,stderr=subprocess.STDOUT)
    (OUT/"cvc5-version.txt").write_text(version)
    choices=choose_paths(SRC/"data"/"benchmarks")
    rows=[]
    for i,path in enumerate(choices):
        rel=path.relative_to(SRC).as_posix()
        raw=path.read_bytes()
        row={
          "index":i,
          "path":rel,
          "category":"easy" if i<3 else "hard",
          "source_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
          "source_original_sha256":sha256(raw),
          "source_bytes":len(raw),
        }
        try:
            original=raw.decode("utf-8")
            parsed=top_level_forms(original)
            constraints=[p for p in parsed if get_cmd(p[2])=="constraint"]
            synths=[p for p in parsed if get_cmd(p[2])=="synth-fun"]
            checks=[p for p in parsed if get_cmd(p[2])=="check-synth"]
            row.update({
              "original_constraint_count":len(constraints),
              "synth_fun_count":len(synths),
              "check_synth_count":len(checks),
            })
            if len(constraints)<3 or len(synths)!=1 or len(checks)!=1:
                row["status"]="INELIGIBLE_STRUCTURE"
                rows.append(row)
                continue
            a,b,heldout=constraints[-1]
            row["withheld_last_constraint_sha256"]=sha256(heldout.encode())
            source_only=original[:a]+original[b:]
            if len(top_level_forms(source_only)) != len(parsed)-1:
                raise ValueError("removal-structural-check-failed")
            # A source-only solver is not allowed to see heldout formula.
            assert heldout not in source_only
            row["source_only_sha256"]=sha256(source_only.encode())
            inp=OUT/("input-source-only-%02d.sl" % i)
            inp.write_text(source_only)
            stdout,stderr,metrics=bounded_cvc5(inp)
            (OUT/"raw"/("%02d.stdout"%i)).write_text(stdout)
            (OUT/"raw"/("%02d.stderr"%i)).write_text(stderr)
            row.update(metrics)
            low=stdout.lower()+"\n"+stderr.lower()
            candidates=re.findall(r"\(\s*define-fun\s+",stdout)
            row["candidate_define_fun_count"]=len(candidates)
            row["status"]=(
                "C_CANDIDATE_NOT_HELDOUT_GRADED" if (
                    row["exit_code"]==0 and not row["forced"]
                    and len(candidates)>=1 and not re.search(r"error|exception|unsupported",low))
                else "C_HOLD_NO_SOLUTION_OR_EXECUTOR"
            )
            # Do not upload source input itself. Only raw solver outputs, hashes.
            inp.unlink()
        except Exception as e:
            row["status"]="HOLD_PREP_OR_RUNTIME"
            row["exception_type"]=type(e).__name__
            row["exception_detail"]=str(e)[:200]
        rows.append(row)
        print("FIRST_ROW",i,rel,row["status"],row.get("wall_seconds"),flush=True)
    result={
      "purpose":"Original cross-project source-only solver candidate FIRST. NO future gold used in synthesis.",
      "repo":"Barnard-PL-Labs/sygus-sgi-1",
      "source_commit":UPSTREAM_SHA,
      "prereg_commit":PREREG_SHA,
      "chosen_paths":[r["path"] for r in rows],
      "native_solver":"cvc5",
      "native_solver_version":version,
      "model_training":"NOT_RUN",
      "independent_heldout_verification":"NOT_RUN",
      "global_Q1_Q7":"OPEN",
      "G1":"HOLD",
      "rows":rows
    }
    out=OUT/"FIRST_CVC5_SOURCE_ONLY.json"
    out.write_text(json.dumps(result,sort_keys=True,indent=2))
    (OUT/"FIRST_SHA256.txt").write_text(sha256(out.read_bytes())+"  "+str(out)+"\n")
    print("FIRST_SHA256",sha256(out.read_bytes()),flush=True)
    print("COUNTS",json.dumps({s:sum(r["status"]==s for r in rows) for s in sorted({r["status"] for r in rows})}))
if __name__=="__main__":
    main()
