"""Q3: actual causal transfer of SOURCE-trained representation-selection policy.

No original-author TARGET data used. Entire source teaching file is frozen.
Teacher tasks 0:30 train the PRIOR; tasks 30:50 are disjoint evaluation.
Same ISA/grammar and same proposal budget A/C, extra A12 comparator.
Inspect independently heldout SOURCE examples only in the verifier,
not during policy.prepare(). ALL exact counts are SOURCE-only.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_representation_policy import LearnedRepresentationPrior
from neumann1.q3_structural_invention import StructuralInventionPolicy

SCHEMA="NEUMANN.Q3.CAUSAL-SOURCE-DISCOVERY-CROSS-TASK-v1"


def _json(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def _exact(code,train,check,runner):
    inputs=[x for x,y in (*train,*check)]
    out=runner.evaluate(code,inputs)
    if out.status!="EXECUTED" or len(out.outputs)!=len(inputs):
        return False
    return all(source_same_value(v,y)
               for v,(_,y) in zip(out.outputs,(*train,*check)))


def compare(source_path,out,*,teacher_count=30,heldout_count=20):
    p=Path(source_path)
    data=json.loads(p.read_text())
    if (data.get("schema")!="NEUMANN.Q3.ORIGINAL-ARC2-SOURCE-TEACHING.v1"
            or data.get("upstream_revision")!=
               "f3283f727488ad98fe575ea6a5ac981e4a188e49"
            or data.get("original_source_count")!=50
            or not data.get("no_target_gold_in_payload")
            or teacher_count!=30 or heldout_count!=20):
        raise ValueError("unexpected SOURCE-only pre-registered experiment")
    records=data["records"]
    assert len(records)==50
    assert len({r["source_id"] for r in records})==50
    teacher=records[:teacher_count]
    testing=records[teacher_count:teacher_count+heldout_count]
    runner=IsolatedPython(max_seconds=8)
    trials=[(r["source_id"],r["source_train"],
             r["source_independent_checks"]) for r in teacher]
    learned=LearnedRepresentationPrior.learn_source_trials(
        trials,runner,max_episodes=50)
    print("Q3_DISJOINT_SOURCE_REPRESENTATION_TRAIN",
          learned.evidence(),flush=True)
    outcome=[]
    for rec in testing:
        train=tuple((x,y) for x,y in rec["source_train"])
        check=tuple((x,y) for x,y in rec["source_independent_checks"])
        row={"id":rec["source_id"],"modes":{}}
        for mode,prior in (("A",None),("C",learned)):
            policy=StructuralInventionPolicy(
                max_states=6500,max_evaluations=250000,
                max_candidates=12,representation_prior=prior)
            policy.prepare(train)
            candidates=policy.receipt.candidates
            verified={}
            for limit in ((2,12) if mode=="A" else (2,)):
                first_pass=None
                for index,code in enumerate(candidates[:limit]):
                    if _exact(code,train,check,runner):
                        first_pass=index+1
                        break
                verified[str(limit)]={
                    "source_exact":first_pass is not None,
                    "first_verified_proposal":first_pass,
                    "actual_proposals_checked":min(
                        limit,len(candidates))}
            row["modes"][mode]={
                "verified":verified,
                "first_program_sha256":sha256(
                    candidates[0].encode()).hexdigest() if candidates else None,
                "first_candidate_excerpt":candidates[0][:120]
                    if candidates else None,
            }
        outcome.append(row)
        print("Q3_CROSS_TASK_HIDDEN_SOURCE",row["id"],{
            m:{k:v["source_exact"] for k,v in x["verified"].items()}
            for m,x in row["modes"].items()},flush=True)
        Path(str(out)+".SOURCE_PARTIAL").write_text(
            _json({"source_only":True,"results":outcome})+"\n")
    summary={
        "tasks":len(outcome),
        "A2":sum(x["modes"]["A"]["verified"]["2"]["source_exact"]
                 for x in outcome),
        "A12":sum(x["modes"]["A"]["verified"]["12"]["source_exact"]
                 for x in outcome),
        "C2":sum(x["modes"]["C"]["verified"]["2"]["source_exact"]
                 for x in outcome),
        "C2_only_vs_A2":sum(
            x["modes"]["C"]["verified"]["2"]["source_exact"]
            and not x["modes"]["A"]["verified"]["2"]["source_exact"]
            for x in outcome),
        "C2_only_vs_A12":sum(
            x["modes"]["C"]["verified"]["2"]["source_exact"]
            and not x["modes"]["A"]["verified"]["12"]["source_exact"]
            for x in outcome),
        "no_original_target_gold":True,
        "scientific_scope":"DISJOINT_AUTHOR_TRAIN_SOURCE_ONLY",
        "q3_global":"OPEN",
        "frozen_source_sha256":sha256(p.read_bytes()).hexdigest(),
        "learned_prior":learned.evidence(),
    }
    Path(out).write_text(_json(
        {"schema":SCHEMA,"summary":summary,"source":outcome})+"\n")
    print("Q3_CAUSAL_SOURCE_CROSS_TASK_VERDICT",
          _json(summary),flush=True)


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--frozen-source",required=True)
    a.add_argument("--out",required=True)
    opts=a.parse_args()
    compare(opts.frozen_source,opts.out)
