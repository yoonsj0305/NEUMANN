"""Pre-registered next-100 Q3 transfer: SOURCE-learned invention-policy C vs A.

No original AUTHOR TEST target exists in SOURCE, learn, or invention phases.
Disjoint original AUTHOR filenames are HASH selected BEFORE looking at their
outcomes. The design and grammar were developed on the previous 100 and
are frozen for the newly selected 100. Not globally first-exposed across
the repository's long ARC history: only formally disjoint from the 150
registered recent SOURCE authors.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_representation_policy import LearnedRepresentationPrior
from neumann1.q3_structural_invention import StructuralInventionPolicy
from research.q3.q3_coordinate_original_source_gate import (
    canonical,SCHEMA,UPSTREAM,sha,score as independent_author_score)

SRC_SCHEMA="NEUMANN.Q3.ORIGINAL-ARC2-SOURCE-TEACHING.v1"
SCOPE="NEXT100_RELATIVE_TO_PRIOR_150_ONLY"
SALT="NEUMANN.Q3.POSITIVE-EVIDENCE.NEXT100.20261110.v1"


def _read(path):
    return json.loads(Path(path).read_text())


def _save(path,data):
    Path(path).write_text(canonical(data)+"\n")


def freeze(root,prior50_path,prior100_path,out):
    first=_read(prior50_path);dev=_read(prior100_path)
    if (first.get("original_source_count")!=50
        or dev.get("original_source_count")!=100
        or first.get("upstream_revision")!=UPSTREAM
        or dev.get("upstream_revision")!=UPSTREAM
        or first.get("no_target_gold_in_payload") is not True
        or dev.get("no_target_gold_in_payload") is not True):
        raise ValueError("frozen 50 and 100 SOURCE registries required")
    old50=set(first["original_ids"]);old100=set(dev["original_ids"])
    if len(old50)!=50 or len(old100)!=100 or old50&old100:
        raise ValueError("prior-source leakage or identifier overlap")
    files=list(Path(root).glob("*.json"))
    if len(files)!=1000:
        raise ValueError("1000 original author files expected")
    files=[f for f in files if f.stem not in old50|old100]
    files.sort(key=lambda f:sha256(
        (SALT+"/"+f.stem).encode()).hexdigest())
    selected=files[:100]
    if len(selected)!=100:raise ValueError("insufficient original sources")
    records=[]
    for f in selected:
        data=_read(f)
        train=data["train"]
        records.append({
            "source_id":f.stem,
            "original_author_file_sha256":sha(f),
            "source_pairs":[[x["input"],x["output"]] for x in train],
        })
    result={
        "schema":SRC_SCHEMA,
        "upstream_revision":UPSTREAM,
        "original_source_count":100,
        "no_target_gold_in_payload":True,
        "source_scope":SCOPE,
        "source_registry":"sha256-file-names:"+SALT,
        "prior_150_source_ids_sha256":sha256(
            canonical(sorted(old50|old100)).encode()).hexdigest(),
        "original_ids":[r["source_id"] for r in records],
        "records":records,
        "q3_global":"OPEN",
    }
    _save(out,result)
    print("Q3_NEXT100_SOURCE_REGISTRY_FROZEN",{
        "ids":len(records),
        "overlap_with_prior150":0,
        "sha256":sha(out),"target_gold_present":False},flush=True)


def learn(development_source_path,out):
    dev=_read(development_source_path)
    if (dev.get("original_source_count")!=100
            or dev.get("source_scope")!=
                 "PROSPECTIVE_100_RELATIVE_TO_PRIOR_50_ONLY"
            or dev.get("no_target_gold_in_payload") is not True):
        raise ValueError("prior original-author SOURCE development required")
    trials=[];skipped=[]
    for r in dev["records"]:
        pairs=r["source_pairs"]
        if not 3<=len(pairs)<=32:
            skipped.append(r["source_id"]);continue
        train=pairs[:-1];checks=pairs[-1:]
        keys=[canonical(x) for x,y in pairs]
        if len(keys)!=len(set(keys)):
            skipped.append(r["source_id"]);continue
        trials.append((r["source_id"],train,checks))
    if not trials:raise ValueError("positive evidence teacher data missing")
    runner=IsolatedPython(max_seconds=8)
    prior=LearnedRepresentationPrior.learn_source_trials(
        trials,runner,max_episodes=128)
    snapshot=prior.source_snapshot()
    snapshot.update({
        "phase":"FROZEN_SOURCE_LEARNED_BEFORE_NEXT100",
        "teacher_scope":"PREVIOUS_100_SOURCE_ONLY",
        "teacher_source_sha256":sha(development_source_path),
        "teacher_count":len(trials),
        "teacher_skipped_count":len(skipped),
        "original_target_gold_read":False})
    _save(out,snapshot)
    print("Q3_LEARNED_DISCOVERY_FROM_PRIOR100_SOURCE",{
        "teacher_count":len(trials),
        "verifier_executions":prior.check_executions,
        "outcomes":[(x.name,x.successful_transfer,
                     x.falsified_transfer) for x in prior.outcomes],
        "snapshot_sha256":sha(out)},flush=True)


def _verify(code,train,checks,runner):
    combined=tuple(train)+tuple(checks)
    result=runner.evaluate(code,[x for x,y in combined])
    return (result.status=="EXECUTED" and
            len(result.outputs)==len(combined) and
            all(source_same_value(got,y) for got,(_,y)
                in zip(result.outputs,combined)))


def invent(new100_path,prior_path,out):
    cohort=_read(new100_path)
    data=_read(prior_path)
    if (cohort.get("source_scope")!=SCOPE
        or cohort.get("original_source_count")!=100
        or cohort.get("no_target_gold_in_payload") is not True
        or data.get("phase")!="FROZEN_SOURCE_LEARNED_BEFORE_NEXT100"
        or data.get("original_target_gold_read") is not False):
        raise ValueError("fixed original SOURCE evidence required")
    prior=LearnedRepresentationPrior.from_source_snapshot(data)
    runner=IsolatedPython(max_seconds=8)
    receipts=[]
    for i,task in enumerate(cohort["records"]):
        source=task["source_pairs"];certified=[]
        arm_counts={"A2":0,"A12":0,"C2":0}
        if 3<=len(source)<=32:
            train=source[:-1];checks=source[-1:]
            if len({canonical(x) for x,y in source})==len(source):
                for mode,prior_arg in (("A",None),("C",prior)):
                    policy=StructuralInventionPolicy(
                        max_candidates=12,
                        max_states=6500,max_evaluations=250000,
                        representation_prior=prior_arg)
                    policy.prepare(train)
                    candidates=policy.receipt.candidates
                    limit=12 if mode=="A" else 2
                    for index,code in enumerate(candidates[:limit]):
                        if not _verify(code,train,checks,runner):
                            continue
                        digest=sha256(code.encode()).hexdigest()
                        arms=["A12"]
                        if mode=="A" and index<2:arms=["A2","A12"]
                        if mode=="C":arms=["C2"]
                        for arm in arms:arm_counts[arm]+=1
                        certified.append({
                            "program":code,
                            "program_sha256":digest,
                            "representation":"SOURCE_INFERRED_PROGRAM",
                            "source_check_count":len(checks),
                            "source_train_count":len(train),
                            "independent_source_certified":True,
                            "arm":arms[0],
                            "arms":arms,
                        })
        receipts.append({
            "id":task["source_id"],
            "status":"SOURCE_VERIFIED" if certified else "NO_SOURCE_VERIFIED",
            "certified":certified,
            "original_author_file_sha256":
                task["original_author_file_sha256"],
            "arm_verified_counts":arm_counts,
            "source_examples":len(source),
        })
        if (i+1)%20==0:print("Q3_NEXT100_SOURCE_PROGRESS",i+1,flush=True)
    summary={arm:sum(bool(r["arm_verified_counts"][arm]) for r in receipts)
             for arm in ("A2","A12","C2")}
    summary["C2_only_vs_A2"]=sum(
        bool(r["arm_verified_counts"]["C2"])
        and not r["arm_verified_counts"]["A2"] for r in receipts)
    summary["C2_only_vs_A12"]=sum(
        bool(r["arm_verified_counts"]["C2"])
        and not r["arm_verified_counts"]["A12"] for r in receipts)
    out_data={
        "schema":SCHEMA,
        "original_source_file_sha256":sha(new100_path),
        "original_revision":UPSTREAM,
        "source_originals":100,
        "source_verified_count":sum(bool(x["certified"]) for x in receipts),
        "prior_exposure":SCOPE,
        "target_gold_accessed":False,
        "receipts":receipts,
        "learned_prior_sha256":sha(prior_path),
        "SOURCE_ABLATION":summary,
        "q3_global":"OPEN",
    }
    _save(out,out_data)
    print("Q3_NEXT100_REAL_SOURCE_POLICY_ABLATION",{
        **summary,
        "source_certified_any":out_data["source_verified_count"],
        "original_target_gold_read":False,"q3_global":"OPEN"},flush=True)


def score(author_root,methods_path,blind_path,predictions_path,expected_sha,out):
    if sha(predictions_path)!=expected_sha:
        raise ValueError("expected immutable original prediction SHA")
    methods=_read(methods_path)
    if methods["prior_exposure"]!=SCOPE or methods["source_originals"]!=100:
        raise ValueError("wrong prospective cohort")
    score_path=str(Path(out).with_suffix(".independent_tmp.json"))
    independent_author_score(author_root,blind_path,methods_path,
                             predictions_path,expected_sha,score_path)
    scored=_read(score_path)
    Path(score_path).unlink()
    cert_by_id={r["id"]:r for r in methods["receipts"]}
    arm_counts={arm:0 for arm in ("A2","A12","C2")}
    record_summary=[]
    for record in scored["records"]:
        chosen=cert_by_id[record["id"]]["certified"]
        wins={p["program_sha256"]:p["exact_original"]
              for p in record["programs"]}
        arm_results={
            arm:any(wins.get(p["program_sha256"],False)
                    for p in chosen if arm in p["arms"])
            for arm in arm_counts}
        for arm in arm_counts:
            arm_counts[arm]+=arm_results[arm]
        record_summary.append({"id":record["id"],"arms":arm_results})
    score_by_id={r["id"]:r["arms"] for r in record_summary}
    exclusively_a2=sum(r["C2"] and not r["A2"]
                       for r in score_by_id.values())
    exclusively_a12=sum(r["C2"] and not r["A12"]
                        for r in score_by_id.values())
    result={
        "schema":"NEUMANN.Q3.NEXT100.POSTFROZEN-ORIGINAL-A-C.v1",
        "original_exact":arm_counts,
        "C2_exclusive_vs_A2":exclusively_a2,
        "C2_exclusive_vs_A12":exclusively_a12,
        "cohort_denominator":100,
        "scientific_scope":SCOPE,
        "prediction_sha256":expected_sha,
        "source_policy_ablation":methods["SOURCE_ABLATION"],
        "q3_global":"OPEN",
        "not_proof_of_cross_author_transfer":True,
        "records":record_summary,
    }
    _save(out,result)
    print("Q3_NEXT100_POSTFROZEN_ORIGINAL_AUTHOR_POLICY_SCORE",
          {k:v for k,v in result.items() if k!="records"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    for command in ("freeze","learn","invent","score"):
        opt=sub.add_parser(command)
        opt.add_argument("--out",required=True)
        if command=="freeze":
            opt.add_argument("--author-root",required=True)
            opt.add_argument("--old50",required=True)
            opt.add_argument("--prior100",required=True)
        elif command=="learn":
            opt.add_argument("--prior100",required=True)
        elif command=="invent":
            opt.add_argument("--new100",required=True)
            opt.add_argument("--prior",required=True)
        elif command=="score":
            opt.add_argument("--author-root",required=True)
            opt.add_argument("--methods",required=True)
            opt.add_argument("--blind",required=True)
            opt.add_argument("--predictions",required=True)
            opt.add_argument("--expected-sha",required=True)
    a=p.parse_args()
    if a.cmd=="freeze":freeze(a.author_root,a.old50,a.prior100,a.out)
    if a.cmd=="learn":learn(a.prior100,a.out)
    if a.cmd=="invent":invent(a.new100,a.prior,a.out)
    if a.cmd=="score":
        score(a.author_root,a.methods,a.blind,a.predictions,
              a.expected_sha,a.out)
