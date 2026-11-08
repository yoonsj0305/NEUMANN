"""Q3 frozen proposal -> independent scoring on ARC2 TRAINING tasks' test splits.

Public author's TRAINING directory only. Do not confuse these test fields with
official ARC-AGI-2 EVALUATION originals or a previously untouched Q3 FIRST.

Stages:
 prepare: From exact pinned upstream, create a STRICT blind copy with NO test
          gold fields. Only the prep process touches test gold container.
 propose: The solution process has access ONLY to blind copy's demonstrations
          and test input. Freeze its predictions on disk.
 score:   In a different process after predictions are SHA-locked, open
          original training task test gold and record correctness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import subprocess
import time
from collections import Counter

from neumann1.composed_grid_inventor import ComposedGridInventor
from neumann1 import arc2_meta_grid_reasoner as old
from research.q3.q3_arc2_composed_training_source_diagnostic import (
    PINNED_ARC2, SALT)


def sha_bytes(blob:bytes):
    return hashlib.sha256(blob).hexdigest()


def checked_upstream(path):
    commit=subprocess.check_output(
        ["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()
    if commit != PINNED_ARC2:
        raise ValueError("external official source revision changed")
    return path/"data"/"training"


def selection(root,n):
    files=sorted(root.glob("*.json"),
                 key=lambda x:sha_bytes((SALT+x.name).encode()))[:n]
    if len(files)!=n or not 1<=n<=128:
        raise ValueError("unexpected source sample denominator")
    return files


def prepare(upstream, blind, n):
    root=checked_upstream(upstream)
    files=selection(root,n)
    blind.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for path in files:
        payload=json.loads(path.read_text())
        if "train" not in payload or "test" not in payload:
            raise ValueError("invalid author original schema")
        target=[
            {"input":case["input"]} for case in payload["test"]
        ]
        scrub={"train":payload["train"],"test":target}
        (blind/path.name).write_text(json.dumps(scrub,separators=(",",":")))
        manifest.append({
            "source_id":path.stem,
            "original_file_sha256":sha_bytes(path.read_bytes()),
            "blind_file_sha256":sha_bytes((blind/path.name).read_bytes())})
    (blind/"manifest.json").write_text(json.dumps({
        "external_upstream_commit":PINNED_ARC2,
        "target_gold_removed":True,
        "records":manifest},indent=2)+"\n")
    print("PREPARED BLIND TRAINING-ONLY SOURCE TASKS",n)


def propose(blind,output,max_rel_ms):
    manifest=json.loads((blind/"manifest.json").read_text())
    records=[]
    for record in manifest["records"]:
        task=json.loads((blind/(record["source_id"]+".json")).read_text())
        if any("output" in item for item in task["test"]):
            raise ValueError("TEST GOLD LEAK INTO SOURCE PROPOSER")
        raw_train=task["train"]
        if len(raw_train)<3:
            records.append({"source_id":record["source_id"],
                            "status":"SKIP_INSUFFICIENT_SOURCE"})
            continue
        train=[(old.G(x["input"]),old.G(x["output"]))
               for x in raw_train[:-1]]
        valid_x=old.G(raw_train[-1]["input"])
        valid_y=old.G(raw_train[-1]["output"])
        targets=[old.G(x["input"]) for x in task["test"]]
        # Existing complete fixed grammar with same original source data.
        t0=time.perf_counter_ns()
        winners,checks=old.fit_task(
            train,range(len(old.PROGRAMS)),len(old.PROGRAMS),
            max_hits=len(old.PROGRAMS))
        matched=[]
        for j,adapter in sorted(winners,key=lambda item:(
                item[1]["kind"]!="exact",len(old.PROGRAMS[item[0]]),item[0])):
            def classify(v):
                pred=old.predict(v,old.PROGRAMS[j])
                if pred is not None and adapter["kind"]=="recolor":
                    pred=old.recolor(pred,adapter["mapping"])
                return pred
            if classify(valid_x)!=valid_y:
                continue
            future=[classify(x) for x in targets]
            if all(x is not None for x in future):
                if future not in matched:
                    matched.append(future)
            if len(matched)==2:break
        old_ms=(time.perf_counter_ns()-t0)/1e6
        t0=time.perf_counter_ns()
        result=ComposedGridInventor(
            max_geometries=12,max_relational_ms=max_rel_ms).solve(
                train,(valid_x,*targets))
        composed_ms=(time.perf_counter_ns()-t0)/1e6
        # The source verifier filters candidates BEFORE any original test
        # answer has been loaded in the current process.
        accepted=[]
        for program_predictions in result.candidates:
            if program_predictions[0]!=valid_y:continue
            future=list(program_predictions[1:])
            if any(x is None for x in future):continue
            if future not in accepted:accepted.append(future)
            if len(accepted)==2:break
        new_rule=None
        if result.invented_program is not None and (
                result.invented_program.apply(valid_x)==valid_y):
            new_rule=[result.invented_program.apply(x) for x in targets]
            if any(x is None for x in new_rule):new_rule=None
        records.append({
            "source_id":record["source_id"],
            "status":"PREDICTED",
            "test_count":len(targets),
            "old_candidates":matched[:2],
            "composed_candidates":accepted[:2],
            "new_composed_rule_candidate":new_rule,
            "old_source_search_ms":round(old_ms,5),
            "composed_source_search_ms":round(composed_ms,5),
            "original_file_sha256":record["original_file_sha256"],
            "original_was_never_scored_in_proposer":True
        })
    proposals={
        "schema":"NEUMANN.Q3.external.ARC2.public-training-test-blind.v1",
        "official_evaluation_originals_opened":False,
        "official_training_test_gold_opened_by_proposer":False,
        "upstream_sha":PINNED_ARC2,
        "records":records
    }
    output.write_text(json.dumps(proposals,separators=(",",":"))+"\n")
    print("PROPOSAL_FROZEN",len(records),sha_bytes(output.read_bytes()))


def score(upstream,predictions,expected_sha,output):
    root=checked_upstream(upstream)
    if sha_bytes(predictions.read_bytes())!=expected_sha:
        raise ValueError("predictions changed after freeze")
    proposed=json.loads(predictions.read_text())
    if proposed["upstream_sha"]!=PINNED_ARC2:
        raise ValueError("source family switched after freeze")
    records=[]
    for row in proposed["records"]:
        if row["status"]!="PREDICTED":
            records.append({"source_id":row["source_id"],"status":"SKIPPED"})
            continue
        path=root/(row["source_id"]+".json")
        if sha_bytes(path.read_bytes())!=row["original_file_sha256"]:
            raise ValueError("original source mutated between proposal and scoring")
        original=json.loads(path.read_text())
        gold=tuple(old.G(case["output"]) for case in original["test"])
        if len(gold)!=row["test_count"]:
            raise ValueError("original gold count changed")
        def matches(preds):
            return bool(preds) and any(
                tuple(old.G(x) for x in candidate)==gold
                for candidate in preds)
        classical=matches(row["old_candidates"])
        combined=matches(row["composed_candidates"])
        new_rule=bool(row["new_composed_rule_candidate"]) and (
            tuple(old.G(x) for x in row["new_composed_rule_candidate"])==gold)
        records.append({
            "source_id":row["source_id"],"status":"SCORED",
            "old_correct":classical,
            "composed_correct":combined,
            "invented_only_correct":new_rule and not classical,
            "new_rule_correct":new_rule,
            "source_inv_correct":row["new_composed_rule_candidate"] is not None
        })
    evaluated=[x for x in records if x["status"]=="SCORED"]
    source=[x for x in proposed["records"] if x["status"]=="PREDICTED"]
    result={
        "source_samples_selected":len(proposed["records"]),
        "source_samples_scored":len(evaluated),
        "source_samples_skipped":len(records)-len(evaluated),
        "old_626_correct_original_training_tests":sum(x["old_correct"] for x in evaluated),
        "new_composer_correct_original_training_tests":sum(x["composed_correct"] for x in evaluated),
        "invented_only_correct_original_training_tests":sum(x["invented_only_correct"] for x in evaluated),
        "new_rule_correct_original_training_tests":sum(x["new_rule_correct"] for x in evaluated),
        "total_old_source_search_seconds":round(sum(
            x["old_source_search_ms"] for x in source)/1000,5),
        "total_composed_source_search_seconds":round(sum(
            x["composed_source_search_ms"] for x in source)/1000,5),
        "prediction_frozen_sha256":expected_sha,
        "original_first_claim":False,
        "global_q3_q4_q6_pass":False
    }
    output.write_text(json.dumps({"schema":"NEUMANN.Q3.ARC2.train-original-test-replay.v1",
                    "source_upstream_sha":PINNED_ARC2,"summary":result,
                    "records":records},indent=2)+"\n")
    print(json.dumps(result,indent=2))


def main():
    p=argparse.ArgumentParser()
    s=p.add_subparsers(dest="command",required=True)
    a=s.add_parser("prepare")
    a.add_argument("--upstream",type=pathlib.Path,required=True)
    a.add_argument("--blind",type=pathlib.Path,required=True)
    a.add_argument("--n",type=int,default=96)
    a=s.add_parser("propose")
    a.add_argument("--blind",type=pathlib.Path,required=True)
    a.add_argument("--output",type=pathlib.Path,required=True)
    a.add_argument("--max-rel-ms",type=int,default=120)
    a=s.add_parser("score")
    a.add_argument("--upstream",type=pathlib.Path,required=True)
    a.add_argument("--predictions",type=pathlib.Path,required=True)
    a.add_argument("--expected-sha",required=True)
    a.add_argument("--output",type=pathlib.Path,required=True)
    q=p.parse_args()
    if q.command=="prepare":prepare(q.upstream,q.blind,q.n)
    elif q.command=="propose":propose(q.blind,q.output,q.max_rel_ms)
    else:score(q.upstream,q.predictions,q.expected_sha,q.output)


if __name__=="__main__":main()
