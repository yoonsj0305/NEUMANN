"""Q3 learned open-program repair: real model failures, real SOURCE-certified methods.

No authored operator, ARC-family router, or target labels. The source of the
corrected program is an ALREADY independently SOURCE-certified executable
from a previous immutable development experiment; the wrong program is an
actual pretrained-model proposal. Therefore this produces *assisted*
on-policy-error -> verified-correction supervised data, NOT proof that the
model originally authored the corrected program. It must improve a frozen
heldout C-only exact original to count as causal invention progress.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import (
    IsolatedPython,validate_code,source_same_value,UnsafeProposal,
)
from neumann1.q3_prompt_contract import source_discovery_prompt
from neumann1.q3_source_repair_learning import recertified_repair_prompt
from neumann1.q3_single_discovery_core import SourceMethodMemory
from neumann1.q3_trainable_code_policy import LocalCausalCodePolicy


def _sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def collect(source_path,method_path,*,out,report,model_revision,max_tasks=6,
            seed=1007):
    if (not isinstance(model_revision,str) or
            len(model_revision)!=40 or
            any(c not in "0123456789abcdef" for c in model_revision)):
        raise ValueError("immutable model-weight SHA required")
    source=json.loads(Path(source_path).read_text())
    methods=json.loads(Path(method_path).read_text())
    if (source.get("original_source_count")!=50 or
            source.get("no_target_gold_in_payload") is not True or
            methods.get("source_originals")!=50 or
            methods.get("target_gold_accessed") is not False or
            not 1<=max_tasks<=50):
        raise ValueError("pinned original-author SOURCE-only teacher required")
    by_id={x["source_id"]:x for x in source["records"]}
    verified=[item for item in methods["receipts"]
              if item.get("certified")]
    if not verified:
        raise ValueError("no independent SOURCE-certified prior programs")
    verified.sort(key=lambda item:item["id"])
    # Do NOT select based on model failure or ORIGINAL TEST success.
    verified=verified[:max_tasks]
    runner=IsolatedPython(max_seconds=8)
    memory=SourceMethodMemory(runner,max_episodes=max_tasks)
    proposer=LocalCausalCodePolicy(
        model_revision=model_revision,
        max_new_tokens=320,temperature=0.3,seed=seed)
    rows=[]
    trials=[]
    for item in verified:
        sid=item["id"]
        record=by_id.get(sid)
        if record is None:
            raise ValueError("method original ID not in SOURCE registry")
        pairs=record["source_pairs"]
        if not 3<=len(pairs)<=32:
            raise ValueError("unexpected independent SOURCE split")
        train=tuple((x,y) for x,y in pairs[:-1])
        checks=tuple((x,y) for x,y in pairs[-1:])
        corrected=item["certified"][0]
        # Full recertification independently checks all actual author SOURCE
        # witnesses in the same no-network Docker backend.
        entry=memory.admit(sid,train,checks,corrected["program"])
        initial_prompt=source_discovery_prompt(train)
        raw=proposer.propose(initial_prompt)
        trial={"id":sid,"prior_certified_sha256":entry.program_sha256,
               "model_revision":model_revision,"model_did_correct":False,
               "target_gold_accessed":False}
        try:
            wrong=validate_code(raw)
        except (UnsafeProposal,ValueError,TypeError):
            trial["status"]="MODEL_CODE_NOT_EXECUTABLE"
            trials.append(trial)
            continue
        trial["model_first_program_sha256"]=sha256(wrong.encode()).hexdigest()
        # A wrong model proposal is never a positive teacher; only a
        # SOURCE-refuted stimulus for an already certified correction.
        episode={
            "schema":"NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1",
            "provenance":"ORIGINAL_SOURCE_ONLY",
            "original_id":sid,"pairs":[list(p) for p in (*train,*checks)],
            "independent_checks":len(checks),
            "program":entry.program,"sha256":entry.program_sha256,
            "repair_prior_program":wrong,
            "repair_prior_sha256":sha256(wrong.encode()).hexdigest(),
            "repair_phase":"TRAIN_SOURCE",
            "no_target_gold":True,
            "correction_source":"PREEXISTING_INDEPENDENT_SOURCE_CERTIFICATE",
            "prior_error_source":"ACTUAL_PINNED_PRETRAINED_MODEL"}
        # Never synthesize fake repair evidence; infer its actual status
        # from reexecution and let fully-correct first proposals abstain.
        first=runner.evaluate(wrong,[x for x,y in train])
        if first.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
            trial["status"]="MODEL_NOT_EXECUTED"
            trials.append(trial)
            continue
        source_wrong=(
            first.status!="EXECUTED" or
            len(first.outputs)!=len(train) or
            any(not source_same_value(got,y)
                for got,(_,y) in zip(first.outputs,train)))
        episode["repair_phase"]=(
            "TRAIN_SOURCE" if source_wrong else "INDEPENDENT_SOURCE")
        try:
            prompt,phase=recertified_repair_prompt(episode,runner)
        except (ValueError,UnsafeProposal):
            trial["status"]="NO_GENUINE_REFUTATION"
            trials.append(trial)
            continue
        if phase!=episode["repair_phase"]:
            raise AssertionError("repair phase mismatch")
        trial.update({"status":"ACTUAL_MODEL_SOURCE_REFUTATION",
                      "repair_phase":phase,
                      "repair_prompt_sha256":sha256(prompt.encode()).hexdigest()})
        rows.append(episode)
        trials.append(trial)
        print("Q3_ACTUAL_ON_POLICY_ERROR_ASSISTED_REPAIR",{
            "id":sid,"prior_sha256":episode["repair_prior_sha256"],
            "corrected_sha256":entry.program_sha256,
            "refutation":phase},flush=True)
    memory.freeze()
    Path(out).write_text("".join(_canonical(x)+"\n" for x in rows))
    summary={
        "schema":"NEUMANN.Q3.ASSISTED-ON-POLICY-SOURCE-REPAIR.v1",
        "pretrained_model_revision":model_revision,
        "source_registry_sha256":_sha(source_path),
        "certified_methods_sha256":_sha(method_path),
        "source_certified_prior_methods_selected":len(verified),
        "actual_model_proposals":len(trials),
        "source_refuted_executable_repair_examples":len(rows),
        "repair_training_file_sha256":_sha(out),
        "repair_teacher_is_model_authored":False,
        "original_target_gold_accessed":False,
        "q3_global":"OPEN","trials":trials}
    Path(report).write_text(_canonical(summary)+"\n")
    print("Q3_REAL_ASSISTED_MODEL_SOURCE_REPAIR_COLLECTION",{
        k:v for k,v in summary.items() if k!="trials"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--methods",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--model-revision",required=True)
    p.add_argument("--max-tasks",type=int,default=6)
    a=p.parse_args()
    collect(a.source,a.methods,out=a.out,report=a.report,
            model_revision=a.model_revision,max_tasks=a.max_tasks)
