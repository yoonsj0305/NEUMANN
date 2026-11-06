"""Actual already-opened CHC copy2 human relational-H1 proof, not Q3 learning.
Prove each published original unchanged Horn clause, retain first failure.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/Q3_TWO_ARRAY_COPY_REAL_CHC_DEV_FIRST_2026_11_06.json"
ARR="(Array Int Int)"
SIGNATURES={
 "main@entry":["Int","Int"],
 "main@bb13.i":["Int","Int","Int",ARR,"Int",ARR,"Int","Int",ARR],
 "main@bb30.i":["Int",ARR,"Int",ARR,"Int","Int",ARR,"Int"],
 "main@bb44.i":["Int",ARR,"Int",ARR,"Int","Int"],
 "main@verifier.error.split":[]
}
COPY="""(define-fun COPY_PREFIX
 ((dst (Array Int Int)) (db Int) (src (Array Int Int)) (sb Int) (cursor Int)) Bool
 (forall ((j Int)) (=> (and (<= 0 j) (< j cursor))
 (= (select dst (+ db j)) (select src (+ sb j))))))"""
WRONG="""(define-fun COPY_PREFIX_WRONG
 ((dst (Array Int Int)) (db Int) (src (Array Int Int)) (sb Int) (cursor Int)) Bool
 (forall ((j Int)) (=> (and (<= 0 j) (< j cursor))
 (= (select dst (+ db j)) (+ (select src (+ sb j)) 1)))))"""


def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def blob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()


def forms(text:str)->list[str]:
    out=[];depth=0;start=0;comment=False;quoted=False
    for i,ch in enumerate(text):
        if comment:
            if ch in "\r\n":comment=False
            continue
        if quoted:
            if ch=="|":quoted=False
            continue
        if ch==";":comment=True;continue
        if ch=="|":quoted=True;continue
        if ch=="(":
            if depth==0:start=i
            depth+=1
        elif ch==")":
            depth-=1
            if depth<0:raise ValueError("BAD_ORIGINAL_SOURCE_PAREN")
            if depth==0:out.append(text[start:i+1])
    if depth!=0 or quoted:raise ValueError("UNBALANCED_ORIGINAL_SOURCE")
    return out


def call(dst,db,src,sb,cursor,wrong=False):
    return "("+("COPY_PREFIX_WRONG" if wrong else "COPY_PREFIX")+" "+dst+" "+db+" "+src+" "+sb+" "+cursor+")"


def predicate(name:str,wrong:bool=False)->str:
    args=" ".join("(x"+str(i)+" "+s+")" for i,s in enumerate(SIGNATURES[name]))
    body={
       "main@entry":"true",
       "main@verifier.error.split":"false",
       "main@bb13.i":"(and (> x1 0) (> x4 0) (> x6 0) (> x7 0) (<= 0 x2) (<= x2 x7) "+
                         call("x3","x1","x5","x4","x2")+")",
       "main@bb30.i":"(and (> x0 0) (> x2 0) (> x5 0) (> x7 0) (<= 0 x4) (<= x4 x7) "+
                         call("x1","x0","x3","x2","x7")+" "+
                         call("x6","x5","x3","x2","x4",wrong=wrong)+")",
       "main@bb44.i":"(and (> x0 0) (> x2 0) (> x5 0) (<= 0 x4) (<= x4 x5) "+
                         call("x1","x0","x3","x2","x5")+")"
    }[name]
    return "(define-fun |"+name+"| ("+args+") Bool "+body+")"


def compiled(original:str,wrong:bool=False)->dict:
    source_forms=forms(original)
    found={}
    for form in source_forms:
        m=re.fullmatch(r"\(\s*declare-fun\s+\|([^|]+)\|\s*\(\s*(.*?)\s*\)\s+Bool\s*\)",form,re.S)
        if m:
            name=m[1]
            if name not in SIGNATURES or name in found:
                raise ValueError("UNKNOWN_OR_DUPLICATE_RELATION_"+name)
            sorts=re.findall(r"\(Array\s+Int\s+Int\)|Int|Bool",m[2])
            if sorts!=SIGNATURES[name]:
                raise ValueError("CHANGED_ORIGINAL_SORTS_"+name)
            found[name]=form
    if set(found)!=set(SIGNATURES):
        raise ValueError("SOURCE_PREDICATE_SET_DRIFT")
    assertions=[f for f in source_forms if re.match(r"^\(\s*assert\s+",f)]
    if len(assertions)!=9:
        raise ValueError("ORIGINAL_SOURCE_CLAUSE_COUNT_NOT_9")
    prefix="(set-logic ALL)\n"+COPY+"\n"+(WRONG+"\n" if wrong else "")+ \
           "\n".join(predicate(name,wrong) for name in SIGNATURES)+"\n"
    return {"prefix":prefix,"assertions":assertions}


def prove(data:dict,directory:Path,limit_s:int=7,stop_at_sat:bool=False):
    directory.mkdir(parents=True,exist_ok=False)
    items=[]
    for i,original in enumerate(data["assertions"]):
        phi=original[len("(assert"):-1].strip()
        script=data["prefix"]+"(assert (not "+phi+"))\n(check-sat)\n"
        path=directory/("obligation_%02d.smt2"%i)
        path.write_text(script)
        begin=time.perf_counter_ns()
        try:
            p=subprocess.run(["z3","-smt2","-T:"+str(limit_s),str(path)],
                text=True,capture_output=True,timeout=limit_s+2,check=False)
            output=[x.strip() for x in p.stdout.splitlines() if x.strip()]
            result=output[0] if p.returncode==0 and output in (["sat"],["unsat"],["unknown"]) else "CHECKER_ERROR"
            error=p.stderr[-180:]
        except subprocess.TimeoutExpired:
            result="TIMEOUT_CENSORED";error="TIMEOUT"
        items.append({"index":i,"original_assert_sha256":sha(original.encode()),
                      "negated_obligation_sha256":sha(script.encode()),"result":result,
                      "stderr_tail":error,
                      "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3)})
        if (stop_at_sat and result=="sat") or (not stop_at_sat and result!="unsat"):
            break
    return items


def first(directory:Path):
    if directory.exists():raise ValueError("DO_NOT_OVERWRITE_FIRST_PROOF")
    c=json.loads(CONTRACT.read_text()); m=c["original"]
    url="https://raw.githubusercontent.com/"+m["repo"]+"/"+m["commit"]+"/"+m["file"]
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-relational-original-dev"}),timeout=45) as handle:
        raw=handle.read(15000)
    if blob(raw)!=m["git_blob"] or len(raw)!=m["bytes"]:
        raise ValueError("PINNED_OPENED_ORIGINAL_BLOB_DRIFT")
    directory.mkdir(parents=True)
    base=compiled(raw.decode("utf8"))
    good=prove(base,directory/"independent_proof")
    certified=len(good)==9 and all(x["result"]=="unsat" for x in good)
    bad=None
    if certified:
        bad=prove(compiled(raw.decode("utf8"),wrong=True),directory/"wrong_operator",stop_at_sat=True)
    corrupted_rejected=bad is not None and any(x["result"]=="sat" for x in bad)
    report={
      "schema":"neumann.q3.relational-human-H1-real-original-CHC-development-first.v1",
      "original_source":m["file"],"git_blob":blob(raw),"sha256":sha(raw),
      "operator_origin":"HUMAN_DESIGNED_NOT_LEARNED",
      "source_original_clauses_unchanged":True,
      "original_total":9,"original_independent_proofs":sum(x["result"]=="unsat" for x in good),
      "original_all_proven":certified,
      "wrong_cross_array_copy_mutant_refuted_by_SAT":corrupted_rejected,
      "scientific_status":"SCOPED_REAL_ORIGINAL_H1_PASS" if certified and corrupted_rejected else "ORIGINAL_H1_FAIL_OR_UNKNOWN",
      "new_self_weight_operator_invented":False,"global_Q3":"OPEN","global_Q6":"OPEN",
      "positive_obligations":good,"negative_obligations":bad
    }
    (directory/"FIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("positive_obligations","negative_obligations")},indent=2,sort_keys=True))
    if report["scientific_status"]!="SCOPED_REAL_ORIGINAL_H1_PASS":
        raise RuntimeError("ORIGINAL_RELATIONAL_COPY_FIRST_FAILED")
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    first(p.parse_args().out)
