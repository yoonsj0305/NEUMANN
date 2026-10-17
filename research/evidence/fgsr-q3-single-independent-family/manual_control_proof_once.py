"""Bounded authentic 48-Horn original independent proof with an explicit human-designed
finite-control invariant. Developer hypothesis, NOT learned discovery and NOT model Q3.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.request
import z3

REPO="chc-comp/chc-comp26-benchmarks"
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
OUT=Path(os.environ.get("FGSR_RESULT","proof_receipt.json"))
ALLOWED=(-1,2,4,5,6,7,8)

def split_top(s):
    out=[];depth=0;start=None;in_comment=False;quoted=False
    for i,c in enumerate(s):
        if c=="\n":in_comment=False
        if in_comment:continue
        if not quoted and c==";":in_comment=True;continue
        if c=="|":quoted=not quoted
        if quoted:continue
        if c=="(":
            if depth==0:start=i
            depth+=1
        elif c==")":
            depth-=1
            if depth<0:raise ValueError("unbalanced at "+str(i))
            if depth==0:out.append(s[start:i+1])
    if depth:raise ValueError("unbalanced at EOF")
    return out

def invariant(args):
    if len(args)!=8:raise ValueError("wrong relation arity")
    a,b,c,d,e,f,g,h=args
    membership=lambda v: "(or "+" ".join(f"(= {v} {i})" if i>=0 else f"(= {v} (- 1))" for i in ALLOWED)+")"
    return "(and "+" ".join([
        f"(= {f} (- 1))",f"(= {g} (- 1))",
        "(or "+" ".join(f"(= {h} {i})" for i in range(5))+")",
        f"(=> (not (= {h} 0)) (= {a} 0))",
        f"(=> (not (= {h} 4)) (and (= {d} (- 1)) (= {e} (- 1))))",
        membership(d),membership(e)])+")"

INV_RE=re.compile(r"\(\s*\|?Inv\|?\s+((?:[A-Za-z_][A-Za-z_0-9]*\s+){7}[A-Za-z_][A-Za-z_0-9]*)\s*\)")
FALSE_RE=re.compile(r"(?<![A-Za-z_0-9|])CHC_COMP_FALSE(?![A-Za-z_0-9|])")

def compile_rule(assertion, enabled=True):
    expr=assertion.strip()
    if not re.match(r"^\(assert\s",expr):raise ValueError("unsupported assertion")
    form=expr[len("(assert"): -1].strip()
    n=[0]
    def repl(m):
        n[0]+=1
        return invariant(m.group(1).split()) if enabled else "true"
    form=INV_RE.sub(repl,form)
    if re.search(r"\(\s*\|?Inv\|?\s",form):raise ValueError("unsubstituted relation")
    form=FALSE_RE.sub("false",form)
    if "CHC_COMP_FALSE" in form:raise ValueError("unsubstituted false predicate")
    return form,n[0]

def check(form):
    solver=z3.Solver()
    solver.set(timeout=2000)
    solver.from_string("(assert (not "+form+"))")
    t=time.perf_counter_ns()
    verdict=str(solver.check())
    return {"status":verdict,"wall_ms":round((time.perf_counter_ns()-t)/1e6,3),
            "reason":solver.reason_unknown() if verdict=="unknown" else None,
            "counterexample":str(solver.model())[:900] if verdict=="sat" else None}

def main():
    t0=time.perf_counter_ns()
    result={
        "experiment":"FGSR authentic 48-Horn explicit manual finite-control invariant proof",
        "source_expected_sha256":SHA,
        "candidate_source":"RESEARCHER_AUTHORED_AFTER_OPENING_SOURCE",
        "neural_calls":0,"neumann_learned_Q3":False,
        "global_questions":"Q1-Q7 OPEN","status":"BLOCKED",
        "z3_version":z3.get_version_string(),
        "independent_original_source":True,
        "original_source_modified":False
    }
    try:
        req=f"https://raw.githubusercontent.com/{REPO}/{REV}/{SOURCE}"
        with urllib.request.urlopen(req,timeout=35) as f:raw=f.read()
        if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("SOURCE_MISMATCH")
        original=raw.decode()
        original_forms=split_top(original)
        assertions=[x for x in original_forms if re.match(r"^\(assert\s",x)]
        if len(assertions)!=48:raise ValueError("SOURCE_COUNT_MISMATCH:"+str(len(assertions)))
        if len([x for x in original_forms if x.startswith("(declare-fun")])!=2:
            raise ValueError("SOURCE_DECL_MISMATCH")
        result["original_sha256_verified"]=True
        result["original_clause_count"]=len(assertions)
        result["per_clause"]=[]
        result["atom_replacements"]=0
        for ix,assertion in enumerate(assertions,1):
            form,n=compile_rule(assertion)
            result["atom_replacements"]+=n
            observation=check(form)
            result["per_clause"].append({"rule_index":ix,**observation})
            if observation["status"]!="unsat":break
        result["verified_original_unsat_count"]=sum(r["status"]=="unsat" for r in result["per_clause"])
        result["first_non_unsat"]=next((r for r in result["per_clause"] if r["status"]!="unsat"),None)
        result["proof_ms"]=round(sum(r["wall_ms"] for r in result["per_clause"]),3)
        result["status"]=(
           "ORIGINAL_ALL_48_CERTIFIED_MANUAL_INVARIANT"
           if len(result["per_clause"])==48 and all(r["status"]=="unsat" for r in result["per_clause"])
           else "REJECTED_OR_INCOMPLETE_ORIGINAL_PROOF"
        )
        # Negative control of independent proof authority: omitted invariant is
        # not a proof; needs SAT on at least one original goal clause.
        if result["status"]=="ORIGINAL_ALL_48_CERTIFIED_MANUAL_INVARIANT":
            controls=[]
            for index in (46,47,48):
                form,_=compile_rule(assertions[index-1],enabled=False)
                controls.append({"rule":index,"status":check(form)["status"]})
            result["negative_controls"]=controls
            if not any(x["status"]=="sat" for x in controls):
                result["status"]="NEGATIVE_CONTROL_FAILED"
    except Exception as exc:
        result["status"]="RUNTIME_OR_SOURCE_ERROR"
        result["error"]=type(exc).__name__+": "+str(exc)[:900]
    result["total_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("ORIGINAL_PROOF",result["status"])
    print("CANDIDATE",result.get("verified_original_unsat_count"),"of",result.get("original_clause_count"))
    print("ERROR",result.get("first_non_unsat") or result.get("error"))
    print("NEGATIVE_CONTROLS",result.get("negative_controls"))
    print("SCIENTIFIC_Q","Q1-Q7 OPEN")
if __name__=="__main__":main()
