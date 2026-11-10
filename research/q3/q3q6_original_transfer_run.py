"""Q3/Q6 original-author two-domain SOURCE-only A/B/C and sealed scorer.

infer NEVER opens original TARGET gold. score has no model. Production core
must learn latent-world hypotheses from trusted SOURCE, not answer programs.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

from neumann1.causal_experience import CausalExperienceCore
from neumann1.q3_latent_world_policy import TrainableLatentWorldPolicy
from research.q3.q3q6_two_author_freeze import (
    DOMAIN_IDS,MODEL,REV,canonical,digest)


def load(path):
    return json.loads(Path(path).read_text())


class PolicyView:
    def __init__(self,model,memory,learn):
        self.model=model
        self.memory=tuple(memory)
        self.learn=learn

    def hypotheses(self,context,history,queries):
        return self.model.hypotheses(
            context,self.memory+tuple(history),queries)

    def learn_from_counterexample(self,events):
        if self.learn:
            return self.model.learn_from_counterexample(events)
        return None


def authorized_oracle(task_id,labels):
    def verify(task,query_id,query,actual,evidence_id):
        row=labels.get(query_id)
        return (
            task==task_id and row is not None and
            evidence_id==task_id+"/"+query_id+"/SOURCE-only" and
            canonical(row["input"])==canonical(query) and
            canonical(row["label"])==canonical(actual))
    return verify


def attempt(model,task,memory,labels,*,training):
    t0=time.perf_counter()
    core=CausalExperienceCore(
        PolicyView(model,memory,training),
        max_hypotheses=2,max_experiences=16)
    context={
        "original_author_domain":task["domain"],
        "known_source_example":task["demonstration"],
        "infer_new_latent_variables":"Use observed examples and falsifiable "
                                    "relations, not a task-specific solver",
    }
    allowed={
        "probe":task["probe"]["input"],
        "sealed":task["sealed"]["input"],
    }
    if not training:
        allowed["target"]=task["target"]["input"]
    first=None
    second=None
    trained=None
    sealed=False
    raw_prediction=None
    submitted=None
    status="ABSTAIN_NO_MODEL_HYPOTHESIS"
    try:
        core.start(
            task["task_id"],context,allowed,
            sealed_queries={"sealed"},
            target_queries=() if training else {"target"})
        first=core.hypotheses[0].digest
        updates=core.observe(
            "probe",labels["probe"]["label"],
            evidence_id=task["task_id"]+"/probe/SOURCE-only",
            verify_source=authorized_oracle(task["task_id"],labels))
        trained=updates[0].learning_receipt
        core.revise(context)
        second=core.hypotheses[0].digest
        core.freeze()
        sealed=core.certify_sealed_source(
            "sealed",labels["sealed"]["label"],
            evidence_id=task["task_id"]+"/sealed/SOURCE-only",
            verify_source=authorized_oracle(task["task_id"],labels))
        if not training:
            raw_prediction=core.hypotheses[0].predictions.get("target")
            if sealed:
                submitted=core.predict_target("target")
        status="CERTIFIED_SOURCE" if sealed else "ABSTAIN_SOURCE_CONTRADICTION"
    except (ValueError,TypeError,KeyError,RuntimeError) as exc:
        status="ABSTAIN_"+type(exc).__name__
    return {
        "status":status,
        "source_certified":sealed,
        "initial_latent_sha256":first,
        "revised_latent_sha256":second,
        "revised_latent_changed":bool(first and second and first!=second),
        "learning_receipt":trained,
        "frozen_submitted_prediction":submitted,
        "frozen_raw_diagnostic_prediction":raw_prediction,
        "elapsed_seconds":round(time.perf_counter()-t0,4),
        "TARGET_gold_seen":False,
    }


def tokenize(x):
    return re.findall(r"[a-z0-9]+",canonical(x).lower())


def nearest(query,rows):
    """Transparent matched-SOURCE classical retrieval; not SOTA specialist."""
    if not rows:
        return None
    q=Counter(tokenize(query))
    docs=[Counter(tokenize(x["query"])) for x in rows]
    df=Counter()
    for doc in docs:
        df.update(doc.keys())
    idf={w:math.log((len(docs)+1)/(1+df[w]))+1 for w in df}
    nq=math.sqrt(sum((v*idf.get(w,1))**2 for w,v in q.items()))
    best=(float("-inf"),0)
    for i,doc in enumerate(docs):
        nd=math.sqrt(sum((v*idf[w])**2 for w,v in doc.items()))
        dot=sum(v*doc.get(w,0)*idf.get(w,1)**2 for w,v in q.items())
        similarity=dot/(nq*nd) if nq*nd else 0
        if (similarity,-i)>best:
            best=(similarity,-i)
    return rows[-best[1]]["label"]


def infer(visible_path,source_path,out,revision):
    visible=load(visible_path)
    source_oracle=load(source_path)
    if (visible.get("schema")!=
        "NEUMANN.Q3Q6.TWO-AUTHOR-ORIGINAL-VISIBLE.v1" or
        len(visible["training_episodes"])!=4 or
        len(visible["evaluation_tasks"])!=8):
        raise ValueError("frozen original author cohort altered")
    if any("label" in t["target"] for t in visible["evaluation_tasks"]):
        raise ValueError("original TARGET gold reached model inputs")
    hidden={row["task_id"]:row for row in source_oracle}
    if set(hidden)!={t["task_id"] for t in visible["evaluation_tasks"]}:
        raise ValueError("SOURCE checker alignment invalid")
    for e in visible["memory_examples"]:
        if e["scope"]!="TRUSTED_SOURCE_ONLY":
            raise ValueError("TARGET gold in remembered experiences")
    results={"A":[],"B":[],"C":[]}
    training=[]
    updates=0
    delta=0.0
    for arm in ("A","B","C"):
        neural=TrainableLatentWorldPolicy(
            revision=revision,max_new_tokens=500,
            max_context_tokens=4096,max_updates=4,seed=1007)
        if arm=="C":
            for e in visible["training_episodes"]:
                labels={n:e[n] for n in ("probe","sealed")}
                record=attempt(neural,e,visible["memory_examples"],
                               labels,training=True)
                training.append({
                    "domain":e["domain"],"task_id":e["task_id"],
                    "result":record})
                print("Q3Q6_SOURCE_GRADIENT",{
                    "task":e["task_id"],"status":record["status"],
                    "weight_updates":neural.update_count},flush=True)
            updates=neural.update_count
            delta=sum(
                record["result"]["learning_receipt"][
                    "actual_trainable_weight_delta_l1"]
                for record in training
                if record["result"]["learning_receipt"] is not None)
        for t in visible["evaluation_tasks"]:
            task_id=t["task_id"]
            h=hidden[task_id]
            labels={
                "probe":{"input":t["probe"]["input"],
                         "label":h["probe_label"]},
                "sealed":{"input":t["sealed"]["input"],
                          "label":h["sealed_label"]},
            }
            memory=([m for m in visible["memory_examples"]
                     if m["domain"]==t["domain"]] if arm!="A" else [])
            r=attempt(neural,t,memory,labels,training=False)
            examples=[{"query":m["query"],"label":m["observed"]}
                      for m in visible["memory_examples"]
                      if m["domain"]==t["domain"]]
            examples.append({
                "query":t["demonstration"]["input"],
                "label":t["demonstration"]["label"]})
            r["classical_matched_source_prediction"]=nearest(
                t["target"]["input"],examples)
            r["task_id"]=task_id
            r["domain"]=t["domain"]
            r["original_id"]=t["target"]["original_id"]
            results[arm].append(r)
            print("Q3Q6_MODEL_FROZEN_ORIGINAL",{
                "arm":arm,"domain":t["domain"],
                "task":task_id,"status":r["status"],
                "gold_access":False},flush=True)
        del neural
        gc.collect()
    receipt={
        "schema":"NEUMANN.Q3Q6.ORIGINAL-UNSEEN-PREDICTIONS.v1",
        "visible_sha256":digest(Path(visible_path).read_bytes()),
        "source_oracle_sha256":digest(Path(source_path).read_bytes()),
        "base_revision":revision,
        "same_pretrained_weights":True,
        "same_context_cap":4096,
        "same_proposal_budget":True,
        "B_C_same_approved_source_memory":True,
        "C_actual_weight_updates":updates,
        "C_weight_delta_l1":delta,
        "original_TARGET_gold_read":False,
        "training":training,
        "A_B_C":results,
    }
    Path(out).write_text(canonical(receipt)+"\n")
    print("Q3Q6_PREDICTIONS_FROZEN",{
        "sha256":digest(Path(out).read_bytes()),
        "C_updates":updates,"C_weight_delta_l1":delta,
        "scoring_hidden_original_TARGET_not_read":True},flush=True)


def score(predictions,gold_path,manifest_path,out):
    p=load(predictions)
    gold=load(gold_path)
    manifest=load(manifest_path)
    if p.get("schema")!="NEUMANN.Q3Q6.ORIGINAL-UNSEEN-PREDICTIONS.v1":
        raise ValueError("not frozen independent predictions")
    if p["original_TARGET_gold_read"] is not False:
        raise ValueError("TARGET label was already opened")
    if (manifest["TARGET_gold_sha256"]!=digest(
            Path(gold_path).read_bytes()) or
        manifest["model_visible_sha256"]!=p["visible_sha256"] or
        manifest["SOURCE_oracle_sha256"]!=p["source_oracle_sha256"]):
        raise ValueError("immutable data split SHA mismatch")
    truth={x["task_id"]:x for x in gold}
    if len(truth)!=8:
        raise ValueError("incorrect heldout original target count")
    outputs=[]
    for idx in range(8):
        by_arm={a:p["A_B_C"][a][idx] for a in ("A","B","C")}
        task=by_arm["A"]["task_id"]
        if not all(r["task_id"]==task for r in by_arm.values()):
            raise ValueError("different test tasks across A B C")
        actual=truth[task]["label"]
        labels={}
        for arm,r in by_arm.items():
            submitted=r["frozen_submitted_prediction"]
            raw=r["frozen_raw_diagnostic_prediction"]
            labels[arm]={
                "exact":submitted is not None and
                        canonical(submitted)==canonical(actual),
                "raw_unverified_exact":raw is not None and
                        canonical(raw)==canonical(actual),
                "source_certified":r["source_certified"],
                "status":r["status"],
                "seconds":r["elapsed_seconds"],
                "prediction_sha256":digest(canonical(submitted)),
            }
        classical=by_arm["C"]["classical_matched_source_prediction"]
        labels["classical_nearest"]={"exact":classical==actual}
        outputs.append({
            "task_id":task,"original_id":truth[task]["original_id"],
            "domain":truth[task]["domain"],"results":labels})
    stats={}
    for domain in DOMAIN_IDS:
        subset=[x for x in outputs if x["domain"]==domain]
        stats[domain]={
            "original_count":len(subset),
            "A_exact":sum(x["results"]["A"]["exact"] for x in subset),
            "B_exact":sum(x["results"]["B"]["exact"] for x in subset),
            "C_exact":sum(x["results"]["C"]["exact"] for x in subset),
            "classical_exact":sum(
                x["results"]["classical_nearest"]["exact"] for x in subset),
            "C_exclusive_over_B":sum(
                x["results"]["C"]["exact"] and
                not x["results"]["B"]["exact"] for x in subset),
            "C_exclusive_over_B_and_classical":sum(
                x["results"]["C"]["exact"] and
                not x["results"]["B"]["exact"] and
                not x["results"]["classical_nearest"]["exact"]
                for x in subset),
            "C_unverified_raw_exact":sum(
                x["results"]["C"]["raw_unverified_exact"] for x in subset),
        }
    eligible=(p["C_actual_weight_updates"]>0 and
              p["C_weight_delta_l1"]>0)
    condition=eligible and all(
        stats[x]["C_exclusive_over_B_and_classical"]>0
        for x in DOMAIN_IDS)
    report={
        "schema":"NEUMANN.Q3Q6.CAUSAL-ORIGINAL-SCORE.v1",
        "causal_two_domain_initial_condition":bool(condition),
        "C_actual_weight_updates":p["C_actual_weight_updates"],
        "C_weight_delta_l1":p["C_weight_delta_l1"],
        "domains":stats,
        "originals":outputs,
        "independent_replication_done":False,
        "strongest_possible_specialist_exhausted":False,
        "public_benchmark_pretraining_overlap_unknown":True,
        "Q3_global":"OPEN","Q6_global":"OPEN",
        "prediction_bundle_sha256":digest(Path(predictions).read_bytes()),
        "original_TARGET_sha256":digest(Path(gold_path).read_bytes()),
    }
    Path(out).write_text(canonical(report)+"\n")
    print("Q3Q6_INDEPENDENT_ORIGINAL_SCORE",{
        "domains":stats,"C_updates":p["C_actual_weight_updates"],
        "two_domain_condition":bool(condition),
        "Q3_global":"OPEN","Q6_global":"OPEN"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="action",required=True)
    e=sub.add_parser("infer")
    for n in ("visible","source-oracle","out"):
        e.add_argument("--"+n,required=True)
    e.add_argument("--revision",default=REV)
    s=sub.add_parser("score")
    for n in ("predictions","gold","manifest","out"):
        s.add_argument("--"+n,required=True)
    args=p.parse_args()
    if args.action=="infer":
        infer(args.visible,args.source_oracle,args.out,args.revision)
    else:
        score(args.predictions,args.gold,args.manifest,args.out)
