"""Fourth disjoint ARC-AGI-2 TRAINING-original Q3 pairwise causal gate.

Original task IDs are excluded from prior 96 + FIRST/SECOND/THIRD 128:
480 distinct previously-scored original training source tasks are excluded.
Hash-salted selection, no test gold to proposer, SHA freeze, separate scoring.

This is an independent-author TRAINING-only development experiment.
It neither opens ARC public evaluation nor proves Q3 generality/frontier.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys
import time

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from q3_arc2_object_blind_first import (
    _predict_old, _predict_prior, _predict_object, freeze_options)
from q3_arc2_training_original_test_freeze import (
    checked_upstream, PINNED_ARC2, sha_bytes)
from neumann1.relational_action_inventor import RelationalActionInventor
from neumann1 import arc2_meta_grid_reasoner as old

HERE=pathlib.Path(__file__).resolve().parent
FOURTH_EXCLUSION=HERE/"arc2_object_third128_exclusions.json"


def fourth_manifest():
    prior,prior_salt=freeze_options("third")
    other=json.loads(FOURTH_EXCLUSION.read_text())
    fourth=set(other["excluded_fourth_prior_ids"])
    if len(prior)!=352 or len(fourth)!=128 or prior & fourth:
        raise ValueError("fourth task original author cohort overlaps previous 480")
    return prior|fourth,other["salt"]


def prepare(upstream,blind,n):
    excluded,salt=fourth_manifest()
    root=checked_upstream(upstream)
    choices=sorted((p for p in root.glob("*.json")
                    if p.stem not in excluded),
                   key=lambda p:hashlib.sha256(
                       (salt+p.name).encode()).hexdigest())[:n]
    if not 1<=n<=128 or len(choices)!=n:
        raise ValueError("not enough unused external original tasks")
    blind.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for path in choices:
        source=json.loads(path.read_text())
        clean={"train":source["train"],
               "test":[{"input":t["input"]} for t in source["test"]]}
        dst=blind/path.name
        dst.write_text(json.dumps(clean,separators=(",",":")))
        manifest.append({"task_id":path.stem,
                         "author_source_sha":sha_bytes(path.read_bytes()),
                         "blind_source_sha":sha_bytes(dst.read_bytes())})
    (blind/"manifest.json").write_text(json.dumps({
        "upstream_commit":PINNED_ARC2,
        "excluded_old_originals":len(excluded),
        "all_test_gold_removed":True,
        "records":manifest},indent=2))
    print("FROZEN FOURTH 128 SOURCE ORIGINALS EXCLUDING",len(excluded))


def _causal(source,verify,inputs,budget):
    t=time.perf_counter_ns()
    try:
        learned=RelationalActionInventor(
            max_source_ms=budget,max_witnesses=128).invent(
                source,verification=(verify,),max_rules=2)
    except (TypeError,ValueError,ArithmeticError):
        learned=None
    ms=(time.perf_counter_ns()-t)/1e6
    answers=[]
    if learned is not None:
        for rule in learned.rules:
            try:
                values=tuple(rule.apply(x) for x in inputs)
            except (TypeError,ValueError,ArithmeticError):
                continue
            if all(x is not None for x in values) and values not in answers:
                answers.append(values)
    return answers[:2],round(ms,5),bool(learned and learned.source_fit)


def _unique(*groups):
    answer=[]
    for group in groups:
        for candidate in group:
            if candidate not in answer:
                answer.append(candidate)
                if len(answer)>=2:return answer
    return answer


def propose(blind,output,*,max_causal_ms=350):
    manifest=json.loads((blind/"manifest.json").read_text())
    if (not manifest["all_test_gold_removed"] or
            manifest["excluded_old_originals"]!=480):
        raise ValueError("source-only author/provenance gate")
    results=[]
    for source in manifest["records"]:
        task=blind/(source["task_id"]+".json")
        if sha_bytes(task.read_bytes())!=source["blind_source_sha"]:
            raise ValueError("blind task changed")
        data=json.loads(task.read_text())
        if any("output" in t for t in data["test"]):
            raise ValueError("LEAK: original test output in proposer")
        pairs=[(old.G(x["input"]),old.G(x["output"]))
               for x in data["train"]]
        if len(pairs)<3:
            results.append({"task_id":source["task_id"],
                            "status":"SKIP_INSUFFICIENT_SOURCE"})
            continue
        source_pairs=pairs[:-1]
        check=pairs[-1]
        targets=tuple(old.G(t["input"]) for t in data["test"])
        t0=time.perf_counter_ns()
        classical,checks=_predict_old(source_pairs,check,targets)
        classical_ms=(time.perf_counter_ns()-t0)/1e6
        t0=time.perf_counter_ns()
        prior,_=_predict_prior(source_pairs,check,targets,120)
        prior_ms=(time.perf_counter_ns()-t0)/1e6
        t0=time.perf_counter_ns()
        single,_=_predict_object(source_pairs,check,targets,350)
        single_ms=(time.perf_counter_ns()-t0)/1e6
        causal,causal_ms,causal_fit=_causal(
            source_pairs,check,targets,max_causal_ms)
        strongest_prior=_unique(classical,prior,single)
        integrated=_unique(classical,prior,single,causal)
        results.append({
            "task_id":source["task_id"],"status":"PREDICTED",
            "source_sha256":source["author_source_sha"],
            "target_count":len(targets),
            "classical":classical,"previous_composed":prior,
            "previous_object":single,
            "prior_two_attempt":strongest_prior,
            "new_causal":causal,
            "integrated_two_attempt":integrated,
            "source_causal_fit":causal_fit,
            "classical_ms":round(classical_ms,5),
            "prior_ms":round(prior_ms,5),
            "object_ms":round(single_ms,5),
            "causal_ms":causal_ms
        })
    frozen={
        "schema":"NEUMANN.Q3.fourth-causal-128.blind.v1",
        "source_upstream_commit":PINNED_ARC2,
        "previous_originals_excluded":480,
        "test_gold_used":False,
        "records":results
    }
    output.write_text(json.dumps(frozen,separators=(",",":"))+"\n")
    print("Q3 CAUSAL PROPOSALS FROZEN",len(results),sha_bytes(output.read_bytes()))


def score(upstream,predictions,sha,output):
    if sha_bytes(predictions.read_bytes())!=sha:
        raise ValueError("tampered frozen prediction artifact")
    source=json.loads(predictions.read_text())
    if source["source_upstream_commit"]!=PINNED_ARC2:
        raise ValueError("source revision switched")
    exclude,_=fourth_manifest()
    root=checked_upstream(upstream)
    scored=[]
    for row in source["records"]:
        if row["task_id"] in exclude:
            raise ValueError("previous original task reused")
        if row["status"]!="PREDICTED":
            scored.append({"task_id":row["task_id"],"status":"SKIPPED"})
            continue
        author=root/(row["task_id"]+".json")
        if sha_bytes(author.read_bytes())!=row["source_sha256"]:
            raise ValueError("external author source changed")
        problem=json.loads(author.read_text())
        answers=tuple(old.G(t["output"]) for t in problem["test"])
        if len(answers)!=row["target_count"]:
            raise ValueError("target count change")
        def right(candidates):
            return any(tuple(old.G(x) for x in candidate)==answers
                       for candidate in candidates)
        classical=right(row["classical"])
        prior_correct=right(row["prior_two_attempt"])
        novel=right(row["new_causal"])
        integrated=right(row["integrated_two_attempt"])
        scored.append({
            "task_id":row["task_id"],"status":"SCORED",
            "classical":classical,"prior":prior_correct,"causal":novel,
            "integrated":integrated,
            "new_residual_vs_prior":novel and not prior_correct,
            "integrated_regression":prior_correct and not integrated})
    valid=[r for r in scored if r["status"]=="SCORED"]
    predicted=[r for r in source["records"] if r["status"]=="PREDICTED"]
    summary={
        "selected":len(scored),"evaluated":len(valid),
        "skipped":len(scored)-len(valid),
        "classical_correct":sum(r["classical"] for r in valid),
        "prior_2attempt_correct":sum(r["prior"] for r in valid),
        "causal_only_correct":sum(r["causal"] for r in valid),
        "integrated_2attempt_correct":sum(r["integrated"] for r in valid),
        "causal_new_residual_originals":sum(
            r["new_residual_vs_prior"] for r in valid),
        "integrated_regressions":sum(r["integrated_regression"] for r in valid),
        "source_causal_fits":sum(r["source_causal_fit"] for r in predicted),
        "base_classical_seconds":round(sum(r["classical_ms"] for r in predicted)/1000,5),
        "old_composed_seconds":round(sum(r["prior_ms"] for r in predicted)/1000,5),
        "old_object_seconds":round(sum(r["object_ms"] for r in predicted)/1000,5),
        "new_causal_seconds":round(sum(r["causal_ms"] for r in predicted)/1000,5),
        "frozen_prediction_sha256":sha,
        "official_evaluation":False,
        "global_q3_pass":False
    }
    output.write_text(json.dumps({
        "schema":"NEUMANN.Q3.fourth-causal-128.original-scored.v1",
        "upstream_commit":PINNED_ARC2,
        "summary":summary,"records":scored,
        "known_limits":[
            "Original author TRAINING tasks; not official public or private evaluation",
            "Typed object extraction, anchor relation basis and witness mechanics human supplied",
            "No implication that arbitrary future unseen tasks share these causal primitives",
            "Not compared to strongest modern specialist or frontier system"
        ]
    },indent=2)+"\n")
    print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("prepare")
    a.add_argument("--upstream",type=pathlib.Path,required=True)
    a.add_argument("--blind",type=pathlib.Path,required=True)
    a.add_argument("--n",type=int,default=128)
    a=sub.add_parser("propose")
    a.add_argument("--blind",type=pathlib.Path,required=True)
    a.add_argument("--output",type=pathlib.Path,required=True)
    a.add_argument("--causal-ms",type=int,default=350)
    a=sub.add_parser("score")
    a.add_argument("--upstream",type=pathlib.Path,required=True)
    a.add_argument("--predictions",type=pathlib.Path,required=True)
    a.add_argument("--expected-sha",required=True)
    a.add_argument("--output",type=pathlib.Path,required=True)
    args=p.parse_args()
    if args.command=="prepare":
        prepare(args.upstream,args.blind,args.n)
    elif args.command=="propose":
        propose(args.blind,args.output,max_causal_ms=args.causal_ms)
    else:
        score(args.upstream,args.predictions,args.expected_sha,args.output)


if __name__=="__main__":
    main()
