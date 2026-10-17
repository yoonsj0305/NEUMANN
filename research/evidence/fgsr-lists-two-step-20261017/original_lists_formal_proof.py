"""Opened real RustHorn Lists-4: candidate sum-delta zipper law.
Human-designed AFTER seeing original. Never claim learned Q3 or blind transfer.
All original 12 assertions independently checked, no deletion.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, pathlib, time

HERE=pathlib.Path(__file__).resolve().parent
CORE35=HERE.parent/"core35-20261016"/"core35.py"
SOURCE_NAME="lists-4-inc-some2-safe.smt2"
REV="e5a86a1ad252fe1df75e06814769ec1d14540032"
SHA256="a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db"
BLOB="5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9"
TUP="~Tup<~Mut<Int>-~Mut<%List>>"
WITNESS=r"""
(define-fun-rec FGSR_SUM ((l %List)) Int
 (ite (= l %List-1) 0 (+ (%List-0.0 l) (FGSR_SUM (%List-0.1 l)))))
(define-fun FGSR_DELTA ((q ~Tup<~Mut<Int>-~Mut<%List>>)) Int
 (+ (- (~ret<Int> (~at0/<~Mut<Int>-~Mut<%List>> q))
       (~cur<Int> (~at0/<~Mut<Int>-~Mut<%List>> q)))
    (- (FGSR_SUM (~ret<%List> (~at1/<~Mut<Int>-~Mut<%List>> q)))
       (FGSR_SUM (~cur<%List> (~at1/<~Mut<Int>-~Mut<%List>> q))))))
(define-fun %sum ((l %List) (n Int)) Bool (= n (FGSR_SUM l)))
(define-fun %sum.0 ((l %List) (n Int)) Bool (= n (FGSR_SUM l)))
(define-fun %take_some_rest
 ((m ~Mut<%List>) (q ~Tup<~Mut<Int>-~Mut<%List>>)) Bool
 (= (- (FGSR_SUM (~ret<%List> m)) (FGSR_SUM (~cur<%List> m))) (FGSR_DELTA q)))
(define-fun %take_some_rest.0
 ((m ~Mut<%List>) (q ~Tup<~Mut<Int>-~Mut<%List>>)) Bool
 (= (- (FGSR_SUM (~ret<%List> m)) (FGSR_SUM (~cur<%List> m))) (FGSR_DELTA q)))
(define-fun %take_some_rest.4
 ((m ~Mut<%List>) (h ~Mut<Int>) (rest ~Mut<%List>) (flag Bool)
  (q ~Tup<~Mut<Int>-~Mut<%List>>)) Bool
 (and
   (= (~ret<%List> m) (~cur<%List> m))
   (= (FGSR_DELTA q)
      (+ (- (~ret<Int> h) (~cur<Int> h))
         (- (FGSR_SUM (~ret<%List> rest)) (FGSR_SUM (~cur<%List> rest)))))))
(define-fun %main.5
 ((l %List) (originalSum Int) (m1 ~Mut<Int>) (r1 ~Mut<%List>)
  (m2 ~Mut<Int>) (newSum Int) (bad Bool) (ret Bool)) Bool
 (= bad ret))
(define-fun %main ((ret Bool)) Bool (not ret))
"""

def original_engine():
    spec=importlib.util.spec_from_file_location("neumann_core35_native",CORE35)
    if spec is None or spec.loader is None:raise RuntimeError("MISSING_ORIGINAL_ENGINE")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def source_identity(data):
    g=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()
    return {"sha256":hashlib.sha256(data).hexdigest(),"blob":g}

def split(source,original):
    expr=original.top_level(source)
    dtype=[e for e in expr if e.startswith("(declare-datatypes")]
    rules=[e for e in expr if e.startswith("(assert ")]
    if len(dtype)!=5 or len(rules)!=12:raise ValueError(f"UNEXPECTED_ORIGINAL_SHAPE:{len(dtype)}:{len(rules)}")
    if sum(e.startswith("(check-sat") for e in expr)!=1:raise ValueError("MISSING_CHECK_SAT")
    return dtype,rules

def negated_source(dtype,assertion,witness=WITNESS):
    prefix="(set-logic ALL)\\n"+"\\n".join(dtype)+"\\n"+witness+"\\n"
    return prefix+"(assert (not "+assertion[len("(assert "):-1]+"))\\n(check-sat)\\n"

def run(source,timeout_s):
    original=original_engine()
    data=source.read_bytes()
    ident=source_identity(data)
    if ident!={"sha256":SHA256,"blob":BLOB}:raise ValueError("ORIGINAL_SOURCE_HASH_MISMATCH")
    dtype,rules=split(data.decode(),original)
    result={"experiment":"FGSR Lists-4 original source posthoc candidate",
       "source":SOURCE_NAME,"source_git_commit":REV,"source_sha256":SHA256,
       "source_git_blob":BLOB,"source_bytes":len(data),"original_clause_count":len(rules),
       "human_designed_after_inspection":True,"neural_calls":0,"q1_q7":"OPEN",
       "status":"NOT_PROVEN","original_verdicts":[],"original_wall_ms":[],
       "negative_controls":{}}
    for clause in rules:
        actual=original.one(negated_source(dtype,clause),timeout_s)
        result["original_verdicts"].append(actual["verdict"])
        result["original_wall_ms"].append(actual["wall_ms"])
    # Corrupted helper: same original assertions, different unsound interpretation.
    poison=WITNESS.replace("(FGSR_DELTA q)))","(+ 1 (FGSR_DELTA q))))",1)
    if poison==WITNESS:raise ValueError("POISON_DID_NOT_CHANGE")
    # Candidate poison is expected to be syntactically valid but must not certify.
    poisoned=original.one(negated_source(dtype,rules[6],poison),timeout_s)
    result["negative_controls"]["corrupt_sum_delta_witness"]=poisoned["verdict"]
    # A logically different goal is not licensed by the verified original.
    changed=rules[-1].replace("(%main true) false","(%main false) false")
    if changed==rules[-1]:raise ValueError("GOAL_MUTATION_FAILED")
    altered=original.one(negated_source(dtype,changed),timeout_s)
    result["negative_controls"]["changed_goal"]=altered["verdict"]
    complete=all(x=="unsat" for x in result["original_verdicts"])
    negative=all(x=="sat" for x in result["negative_controls"].values())
    result["status"]=("OPENED_ORIGINAL_FORMAL_CERTIFICATE_PASS"
                      if complete and negative else "ABSTAIN_CERTIFICATE_INCOMPLETE")
    result["limitations"]=(
      "Pure classical/HUMAN formula proposed after inspecting opened source; "
      "no neural learning or blind transfer. Individual clauses are exact universal "
      "original assertions; UNKNOWN/TIMEOUT never pass. No complete human development "
      "cost, frontier equivalence or end-to-end 10x comparison.")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--per-rule-cap",type=int,default=8)
    args=p.parse_args()
    result=run(args.source,args.per_rule_cap)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\\n")
    print("REAL_ORIGINAL",result["status"])
    print("SOURCE_CLAUSES",result["original_verdicts"])
    print("NEGATIVES",result["negative_controls"])
    print("GLOBAL_QUESTIONS",result["q1_q7"])
    if result["status"]!="OPENED_ORIGINAL_FORMAL_CERTIFICATE_PASS":raise SystemExit(2)

if __name__=="__main__":main()
