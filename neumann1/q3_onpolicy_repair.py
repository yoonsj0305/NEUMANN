"""Q3: train on the model's *actual* failed SOURCE hypotheses, not AST corruptions.

PRECONDITION: immutable independently SOURCE-certified model-authored teacher
programs. The same frozen base policy produces a whole proposed Python program
using leave-self-out past methods and its task SOURCE examples. The independent
sandbox executes its hypothesis and discovers original SOURCE counterexamples.

This creates a supervised REPAIR observation: SOURCE + original failed
program + measured witness -> a previously SOURCE-certified correct method.
No human-coded task-family solution, no target-gold output, no synthetic
negative program or missing model state. Scientific generalization requires
separate original-author gold scored only after predictions are frozen.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .open_program_inventor import validate_code, UnsafeProposal, IsolatedPython
from .q3_prompt_contract import source_revision_prompt


SCHEMA = "NEUMANN.Q3.ONPOLICY-REPAIR-SOURCE.v1"


def _sha(data: str) -> str:
    return sha256(data.encode()).hexdigest()


def source_error_witness(program, teacher, runner):
    """Recompute SOURCE evidence using the real sandbox, never target gold."""
    from .open_program_inventor import Execution
    program = validate_code(program)
    items = teacher["pairs"]
    n_check = teacher["independent_checks"]
    if not isinstance(n_check, int) or not 1 <= n_check < len(items):
        raise ValueError("disjoint independently certified SOURCE split required")
    train = items[:-n_check]
    checks = items[-n_check:]
    result = runner.evaluate(program, [x for x, _ in items])
    if (result.status not in ("EXECUTED", "EXECUTED_WITH_ERRORS")
        or len(result.outputs) != len(items)
        or len(result.errors) != len(items)):
        return None
    train_correct = sum(
        err is None and got == y for got, err, (_, y) in zip(
            result.outputs[:len(train)], result.errors[:len(train)], train))
    check_correct = sum(
        err is None and got == y for got, err, (_, y) in zip(
            result.outputs[len(train):], result.errors[len(train):], checks))
    if train_correct == len(train) and check_correct == len(checks):
        return None  # never label a working solution as a failure
    if train_correct == len(train):
        kind = "independent_source"
        evidence = [{
            "source_input":x, "source_expected":y,
            "previous_observed":got, "runtime_error":err}
            for got, err, (x,y) in zip(
                result.outputs[len(train):],result.errors[len(train):],checks)
            if err is not None or got != y]
    else:
        kind = "source"
        evidence = [{
            "input":x, "expected":y, "runtime_failure":err}
            if err is not None else {
                "input":x, "expected":y, "got":got}
            for got, err, (x,y) in zip(
                result.outputs[:len(train)],result.errors[:len(train)],train)
            if err is not None or got != y]
    if not evidence:
        raise ValueError("failure claimed without actual SOURCE counterexample")
    return {
        "kind":kind, "evidence":evidence[:3],
        "train_correct":train_correct, "train_total":len(train),
        "independent_correct":check_correct, "independent_total":len(checks),
    }


def _get_identity(row):
    original = row.get("original_id",row.get("source_id"))
    if not isinstance(original, (str,int)) or not str(original):
        raise ValueError("teacher original source identity is required")
    name = str(original)
    return name if name.startswith("source-teacher/") else "source-teacher/"+name


def _certified_teacher_map(rows,memory):
    found = {_get_identity(r): r for r in rows}
    if len(found)!=len(rows) or len(found)!=len(memory.episodes):
        raise ValueError("SOURCE teacher identity mismatch/duplicate")
    for e in memory.episodes:
        row=found.get(e.source_id)
        if row is None or row["program"]!=e.program:
            raise ValueError("SOURCE-certified program mismatch")
    if not memory.frozen:
        raise ValueError("teacher method library must be frozen")
    return found


def collect_onpolicy_episodes(rows, memory, runner, model,
                              *, max_per_teacher=1):
    """Actual base model proposals. Never mutate ASTs or retrieve self code."""
    from .q3_trainable_code_policy import contextual_training_prompt
    if not 1 <= max_per_teacher <= 3:
        raise ValueError("bounded model hypothesis budget")
    by_id = _certified_teacher_map(rows,memory)
    results = []
    for original_id,teacher in sorted(by_id.items()):
        prompt = contextual_training_prompt(teacher,memory)
        for attempt_index in range(max_per_teacher):
            # Repeated actual samples from the same frozen model, independent
            # of TARGET performance, not a policy update or manual heuristic.
            if hasattr(model,"seed"):
                model.seed = 1007 + 7919*attempt_index
            raw=model.propose(prompt)
            try:
                failed=validate_code(raw)
            except (UnsafeProposal,ValueError,TypeError):
                # An invalid program cannot yield a semantic counterexample.
                continue
            if failed==teacher["program"]:
                continue
            observation=source_error_witness(failed,teacher,runner)
            if observation is None:
                continue
            repair_prompt=source_revision_prompt(
                prompt,failed,observation["evidence"],
                kind=observation["kind"])
            # A real SOURCE failure is the only authority to train the repair.
            results.append({
                "schema":SCHEMA,
                "provenance":"ACTUAL_FROZEN_MODEL_SOURCE_FAILURE",
                "original_source_id":original_id,
                "attempt_index":attempt_index,
                "failed_program":failed,
                "failed_sha256":_sha(failed),
                "correct_program_sha256":_sha(teacher["program"]),
                "observation":observation,
                "repair_prompt_sha256":_sha(repair_prompt),
            })
        print("Q3_ONPOLICY_SOURCE_FAILURE",original_id,
              sum(r["original_source_id"]==original_id for r in results),
              flush=True)
    return results


def verify_onpolicy_episodes(rows,memory,runner,episodes):
    """Reject self-signed positive and negative programs before gradients."""
    from .q3_trainable_code_policy import contextual_training_prompt
    by_id=_certified_teacher_map(rows,memory)
    if not episodes or len(episodes)>4096:
        raise ValueError("nonempty bounded real-model SOURCE episodes required")
    verified=[]
    seen=set()
    for row in episodes:
        if (row.get("schema")!=SCHEMA or
            row.get("provenance")!="ACTUAL_FROZEN_MODEL_SOURCE_FAILURE"):
            raise ValueError("SOURCE provenance contract violated")
        identity=row.get("original_source_id")
        teacher=by_id.get(identity)
        if teacher is None:
            raise ValueError("SOURCE teacher identity not found")
        failed=validate_code(row.get("failed_program"))
        if (_sha(failed)!=row.get("failed_sha256")
            or row.get("correct_program_sha256")!=_sha(teacher["program"])):
            raise ValueError("candidate hash/positive program SHA mismatch")
        key=(identity,_sha(failed))
        if key in seen:
            raise ValueError("duplicate on-policy training episode")
        seen.add(key)
        current=source_error_witness(failed,teacher,runner)
        if current is None or current!=row.get("observation"):
            raise ValueError("SOURCE falsification not independently reproduced")
        prompt=source_revision_prompt(
            contextual_training_prompt(teacher,memory),
            failed,current["evidence"],kind=current["kind"])
        if _sha(prompt)!=row.get("repair_prompt_sha256"):
            raise ValueError("SOURCE prompt contract has changed")
        verified.append({
            "prompt":prompt,
            "program":teacher["program"],
            "original_source_id":identity,
            "negative_sha256":_sha(failed),
            "train_correct":current["train_correct"],
            "train_total":current["train_total"],
            "independent_correct":current["independent_correct"],
            "kind":current["kind"],
            "source_only":True,
        })
    return verified


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sources",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--model",default="Qwen/Qwen2.5-Coder-0.5B-Instruct")
    p.add_argument("--model-revision",required=True)
    p.add_argument("--max-per-teacher",type=int,default=1)
    args=p.parse_args()
    from .q3_trainable_code_policy import (
        source_training_rows, certified_source_memory, LocalCausalCodePolicy)
    rows,_=source_training_rows(args.sources)
    runner=IsolatedPython(max_seconds=8)
    memory=certified_source_memory(rows,runner=runner)
    policy=LocalCausalCodePolicy(
        model_name=args.model,model_revision=args.model_revision,
        max_new_tokens=384,temperature=0.3)
    episodes=collect_onpolicy_episodes(
        rows,memory,runner,policy,max_per_teacher=args.max_per_teacher)
    verified=verify_onpolicy_episodes(rows,memory,runner,episodes) if episodes else []
    with Path(args.out).open("w",encoding="utf-8") as handle:
        for item in episodes:
            handle.write(json.dumps(item,sort_keys=True)+"\n")
    print("Q3_REAL_MODEL_SOURCE_FAILURE_EPISODES",
          json.dumps({"teachers":len(rows),"verified_negatives":len(verified),
                      "model_revision":args.model_revision,
                      "source_only":True,
                      "no_target_gold":True,
                      "episode_file_sha256":sha256(Path(args.out).read_bytes()).hexdigest()}),
          flush=True)

if __name__=="__main__":
    main()
