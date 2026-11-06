"""NEUMANN G2: native-expert-first source-only headroom screen for TWO distinct formalisms.

This is NOT a neural experiment and does not prove a general intelligence gap.
Metadata-selected original sources are preregistered with Git blobs before
first body exposure. Solver gets published complete original grammar.
- BV original PBE: LAST original ground constraint withheld from synthesis.
- INV original induction: original pre/trans/post/inv constraints to synth;
  proof discharges all three universal implications using SMT counterexample UNSAT.
- CVC5 parse failure/UNKNOWN/timeout NEVER counts as a new capability gap.
Never claims unsolvability, 10x, neural originality or universal BV equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/"docs/experiments/G2_NATIVE_RESIDUAL_24_SOURCE_METADATA_FIRST_PREREG_2026_11_06.json"
TOOLS_COMMIT="9f5cc084b77ce172a22c646dc54528b639ffb139"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def gitblob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def top_forms(src:str)->list[str]:
    forms=[]
    level=0;begin=None;quoted=False;comment=False;i=0
    while i<len(src):
        c=src[i]
        if comment:
            if c in "\r\n":comment=False
            i+=1;continue
        if quoted:
            if c=='"':
                if i+1<len(src) and src[i+1]=='"':
                    i+=2;continue
                quoted=False
            i+=1;continue
        if c==';':
            comment=True
        elif c=='"':
            quoted=True
        elif c=='(':
            if level==0:begin=i
            level+=1
        elif c==')':
            level-=1
            if level<0:raise ValueError("BAD_CLOSE_PAREN")
            if level==0:forms.append(src[begin:i+1]);begin=None
        i+=1
    if quoted or level:raise ValueError("UNTERMINATED_S_EXPRESSION")
    return forms

def form_name(s:str)->str|None:
    m=re.match(r"^\(\s*([A-Za-z0-9_.!+\-]+)",s)
    return m.group(1) if m else None

def first_define(output:str,symbol:str)->str|None:
    # Find only fully balanced top-level DEFINE, ignoring outer ((...)).
    pattern=r"\(\s*define-fun\s+"+re.escape(symbol)+r"\b"
    match=re.search(pattern,output)
    if not match:return None
    piece=output[match.start():]
    depth=0;quoted=False;i=0
    while i<len(piece):
        c=piece[i]
        if quoted:
            if c=='"':
                if i+1<len(piece) and piece[i+1]=='"':
                    i+=2;continue
                quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return piece[:i+1]
            if depth<0:return None
        i+=1
    return None

def prepare_bv_train(raw:str)->dict:
    forms=top_forms(raw)
    constraints=[f for f in forms if form_name(f)=="constraint"]
    if len(constraints)<2:return {"ok":False,"error":"INSUFFICIENT_PBE"}
    heldout=constraints[-1]
    start=raw.rfind(heldout)
    if start<0:raise ValueError("MISSING_SOURCE_HELDOUT")
    end=start+len(heldout)
    train=raw[:start]+raw[end:]
    remaining=[f for f in top_forms(train) if form_name(f)=="constraint"]
    if len(remaining)!=len(constraints)-1:
        raise ValueError("BAD_EXACTLY_ONE_SOURCE_WITHHELD")
    if heldout in train:raise ValueError("DUPLICATE_HELDOUT_SOURCE_LEAK")
    return {"ok":True,"train":train,"heldout":heldout,"all_constraints":constraints,
       "train_constraints":remaining,"constraint_count":len(constraints),
       "train_sha256":sha(train.encode()),"heldout_sha256":sha(heldout.encode())}

def original_invariant_signature(raw:str)->dict:
    fs=top_forms(raw)
    inv=[f for f in fs if form_name(f)=="synth-inv"]
    inv_specs=[f for f in fs if form_name(f)=="inv-constraint"]
    if len(inv)!=1 or len(inv_specs)!=1:return {"ok":False,"error":"MISSING_INV_SPEC"}
    match=re.match(r"\(\s*synth-inv\s+([A-Za-z0-9_.-]+)\s+\(",inv[0])
    if not match:return {"ok":False,"error":"BAD_SYNTH_INV_NAME"}
    name=match.group(1)
    vpart=inv[0]
    params=re.findall(r"\(\s*([A-Za-z0-9_!.-]+)\s+(Int|Bool)\s*\)",vpart)
    if not params:return {"ok":False,"error":"NO_GROUNDED_INV_PARAMS"}
    # Restrict to source INV induction with simple integer/boolean variable sorts.
    original={f for f in fs if form_name(f)=="define-fun"}
    spec_match=re.fullmatch(r"\(\s*inv-constraint\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*\)",inv_specs[0])
    if not spec_match or spec_match.group(1)!=name:
        return {"ok":False,"error":"UNEXPECTED_INV_OBLIGATION"}
    definition_names={}
    for f in original:
        z=re.match(r"\(\s*define-fun\s+(\S+)\s+",f)
        if not z:return {"ok":False,"error":"UNPARSEABLE_HELPER_FUNCTION"}
        definition_names[z.group(1)]=f
    pre,trans,post=spec_match.group(2,3,4)
    if not all(x in definition_names for x in (pre,trans,post)):
        return {"ok":False,"error":"UNDEFINED_INV_OBLIGATION"}
    return {"ok":True,"params":params,"name":name,"pre":pre,"trans":trans,
       "post":post,"definitions":list(original),
       "definitions_sha256":sha("\n".join(sorted(original)).encode())}

def convert_old(src:str,tools:Path)->dict:
    p=subprocess.run(["git","-C",str(tools),"rev-parse","HEAD"],capture_output=True,text=True)
    if p.returncode or p.stdout.strip()!=TOOLS_COMMIT:
        raise ValueError("UNPINNED_OFFICIAL_CONVERTER")
    with tempfile.NamedTemporaryFile("w",encoding="utf8",suffix=".sl") as f:
        f.write(src);f.flush()
        env=os.environ.copy();env["PYTHONPATH"]=str(tools)
        c=subprocess.run([sys.executable,"-m","sygus.bin.convert","-s","1","-t","2",f.name],
            capture_output=True,text=True,timeout=15,env=env)
    if c.returncode!=0 or "(check-synth)" not in c.stdout:
        return {"ok":False,"status":"PUBLISHER_CONVERTER_FAIL","exit":c.returncode,"stderr":c.stderr[-400:]}
    return {"ok":True,"source":c.stdout,"converted_sha256":sha(c.stdout.encode())}

def run_cli(src:str,lang:str="sygus2",timeout:float=12.):
    with tempfile.NamedTemporaryFile("w",encoding="utf8",suffix=".sl") as f:
        f.write(src);f.flush()
        start=time.perf_counter_ns()
        try:
            p=subprocess.run(["cvc5","--lang="+lang,"--sygus",
                   "--tlimit-per="+str(int(timeout*1000)),f.name],
                   capture_output=True,text=True,timeout=timeout+1)
            return {"kind":"COMPLETE","exit":p.returncode,
                "stdout":p.stdout,"stderr_tail":p.stderr[-500:],
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
        except subprocess.TimeoutExpired:
            return {"kind":"TIMEOUT","wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def check_smt(source:str):
    with tempfile.NamedTemporaryFile("w",encoding="utf8",suffix=".smt2") as f:
        f.write(source);f.flush()
        try:
            r=subprocess.run(["cvc5","--lang=smt2",f.name],
                 capture_output=True,text=True,timeout=6)
        except subprocess.TimeoutExpired:
            return {"proof":"UNKNOWN_TIMEOUT"}
    results=[v.strip() for v in r.stdout.splitlines() if v.strip()]
    return {"proof":"UNSAT" if r.returncode==0 and results==["unsat"] else "NOT_PROVED",
       "stdout":results[:3],"exit":r.returncode,"stderr":r.stderr[-350:]}

def prove_bv(program:str,prepared:dict)->dict:
    # Complete source helpers are part of the published original semantics.
    # Prove the DISJUNCTION of all possible ground sample violations UNSAT
    # in one SMT call, not 100 separate expensive cvc5 process launches.
    helpers=[f for f in top_forms(prepared["train"]) if form_name(f)=="define-fun"]
    checks=[]
    for label,cs in (("TRAIN",prepared["train_constraints"]),
                     ("HELDOUT",[prepared["heldout"]])):
        neg=[]
        for original in cs:
            expr=original.strip()
            if not expr.startswith("(constraint ") or not expr.endswith(")"):
                return {"verified":False,"reason":"MALFORMED_ORIGINAL_PBE",
                    "checks":checks}
            neg.append("(not "+expr[len("(constraint "):-1]+")")
        any_violation=neg[0] if len(neg)==1 else "(or "+" ".join(neg)+")"
        source="(set-logic ALL)\n"+"\n".join(helpers)+"\n"+program+ \
               "\n(assert "+any_violation+")\n(check-sat)\n"
        result=check_smt(source)
        checks.append({"split":label,"original_ground_constraints":len(cs),
                       "counterexample_proof":result})
        if result["proof"]!="UNSAT":
            return {"verified":False,"checks":checks,
                    "reason":"ORIGINAL_"+label+"_COUNTEREXAMPLE_NOT_UNSAT"}
    return {"verified":True,
       "original_source_examples_proven":len(prepared["train_constraints"])+1,
       "train_examples":len(prepared["train_constraints"]),
       "heldout_examples":1,
       "checks":checks}

def prove_inv(program:str,spec:dict)->dict:
    ps=spec["params"]
    names=[v for v,_ in ps]
    nextnames=[v+"!" for v in names]
    vars="\n".join("(declare-const "+v+" "+s+")" for v,s in ps)+"\n"+ \
         "\n".join("(declare-const "+v+"! "+s+")" for v,s in ps)
    orig="\n".join(spec["definitions"])
    def call(f,args):return "("+f+" "+" ".join(args)+")"
    inv=spec["name"];pre=spec["pre"];trans=spec["trans"];post=spec["post"]
    predicates=[
       ("init", "(and "+call(pre,names)+" (not "+call(inv,names)+"))"),
       ("step", "(and "+call(inv,names)+" "+call(trans,names+nextnames)+
          " (not "+call(inv,nextnames)+"))"),
       ("safe", "(and "+call(inv,names)+" (not "+call(post,names)+"))")
    ]
    checks=[]
    for title,formula in predicates:
        source="(set-logic ALL)\n"+orig+"\n"+program+"\n"+vars+"\n(assert "+formula+")\n(check-sat)\n"
        result=check_smt(source)
        checks.append({"obligation":title,"result":result})
        if result["proof"]!="UNSAT":
            return {"verified":False,"obligations":checks,
                "reason":"INV_"+title.upper()+"_NOT_PROVEN"}
    return {"verified":True,"obligations":checks,
            "quantification":"All integer/Boolean states via UNSAT counterexample"}

def probe_one(folder:str, target:dict,ref:str,cohort:str,tools:Path)->dict:
    url="https://raw.githubusercontent.com/SyGuS-Org/benchmarks/"+ref+"/"+folder+"/"+target["file"]
    with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G2-source-precommitted"}),timeout=45) as f:
        raw=f.read(100000)
    observed=gitblob(raw)
    if target["git_blob"]!=observed:raise ValueError("FROZEN_SOURCE_GIT_BLOB_DRIFT_"+target["file"])
    record={"file":target["file"],"cohort":cohort,"blob":observed,"bytes":len(raw)}
    text=raw.decode("utf8")
    if cohort=="INV_INDUCTION":
        spec=original_invariant_signature(text)
        if not spec["ok"]:
            record.update({"status":"UNSUPPORTED_ORIGINAL_SIGNATURE","reason":spec["error"],"verified":False})
            return record
        original_source=text
        expected_n=None
        symbol=spec["name"]
        record["inv_source_variables"]=len(spec["params"])
        record["original_inv_spec_definitions_sha256"]=spec["definitions_sha256"]
    else:
        spec=prepare_bv_train(text)
        if not spec["ok"]:
            record.update({"status":"UNSUPPORTED_PBE_SOURCE","reason":spec["error"],"verified":False})
            return record
        original_source=spec["train"]
        expected_n=spec["constraint_count"]-1
        symbol="f"
        record["train_sha256"]=spec["train_sha256"]
        record["heldout_sha256"]=spec["heldout_sha256"]
        record["original_pbe_count"]=spec["constraint_count"]
    cv=convert_old(original_source,tools)
    if not cv["ok"]:
        record.update({"status":"INFRA_SOURCE_CONVERTER_FAIL","conversion":cv,"verified":False})
        return record
    converted=cv["source"]
    original_count=sum(form_name(f)=="constraint" for f in top_forms(converted))
    if cohort=="BV_FINITE" and expected_n!=original_count:
        record.update({"status":"INCOMPATIBLE_CONVERTED_SOURCE","verified":False,
            "expected_training":expected_n,"actual_training":original_count})
        return record
    record["publisher_conversion_sha256"]=cv["converted_sha256"]
    solver=run_cli(converted,"sygus2",12.)
    if solver["kind"]=="TIMEOUT":
        record.update({"status":"SOLVER_BUDGET_TIMEOUT","verified":False,"solver":solver,
           "native_gap":"BUDGET_UNRESOLVED_ONLY_NOT_UNSOLVABLE"})
        return record
    candidate=first_define(solver["stdout"],symbol)
    record["solver"]={
        "process_exit":solver["exit"],"wall_ms":solver["wall_ms"],
        "stdout_sha256":sha(solver["stdout"].encode()),
        "stderr_tail":solver["stderr_tail"],
        "stdout_excerpt":solver["stdout"][:800]}
    if solver["exit"]!=0:
        record.update({"status":"SOLVER_PARSER_OR_INFRA_FAILURE",
                       "verified":False})
        return record
    if candidate is None:
        record.update({"status":"SOLVER_NO_PROGRAM","verified":False,
                       "native_gap":"UNKNOWN_REQUIRES_SEPARATE_BUDGET_OR_PROOF"})
        return record
    # Freeze candidate before independent original source proof.
    record["candidate"]=candidate
    record["candidate_sha256"]=sha(candidate.encode())
    proof=prove_inv(candidate,spec) if cohort=="INV_INDUCTION" else prove_bv(candidate,spec)
    record["proof"]=proof
    record["verified"]=proof["verified"]
    record["status"]="NATIVE_ORIGINAL_PROVED" if proof["verified"] else "NATIVE_CANDIDATE_NOT_PROVEN"
    return record

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--tools",type=Path,required=True)
    parser.add_argument("--cohort",choices=["INV_INDUCTION","BV_FINITE","PILOT_INV","PILOT_BV"],required=True)
    args=parser.parse_args()
    if args.cohort.startswith("PILOT"):
        coh="INV_INDUCTION" if args.cohort=="PILOT_INV" else "BV_FINITE"
        directory="comp/2018/Inv_Track" if coh=="INV_INDUCTION" else "comp/2018/PBE_BV_Track"
        file="ex1.sl" if coh=="INV_INDUCTION" else "PRE_100_10.sl"
        sha_expected="29420aae47ca3ee36fab64c8e3a17759eac778a8" if coh=="INV_INDUCTION" else "86a82144d3fc75a5c7d3cb76742b1d2639dfa593"
        targets=[{"file":file,"git_blob":sha_expected}]
        ref="13c8deb68a873635879c9a69bc78caebd340f646"
        expected=1
    else:
        doc=json.loads(REG.read_text())
        c=next(c for c in doc["cohorts"] if c["id"]==args.cohort)
        coh=args.cohort
        directory=c["folder"]
        targets=c["targets"]
        ref=doc["original"]["commit"]
        expected=12
    results=[]
    for target in targets:
        try:
            row=probe_one(directory,target,ref,coh,args.tools)
        except Exception as e:
            row={"file":target["file"],"status":"INFRA_FAIL_CLOSED",
                 "error":type(e).__name__+":"+str(e)[:260],"verified":False}
        results.append(row)
    if len(results)!=expected:raise ValueError("SOURCE_DENOMINATOR_DRIFT")
    stats={
      "total_original_tasks":len(results),
      "native_independently_proved":sum(r["verified"] for r in results),
      "native_budget_timeout":sum(r["status"]=="SOLVER_BUDGET_TIMEOUT" for r in results),
      "solver_original_no_program":sum(r["status"]=="SOLVER_NO_PROGRAM" for r in results),
      "source_or_infrastructure_unverified":sum(r["status"] in
         ("INFRA_FAIL_CLOSED","INFRA_SOURCE_CONVERTER_FAIL",
          "SOLVER_PARSER_OR_INFRA_FAILURE","INCOMPATIBLE_CONVERTED_SOURCE",
          "UNSUPPORTED_ORIGINAL_SIGNATURE","UNSUPPORTED_PBE_SOURCE") for r in results),
      "native_candidate_unproven":sum(r["status"]=="NATIVE_CANDIDATE_NOT_PROVEN" for r in results),
      "original_arc_evaluation_IDs_consumed":0,
    }
    result={
      "schema":"neumann.g2.native-first-two-independent-mathematical-formalisms.v1",
      "cohort":args.cohort,
      "science_status":"NATIVE_FIRST_BASELINE_RECORDED_NOT_NEUMANN_Q3_PASS",
      "first_original_denominator":expected,
      "student_training_calls":0,
      "native_correctness_from_original_source_only":True,
      "baseline_proof_unit":"UNSAT of violation not only candidate printed",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "stats":stats,
      "rows":results
    }
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"science_status":"G2_INFRA_FAILURE_NOT_A_SCIENTIFIC_FAIL",
            "message":type(error).__name__+":"+str(error)[:260]}))
        raise SystemExit(2)
