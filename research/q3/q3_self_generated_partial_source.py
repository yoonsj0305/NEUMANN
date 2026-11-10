"""Collect SOURCE-only self-generated causal preferences without answer teachers.

Sample programs from SAME frozen policy; execute on authorized SOURCE train
demonstrations; compare generic typed JSON structural error reduction against
identity. Two wrong programs may create a learning preference, NEVER a Q3
certificate. Independent checks and original TARGET gold are not accessed.
"""
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.q3_prompt_contract import source_discovery_prompt,SourceContextOverflow
from neumann1.open_program_inventor import IsolatedPython,validate_code,UnsafeProposal
from neumann1.q3_semantic_credit import preference_from_source


def _dump(v):
    return json.dumps(v,ensure_ascii=True,sort_keys=True,
                      separators=(",",":"),allow_nan=False)


def collect(source_file,*,model_revision,out,report,max_tasks=12,
            proposals_per_task=3):
    dataset=json.loads(Path(source_file).read_text())
    if (dataset.get("original_source_count")!=50 or
        dataset.get("no_target_gold_in_payload") is not True or
        not 1<=max_tasks<=30 or not 2<=proposals_per_task<=5):
        raise ValueError("frozen SOURCE-only original author registry required")
    ids=[r["source_id"] for r in dataset["records"]]
    if len(set(ids))!=50:raise ValueError("repeated source ID")
    tasks=sorted(dataset["records"],
        key=lambda r:hashlib.sha256((
            "Q3.ONE.CORE.SOURCE.PREFERENCE.PRECOMMIT/"+
            r["source_id"]).encode()).hexdigest())[:max_tasks]
    runner=IsolatedPython(max_seconds=8)
    model=LocalCausalCodePolicy(model_revision=model_revision,
        max_new_tokens=320,temperature=0.3,seed=1007,
        max_context_tokens=4096)
    collected=[];trials=[]
    for t in tasks:
        source=t["source_train"]
        if not source:raise ValueError("missing real AUTHOR SOURCE training")
        prompt=source_discovery_prompt(source)
        proposals=[]
        row={"id":t["source_id"],"sampled":proposals_per_task,
             "positive_preference":False,"original_target_gold_read":False}
        for sample in range(proposals_per_task):
            # Change only the sampler RNG; NO answer hints/family IDs/tools.
            model.seed=1007+sample*1009
            try:
                code=validate_code(model.propose(prompt))
            except SourceContextOverflow:
                row["status"]="ABSTAIN_SOURCE_PROMPT_OVERFLOW"
                break
            except (UnsafeProposal,ValueError,TypeError):
                continue
            if code not in proposals:proposals.append(code)
        row["executable_candidates_proposed"]=len(proposals)
        comparisons=[]
        for i,a in enumerate(proposals):
            for b in proposals[i+1:]:
                preference=preference_from_source(
                    source,runner,a,b,margin=0.02)
                if preference is not None:comparisons.append(preference)
        if comparisons:
            comparisons.sort(key=lambda p:(
                p["positive_credit"]["gain"]-
                p["negative_credit"]["gain"],
                p["positive_credit"]["exact"],
                len(p["negative_program"])-len(p["positive_program"])
            ),reverse=True)
            selected=comparisons[0]
            selected.update({
                "schema":"NEUMANN.Q3.SOURCE-ONLY-SELF-GENERATED-PREFERENCE.v1",
                "task_id":t["source_id"],
                "source_train":source,
                "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
                "positive_program_sha256":hashlib.sha256(
                    selected["positive_program"].encode()).hexdigest(),
                "negative_program_sha256":hashlib.sha256(
                    selected["negative_program"].encode()).hexdigest(),
                "origin":"TWO_ACTUAL_SAME_MODEL_SOURCE_RUNNABLE_PROPOSALS",
            })
            collected.append(selected)
            row["positive_preference"]=True
            row["status"]="SOURCE_RELATIVE_PROGRAM_PREFERENCE_ONLY"
            row["best_gain"]=selected["positive_credit"]["gain"]
            row["worse_gain"]=selected["negative_credit"]["gain"]
            row["best_exact_train"]=selected["positive_credit"]["exact"]
        else:
            row.setdefault("status","ABSTAIN_NO_NONTRIVIAL_PARTIAL_SIGNAL")
        trials.append(row)
        print("Q3_SOURCE_PROGRAM_SELF_CREDIT",row,flush=True)
    Path(out).write_text("".join(_dump(p)+"\n" for p in collected))
    summary={
        "schema":"NEUMANN.Q3.SELF-GENERATED-SOURCE-CREDIT-AUDIT.v1",
        "teacher_source_tasks":len(tasks),
        "same_model_sample_count":sum(t["sampled"] for t in trials),
        "genuine_executable_partial_preferences":len(collected),
        "source_registry_sha256":hashlib.sha256(
            Path(source_file).read_bytes()).hexdigest(),
        "pretrained_model_revision":model_revision,
        "preferences_sha256":hashlib.sha256(Path(out).read_bytes()).hexdigest(),
        "independent_source_checks_read":False,
        "original_target_gold_read":False,
        "all_preferences_uncertified":True,
        "q3_global":"OPEN","trials":trials,
    }
    Path(report).write_text(_dump(summary)+"\n")
    print("Q3_REAL_ONPOLICY_PARTIAL_SOURCE_PREFERENCE_COLLECTION",
          {k:v for k,v in summary.items() if k!="trials"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--model-revision",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--max-tasks",type=int,default=12)
    p.add_argument("--proposals-per-task",type=int,default=3)
    a=p.parse_args()
    collect(a.source,model_revision=a.model_revision,out=a.out,
            report=a.report,max_tasks=a.max_tasks,
            proposals_per_task=a.proposals_per_task)
