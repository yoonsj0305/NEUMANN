"""Q3 task-agnostic executable-program refutation -> repair learning contract.

No domain operator is introduced here. The previous *program itself* and
the observed SOURCE counterexample are the causal inputs to next invention.
A policy gradient may train on the exact same prompt contract. SOURCE means
actual author demonstrations or authorized independent SOURCE checks, never
unseen original author TEST labels.

A proof-bearing repair record must include a sandbox-refuted prior program
and a separately sandbox-certified corrected program. No fake "success"
from program text, code similarity, or a hand-written task-family dispatch.
"""
from __future__ import annotations

from hashlib import sha256
import json

from .q3_prompt_contract import source_discovery_prompt
from .open_program_inventor import source_same_value,validate_code


def _witnesses(pairs, execution):
    errors = tuple(getattr(execution, "errors", ()))
    if len(execution.outputs) != len(pairs):
        return [{"reason": execution.status}]
    evidence=[]
    for index,(predicted,(x,y)) in enumerate(zip(execution.outputs,pairs)):
        error=errors[index] if index<len(errors) else None
        if error is not None or not source_same_value(predicted,y):
            evidence.append({
                "source_input":x,
                "source_expected":y,
                "previous_observed":predicted,
                "runtime_error":error,
            })
    return evidence


def source_refutation_feedback(code, pairs, execution, *,
                               independent=False, rich=True):
    """Shared inference/training feedback; include the wrong executable code.

    Previous Q3 inference omitted code from the revision prompt. The model
    could not distinguish two different wrong programs with the same
    counterexample descriptions. A model cannot learn a *repair function*
    without receiving the object to repair.
    """
    code=validate_code(code)
    pairs=tuple((x,y) for x,y in pairs)
    if not pairs:
        raise ValueError("real SOURCE refutation required")
    if execution.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
        observation={"execution_status":execution.status}
    elif rich:
        observation={"source_counterexamples":_witnesses(pairs,execution)[:3]}
    else:
        observation={"source_counterexamples":"OPAQUE_SOURCE_REFUTATION"}
    if (execution.status=="EXECUTED" and
        len(execution.outputs)==len(pairs) and
        all(source_same_value(a,b) for a,(_,b)
            in zip(execution.outputs,pairs))):
        raise ValueError("program was not refuted on supplied SOURCE")
    phase=("new independent SOURCE" if independent
           else "initial SOURCE")
    return (
        "\nYour prior executable algorithm was falsified by "+phase+
        ". The exact prior program to REVISE is:\n"+
        code[:3000]+
        "\nObserved source-only causal errors:\n"+
        json.dumps(observation,ensure_ascii=True,
                   sort_keys=True,separators=(",",":"))[:3500]+
        "\nInfer a missing invariant or relation; produce one revised "
        "self-contained executable transform(x). Do not memorize examples.\n"
    )


def recertified_repair_prompt(row,runner):
    """Construct learned repair input from actual independent SOURCE evidence.

    Never trust a free-text prompt from a teacher file. Recertify the
    counterexample against the prior source program in the same sandbox.
    The corrected program is independently certified by the caller's
    SourceMethodMemory before gradient updates.
    """
    if row.get("schema")!="NEUMANN.Q3.PROGRAM-SOURCE-TEACHER.v1":
        raise ValueError("source teacher schema required")
    if row.get("provenance")!="ORIGINAL_SOURCE_ONLY":
        raise ValueError("author-original SOURCE provenance required")
    pairs=row.get("pairs")
    count=row.get("independent_checks")
    if (not isinstance(pairs,list)
        or not isinstance(count,int) or not 1<=count<len(pairs)):
        raise ValueError("explicit independent SOURCE split required")
    train=tuple((x,y) for x,y in pairs[:-count])
    checks=tuple((x,y) for x,y in pairs[-count:])
    prior=row.get("repair_prior_program")
    if not isinstance(prior,str) or not prior:
        raise ValueError("genuine failed prior program required")
    code=validate_code(prior)
    if sha256(code.encode()).hexdigest()!=row.get("repair_prior_sha256"):
        raise ValueError("prior program SHA tampered")
    # The learner refuses a prior that is not actually source-falsified.
    outcome=runner.evaluate(code,[x for x,y in train])
    if outcome.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
        raise ValueError("prior program did not execute in sandbox")
    if _witnesses(train,outcome):
        suffix=source_refutation_feedback(code,train,outcome)
        phase="TRAIN_SOURCE"
    else:
        # Only checks that the inference loop may legally disclose can be
        # part of a repair prompt. The last independent SOURCE check stays
        # sealed even while past teacher episodes are recertified.
        feedback_count=row.get("repair_feedback_checks_count",0)
        if (type(feedback_count) is not int or
                not 1<=feedback_count<len(checks)):
            raise ValueError("no fresh sealed SOURCE check after repair")
        feedback=checks[:feedback_count]
        held=runner.evaluate(code,[x for x,y in feedback])
        if held.status not in ("EXECUTED","EXECUTED_WITH_ERRORS"):
            raise ValueError("prior cannot be checked in independent sandbox")
        if not _witnesses(feedback,held):
            raise ValueError("prior was not falsified by feedback SOURCE")
        suffix=source_refutation_feedback(
            code,feedback,held,independent=True)
        phase="INDEPENDENT_SOURCE"
    if phase!=row.get("repair_phase"):
        raise ValueError("repair counterexample phase mismatches provenance")
    prompt=source_discovery_prompt(train)+suffix
    # The exact SOURCE checker labels, rather than any TARGET, are all the
    # additional information the model may see in this repair episode.
    return prompt,phase
