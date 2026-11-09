"""ARC2 independent-training-original cohort: frozen object-grammar vs full prior.

Chosen from OFFICIAL independent-author TRAINING data, excluding all 96
previously scored source IDs. No public evaluation test outputs opened.
This is a distinct source-original development cohort, not an official
frontier/untouched private evaluation.

Separate prepare/propose/score processes: proposer receives NO test gold.
All candidate predictions SHA-locked before test outputs can be accessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from q3_arc2_training_original_test_freeze import (
    PINNED_ARC2, checked_upstream, sha_bytes)
from neumann1 import arc2_meta_grid_reasoner as old
from neumann1.composed_grid_inventor import ComposedGridInventor
from neumann1.scene_graph_inventor import ObjectGrammarInventor


HERE=pathlib.Path(__file__).resolve().parent
EXCLUSION=HERE/"arc2_previous_96_exclusions.json"
SECOND_EXCLUSION=HERE/"arc2_object_first128_exclusions.json"
THIRD_EXCLUSION=HERE/"arc2_object_second128_exclusions.json"


def freeze_options(cohort="third"):
    rules=json.loads(EXCLUSION.read_text())
    ids=set(rules["excluded_prior_ids"])
    if len(ids)!=96:
        raise ValueError("pre-exposed task exclusion contract invalid")
    if cohort=="first":
        return ids,rules["salt"]
    if cohort in ("second","third"):
        second=json.loads(SECOND_EXCLUSION.read_text())
        new=set(second["excluded_second_prior_ids"])
        if len(new)!=128 or new & ids:
            raise ValueError("second-original first cohort not disjoint")
        if cohort=="second":
            return ids|new,second["salt"]
        third=json.loads(THIRD_EXCLUSION.read_text())
        fresh=set(third["excluded_third_prior_ids"])
        if len(fresh)!=128 or fresh & (ids|new):
            raise ValueError("third-source original IDs not independent")
        return ids|new|fresh,third["salt"]
    raise ValueError("unknown cohort; cannot reuse previously scored target gold")


def prepare(upstream,blind,n,*,cohort="third"):
    excluded,salt=freeze_options(cohort)
    root=checked_upstream(upstream)
    candidates=[p for p in root.glob("*.json")
                if p.stem not in excluded]
    selected=sorted(candidates,key=lambda p:hashlib.sha256(
        (salt+p.name).encode()).hexdigest())[:n]
    if not 1<=n<=128 or len(selected)!=n:
        raise ValueError("invalid external-source cohort denominator")
    if set(p.stem for p in selected)&excluded:
        raise ValueError("source task already appeared in previous 96")
    blind.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for path in selected:
        data=json.loads(path.read_text())
        if "train" not in data or "test" not in data:
            raise ValueError("missing official original data")
        clean={"train":data["train"],
               "test":[{"input":t["input"]} for t in data["test"]]}
        output=blind/path.name
        output.write_text(json.dumps(clean,separators=(",",":")))
        manifest.append({
            "task_id":path.stem,
            "source_sha256":sha_bytes(path.read_bytes()),
            "blind_sha256":sha_bytes(output.read_bytes())})
    (blind/"manifest.json").write_text(json.dumps({
        "external_commit":PINNED_ARC2,
        "salt":salt,
        "excluded_prior_training_tasks":len(excluded),
        "cohort":cohort,
        "all_test_answers_removed":True,
        "files":manifest},indent=2)+"\n")
    print("NEW EXTERNAL TASK IDS FROZEN:",n, "EXCLUDED:",len(excluded))


def _predict_old(demo,source_check,inputs):
    old_results,checks=old.fit_task(
        demo,range(len(old.PROGRAMS)),len(old.PROGRAMS),
        max_hits=len(old.PROGRAMS))
    winners=[]
    seen=set()
    for j,adapter in sorted(old_results,key=lambda item:(
            item[1]["kind"]!="exact",len(old.PROGRAMS[item[0]]),item[0])):
        def out(x):
            p=old.predict(x,old.PROGRAMS[j])
            if p is not None and adapter["kind"]=="recolor":
                p=old.recolor(p,adapter["mapping"])
            return p
        if out(source_check[0])!=source_check[1]:continue
        prediction=tuple(out(x) for x in inputs)
        if any(x is None for x in prediction):continue
        key=repr(prediction)
        if key in seen:continue
        winners.append(prediction)
        seen.add(key)
        if len(winners)>=2:break
    return winners,checks


def _predict_prior(demo,source_check,inputs,relational_ms):
    try:
        proposal=ComposedGridInventor(max_geometries=12,
                                      max_relational_ms=relational_ms).solve(
            demo,(source_check[0],*inputs))
    except (ValueError,TypeError,ArithmeticError):
        return [],False
    preds=[]
    seen=set()
    for pair in proposal.candidates:
        if pair[0]!=source_check[1]:continue
        future=tuple(pair[1:])
        if any(x is None for x in future):continue
        key=repr(future)
        if key not in seen:preds.append(future);seen.add(key)
        if len(preds)>=2:break
    return preds,proposal.invented_source_fit


def _predict_object(demo,source_check,inputs,object_ms):
    try:
        fitted=ObjectGrammarInventor(
            max_source_ms=object_ms).invent(
                demo,verification=[source_check],max_programs=2)
    except (TypeError,ValueError,ArithmeticError):
        return [],0
    choices=[]
    for method in fitted.programs:
        try:
            predicted=tuple(method.apply(x) for x in inputs)
        except (ValueError,TypeError,ArithmeticError):
            continue
        if all(x is not None for x in predicted) and predicted not in choices:
            choices.append(predicted)
    return choices[:2],fitted.source_checks


def _unique_candidates(*groups,max_attempts=2):
    result=[]
    for group in groups:
        for candidate in group:
            if candidate not in result:
                result.append(candidate)
                if len(result)>=max_attempts:return result
    return result


def propose(blind,out,*,relational_ms,object_ms):
    manifest=json.loads((blind/"manifest.json").read_text())
    records=[]
    for record in manifest["files"]:
        path=blind/(record["task_id"]+".json")
        if sha_bytes(path.read_bytes())!=record["blind_sha256"]:
            raise ValueError("blind source mutated")
        data=json.loads(path.read_text())
        if any("output" in x for x in data["test"]):
            raise ValueError("TARGET GOLD LEAK")
        pairs=[(old.G(x["input"]),old.G(x["output"]))
               for x in data["train"]]
        if len(pairs)<3:
            records.append({"task_id":record["task_id"],
                            "status":"SKIP_UNDERSPECIFIED_SOURCE"})
            continue
        source=pairs[:-1]
        verified_source=pairs[-1]
        target_inputs=tuple(old.G(x["input"]) for x in data["test"])

        t=time.perf_counter_ns()
        classical,checks=_predict_old(source,verified_source,target_inputs)
        classical_ms=(time.perf_counter_ns()-t)/1e6
        t=time.perf_counter_ns()
        prior,prior_fit=_predict_prior(
            source,verified_source,target_inputs,relational_ms)
        prior_ms=(time.perf_counter_ns()-t)/1e6

        # No original test outputs are opened here; all decisions use
        # only original TRAINING demonstrations + final source verifier.
        t=time.perf_counter_ns()
        object_candidates,object_checks=_predict_object(
            source,verified_source,target_inputs,object_ms)
        object_ms_elapsed=(time.perf_counter_ns()-t)/1e6

        # Classical source-certified exact candidates are preferred.
        if classical:
            merged=_unique_candidates(classical,object_candidates,prior)
        else:
            merged=_unique_candidates(object_candidates,prior)

        records.append({
            "task_id":record["task_id"],
            "status":"PREDICTED","original_file_sha256":record["source_sha256"],
            "original_test_count":len(target_inputs),
            "classical":classical,
            "prior_composed":prior,
            "new_object":object_candidates,
            "integrated":merged,
            "source_classical_fit":bool(classical),
            "source_prior_fit":bool(prior),
            "source_object_fit":bool(object_candidates),
            "fixed_grammar_checks":checks,
            "object_search_checks":object_checks,
            "classical_search_ms":round(classical_ms,5),
            "prior_search_ms":round(prior_ms,5),
            "object_search_ms":round(object_ms_elapsed,5),
            "no_original_test_gold_seen":True
        })
    output={
        "schema":"NEUMANN.Q3.object-grammar-external-fresh-128.blind.v1",
        "upstream_commit":PINNED_ARC2,
        "old_ids_excluded":manifest["excluded_prior_training_tasks"],
        "cohort":manifest["cohort"],
        "all_test_outputs_removed_before_proposal":True,
        "records":records
    }
    out.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print("OBJECT FIRST PROPOSALS FROZEN:",len(records),
          sha_bytes(out.read_bytes()))


def score(upstream,predictions,frozen_sha,out):
    if sha_bytes(predictions.read_bytes())!=frozen_sha:
        raise ValueError("the predictions changed after source-only proposal")
    root=checked_upstream(upstream)
    data=json.loads(predictions.read_text())
    excluded,_=freeze_options(data.get("cohort","first"))
    if data.get("old_ids_excluded")!=len(excluded):
        raise ValueError("frozen excluded-cohort contract changed")
    scored=[]
    for rec in data["records"]:
        if rec["task_id"] in excluded:
            raise ValueError("overlaps previously scored training original")
        if rec["status"]!="PREDICTED":
            scored.append({"task_id":rec["task_id"],"status":"SKIPPED"})
            continue
        original=root/(rec["task_id"]+".json")
        if sha_bytes(original.read_bytes())!=rec["original_file_sha256"]:
            raise ValueError("external data modified")
        source=json.loads(original.read_text())
        gold=tuple(old.G(y["output"]) for y in source["test"])
        if len(gold)!=rec["original_test_count"]:
            raise ValueError("target count changed")
        def exact(options):
            return any(tuple(old.G(x) for x in row)==gold for row in options)
        old_correct=exact(rec["classical"])
        prior_correct=exact(rec["prior_composed"])
        obj_correct=exact(rec["new_object"])
        merged_correct=exact(rec["integrated"])
        scored.append({
            "task_id":rec["task_id"],"status":"SCORED",
            "classical_correct":old_correct,
            "prior_correct":prior_correct,
            "object_correct":obj_correct,
            "integrated_correct":merged_correct,
            "object_only_vs_prior":obj_correct and not prior_correct,
            "object_only_vs_classical":obj_correct and not old_correct,
            "integrated_regression_vs_prior":prior_correct and not merged_correct,
        })
    active=[r for r in scored if r["status"]=="SCORED"]
    predicted=[r for r in data["records"] if r["status"]=="PREDICTED"]
    summary={
        "selected_new_external_ids":len(data["records"]),
        "scored":len(active),"skipped":len(scored)-len(active),
        "classical_626_correct":sum(r["classical_correct"] for r in active),
        "prior_composer_correct":sum(r["prior_correct"] for r in active),
        "object_grammar_correct":sum(r["object_correct"] for r in active),
        "integrated_two_attempt_correct":sum(r["integrated_correct"] for r in active),
        "object_additions_vs_prior":sum(r["object_only_vs_prior"] for r in active),
        "object_additions_vs_classical":sum(r["object_only_vs_classical"] for r in active),
        "integrated_regressions_vs_prior":sum(
            r["integrated_regression_vs_prior"] for r in active),
        "classical_seconds":round(sum(
            r["classical_search_ms"] for r in predicted)/1000,5),
        "prior_composer_seconds":round(sum(
            r["prior_search_ms"] for r in predicted)/1000,5),
        "new_object_seconds":round(sum(
            r["object_search_ms"] for r in predicted)/1000,5),
        "integrated_source_seconds":round(sum(
            r["prior_search_ms"]+r["object_search_ms"]
            for r in predicted)/1000,5),
        "sha256_frozen_before_any_test_gold":frozen_sha,
        "full_q3_q4_q6_pass":False,
        "official_arcagi2_evaluation":False
    }
    out.write_text(json.dumps({
        "schema":"NEUMANN.Q3.object-grammar-external-fresh-128.scored.v1",
        "upstream_sha":PINNED_ARC2,
        "summary":summary,
        "records":scored,
        "caveats":[
            "External independent-author TRAINING task test, NOT ARC official EVALUATION.",
            "Some other ARC training task IDs may have been examined in older pre-PR studies.",
            "All object feature/segmentation/render interpreter primitives human-defined.",
            "No proof of arbitrary grammar invention or transfer to unrelated mathematics.",
            "No strongest specialist or full amortized inference cost comparison."
        ]
    },indent=2)+"\n")
    print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    q=sub.add_parser("prepare")
    q.add_argument("--upstream",type=pathlib.Path,required=True)
    q.add_argument("--blind",type=pathlib.Path,required=True)
    q.add_argument("--n",type=int,default=128)
    q.add_argument("--cohort",choices=("first","second","third"),default="third")
    q=sub.add_parser("propose")
    q.add_argument("--blind",type=pathlib.Path,required=True)
    q.add_argument("--output",type=pathlib.Path,required=True)
    q.add_argument("--rel-ms",type=int,default=120)
    q.add_argument("--obj-ms",type=int,default=350)
    q=sub.add_parser("score")
    q.add_argument("--upstream",type=pathlib.Path,required=True)
    q.add_argument("--predictions",type=pathlib.Path,required=True)
    q.add_argument("--expected-sha",required=True)
    q.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    if a.cmd=="prepare":prepare(a.upstream,a.blind,a.n,cohort=a.cohort)
    elif a.cmd=="propose":propose(a.blind,a.output,
                                 relational_ms=a.rel_ms,object_ms=a.obj_ms)
    else:score(a.upstream,a.predictions,a.expected_sha,a.output)


if __name__=="__main__":main()
