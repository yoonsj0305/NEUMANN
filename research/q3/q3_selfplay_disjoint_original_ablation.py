"""Q3 self-play causal A/C: identical code core and execution budgets.

A: frozen original pretrained model
C: SAME pretrained weights + self-generated verified task-curriculum LoRA

No handcrafted target solvers. Tests on new generator programs (program SHA
disjoint from training) plus previously exposed ORIGINAL AUTHOR SOURCE-only.
No original author TARGET/test gold ever read, therefore no global Q3 proof.
"""
from __future__ import annotations

import argparse,gc,hashlib,json,time
from pathlib import Path

from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.open_program_inventor import (
    GenerativeProgramInventor,IsolatedPython,source_same_value)
from research.q3.q3_selfplay_worlds import SCHEMA,canonical

ORIGINAL_IDS=(
    "67e8384a","a87f7484","c909285e",
    "575b1a71","c8f0f002","c8b7cc0f",
)


def _rows(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()
            if x.strip()]


def evaluate(train_worlds,heldout_worlds,original_source,adapter,revision,out):
    train=_rows(train_worlds)
    heldout=_rows(heldout_worlds)
    if len(train)<2 or not heldout:
        raise ValueError("synthetic model-authored worlds are insufficient")
    train_ids={w["program_sha256"] for w in train}
    hold_ids={w["program_sha256"] for w in heldout}
    if train_ids&hold_ids or len(train_ids)!=len(train) or len(hold_ids)!=len(heldout):
        raise ValueError("selfplay train/heldout program leakage")
    if any(w.get("schema")!=SCHEMA for w in (*train,*heldout)):
        raise ValueError("not verified model-authored synthetic worlds")
    manifest=json.loads((Path(adapter)/
        "neumann_selfplay_training_manifest.json").read_text())
    if (manifest.get("source_worlds_sha256")!=
            hashlib.sha256(Path(train_worlds).read_bytes()).hexdigest()
        or manifest.get("model_revision")!=revision
        or manifest.get("self_play_only") is not True
        or manifest.get("original_author_TARGET_gold_read") is not False):
        raise ValueError("wrong trained model source world provenance")
    cohort=json.loads(Path(original_source).read_text())
    if (cohort.get("original_source_count")!=100 or
            cohort.get("no_target_gold_in_payload") is not True):
        raise ValueError("external AUTHOR SOURCE only")
    index={r["source_id"]:r for r in cohort["records"]}
    if not set(ORIGINAL_IDS)<=set(index):
        raise ValueError("original SOURCE identifiers missing")
    runner=IsolatedPython(max_seconds=8)
    output={"synthetic":{},"real_original_source":{}}
    for name,adapter_path in (("A_base",None),("C_selfplay",adapter)):
        model=LocalCausalCodePolicy(
            model_revision=revision,adapter_path=adapter_path,
            max_new_tokens=320,temperature=0.3,seed=1007,
            max_context_tokens=4096)
        for task in heldout:
            id=task["world_id"]
            start=time.perf_counter()
            d=GenerativeProgramInventor(
                model,runner,max_proposals=2).discover(
                task["source_train"],
                independent_source_checks=task["source_sealed_check"])
            exact=False
            if d.verified:
                test=task["synthetic_test"]
                result=runner.evaluate(d.program,[x for x,y in test])
                exact=(result.status=="EXECUTED" and
                       len(result.outputs)==len(test) and all(
                    source_same_value(pred,y)
                    for pred,(_,y) in zip(result.outputs,test)))
            output["synthetic"].setdefault(id,{
                "source_type":task["program_generation_type"]})[name]={
                "SOURCE_verified":bool(d.verified),
                "independent_synthetic_TEST_exact":bool(exact),
                "status":d.status,
                "wall_s":round(time.perf_counter()-start,3)}
            print("Q3_SELFPLAY_PROGRAM_DISJOINT",name,id,
                  {"certified":d.verified,"test_exact":exact},flush=True)
        for id in ORIGINAL_IDS:
            source=index[id]["source_pairs"]
            start=time.perf_counter()
            d=GenerativeProgramInventor(
                model,runner,max_proposals=2).discover(
                source[:-1],independent_source_checks=source[-1:])
            output["real_original_source"].setdefault(id,{})[name]={
                "SOURCE_verified":bool(d.verified),"status":d.status,
                "wall_s":round(time.perf_counter()-start,3),
                "best_SOURCE_train_correct":max(
                    (a.source_correct for a in d.attempts),default=0)}
            print("Q3_SELFPLAY_REAL_ORIGINAL_SOURCE",name,id,
                  d.verified,flush=True)
        del model;gc.collect()
    syn=list(output["synthetic"].values())
    real=list(output["real_original_source"].values())
    summ={
        "schema":"NEUMANN.Q3.ONE-CORE-SELFPLAY-LEARNED-DISCOVERY.v1",
        "source_train_worlds":len(train),
        "strict_program_disjoint_synthetic_heldout":len(syn),
        "frozen_real_original_SOURCE":len(real),
        "A_synthetic_original_exact":sum(x["A_base"][
            "independent_synthetic_TEST_exact"] for x in syn),
        "C_synthetic_original_exact":sum(x["C_selfplay"][
            "independent_synthetic_TEST_exact"] for x in syn),
        "C_synthetic_exclusive":sum(
            x["C_selfplay"]["independent_synthetic_TEST_exact"] and
            not x["A_base"]["independent_synthetic_TEST_exact"] for x in syn),
        "A_real_original_SOURCE_exact":sum(
            x["A_base"]["SOURCE_verified"] for x in real),
        "C_real_original_SOURCE_exact":sum(
            x["C_selfplay"]["SOURCE_verified"] for x in real),
        "C_real_original_SOURCE_exclusive":sum(
            x["C_selfplay"]["SOURCE_verified"] and
            not x["A_base"]["SOURCE_verified"] for x in real),
        "original_author_TARGET_gold_accessed":False,
        "no_human_written_target_operator":True,
        "q3_global":"OPEN",
        "train_worlds_sha256":hashlib.sha256(
            Path(train_worlds).read_bytes()).hexdigest(),
        "heldout_worlds_sha256":hashlib.sha256(
            Path(heldout_worlds).read_bytes()).hexdigest(),
    }
    Path(out).write_text(canonical(
        {"summary":summ,"per_task":output})+"\n")
    print("Q3_REAL_ONE_CORE_AUTOGENERATED_SELFPLAY_CAUSAL_VERDICT",
          summ,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--train-worlds",required=True)
    p.add_argument("--heldout-worlds",required=True)
    p.add_argument("--original-source",required=True)
    p.add_argument("--adapter",required=True)
    p.add_argument("--revision",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    evaluate(a.train_worlds,a.heldout_worlds,a.original_source,
             a.adapter,a.revision,a.out)
