"""Actual original RustHorn Lists-3: enumerate 27 signed delta coefficients.

FULL original 12-rule proof using recursive list fold + state delta relation.
Post-inspection CLASSICAL synthesis of 3 signs within HUMAN-SUPPLIED grammar.
No learned model; no global Q3/Q4/Q7 claim.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from time import perf_counter_ns
from urllib.request import urlopen

import z3

REV="e5a86a1ad252fe1df75e06814769ec1d14540032"
NAME="lists-3-inc-some-safe.smt2"
SHA="caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d"
HOLE="(= (+ (FGSR_DL m) (FGSR_DI h) (FGSR_DL r)) (FGSR_DI n))"
WITNESS=r"""
(define-fun-rec FGSR_SUM ((l %List)) Int
 (ite (= l %List-1) 0 (+ (%List-0.0 l) (FGSR_SUM (%List-0.1 l)))))
(define-fun FGSR_DL ((m ~Mut<%List>)) Int
 (- (FGSR_SUM (~ret<%List> m)) (FGSR_SUM (~cur<%List> m))))
(define-fun FGSR_DI ((m ~Mut<Int>)) Int
 (- (~ret<Int> m) (~cur<Int> m)))
(define-fun %sum ((l %List) (n Int)) Bool (= n (FGSR_SUM l)))
(define-fun %sum.0 ((l %List) (n Int)) Bool (= n (FGSR_SUM l)))
(define-fun %take_some ((m ~Mut<%List>) (n ~Mut<Int>)) Bool
 (= (FGSR_DL m) (FGSR_DI n)))
(define-fun %take_some.0 ((m ~Mut<%List>) (n ~Mut<Int>)) Bool
 (= (FGSR_DL m) (FGSR_DI n)))
(define-fun %take_some.4
 ((m ~Mut<%List>)(h ~Mut<Int>)(r ~Mut<%List>)(flag Bool)(n ~Mut<Int>)) Bool
 (= (+ (FGSR_DL m) (FGSR_DI h) (FGSR_DL r)) (FGSR_DI n)))
(define-fun %main.4
 ((l %List)(oldsum Int)(changed ~Mut<Int>)(newsum Int)(bad Bool)(ret Bool)) Bool
 (and (= (~ret<Int> changed) (~cur<Int> changed)) (= bad ret)))
(define-fun %main ((ret Bool)) Bool (not ret))
"""

def forms(raw):
    out=[];depth=0;start=None;comment=False
    for i,c in enumerate(raw):
        if c=="\n":comment=False
        if comment:continue
        if c==";":comment=True;continue
        if c=="(":
            if depth==0:start=i
            depth+=1
        if c==")":
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_ORIGINAL")
            if depth==0:out.append(raw[start:i+1])
    if depth!=0:raise ValueError("INCOMPLETE_ORIGINAL")
    return out

def source():
    with urlopen(f"https://raw.githubusercontent.com/chc-comp/rust-horn/{REV}/{NAME}",timeout=30) as resp:
        raw=resp.read()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError("PINNED_ORIGINAL_SHA_MISMATCH")
    allforms=forms(raw.decode())
    datatypes=[f for f in allforms if f.startswith("(declare-datatypes")]
    rules=[f for f in allforms if f.startswith("(assert ")]
    if len(datatypes)!=4 or len(rules)!=12:
        raise ValueError("ORIGINAL_SOURCE_SHAPE_CHANGED")
    if sum(f=="(check-sat)" for f in allforms)!=1:
        raise ValueError("ORIGINAL_CHECKSAT_CHANGED")
    return datatypes,rules,len(raw)

def signed_terms(coeff):
    terms=[]
    for x,n in zip(coeff,("(FGSR_DL m)","(FGSR_DI h)","(FGSR_DL r)")):
        if x==1:terms.append(n)
        elif x==-1:terms.append(f"(- {n})")
        elif x!=0:raise ValueError("UNREGISTERED_SIGN")
    if len(terms)==0:return "0"
    if len(terms)==1:return terms[0]
    return "(+ "+" ".join(terms)+")"

def candidate(coeff):
    if WITNESS.count(HOLE)!=1:raise ValueError("GRAMMAR_HOLE_MISMATCH")
    return WITNESS.replace(HOLE,f"(= {signed_terms(coeff)} (FGSR_DI n))")

def refute(original,datatypes,w):
    if not original.startswith("(assert ") or not original.endswith(")"):
        raise ValueError("SOURCE_ASSERTION_CHANGED")
    body=original[len("(assert "):-1]
    smt="(set-logic ALL)\n"+"\n".join(datatypes)+"\n"+w+"\n"
    parsed=z3.parse_smt2_string(smt+"(assert (not "+body+"))\n")
    if len(parsed)!=1:raise ValueError("NEGATED_ORIGINAL_NOT_ONE")
    solver=z3.Solver();solver.set(timeout=5000);solver.add(parsed[0])
    return str(solver.check())

def run():
    ds,rs,nbytes=source();start=perf_counter_ns()
    rows=[]
    for coeff in itertools.product((-1,0,1),repeat=3):
        w=candidate(coeff);out=[]
        for clause in rs:
            v=refute(clause,ds,w);out.append(v)
            if v!="unsat":break
        rows.append({"coefficients":list(coeff),"original_rule_results":out,
                     "all_originals_proved":len(out)==12 and out==["unsat"]*12})
    proven=[r for r in rows if r["all_originals_proved"]]
    for r in proven:
        c=r["coefficients"];w=candidate(c)
        assert [refute(rule,ds,w) for rule in rs]==["unsat"]*12
    if len(proven)==1:
        modified=rs[-1].replace("(%main true)","(%main false)")
        if modified==rs[-1]:raise ValueError("SOURCE_GOAL_MUTATION_FAILED")
        goal_result=refute(modified,ds,candidate(proven[0]["coefficients"]))
    else:goal_result="NOT_RUN"
    results={"date":"2026-10-18","status":"ONE_POSTHOC_CLASSICAL_AUTOSYNTH_ORIGINAL_12_PROOF" if
           len(proven)==1 and goal_result=="sat" and proven[0]["coefficients"]==[1,1,1]
           else "NOT_ADMITTED",
           "source_sha256":SHA,"upstream_commit":REV,"source_bytes":nbytes,
           "original_rule_count":len(rs),"quantified_original_unmodified":True,
           "z3_version":z3.get_version_string(),
           "candidate_count":len(rows),
           "complete_certificates":[r["coefficients"] for r in proven],
           "original_rule_counts_checked":[len(r["original_rule_results"]) for r in rows],
           "rejected_candidates":sum(not r["all_originals_proved"] for r in rows),
           "negative_goal_mutation":goal_result,
           "zero_coefficients":next(r for r in rows if r["coefficients"]==[0,0,0]),
           "model_calls":0,"training_steps":0,
           "wall_ms":(perf_counter_ns()-start)/1e6,
           "human_supplied_math_language":True,
           "global_q1_q7":"OPEN",
           "limit":"Seven source-specific predicate forms plus recursive fold/delta grammar are designed post-inspection; only three coefficients are learned by classical exhaustive search. This is NOT neural Q3/10x or a new blind external benchmark."}
    return results

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True,type=Path)
    args=p.parse_args();r=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2)+"\n")
    print("Q3E",r["status"],r["candidate_count"],r["complete_certificates"],r["negative_goal_mutation"])
    if r["status"]!="ONE_POSTHOC_CLASSICAL_AUTOSYNTH_ORIGINAL_12_PROOF":raise SystemExit(2)
