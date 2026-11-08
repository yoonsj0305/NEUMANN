"""Q3/Q4/Q6: frozen self-revised discovery method, 100 fresh tasks.

Source oracles are researcher-generated, not ARC original tasks.
The SAME learned recursive control AST drives two non-isomorphic classical
backends: GF2 polynomial feature fitting and periodic word inference.
All target labels are kept out of source discovery.

All source acquisition, meta-training grading, feedback, retraining, and
fresh evaluation are counted. Compare against an explicit STRONG classical
upper-bound algorithm, not only a deliberately truncated fixed policy.
"""
from __future__ import annotations
from itertools import combinations
from random import Random
from time import perf_counter_ns
from pathlib import Path
import argparse
import json

from neumann1.recursive_method_discovery import (
    MetaCase,ObservedOracle,RecursiveMethodInventor,RecursiveMethod,execute)
from research.q3.meta_domain_adapters import (
    BooleanPolynomialBackend,PeriodicProcessBackend)


def polynomial_law(seed,degree=3,width=10):
    rng=Random(seed)
    terms=set()
    while len(terms)<5:
        terms.add(tuple(sorted(rng.sample(range(width),degree))))
    def oracle(x):
        return sum(all(x[i] for i in term) for term in terms)&1
    return oracle


def periodic_law(seed,period):
    rng=Random(seed)
    while True:
        pat=tuple(rng.getrandbits(1) for _ in range(period))
        if all(any(pat[i]!=pat[i%k] for i in range(period))
               for k in range(1,period)):
            return lambda t,p=pat:p[t%len(p)]


def example(family,seed,complexity,width=10):
    if family=="boolean":
        oracle=polynomial_law(seed,complexity,width)
        pool=[j for j in range(1<<width) if j.bit_count()>5]
        heldout=tuple(tuple((i>>j)&1 for j in range(width))
                      for i in Random(seed+12345).sample(pool,80))
        def factory(ledger):
            return BooleanPolynomialBackend(width,ledger,seed+900)
    else:
        oracle=periodic_law(seed,complexity)
        heldout=tuple(range(300,400))
        def factory(ledger):
            return PeriodicProcessBackend(ledger,seed+900)
    return MetaCase(family,factory,oracle,heldout)


def evaluate(method,tasks):
    result={"correct":0,"queries":0,"cpu_ms":0.0,
            "by_family":{},"failed_ids":[]}
    for i,c in enumerate(tasks):
        ledger=ObservedOracle(c.oracle,c.heldout)
        run=execute(method,c.backend_factory(ledger))
        # All TARGET gold accessed only after model was frozen.
        truth=tuple(c.oracle(x) for x in c.heldout)
        passed=(run.model is not None and
                all(run.apply(x)==y for x,y in zip(c.heldout,truth)))
        bucket=result["by_family"].setdefault(c.family,{
            "cases":0,"solved":0,"queries":0})
        bucket["cases"]+=1
        bucket["solved"]+=int(passed)
        bucket["queries"]+=run.source_queries
        result["correct"]+=int(passed)
        result["queries"]+=run.source_queries
        result["cpu_ms"]+=run.elapsed_ms
        if not passed:
            result["failed_ids"].append(i)
    result["cpu_ms"]=round(result["cpu_ms"],3)
    return result


def strong_classical_reference(tasks,challenge_count=64):
    """Source-only specialist with KNOWN finite model upper bounds.

    Degree-5 interpolation for GF2; prefix length 18 + minimal-period scan
    and fresh 64 source checks for symbolic periodic sequences. Source
    queries and CPU are measured on the same evaluation task set.
    """
    result={"correct":0,"queries":0,"cpu_ms":0.0,
            "by_family":{}}
    for c in tasks:
        ledger=ObservedOracle(c.oracle,c.heldout)
        t0=perf_counter_ns()
        if c.family=="boolean":
            step=c.backend_factory(ledger).attempt(5,challenge_count)
            model=step.hypothesis if step.status=="VERIFIED" else None
        else:
            prefix=tuple(ledger.ask(t) for t in range(18))
            period=next(k for k in range(1,10)
                        if all(prefix[t]==prefix[t%k] for t in range(18)))
            cycle=prefix[:period]
            model=lambda t,p=cycle:p[t%len(p)]
            if not all(model(t)==ledger.ask(t)
                       for t in range(40,40+challenge_count)):
                model=None
        elapsed=(perf_counter_ns()-t0)/1e6
        passed=(model is not None and
                all(model(x)==c.oracle(x) for x in c.heldout))
        if not passed:
            raise AssertionError("reference source task not solved")
        entry=result["by_family"].setdefault(c.family,{
            "cases":0,"solved":0,"queries":0})
        entry["cases"]+=1
        entry["solved"]+=1
        entry["queries"]+=len(ledger.cache)
        result["correct"]+=1
        result["queries"]+=len(ledger.cache)
        result["cpu_ms"]+=elapsed
    result["cpu_ms"]=round(result["cpu_ms"],3)
    return result


