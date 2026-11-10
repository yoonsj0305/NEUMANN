"""Collect actual SOURCE-refuted open-code program repairs from 7 frozen teachers.

No named task operator, no new answer code authored by experimenter.
Correct programs come ONLY from already independently SOURCE-certified prior
open-model research teacher records; bad programs come from the SAME current
frozen 0.5B pretrained model. Every positive/negative is independently
re-executed on the real source inputs in no-network Docker.

This teacher pool is old development SOURCE, not new original-author TEST.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from neumann1.open_program_inventor import (
    IsolatedPython,validate_code,UnsafeProposal,source_same_value)
from neumann1.q3_prompt_contract import (
    SourceContextOverflow,source_discovery_prompt)
from neumann1.q3_source_repair_learning import recertified_repair_prompt
from neumann1.q3_trainable_code_policy import (
    LocalCausalCodePolicy,source_training_rows,recertify_source_rows)


def _hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=True,allow_nan=False)


def collect(teacher_file,revision,out,report,*,max_teachers=7):
    teachers,source_sha=source_training_rows(teacher_file)
    if not 1<=max_teachers<=7 or len(teachers)!=7:
        raise ValueError("exact frozen prior seven SOURCE teacher cohort required")
    if (not isinstance(revision,str) or len(revision)!=40 or
            any(x not in "0123456789abcdef" for x in revision)):
        raise ValueError("immutable model revision SHA required")
    if len({str(x.get("original_id")) for x in teachers})!=7:
        raise ValueError("teacher identity overlap")
    runner=IsolatedPython(max_seconds=8)
    recertify_source_rows(teachers,runner=runner)
    model=LocalCausalCodePolicy(
        model_revision=revision,max_new_tokens=320,
        temperature=0.3,seed=1007,max_context_tokens=4096)
    repairs=[];trials=[]
    for item in teachers[:max_teachers]:
        source_id=item["original_id"]
        n=item["independent_checks"]
        train=item["pairs"][:-n]
        checks=item["pairs"][-n:]
        initial=source_discovery_prompt(train)
        trial={"id":source_id,"origin":"PRIOR_CERTIFIED_SOURCE_OPEN_PROGRAM",
               "original_TARGET_gold_read":False}
        try:
            raw=model.propose(initial)
            code=validate_code(raw)
        except SourceContextOverflow:
            trial["status"]="ABSTAIN_SOURCE_CONTEXT_LIMIT"
            trials.append(trial);continue
        except (UnsafeProposal,ValueError,TypeError):
            trial["status"]="ABSTAIN_PRETRAINED_PROGRAM_INVALID"
            trials.append(trial);continue
        stage=runner.evaluate(code,[x for x,y in train])
        if stage.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
            trial["status"]="ABSTAIN_PRETRAINED_NOT_EXECUTED"
            trials.append(trial);continue
        # Exactly one sealed SOURCE check is common in historical teachers.
        # If the first program already passes training SOURCE, do NOT mine
        # that sealed check for a repair witness.
        if (stage.status=="EXECUTED" and len(stage.outputs)==len(train)
            and all(source_same_value(y,z)
                    for y,(_,z) in zip(stage.outputs,train))):
            trial["status"]="NO_LEGAL_TRAIN_SOURCE_REFUTATION"
            trials.append(trial);continue
        repaired=dict(item)
        repaired.update({
            "repair_prior_program":code,
            "repair_prior_sha256":sha256(code.encode()).hexdigest(),
            "repair_phase":"TRAIN_SOURCE",
            "repair_feedback_checks_count":0,
            "prior_error_origin":"SAME_FROZEN_BASE_MODEL_LIVE_GENERATION",
            "corrected_program_origin":"PREEXISTING_FROZEN_SOURCE_CERTIFICATE",
            "no_target_gold":True})
        try:
            recertified_repair_prompt(repaired,runner)
        except (ValueError,UnsafeProposal) as exc:
            trial["status"]="ABSTAIN_FAILED_REPAIR_RECERTIFICATION"
            trial["error_type"]=type(exc).__name__
            trials.append(trial);continue
        trials.append({
            **trial,"status":"REAL_MODEL_FAILED_TO_CERTIFIED_SOURCE_REPAIR",
            "failed_program_sha256":repaired["repair_prior_sha256"],
            "certified_repair_sha256":item["sha256"]})
        repairs.append(repaired)
        print("Q3_REAL_MODEL_REPAIR_TEACHER_ADMITTED",
              source_id,repaired["repair_prior_sha256"],flush=True)
    Path(out).write_text("".join(_canonical(x)+"\n" for x in repairs))
    summary={
        "schema":"NEUMANN.Q3.SEVEN-TEACHER-REAL-MODEL-REPAIR.v1",
        "source_teachers":len(teachers),
        "sampled":len(trials),
        "real_model_failed_source_repairs":len(repairs),
        "source_sha256":source_sha,
        "revision":revision,
        "repair_output_sha256":_hash(out),
        "independent_author_TARGET_gold_read":False,
        "q3_global":"OPEN",
        "trials":trials,
    }
    Path(report).write_text(_canonical(summary)+"\n")
    print("Q3_SEVEN_MODEL_AUTHORED_SOURCE_REPAIR_COLLECTION",
          {k:v for k,v in summary.items() if k!="trials"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--teachers",required=True)
    p.add_argument("--model-revision",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--max-teachers",type=int,default=7)
    a=p.parse_args()
    collect(a.teachers,a.model_revision,a.out,a.report,
            max_teachers=a.max_teachers)
