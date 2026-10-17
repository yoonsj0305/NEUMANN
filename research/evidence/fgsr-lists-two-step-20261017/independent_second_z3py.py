"""Independent second REPARSE of pinned original Lists-4 safety certificate.

Uses z3py Solver()/parse_smt2_string on the complete untouched quantified
original clauses. Does NOT invoke the first native proof-checker or its parser.
Reads the frozen candidate as source-level AST literal, without executing it.
Z3 backend shared, so this is independent plumbing, not independent theorem prover.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns
import z3

SOURCE_SHA="a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db"
SOURCE_BLOB="5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9"
HERE=Path(__file__).resolve().parent
CERT_SOURCE=HERE/"original_lists_formal_proof.py"

def top_forms(raw):
    result=[]; start=None; depth=0; comment=False
    for pos,ch in enumerate(raw):
        if ch=="\n":comment=False
        if comment:continue
        if ch==";":comment=True;continue
        if ch=="(":
            if depth==0:start=pos
            depth+=1
        elif ch==")":
            depth-=1
            if depth<0:raise ValueError("NEGATIVE_DEPTH")
            if depth==0:result.append(raw[start:pos+1])
    if depth!=0:raise ValueError("NONZERO_FINAL_DEPTH")
    return result

def frozen_certificate():
    text=CERT_SOURCE.read_text()
    tree=ast.parse(text,filename=str(CERT_SOURCE))
    for item in tree.body:
        if isinstance(item,ast.Assign) and any(
          isinstance(x,ast.Name) and x.id=="WITNESS" for x in item.targets):
            value=ast.literal_eval(item.value)
            if not isinstance(value,str) or len(value)<100:raise ValueError("BAD_CERTIFICATE_LITERAL")
            return value
    raise ValueError("NO_FROZEN_CERTIFICATE")

def make_formula(dtypes,witness,rule):
    if not rule.startswith("(assert ") or not rule.endswith(")"):
        raise ValueError("BAD_ORIGINAL_ASSERTION")
    rule_body=rule[len("(assert "):-1]
    return "(set-logic ALL)\n"+"\n".join(dtypes)+"\n"+witness+"\n(assert (not "+rule_body+"))\n"

def check_one(dtypes,witness,original_rule):
    start=perf_counter_ns()
    solver=z3.Solver()
    solver.set(timeout=9000)
    parsed=z3.parse_smt2_string(make_formula(dtypes,witness,original_rule))
    if len(parsed)!=1:raise ValueError("SMT_SOURCE_DID_NOT_PARSE_AS_ONE_NEGATION")
    solver.add(parsed)
    answer=solver.check()
    status="unsat" if answer==z3.unsat else ("sat" if answer==z3.sat else "unknown")
    return {"status":status,"wall_ms":round((perf_counter_ns()-start)/1e6,3)}

def audit(source_path):
    raw=source_path.read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
    if sha!=SOURCE_SHA or blob!=SOURCE_BLOB:raise ValueError("PINNED_ORIGINAL_MISMATCH")
    forms=top_forms(raw.decode("utf-8"))
    dtypes=[x for x in forms if x.startswith("(declare-datatypes")]
    rules=[x for x in forms if x.startswith("(assert ")]
    if len(dtypes)!=5 or len(rules)!=12:raise ValueError("ORIGINAL_SHAPE_CHANGED")
    if sum(x.startswith("(check-sat") for x in forms)!=1:raise ValueError("MISSING_CHECK_SAT")
    cert=frozen_certificate()
    result={"scope":"opened_source_second_reparse_no_neural","q1_q7":"OPEN",
        "source_sha256":sha,"source_blob":blob,"certificate_sha256":hashlib.sha256(cert.encode()).hexdigest(),
        "verifier":"z3py-4.13.3.0", "z3_version":z3.get_version_string(),
        "source_original_assertions":12,"checks":[],"negative_controls":{},"status":"ABSTAIN"}
    for rule in rules:
        result["checks"].append(check_one(dtypes,cert,rule))
    if len(result["checks"])!=12:raise ValueError("NOT_ALL_ORIGINALS_CHECKED")
    # A weaker witness missing essential caller constraints must fail, as in
    # first registered developer failure. This changes the witness, not source.
    marker="""(and
   (= (~ret<Int> m1) (~cur<Int> m1))
   (= (~ret<%List> r1) (~cur<%List> r1))
   (= (~ret<Int> m2) (~cur<Int> m2))
   (= bad ret)))"""
    if marker not in cert:raise ValueError("UNEXPECTED_FROZEN_MAIN_CERTIFICATE")
    weak=cert.replace(marker,"(= bad ret))")
    weak_check=check_one(dtypes,weak,rules[0])
    result["negative_controls"]["missing_caller_constraints"]=weak_check["status"]
    changed=rules[-1].replace("(%main true) false","(%main false) false")
    if changed==rules[-1]:raise ValueError("GOAL_MUTATION_MISSING")
    changed_check=check_one(dtypes,cert,changed)
    result["negative_controls"]["changed_goal"]=changed_check["status"]
    if all(c["status"]=="unsat" for c in result["checks"]) and all(
        x=="sat" for x in result["negative_controls"].values()):
        result["status"]="SECOND_Z3PY_REPARSE_ORIGINAL_12_OF_12_CERTIFIED"
    result["limitations"]="Same Z3 underlying engine, independently authored parser and Python API; source and witness not blinded; learned Q3 Q4 Q7 OPEN."
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=audit(a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("SECOND_PROOF",result["status"])
    print("TWELVE", [x["status"] for x in result["checks"]])
    print("NEGATIVE",result["negative_controls"])
    print("GLOBAL",result["q1_q7"])
    if result["status"]!="SECOND_Z3PY_REPARSE_ORIGINAL_12_OF_12_CERTIFIED":raise SystemExit(2)
