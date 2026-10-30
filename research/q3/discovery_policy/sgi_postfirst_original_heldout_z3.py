#!/usr/bin/env python3
"""POST-FIRST verification: original last constraint never fed to first CVC5.
Independently check using Z3; all original files, proposals, and sha frozen.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import os

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms, get_cmd, choose_paths, sha256

SRC=pathlib.Path("upstream")
ART=pathlib.Path("first_artifact")
OUT=pathlib.Path("verifier_receipts")
EXPECTED_FIRST_SHA="44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0"
PINNED_UPSTREAM="e7ae840e5546e9243ff94afb1a29064fc050011c"

def balanced_at(source,start):
    assert source[start]=="("
    depth=0
    in_quote=False
    bar=False
    i=start
    while i<len(source):
        ch=source[i]
        if in_quote:
            if ch=='"':
                if i+1<len(source) and source[i+1]=='"':
                    i+=2
                    continue
                in_quote=False
        elif bar:
            if ch=='|':bar=False
        elif ch=='"':in_quote=True
        elif ch=='|':bar=True
        elif ch==';':
            e=source.find("\n",i)
            if e<0:raise ValueError("unterminated-comment")
            i=e+1
            continue
        elif ch=='(':
            depth+=1
        elif ch==')':
            depth-=1
            if depth==0:return source[start:i+1]
        i+=1
    raise ValueError("unterminated-sexp")

def get_candidate(stdout,name):
    # CVC5 prints ((define-fun ...) ...); only extract matching function.
    pat=re.compile(r"\(\s*define-fun\s+"+re.escape(name)+r"(?=\s)")
    hits=list(pat.finditer(stdout))
    if len(hits)!=1:
        raise ValueError("number-of-matching-define-fun-"+str(len(hits)))
    candidate=balanced_at(stdout,hits[0].start())
    if get_cmd(candidate)!="define-fun":
        raise ValueError("bad-candidate")
    return candidate

def body_of_constraint(form):
    m=re.match(r"^\(\s*constraint\s+",form)
    if not m or not form.endswith(")"):
        raise ValueError("non-constraint")
    return form[m.end():-1].strip()

def verify_z3(script,timeout=12):
    code = """
import sys
import z3
try:
    stmts=z3.parse_smt2_string(sys.stdin.read())
    slv=z3.Solver()
    slv.set(timeout=7000)
    slv.add(*stmts)
    print(slv.check())
except Exception as exc:
    print('Z3_PARSE_ERROR_'+type(exc).__name__)
