"""Q3 development: ask the independent author's black-box function, not its code.

These three CodeARC problems were ALREADY SEEN and scored by NEUMANN in
previous studies. This is a capability regression/active-query diagnostic,
NOT FIRST-UNSEEN Q3 or cross-author Q6 evidence.

The evaluator may access author source only to instantiate a locked Docker
oracle with a single query-to-answer interface. The challenge selector sees
only frozen original SOURCE observations, previously generated hypothesis
programs, and its own predictions; not author code or target outputs.

Both active and random controls have identical 4 new SOURCE-query budgets
per example, the identical SOURCE observation and candidate pool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from neumann1.active_oracle_challenges import choose_probes, perturb_inputs
from neumann1.open_program_inventor import IsolatedPython
from research.q3.pinned_author_function_oracle import AuthorFunctionOracle


# Original development SOURCE observations, fixed from the previous frozen
# NEUMANN prediction artifacts. The reference algorithms DO NOT appear here.
# ID 447: SHA-frozen previously-generated false condition / x[0].
# ID 416: SHA-frozen source-repaired false reversed-digit comparator.
# ID 1055: SHA-frozen source-repaired constant output. Source includes
# only 'STAY', which cannot identify the true function by observation alone.
EXPOSED=[
    {
        "id":447,"file":"447.py","entry":"calculate_group_size",
        "arity":2,"hypothesis":(
            "def transform(x):\n"
            "    return x[0] if len(x) == 2 else x[0] + x[1]"),
        "source":[
            [[10,1],10],[[5,4],5],[[20,7],20],[[15,10],15],
            [[30,2],30],[[25,12],25],[[8,6],8]],
        "previous_frozen_artifact":
            "https://github.com/yoonsj0305/NEUMANN/actions/runs/"
            "42565451153/artifacts/13651437285"
    },
    {
        "id":416,"file":"416.py","entry":"is_number_sorted",
        "arity":1,"hypothesis":(
            "def transform(x):\n"
            "    return x <= int(str(x)[::-1])"),
        "source":[
            [123,True],[321,False],[135,True],[97531,False],
            [111,True],[987654321,False],[2468,True]],
        "previous_frozen_artifact":
            "https://github.com/yoonsj0305/NEUMANN/actions/runs/"
            "42567509069/artifacts/13652438396"
    },
    {
        "id":1055,"file":"1055.py","entry":"check_launch_compatibility",
        "arity":2,"hypothesis":(
            "def transform(x):\n"
            "    return 'STAY'"),
        "source":[
            [["GROUPA","COMETA"],"STAY"],
            [["GROUPB","COMETB"],"STAY"],
            [["GROUPC","COMETC"],"STAY"],
            [["GROUPD","COMETD"],"STAY"],
            [["GROUPE","COMETE"],"STAY"],
            [["GROUPF","COMETF"],"STAY"],
            [["GROUPG","COMETG"],"STAY"]],
        "previous_frozen_artifact":
            "https://github.com/yoonsj0305/NEUMANN/actions/runs/"
            "42567509069/artifacts/13652438396"
    }
]


def evaluate(*,author_root,output,query_budget=4):
    if not 1<=query_budget<=8:raise ValueError("bounded oracle calls")
    runner=IsolatedPython(max_seconds=7)
    records=[]
    for task in EXPOSED:
        author=AuthorFunctionOracle(
            source_path=Path(author_root)/task["file"],
            entrypoint=task["entry"],arity=task["arity"])
        source=tuple((x,y) for x,y in task["source"])
        # A single Docker invocation per <=64 proposed SOURCE inputs,
        # not hundreds of isolated containers during input ranking.
        pool=perturb_inputs([x for x,y in source])
        memo={}
        for first in range(0,len(pool),64):
            shard=pool[first:first+64]
            r=runner.evaluate(task["hypothesis"],list(shard))
            if r.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
                continue
            for item,value,error in zip(shard,r.outputs,r.errors):
                if error is None:
                    memo[json.dumps(item,sort_keys=True)]=value
        def predict(x):
            key=json.dumps(x,sort_keys=True)
            if key in memo:
                return memo[key]
            r=runner.evaluate(task["hypothesis"],[x])
            if r.status!="EXECUTED":
                raise ValueError("model program runtime error")
            return r.outputs[0]
        train=runner.evaluate(task["hypothesis"],[x for x,y in source])
        if (train.status!="EXECUTED" or any(
                got!=y for got,(_,y) in zip(train.outputs,source))):
            raise AssertionError(
                "prior scored program did not fit frozen original SOURCE")
        modes=[]
        for mode in ("random","active"):
            probes=choose_probes(
                source,count=query_budget,mode=mode,
                prediction_functions=(predict,))
            output_oracle=author.batch(probes.queries)
            if output_oracle.status!="EXECUTED_ALL":
                modes.append({
                    "mode":mode,"status":output_oracle.status,
                    "input_hash":probes.selected_sha256,
                    "query_count":output_oracle.count})
                continue
            source_new=tuple(zip(probes.queries,output_oracle.outputs))
            predictions=[]
            for x in probes.queries:
                predictions.append(predict(x))
            failures=[
                {"input":x,"new_source_output":y,"old_hypothesis_output":h}
                for (x,y),h in zip(source_new,predictions)
                if y!=h]
            modes.append({
                "mode":mode,"status":"ORACLE_QUERIES_EXECUTED",
                "query_count":len(probes.queries),
                "candidate_pool_count":probes.pool_count,
                "input_hash":probes.selected_sha256,
                "hypothesis_refuted":bool(failures),
                "falsifying_count":len(failures),
                "probes":probes.queries,
                "counterexamples":failures,
            })
        records.append({
            "id":task["id"],
            "previously_exposed":True,
            "already_source_fitted":True,
            "source_count":len(source),
            "hypothesis_sha256":hashlib.sha256(
                task["hypothesis"].encode()).hexdigest(),
            "prior_artifact":task["previous_frozen_artifact"],
            "branches":modes
        })
        print("Q3_ACTIVE_DEV",task["id"],[
            (e["mode"],e.get("hypothesis_refuted"),
             e.get("falsifying_count",0)) for e in modes],flush=True)
    totals={
        "n_original_exposed":len(EXPOSED),
        "oracle_budget_per_task":query_budget,
        "active_refuted":sum(
            next((int(b.get("hypothesis_refuted",False))
                  for b in row["branches"] if b["mode"]=="active"),0)
            for row in records),
        "random_refuted":sum(
            next((int(b.get("hypothesis_refuted",False))
                  for b in row["branches"] if b["mode"]=="random"),0)
            for row in records),
        "author_source_was_not_read_by_learner":True,
        "new_first_original_solutions":0,
        "policy_weights_updated":False,
        "global_q3_q6":"OPEN"
    }
    payload={
        "schema":"NEUMANN.Q3.AUTHOR_ORACLE_DEVELOPMENT.v1",
        "summary":totals,"records":records}
    Path(output).write_text(json.dumps(payload,indent=2)+"\n")
    print("Q3_ORACLE_DEV_SUMMARY",json.dumps(totals,sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--author-root",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--budget",type=int,default=4)
    args=p.parse_args()
    evaluate(author_root=args.author_root,output=args.output,
             query_budget=args.budget)