def experiment():
    start=perf_counter_ns()
    source=tuple(example("boolean",i+3000,3)
                 for i in range(12))+tuple(
        example("period",i+700,3) for i in range(12))
    feedback=tuple(example("boolean",i+80000,4+i%2)
                   for i in range(15))
    learner=RecursiveMethodInventor(
        max_complexity=9,challenges=(4,8,16,32,64,96))
    initial=learner.learn(source)
    initial_feedback=evaluate(initial.method,feedback)
    revised=learner.learn(source+feedback)
    revised_feedback=evaluate(revised.method,feedback)
    assert initial.method.ast!=revised.method.ast
    assert initial.method.transition==("increment",2)
    assert revised.method.transition==("increment",1)
    assert initial.method.challenges==16
    assert revised.method.challenges==64
    assert initial_feedback["correct"]<15
    assert revised_feedback["correct"]==15
    assert revised.correct_on_meta_training==39

    unseen=tuple(example("boolean",i+60000,4+i%2)
                 for i in range(40))+tuple(
        example("period",i+70000,7+2*(i%2))
        for i in range(40))+tuple(
        example("boolean",i+90000,4+i%2,width=11+i%2)
        for i in range(20))
    before=evaluate(initial.method,unseen)
    after=evaluate(revised.method,unseen)
    old_depth=evaluate(RecursiveMethod(("increment",1),64,3),unseen)
    classical=strong_classical_reference(unseen)

    assert after["correct"]==classical["correct"]==100
    assert before["correct"]<after["correct"]

    # Independent exhaustive numeric truth-table and distant symbolic
    # continuation scoring AFTER the revised policy was frozen.
    exhaustive_boolean=0
    periodic_future=0
    for case in unseen:
        run=execute(revised.method,case.backend_factory(
            ObservedOracle(case.oracle,case.heldout)))
        assert run.model is not None
        if case.family=="boolean":
            width=len(case.heldout[0])
            for i in range(1<<width):
                x=tuple((i>>j)&1 for j in range(width))
                assert run.apply(x)==case.oracle(x)
                exhaustive_boolean+=1
        else:
            for t in range(300,3000):
                assert run.apply(t)==case.oracle(t)
                periodic_future+=1

    # Conservative GROSS accounting; we do not credit overlap across
    # initial learning, feedback diagnosis and retraining as free.
    gross_meta_queries=(
        initial.training_cost_queries+initial.grade_label_cost+
        initial_feedback["queries"]+len(feedback)*80+
        revised.training_cost_queries+revised.grade_label_cost+
        revised_feedback["queries"]+len(feedback)*80+
        after["queries"])
    meta_cpu=(
        initial.meta_cpu_ms+initial_feedback["cpu_ms"]+
        revised.meta_cpu_ms+revised_feedback["cpu_ms"]+
        after["cpu_ms"])

    summary={
        "meta_source_tasks":24,
        "meta_feedback_tasks":15,
        "new_evaluation_tasks":100,
        "initial_policy_ast":initial.method.ast,
        "revised_policy_ast":revised.method.ast,
        "initial_feedback_correct":initial_feedback["correct"],
        "revised_feedback_correct":revised_feedback["correct"],
        "initial_unseen":before,
        "revised_unseen":after,
        "fixed_depth_3_unseen":old_depth,
        "strong_classical_unseen":classical,
        "all_boolean_finite_input_matches":exhaustive_boolean,
        "independent_periodic_future_matches":periodic_future,
        "initial_training_source_queries":initial.training_cost_queries,
        "initial_training_grader_labels":initial.grade_label_cost,
        "feedback_initial_source_queries":initial_feedback["queries"],
        "feedback_initial_grader_labels":len(feedback)*80,
        "retraining_source_queries":revised.training_cost_queries,
        "retraining_grader_labels":revised.grade_label_cost,
        "feedback_revised_source_queries":revised_feedback["queries"],
        "feedback_revised_grader_labels":len(feedback)*80,
        "meta_total_source_and_training_queries":gross_meta_queries,
        "classical_eval_only_source_queries":classical["queries"],
        "meta_total_cpu_ms":round(meta_cpu,3),
        "strong_classical_eval_only_cpu_ms":classical["cpu_ms"],
        "classical_math_adapters_human_supplied":True,
        "meta_policy_reads_domain_labels":False,
        "new_test_gold_prohibited_from_source_probes":True,
        "preliminary_synthetic_not_independent_arc":True,
        "global_q3_q4_q6_pass":False,
        "research_limits":[
            "New method is synthesized within a finite human-defined metalanguage.",
            "Both classical backends implement established mathematics.",
            "Synthetic reference oracles are not untouched ARC/real-world problems.",
            "Source challenges are finite, never a universal correctness proof.",
            "The strong classical reference knows degree<=5 and period<=9.",
            "All source, feedback and meta-training costs are included gross.",
            "Researcher development iterations before this frozen comparison not charged.",
            "Training+inference CPU is not cheaper than strong classical here."],
        "elapsed_wall_ms":round((perf_counter_ns()-start)/1e6,3),
    }
    return {"schema":"NEUMANN.Q3.RECURSIVE-META-FIRST.v1",
            "summary":summary}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="q3_recursive_method_meta_first.json")
    args=p.parse_args()
    data=experiment()
    Path(args.output).write_text(json.dumps(data,indent=2)+"\n")
    s=data["summary"]
    print(json.dumps({
        "old_correct":s["initial_unseen"]["correct"],
        "revised_correct":s["revised_unseen"]["correct"],
        "fixed3_correct":s["fixed_depth_3_unseen"]["correct"],
        "strong_classical_correct":s["strong_classical_unseen"]["correct"],
        "all_boolean_finite_input_matches":s["all_boolean_finite_input_matches"],
        "independent_periodic_future_matches":s["independent_periodic_future_matches"],
        "meta_total_source_and_training_queries":s["meta_total_source_and_training_queries"],
        "classical_eval_only_source_queries":s["classical_eval_only_source_queries"],
        "meta_total_cpu_ms":s["meta_total_cpu_ms"],
        "strong_classical_eval_only_cpu_ms":s["strong_classical_eval_only_cpu_ms"],
        "global_pass":s["global_q3_q4_q6_pass"]},indent=2))
