"""Q3 one learned open-program model vs identical pretrained open-program model.

Actual original AUTHOR SOURCE, never author TARGET TEST. Teacher IDs from
old 50 source authors are disjoint from these 100 source authors. Freeze
the same base weight SHA, identical prompt, identical SOURCE check oracle
and proposal budget. This measures learned repair policy effect, not
end-to-end frontier-level Q3 generalization.
"""
from __future__ import annotations

import argparse
import gc
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import (
    GenerativeProgramInventor,IsolatedPython,
)
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy


def _canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def compare(cohort,*,model_revision,adapter,out,limit=6,max_proposals=2):
    source=json.loads(Path(cohort).read_text())
    manifest=json.loads(
        (Path(adapter)/"neumann_source_training_manifest.json").read_text())
    if (source.get("original_source_count")!=100
            or source.get("no_target_gold_in_payload") is not True
            or source.get("source_scope")!=
                "PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"
            or manifest.get("base_model")!=
                "Qwen/Qwen2.5-Coder-0.5B-Instruct"
            or manifest.get("model_revision")!=model_revision
            or manifest.get("training_objective")!="source_repair"
            or manifest.get("repair_examples",0)<1
            or not 1<=limit<=100 or not 1<=max_proposals<=8):
        raise ValueError("wrong frozen SOURCE-only trained repair intervention")
    selected=[r for r in source["records"]
              if 3<=len(r["source_pairs"])<=32]
    selected.sort(key=lambda r:sha256(
        ("NEUMANN.Q3.MODEL_REPAIR.ABLATION.20261110/"+r["source_id"]).encode()
        ).hexdigest())
    selected=selected[:limit]
    if len(selected)!=limit:
        raise ValueError("insufficient prospective originals")
    runner=IsolatedPython(max_seconds=8)
    outcome={}
    for name,path in (("A_pretrained",None),("C_source_repair",adapter)):
        policy=LocalCausalCodePolicy(
            model_revision=model_revision,adapter_path=path,
            max_new_tokens=320,temperature=0.3,seed=1007)
        for task in selected:
            pairs=task["source_pairs"]
            discovery=GenerativeProgramInventor(
                policy,runner,max_proposals=max_proposals
            ).discover(
                pairs[:-1],independent_source_checks=pairs[-1:])
            row=outcome.setdefault(task["source_id"],{
                "id":task["source_id"],"source_examples":len(pairs)})
            row[name]=bool(discovery.verified)
            row[name+"_program_sha256"]=discovery.frozen_sha256
            row[name+"_attempts"]=len(discovery.attempts)
            row[name+"_attempt_statuses"]=[
                a.status for a in discovery.attempts]
            row[name+"_max_train_correct"]=max(
                (a.source_correct for a in discovery.attempts),default=0)
            row[name+"_train_pair_count"]=len(pairs)-1
            row[name+"_abstention_reason"]=(
                discovery.status if not discovery.verified else None)
            print("Q3_MODEL_SOURCE_TRANSFER",name,task["source_id"],
                  {"source_verified":discovery.verified,
                   "statuses":row[name+"_attempt_statuses"],
                   "best_train":row[name+"_max_train_correct"],
                   "train_count":len(pairs)-1,
                   "outcome":discovery.status},flush=True)
        del policy
        gc.collect()
    rows=[outcome[t["source_id"]] for t in selected]
    summary={
        "schema":"NEUMANN.Q3.OPEN-PROGRAM-REPAIR-LEARNING-CROSS-TASK.v1",
        "frozen_cohort_sha256":sha256(Path(cohort).read_bytes()).hexdigest(),
        "model_revision":model_revision,
        "source_originals":len(rows),
        "proposals_per_task":max_proposals,
        "A_exact_source":sum(r["A_pretrained"] for r in rows),
        "C_exact_source":sum(r["C_source_repair"] for r in rows),
        "C_exclusive_source":sum(
            r["C_source_repair"] and not r["A_pretrained"] for r in rows),
        "A_exclusive_source":sum(
            r["A_pretrained"] and not r["C_source_repair"] for r in rows),
        "original_TEST_gold_accessed":False,
        "two_independent_semantic_authors_tested":False,
        "q3_global":"OPEN",
    }
    Path(out).write_text(_canon({"summary":summary,"rows":rows})+"\n")
    print("Q3_REAL_NEURAL_SOURCE_REPAIR_ABLATION",summary,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--cohort",required=True)
    p.add_argument("--model-revision",required=True)
    p.add_argument("--adapter",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--limit",type=int,default=6)
    p.add_argument("--max-proposals",type=int,default=2)
    a=p.parse_args()
    compare(a.cohort,model_revision=a.model_revision,adapter=a.adapter,
            out=a.out,limit=a.limit,max_proposals=a.max_proposals)
