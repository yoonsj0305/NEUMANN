"""Actual OPEN model SOURCE repair pilot on pre-exposed original CodeARC.

Selected IDs were already opened in prior Q3 #744 experiments. This is an
engineering causal study of SOURCE synthesis and counterexample repair,
not new-author FIRST, not Q3 global PASS, and NEVER scores TARGET gold.

A: same pretrained model + certified unrelated-method memory.
B: same model + 10-step contextual SOURCE-program imitation LoRA.
C: same model + 10-step mixed contextual/source-refutation LoRA.
These B/C equal-step groups isolate the effect of repair curriculum.
Same model revision, prompt, one isolated executor and proposal budget.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from neumann1.q3_single_discovery_core import SingleDiscoveryCore,SourceMethodMemory
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy
from neumann1.open_program_inventor import IsolatedPython

IDS=(184,255)
SCHEMA="NEUMANN.Q3.SOURCE-REPAIR-PILOT.v1"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(blind, teachers, adapter, context_adapter, revision, output,
        onpolicy_adapter=None):
    dataset=json.loads(Path(blind).read_text())
    if dataset.get("schema")!="NEUMANN.Q3.NEURAL.CODEARC.BLIND.v1":
        raise ValueError("expected immutable previous original SOURCE")
    indexed={r["id"]:r for r in dataset["records"]}
    if any(i not in indexed for i in IDS):
        raise ValueError("pre-exposed original SOURCE IDs unavailable")
    rows=[json.loads(line) for line in Path(teachers).read_text().splitlines()
          if line.strip()]
    sandbox=IsolatedPython(max_seconds=8)
    memory=SourceMethodMemory(sandbox)
    memory.import_source_teachers(rows)
    memory.freeze()
    if {str(r["original_id"]) for r in rows}&{str(i) for i in IDS}:
        raise ValueError("SOURCE teacher overlaps pre-exposed pilot")
    base=LocalCausalCodePolicy(
        model_revision=revision,max_new_tokens=384,temperature=0.3)
    contextual=LocalCausalCodePolicy(
        model_revision=revision,adapter_path=context_adapter,
        max_new_tokens=384,temperature=0.3)
    modified=LocalCausalCodePolicy(
        model_revision=revision,adapter_path=adapter,
        max_new_tokens=384,temperature=0.3)
    policies=[("A",base),("B",contextual),("C",modified)]
    if onpolicy_adapter:
        actual_model_failures=LocalCausalCodePolicy(
            model_revision=revision,adapter_path=onpolicy_adapter,
            max_new_tokens=384,temperature=0.3)
        policies.append(("D",actual_model_failures))
    records=[]
    for pid in IDS:
        source=indexed[pid]["source"]
        if len(source)!=7:raise ValueError("original SOURCE split changed")
        row={"id":pid,"arms":{}}
        for name,policy in policies:
            core_outcome=SingleDiscoveryCore(
                policy,sandbox,memory=memory,max_proposals=2).discover(
                    source[:6],source[6:],
                    reuse_memory=True)
            discovery=core_outcome.discovery
            row["arms"][name]={
                "status":discovery.status,"source_verified":discovery.verified,
                "program_sha256":discovery.frozen_sha256,
                "source_program":discovery.program if discovery.verified else None,
                "original_target_predictions":[],
                "original_target_execution_status":"NOT_RUN_SOURCE_ABSTAIN",
                "attempts":[{
                    "iteration":a.iteration,"source_correct":a.source_correct,
                    "source_total":a.source_total,"status":a.status,
                    "sha256":a.sha256,
                    # The hypothesis is SOURCE-only, no test gold.
                    "source_hypothesis":a.program}
                    for a in discovery.attempts]}
            if discovery.verified:
                # Only test INPUTS, not author-gold outputs, are exposed here.
                # Freeze all emitted target predictions before a separate
                # independent-author scorer opens withheld originals.
                held_inputs=indexed[pid].get("target_inputs",[])
                if len(held_inputs)!=3:
                    raise ValueError("expected three source-blind original inputs")
                o=sandbox.evaluate(discovery.program,held_inputs)
                row["arms"][name]["original_target_execution_status"]=o.status
                if o.status=="EXECUTED":
                    row["arms"][name]["original_target_predictions"]=list(o.outputs)
        records.append(row)
        print("Q3_STATEFUL_SOURCE_PILOT",pid,
              {k:(v["status"],[
                  a["source_correct"] for a in v["attempts"]])
                  for k,v in row["arms"].items()},flush=True)
    scores={
        k:sum(row["arms"][k]["source_verified"] for row in records)
        for k,_ in policies}
    output_record={
        "schema":SCHEMA,"original_scope":"POSTFIRST_SOURCE_ONLY",
        "model_revision":revision,"blind_sha256":digest(blind),
        "certified_memory_sha256":digest(teachers),
        "pretrained_memory_correct_source":scores["A"],
        "contextual_imitation_10step_correct_source":scores["B"],
        "source_refutation_10step_correct_source":scores["C"],
        "model_generated_repair_10step_correct_source":scores.get("D"),
        "model_generated_repair_residual_over_all_controls":(
            sum(
                r["arms"]["D"]["source_verified"] and not any(
                    r["arms"][k]["source_verified"] for k in ("A","B","C"))
                for r in records)
            if onpolicy_adapter else None),
        "model_generated_repair_regressions_vs_control_B":(
            sum(
                r["arms"]["B"]["source_verified"] and not r["arms"]["D"]["source_verified"]
                for r in records)
            if onpolicy_adapter else None),
        "pre_registered_source_residual":sum(
            r["arms"]["C"]["source_verified"]
            and not r["arms"]["B"]["source_verified"] for r in records),
        "global_q3":"OPEN","original_target_gold_seen":False,
        "model_scientific_scope":"PREEXPOSED_CODEARC_DEV_ONLY",
        "original_outputs_only_independent_score_after_SHA_freeze":True,
        "records":records}
    Path(output).write_text(
        json.dumps(output_record,sort_keys=True,ensure_ascii=True,indent=2)+"\n")
    print("Q3_SOURCE_REFUTATION_ACTUAL_MODEL_RESULT",
          json.dumps({k:v for k,v in output_record.items()
                      if k not in ("records",)},sort_keys=True),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--blind",required=True)
    p.add_argument("--teachers",required=True)
    p.add_argument("--adapter",required=True)
    p.add_argument("--context-adapter",required=True)
    p.add_argument("--onpolicy-adapter",default=None,
                   help="model-trained on its own independently refuted SOURCE hypotheses")
    p.add_argument("--revision",required=True)
    p.add_argument("--out",required=True)
    x=p.parse_args()
    run(x.blind,x.teachers,x.adapter,x.context_adapter,x.revision,x.out,
        onpolicy_adapter=x.onpolicy_adapter)
