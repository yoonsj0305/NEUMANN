"""Independent proof obligations for one genuine public external CHC-COMP original.
Source-derived algebraic invariant witness is researcher-authored AFTER source
inspection. NOT a learned NEUMANN theorem, NOT operator invention.

Every original Horn clause is checked via a fresh SMT solver after inserting
the explicit full interpretation of all five original uninterpreted predicates.
Z3 checks the negation of each original quantified assertion. An exact verified
9/9 UNSAT is an ORIGINAL full inductive safety certificate for this source.

Original is externally authored and fetched from pinned source SHA.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.request
import z3

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
FILE="eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2"
EXPECTED_SHA="f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748"
OUT=Path(os.environ.get("FGSR_RESULT","real_square_full_certificate.json"))

WITNESS={
    "inv_main3":("((n Int))","true"),
    "inv_main8":("((a Int) (b Int) (s Int) (t Int))",
        "(and (= a b) (= s (* b (- a t))) (ite (<= a 0) (= t a) (and (<= 0 t) (<= t a))))"),
    "inv_main13":("((a Int) (b Int) (s Int) (t Int))",
        "(and (= a b) (= s (* b (- a t))) (ite (<= a 0) (= t a) (and (<= 0 t) (<= t a))))"),
    "inv_main22":("((a Int) (b Int) (c Int) (s Int) (t Int))",
        "(and (= a c) (= b (ite (<= a 0) 0 (* a a))) (= s (* c (- a t))) "
        "(ite (<= a 0) (= t a) (and (<= 0 t) (<= t a))))"),
    "inv_main26":("((a Int) (b Int) (c Int))","(= b c)")
}

def top_level(text):
    forms=[];depth=0;start=None;comment=False
    for i,c in enumerate(text):
        if c=="\n":comment=False
        if c==";" and depth==0:comment=True
        if comment:continue
        if c=="(":
            if depth==0:start=i
            depth+=1
        elif c==")":
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_SOURCE")
            if depth==0:forms.append(text[start:i+1])
    if depth:raise ValueError("UNBALANCED_SOURCE_EOF")
    return forms

def definitions(overrides=None):
    entries=dict(WITNESS)
    if overrides:entries.update(overrides)
    return "\n".join("(define-fun |"+name+"| "+args+" Bool "+formula+")"
                     for name,(args,formula) in entries.items()) + (
                     "\n(define-fun |CHC_COMP_FALSE| () Bool false)\n")

def check_one(forall,defs,limit=7000):
    script="(set-logic ALL)\n"+defs+"\n(assert (not "+forall+"))"
    sol=z3.Solver()
    sol.set(timeout=limit)
    start=time.perf_counter_ns()
    try:
        sol.from_string(script)
        r=str(sol.check())
        return {"result":r,"wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
                 "unknown_reason":sol.reason_unknown() if r=="unknown" else None}
    except Exception as e:
        return {"result":"ERROR","error":type(e).__name__+":"+str(e)[:500],
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def main():
    t0=time.perf_counter_ns()
    record={
        "target":"CHC-COMP 2026 genuine external llreve/square_twice_safe.c-1_000",
        "original_sha256":EXPECTED_SHA,"scientific_authorship":"RESEARCHER_AUTHORED_SOURCE_CONDITIONED_CLASSICAL_WITNESS",
        "learned_model_calls":0,"original_modified":False,"global_q1_q7":"OPEN",
        "status":"NOT_RUN","z3_version":z3.get_version_string()
    }
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{FILE}"
        with urllib.request.urlopen(url,timeout=30) as f:original=f.read()
        if hashlib.sha256(original).hexdigest()!=EXPECTED_SHA:raise ValueError("WRONG_ORIGINAL_SHA")
        all_forms=top_level(original.decode())
        clauses=[f for f in all_forms if re.match(r"^\(assert\s",f)]
        if len(clauses)!=9:raise ValueError("WRONG_ORIGINAL_ASSERT_COUNT")
        decls=[f for f in all_forms if f.startswith("(declare-fun")]
        names=re.findall(r"\(declare-fun\s+\|([^|]+)\|",original.decode())
        if sorted(names)!=sorted([*WITNESS.keys(),"CHC_COMP_FALSE"]):
            raise ValueError("DECLARATION_SIGNATURE_NAME_MISMATCH")
        record["actual_source_sha_verified"]=True
        record["source_relation_names"]=names
        record["original_assertions"]=len(clauses)
        prefix=definitions()
        checked=[]
        for i,rule in enumerate(clauses,1):
            formula=rule[len("(assert"):-1].strip()
            chk=check_one(formula,prefix)
            checked.append({"original_rule":i,**chk})
            if chk["result"]!="unsat":break
        record["original_clause_receipts"]=checked
        record["independently_certified_original"]=sum(x["result"]=="unsat" for x in checked)
        record["candidate_complete_certified"]=record["independently_certified_original"]==9
        if record["candidate_complete_certified"]:
            # Verify original error goal actually matters. Replacing final
            # inv_main26 by true must admit a SAT counterexample in clause 9.
            tampered=definitions({"inv_main26":(WITNESS["inv_main26"][0],"true")})
            ninth=clauses[-1][len("(assert"):-1].strip()
            neg=check_one(ninth,tampered)
            record["negative_control_forced_true_final_relation"]=neg
            if neg["result"]!="sat":
                record["status"]="CERTIFICATE_REJECTED_NO_NEGATIVE_CONTROL"
            else:
                record["status"]="CLASSICAL_ORIGINAL_9_OF_9_CERTIFIED"
        else:
            record["status"]="CLASSICAL_WITNESS_REJECTED_OR_INCOMPLETE"
    except Exception as e:
        record["status"]="BLOCKED_ERROR"
        record["error"]=type(e).__name__+":"+str(e)[:600]
    record["elapsed_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    print("REAL_SQUARE_FULL_PROOF",record["status"])
    print("SOURCE_CLAUSES",record.get("independently_certified_original"),"/9")
    print("NEUMANN_GLOBAL_Q",record["global_q1_q7"])

if __name__=="__main__":main()
