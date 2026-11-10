"""Second/final candidate Q3Q6 causal original study, unrelated model-state loss.

HYPOTHESIS: directly learning a query-conditioned *latent predictive state*
from observed SOURCE outcomes can provide a useful generalization signal even
when the base model does not emit a well-formed symbolic hypothesis. A/B/C
same 0.5B pretrained weights, queries, allowed labels and source checks.
C gains 4 real SOURCE-only gradients; B has identical SOURCE memory but no
SGD; A no memory. All original TARGET predictions SHA-frozen BEFORE a separate
scorer downloads author labels. No domain answer operator or code generator.

No novel concept/transfer PASS unless C exclusively solves independent
originals in BOTH separately authored semantic domains; even that is only
minimal initial evidence, not global Q3/Q6 or frontier-scale intelligence.
"""
from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path

from neumann1.q3_predictive_state import PredictiveStatePolicy
from research.q3.q3q6_original_transfer_run import nearest,load
from research.q3.q3q6_two_author_freeze import (
    REV,MODEL,DOMAIN_IDS,canonical,digest)


def context_for_task(task):
    return {
        "observed_original_author_SOURCE":task["demonstration"],
        "domain_observation_metadata":task["domain"],
        "instruction":"Infer a latent relationship from observations; "
                      "do not use a custom task-family rule.",
    }


def evaluate(*,visible_path,source_path,out,revision):
    visible=load(visible_path)
    oracle=load(source_path)
    if (visible.get("schema")!=
        "NEUMANN.Q3Q6.TWO-AUTHOR-ORIGINAL-VISIBLE.v1" or
        len(visible["training_episodes"])!=4 or
        len(visible["evaluation_tasks"])!=8):
        raise ValueError("invalid second original-author SOURCE cohort")
    if any("label" in t["target"] for t in visible["evaluation_tasks"]):
        raise ValueError("original TARGET gold leaked into prediction input")
    source_by_id={s["task_id"]:s for s in oracle}
    if set(source_by_id)!={t["task_id"]
                           for t in visible["evaluation_tasks"]}:
        raise ValueError("SOURCE-only checker split mismatch")
    memory=visible["memory_examples"]
    if not all(m.get("scope")=="TRUSTED_SOURCE_ONLY" for m in memory):
        raise ValueError("unverified memory provenance")
    results={"A":[],"B":[],"C":[]}
    source_training=[]
    update_count=0
    weight_delta=0.0
    for arm in ("A","B","C"):
        model=PredictiveStatePolicy(
            revision=revision,seed=1007,max_updates=4,
            max_context_tokens=4096)
        if arm=="C":
            for episode in visible["training_episodes"]:
                domain=episode["domain"]
                prior=[m for m in memory if m["domain"]==domain]
                out_receipt=model.learn_source(
                    context_for_task(episode),prior,
                    episode["probe"]["input"],
                    episode["probe"]["label"],
                    evidence_id=episode["task_id"]+"/probe/TRUSTED_SOURCE_ONLY")
                source_training.append({
                    "task_id":episode["task_id"],"domain":domain,
                    "receipt":out_receipt})
                print("Q3Q6_PREDICTIVE_STATE_SOURCE_GRADIENT",{
                    "episode":episode["task_id"],
                    "gradient_updates":model.update_count,
                    "actual_weight_delta_l1":out_receipt[
                        "actual_trainable_weight_delta_l1"]},flush=True)
            update_count=model.update_count
            weight_delta=sum(x["receipt"][
                "actual_trainable_weight_delta_l1"]
                for x in source_training)
        for task in visible["evaluation_tasks"]:
            t0=time.perf_counter()
            h=source_by_id[task["task_id"]]
            allowed_history=(
                [m for m in memory if m["domain"]==task["domain"]]
                if arm!="A" else [])
            status="ABSTAIN"
            raw=None
            submitted=None
            correct_source=0
            try:
                ctx=context_for_task(task)
                for key,actual in (
                        ("probe",h["probe_label"]),
                        ("sealed",h["sealed_label"])):
                    observed=model.predict(
                        ctx,allowed_history,task[key]["input"])
                    if observed["prediction"]==actual:
                        correct_source+=1
                target_guess=model.predict(
                    ctx,allowed_history,task["target"]["input"])
                raw=target_guess["prediction"]
                if correct_source==2:
                    submitted=raw
                    status="CERTIFIED_ON_TWO_UNSEEN_SOURCE"
                else:
                    status="ABSTAIN_SOURCE_PREDICTIVE_CONTRADICTION"
            except (ValueError,TypeError,RuntimeError,KeyError) as exc:
                status="ABSTAIN_"+type(exc).__name__
            cases=[{"query":m["query"],"label":m["observed"]}
                   for m in memory if m["domain"]==task["domain"]]
            cases.append({
                "query":task["demonstration"]["input"],
                "label":task["demonstration"]["label"]})
            row={
                "task_id":task["task_id"],
                "domain":task["domain"],
                "original_id":task["target"]["original_id"],
                "source_certified":correct_source==2,
                "status":status,
                "number_correct_independent_source_checks":correct_source,
                "frozen_submitted_prediction":submitted,
                "frozen_raw_diagnostic_prediction":raw,
                "classical_matched_source_prediction":nearest(
                    task["target"]["input"],cases),
                "elapsed_seconds":round(time.perf_counter()-t0,4),
                "original_TARGET_gold_seen":False,
            }
            results[arm].append(row)
            print("Q3Q6_PREDICTIVE_STATE_ORIGINAL",{
                "arm":arm,"task_id":task["task_id"],
                "source_checks_correct":correct_source,
                "submitted":submitted is not None,
                "gold_read":False},flush=True)
        del model
        gc.collect()
    receipt={
        "schema":"NEUMANN.Q3Q6.ORIGINAL-UNSEEN-PREDICTIONS.v1",
        "study_id":"NEUMANN.Q3Q6.PREDICTIVE-STATE-SECOND-FROZEN.v2",
        "visible_sha256":digest(Path(visible_path).read_bytes()),
        "source_oracle_sha256":digest(Path(source_path).read_bytes()),
        "base_revision":revision,"base_model":MODEL,
        "same_pretrained_weights":True,
        "same_CONTEXT_and_query_calls_per_target":True,
        "B_C_same_approved_source_memory":True,
        "C_actual_weight_updates":update_count,
        "C_weight_delta_l1":weight_delta,
        "SOURCE_only_gradient_receipts":source_training,
        "A_B_C":results,"original_TARGET_gold_read":False,
        "model_learned_latent_representation_without_symbolic_output":True,
        "independent_concept_invention_proven":False,
    }
    Path(out).write_text(canonical(receipt)+"\n")
    print("Q3Q6_SECOND_NO_GOLD_PREDICTIONS_FROZEN",{
        "hash":digest(Path(out).read_bytes()),
        "C_updates":update_count,"C_delta":weight_delta},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--visible",required=True)
    p.add_argument("--source-oracle",required=True)
    p.add_argument("--revision",default=REV)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    evaluate(visible_path=a.visible,source_path=a.source_oracle,
             out=a.out,revision=a.revision)