"""
    t=time.monotonic()
    try:
        p=subprocess.run([sys.executable,"-c",code],input=script,text=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        return {"result":p.stdout.strip(),"exit_code":p.returncode,
                "wall_seconds":round(time.monotonic()-t,6),
                "stderr_sha256":sha256(p.stderr.encode())}
    except subprocess.TimeoutExpired:
        return {"result":"TIMEOUT","wall_seconds":round(time.monotonic()-t,6)}

def judge(row):
    index=row["index"]
    path=SRC/row["path"]
    raw=path.read_bytes()
    srctext=raw.decode("utf-8")
    result={
      "index":index,"original_path":row["path"],
      "source_sha256":sha256(raw),
      "source_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
    }
    if result["source_sha256"]!=row["source_original_sha256"] or result["source_blob_sha1"]!=row["source_blob_sha1"]:
        result["status"]="HOLD_ORIGINAL_MISMATCH";return result
    parsed=top_level_forms(srctext)
    cs=[p[2] for p in parsed if get_cmd(p[2])=="constraint"]
    ss=[p[2] for p in parsed if get_cmd(p[2])=="synth-fun"]
    if len(ss)!=1 or len(cs)<3:
        result["status"]="HOLD_ORIGINAL_GOAL_MISMATCH";return result
    m=re.match(r"^\(\s*synth-fun\s+([A-Za-z_][A-Za-z0-9_.-]*)",ss[0])
    if not m:
        result["status"]="HOLD_CANNOT_PARSE_SYNTH_NAME";return result
    name=m.group(1)
    heldout=cs[-1]
    if sha256(heldout.encode())!=row["withheld_last_constraint_sha256"]:
        result["status"]="HOLD_HELDOUT_SHA_MISMATCH";return result
    stdout_path=ART/"raw"/("%02d.stdout"%index)
    stdout=stdout_path.read_bytes()
    if sha256(stdout)!=row.get("stdout_sha256"):
        result["status"]="HOLD_FROZEN_SOLVER_OUTPUT_SHA_MISMATCH";return result
    try:
        candidate=get_candidate(stdout.decode("utf-8"),name)
    except Exception as e:
        result["status"]="HOLD_CANDIDATE_PARSE"
        result["reason"]=str(e)
        return result
    result["candidate_sha256"]=sha256(candidate.encode())
    # All original domain helper function declarations remain available.
    # Ignore grammar/synth-fun and original SyGuS-only query syntax.
    supporting=[p[2] for p in parsed if get_cmd(p[2]) in (
      "define-fun","declare-fun","define-sort","declare-sort","declare-const")]
    unsupported=[get_cmd(p[2]) for p in parsed if get_cmd(p[2]) in (
      "declare-var","inv-constraint","synth-inv","define-fun-rec","define-funs-rec")]
    if unsupported:
        result["status"]="HOLD_SYMBOLIC_DECLARATIONS_UNSUPPORTED"
        result["unsupported"]=unsupported
        return result
    base="\n".join(supporting+[candidate])+"\n"
    bodies=[body_of_constraint(f) for f in cs]
    # To certify original finite PBE conditions, check that the negation
    # of conjunction of all *source* facts is UNSAT under candidate.
    src="(and "+" ".join(bodies[:-1])+")"
    result["z3_source"]=verify_z3(base+"(assert (not "+src+"))\n")
    result["z3_heldout"]=verify_z3(base+"(assert (not "+bodies[-1]+"))\n")
    a=result["z3_source"]; b=result["z3_heldout"]
    result["status"]=(
       "CVC5_SOURCE_ONLY_VERIFIED_HELDOUT_EXACT" if a["result"]=="unsat"
       and b["result"]=="unsat" and a.get("exit_code")==0 and b.get("exit_code")==0
       else "HOLD_OR_FALSE_SOURCE_OR_HELDOUT_Z3")
    # A valid cvc5 proposal is not necessarily exact on heldout.
    if a["result"]=="unsat" and b["result"]=="sat":
        result["status"]="CVC5_HELDOUT_FALSIFIED"
    return result

def main():
    raw=(ART/"FIRST_CVC5_SOURCE_ONLY.json").read_bytes()
    if sha256(raw)!=EXPECTED_FIRST_SHA:
        raise RuntimeError("IMMUTABLE_FIRST_SHA_MISMATCH")
    frozen=json.loads(raw)
    if frozen["source_commit"]!=PINNED_UPSTREAM:
        raise RuntimeError("SOURCE_COMMIT_MISMATCH")
    if subprocess.check_output(["git","-C",str(SRC),"rev-parse","HEAD"],text=True).strip()!=PINNED_UPSTREAM:
        raise RuntimeError("UPSTREAM_CHECKOUT_MISMATCH")
    paths=[p.relative_to(SRC).as_posix() for p in choose_paths(SRC/"data"/"benchmarks")]
    if paths != frozen["chosen_paths"] or len(paths)!=12:
        raise RuntimeError("FROZEN_TASK_SELECTION_MISMATCH")
    results=[]
    for row in frozen["rows"]:
        try:
            result=judge(row)
        except Exception as e:
            result={"index":row["index"],"original_path":row["path"],
              "status":"HOLD_JUDGE_EXCEPTION","exception_type":type(e).__name__,
              "exception_msg":str(e)[:200]}
        results.append(result)
        print("GRADE",result["index"],result["original_path"],result["status"],
          result.get("z3_source",{}).get("result"),result.get("z3_heldout",{}).get("result"),flush=True)
    counts={}
    for r in results:
        counts[r["status"]]=counts.get(r["status"],0)+1
    payload={
       "purpose":"POST-FIRST original-heldout independent Z3 grade of previously frozen CVC5 source-only proposals",
       "frozen_first_sha256":EXPECTED_FIRST_SHA,
       "frozen_upstream_commit":PINNED_UPSTREAM,
       "author_and_model": "External Barnard-PL-Labs dataset; CVC5 1.1.2 classical model, NO NEUMANN neural learning",
       "verifier":"Z3 4.13.3; separate fresh interpreter processes, SMT verdict not proof kernel",
       "denominator":12,"counts":counts,"results":results,
       "Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
    }
    OUT.mkdir(exist_ok=True)
    p=OUT/"POSTFIRST_INDEPENDENT_HELDOUT_Z3.json"
    p.write_text(json.dumps(payload,indent=2,sort_keys=True))
    print("GRADE_COUNTS",json.dumps(counts,sort_keys=True))
    print("GRADE_SHA256",sha256(p.read_bytes()))
if __name__=="__main__":
    main()
