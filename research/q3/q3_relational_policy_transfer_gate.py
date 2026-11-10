"""Q3 prospective 100 actual AUTHOR SOURCE cross-task learned selection gate.

Prior is fitted on 30 disjoint AUTHOR SOURCE teachers from the old 50.
The frozen 100 original AUTHOR SOURCE tasks are never teacher episodes.
A2/A12/C2 all receive identical actual executable syntax and limits,
including relational set-comprehension grammar. Original TEST gold is never
read, and C-only SOURCE is not global Q3 proof.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_representation_policy import LearnedRepresentationPrior
from neumann1.q3_structural_invention import StructuralInventionPolicy


def _digest(p):
    return sha256(Path(p).read_bytes()).hexdigest()


def _canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def _source_exact(code,train,checks,runner):
    data=(*train,*checks)
    observed=runner.evaluate(code,[x for x,y in data])
    if observed.status!="EXECUTED" or len(observed.outputs)!=len(data):
        return False
    return all(source_same_value(got,y) for got,(_,y)
               in zip(observed.outputs,data))


def evaluate(teacher_path,cohort_path,out):
    old=json.loads(Path(teacher_path).read_text())
    prospective=json.loads(Path(cohort_path).read_text())
    if (old.get("original_source_count")!=50
            or prospective.get("original_source_count")!=100
            or old.get("no_target_gold_in_payload") is not True
            or prospective.get("no_target_gold_in_payload") is not True
            or prospective.get("source_scope")!=
                 "PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"):
        raise ValueError("fixed disjoint original AUTHOR SOURCE artifacts required")
    train_ids={r["source_id"] for r in old["records"]}
    test_ids={r["source_id"] for r in prospective["records"]}
    if len(train_ids)!=50 or len(test_ids)!=100 or train_ids&test_ids:
        raise ValueError("train/test AUTHOR IDs overlap")
    runner=IsolatedPython(max_seconds=8)
    teacher=old["records"][:30]
    prior=LearnedRepresentationPrior.learn_source_trials(
        [(t["source_id"],t["source_train"],
          t["source_independent_checks"]) for t in teacher],
        runner,max_episodes=30)
    rows=[]
    for index,record in enumerate(prospective["records"]):
        pairs=record["source_pairs"]
        row={"id":record["source_id"],"source_examples":len(pairs)}
        if len(pairs)<3:
            row["status"]="ABSTAIN_INDEPENDENT_SOURCE_UNAVAILABLE"
            row["A2"]=False;row["A12"]=False;row["C2"]=False
            rows.append(row)
            continue
        train=tuple((x,y) for x,y in pairs[:-1])
        checks=tuple((x,y) for x,y in pairs[-1:])
        results={}
        for mode,selection_prior in (("A",None),("C",prior)):
            policy=StructuralInventionPolicy(
                max_states=6500,max_evaluations=250000,
                max_candidates=12,representation_prior=selection_prior)
            policy.prepare(train)
            proposals=policy.receipt.candidates
            success_at=None
            for attempt,code in enumerate(
                    proposals[:12 if mode=="A" else 2],start=1):
                if _source_exact(code,train,checks,runner):
                    success_at=attempt
                    break
            results[mode]={
                "first_source_verified":success_at,
                "proposed":len(proposals)}
        k=results["A"]["first_source_verified"]
        row.update({
            "status":"SOURCE_EVALUATED",
            "A2":k is not None and k<=2,
            "A12":k is not None and k<=12,
            "C2":results["C"]["first_source_verified"] is not None,
            "A_candidate_count":results["A"]["proposed"],
            "C_candidate_count":results["C"]["proposed"],
        })
        rows.append(row)
        if (index+1)%20==0:
            print("Q3_100_PROSPECTIVE_POLICY_PROGRESS",index+1,flush=True)
    summ={
        "source_cohort":100,
        "source_eligible":sum(r["status"]=="SOURCE_EVALUATED" for r in rows),
        "A2":sum(r["A2"] for r in rows),
        "A12":sum(r["A12"] for r in rows),
        "C2":sum(r["C2"] for r in rows),
        "C2_exclusive_vs_A2":sum(r["C2"] and not r["A2"] for r in rows),
        "C2_exclusive_vs_A12":sum(r["C2"] and not r["A12"] for r in rows),
        "prior_from_30_disjoint_AUTHOR_SOURCE":prior.evidence(),
        "original_target_gold_read":False,
        "grammar":"ALL_SHARED_RELATIONAL_CANDIDATE_FAMILIES",
        "q3_global":"OPEN",
        "previous_teacher_registry_sha256":_digest(teacher_path),
        "prospective_original_source_sha256":_digest(cohort_path),
    }
    Path(out).write_text(_canonical({
        "schema":"NEUMANN.Q3.RELATIONAL-CROSS-TASK-100-SOURCE.v1",
        "summary":summ,"records":rows})+"\n")
    print("Q3_REAL_100_ORIGINAL_SOURCE_LEARNED_C_ABLATION",{
        k:v for k,v in summ.items() if k not in (
            "prior_from_30_disjoint_AUTHOR_SOURCE",)},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--teacher",required=True)
    p.add_argument("--cohort",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    evaluate(a.teacher,a.cohort,a.out)
