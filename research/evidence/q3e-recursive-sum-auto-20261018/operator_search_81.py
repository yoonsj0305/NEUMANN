"""Independent bounded classical program search: 3 list folds × 27 signed deltas.

On the already opened original RustHorn Lists-3 only. Both operator families
were provided by a human after source inspection. Absolutely NO neural model.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
from time import perf_counter_ns

from first_independent_original import (
    WITNESS, refute, source, signed_terms, SHA, REV
)

RECURSIVE="""(define-fun-rec FGSR_SUM ((l %List)) Int
 (ite (= l %List-1) 0 (+ (%List-0.0 l) (FGSR_SUM (%List-0.1 l)))))"""
FOLDS={
    "constant_zero":"(define-fun-rec FGSR_SUM ((l %List)) Int 0)",
    "head_only":"""(define-fun-rec FGSR_SUM ((l %List)) Int
 (ite (= l %List-1) 0 (%List-0.0 l)))""",
    "recursive_sum":RECURSIVE,
}
HOLE="(= (+ (FGSR_DL m) (FGSR_DI h) (FGSR_DL r)) (FGSR_DI n))"

def compose(fold,signs):
    if WITNESS.count(RECURSIVE)!=1 or WITNESS.count(HOLE)!=1:
        raise ValueError("CANDIDATE_LANGUAGE_DRIFT")
    changed=WITNESS.replace(RECURSIVE, FOLDS[fold])
    return changed.replace(HOLE, f"(= {signed_terms(signs)} (FGSR_DI n))")

def run():
    dt,original,source_bytes=source()
    start=perf_counter_ns()
    records=[]
    for fold in FOLDS:
        for signs in itertools.product((-1,0,1),repeat=3):
            w=compose(fold,signs)
            checked=[]
            for clause in original:
                result=refute(clause,dt,w)
                checked.append(result)
                if result!="unsat":break
            if checked and checked[-1] not in ("unsat","sat"):
                raise ValueError("UNKNOWN_PARSER_OR_SOLVER_NOT_EVIDENCE")
            records.append({"fold":fold,"coefficients":list(signs),
              "checked":len(checked),"first_nonproof":next(
                ({"index":i+1,"verdict":v} for i,v in enumerate(checked) if v!="unsat"),None),
              "full_original_certificate":checked==["unsat"]*12})
    approved=[r for r in records if r["full_original_certificate"]]
    if approved!=[{"fold":"recursive_sum","coefficients":[1,1,1],
                   "checked":12,"first_nonproof":None,
                   "full_original_certificate":True}]:
        raise ValueError("PREDECLARED_UNIQUE_RESULT_NOT_REPRODUCED")
    checks=[refute(clause,dt,compose("recursive_sum",(1,1,1))) for clause in original]
    if checks!=["unsat"]*12:raise ValueError("FINAL_CERTIFICATE_DID_NOT_VERIFY")
    corrupt=original[-1].replace("(%main true)","(%main false)")
    if corrupt==original[-1]:raise ValueError("NEGATIVE_CONTROL_MISSING")
    poison=refute(corrupt,dt,compose("recursive_sum",(1,1,1)))
    if poison!="sat":raise ValueError("NEGATIVE_CONTROL_NOT_DETECTED")
    return {"status":"ONE_OF_81_POSTHOC_CLASSICAL_RELATIONAL_PROGRAMS_PROVEN",
        "upstream_commit":REV,"source_sha256":SHA,"source_bytes":source_bytes,
        "source_originals_unchanged":True,"original_rule_count":12,
        "candidate_count":len(records),"number_full_certificates":len(approved),
        "winning_program":approved[0],"final_all_rule_verdicts":checks,
        "goal_mutation":poison,"rejected_candidates":len(records)-len(approved),
        "all_other_candidates_have_sat_counterexample":all(
          r["first_nonproof"] and r["first_nonproof"]["verdict"]=="sat"
          for r in records if not r["full_original_certificate"]),
        "grammar_folds":list(FOLDS),"delta_values":[-1,0,1],
        "model_calls":0,"trained_parameters":0,"q1_q7":"OPEN",
        "whole_search_wall_ms":(perf_counter_ns()-start)/1e6,
        "science_boundary":"Recursive fold and general delta relation are supplied by a human after source inspection; only 1 of 81 pre-given compositions was auto-selected by classical enumeration, NOT learned new operator discovery or Q4."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=run()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3E_AUTOGRAMMAR",r["status"],r["candidate_count"],r["winning_program"],r["goal_mutation"])
