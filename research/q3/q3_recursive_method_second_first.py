"""SECOND disjoint, source-first evaluation of an invented DISCOVERY policy.

150 fresh researcher-generated mathematical tasks. Policy training and
counterexample revision use different fixed seeds; the saved predictor
contains NO target-answer oracle values. Only a separate scoring process
opens the full reference functions after the prediction SHA is frozen.

This is synthetic source-first testing, NOT ARC or human-frontier originals.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter_ns

from neumann1.recursive_method_discovery import (
    RecursiveMethodInventor,ObservedOracle,execute)
from research.q3.q3_recursive_method_meta_first import example


def train_and_freeze_policy():
    source=tuple(example("boolean",i+3000,3)
                 for i in range(12))+tuple(
        example("period",i+700,3) for i in range(12))
    feedback=tuple(example("boolean",i+80000,4+i%2)
                   for i in range(15))
    learner=RecursiveMethodInventor(
        max_complexity=9,challenges=(4,8,16,32,64,96))
    first=learner.learn(source)
    second=learner.learn(source+feedback)
    assert first.method.transition==("increment",2)
    assert second.method.transition==("increment",1)
    assert first.method.challenges==16
    assert second.method.challenges==64
    assert second.correct_on_meta_training==39
    return first,second


def new_tasks():
    for i in range(90):
        yield ("boolean",910003+i*1009,4+i%2,10+i%3)
    for i in range(60):
        yield ("period",710011+i*829,7+2*(i%2),0)


def test_inputs(family,width):
    if family=="boolean":
        return tuple(tuple((i>>j)&1 for j in range(width))
                     for i in range(1<<width))
    return tuple(range(300,3000))


def strong_classical_source_only(case,family):
    source=ObservedOracle(case.oracle,case.heldout)
    t0=perf_counter_ns()
    if family=="boolean":
        r=case.backend_factory(source).attempt(5,64)
        model=r.hypothesis if r.status=="VERIFIED" else None
    else:
        prefix=tuple(source.ask(t) for t in range(18))
        period=next(k for k in range(1,10)
                    if all(prefix[i]==prefix[i%k] for i in range(18)))
        word=prefix[:period]
        model=lambda t,p=word:p[t%len(p)]
        if any(model(t)!=source.ask(t) for t in range(40,104)):
            model=None
    return model,len(source.cache),(perf_counter_ns()-t0)/1e6


def propose(out):
    first,revised=train_and_freeze_policy()
    rows=[]
    for family,seed,complexity,width in new_tasks():
        task=example(family,seed,complexity,
                     width=width if width else 10)
        eval_inputs=test_inputs(family,width)
        source=ObservedOracle(task.oracle,task.heldout)
        run=execute(revised.method,task.backend_factory(source))
        # Construct predictions solely from program execution. The source
        # oracle refuses to open independent heldout target labels.
        predicted=tuple(run.apply(x) for x in eval_inputs) if run.model else ()
        classical,qclass,tclass=strong_classical_source_only(task,family)
        strong=tuple(classical(x) for x in eval_inputs) if classical else ()
        rows.append({
            "family":family,"seed":seed,"complexity":complexity,
            "width":width,"source_status":run.status,
            "source_trace":run.trace,
            "source_queries":run.source_queries,
            "source_cpu_ms":round(run.elapsed_ms,5),
            "classical_source_queries":qclass,
            "classical_source_cpu_ms":round(tclass,5),
            "prediction":predicted,
            "strong_classical_prediction":strong,
            "target_gold_never_queried_by_source":True})
    payload={
        "schema":"NEUMANN.Q3.META-SECOND-FIRST.SOURCE-ONLY.v1",
        "initial_method_ast":first.method.ast,
        "revised_method_ast":revised.method.ast,
        "meta_initial_source_queries":first.training_cost_queries,
        "meta_initial_grading_queries":first.grade_label_cost,
        "meta_revised_source_queries":revised.training_cost_queries,
        "meta_revised_grading_queries":revised.grade_label_cost,
        "meta_initial_cpu_ms":round(first.meta_cpu_ms,5),
        "meta_revised_cpu_ms":round(revised.meta_cpu_ms,5),
        "cohort_ids_frozen":True,
        "target_outputs_used_in_proposal":False,
        "records":rows}
    out.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("SOURCE FIRST PREDICTION SHA256",
          hashlib.sha256(out.read_bytes()).hexdigest())


def score(predictions,expected_sha,out):
    actual=hashlib.sha256(predictions.read_bytes()).hexdigest()
    if actual!=expected_sha:
        raise ValueError("frozen prediction artifact modified")
    frozen=json.loads(predictions.read_text())
    if frozen["target_outputs_used_in_proposal"]:
        raise ValueError("target leakage contract violation")
    answers=[]
    for entry in frozen["records"]:
        case=example(entry["family"],entry["seed"],entry["complexity"],
                     width=entry["width"] if entry["width"] else 10)
        coords=test_inputs(entry["family"],entry["width"])
        reference=tuple(case.oracle(x) for x in coords)
        correct=(len(entry["prediction"])==len(reference) and
                 tuple(entry["prediction"])==reference)
        classical=(len(entry["strong_classical_prediction"])==len(reference)
                   and tuple(entry["strong_classical_prediction"])==reference)
        answers.append({
            "family":entry["family"],"seed":entry["seed"],
            "meta_correct":correct,"strong_classical_correct":classical,
            "tested_inputs":len(coords)})
    cases=frozen["records"]
    summary={
        "second_cohort_tasks":len(answers),
        "boolean_tasks":sum(r["family"]=="boolean" for r in answers),
        "period_tasks":sum(r["family"]=="period" for r in answers),
        "meta_correct":sum(r["meta_correct"] for r in answers),
        "strong_classical_correct":sum(
            r["strong_classical_correct"] for r in answers),
        "total_scored_finite_or_distant_inputs":sum(
            r["tested_inputs"] for r in answers),
        "meta_new_task_source_queries":sum(
            r["source_queries"] for r in cases),
        "strong_classical_new_task_source_queries":sum(
            r["classical_source_queries"] for r in cases),
        "meta_initial_training_source_queries":
            frozen["meta_initial_source_queries"],
        "meta_revised_training_source_queries":
            frozen["meta_revised_source_queries"],
        "meta_two_training_pass_grade_labels":(
            frozen["meta_initial_grading_queries"]+
            frozen["meta_revised_grading_queries"]),
        # Lower bound: does not include the extra feedback-diagnosis run
        # or exploratory R&D. Never call this entire economic cost.
        "meta_train_and_new_task_queries_lower_bound":(
            sum(r["source_queries"] for r in cases)+
            frozen["meta_initial_source_queries"]+
            frozen["meta_revised_source_queries"]+
            frozen["meta_initial_grading_queries"]+
            frozen["meta_revised_grading_queries"]),
        "meta_two_training_passes_plus_new_task_cpu_ms":round(
            frozen["meta_initial_cpu_ms"]+
            frozen["meta_revised_cpu_ms"]+
            sum(r["source_cpu_ms"] for r in cases),4),
        "strong_classical_new_task_cpu_ms":round(sum(
            r["classical_source_cpu_ms"] for r in cases),4),
        "frozen_prediction_sha256":actual,
        "global_q3_q4_q6_pass":False,
        "limitations":[
            "Researcher-generated synthetic functions and periodic processes.",
            "Human-supplied classical backends and bounded metalanguage.",
            "The strong classical algorithms know the problem class upper bounds.",
            "Only the FROZEN policy is transferred, not original task answers.",
            "Finite observations do not prove unrestricted generalization.",
            "Meta total training lower bound excludes exploratory R&D."]}
    out.write_text(json.dumps({
        "schema":"NEUMANN.Q3.META-SECOND-FIRST.SCORED.v1",
        "summary":summary,"records":answers},indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    q=sub.add_parser("propose")
    q.add_argument("--output",type=Path,required=True)
    q=sub.add_parser("score")
    q.add_argument("--predictions",type=Path,required=True)
    q.add_argument("--expected-sha",required=True)
    q.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.command=="propose":
        propose(a.output)
    else:
        score(a.predictions,a.expected_sha,a.output)
