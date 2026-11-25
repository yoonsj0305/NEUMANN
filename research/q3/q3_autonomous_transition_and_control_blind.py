"""Q3 blind, end-to-end invention of T AND meta-discovered iteration method.

This is a source-graded synthetic protocol, NOT official independent ARC.
The proposition process sees only SOURCE successor I/O and separate SOURCE
terminal I/O. The learned typed ASTs and all HELDOUT predictions are SHA
frozen before a distinct scoring invocation opens independent target gold.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from random import Random

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from neumann1 import NeumannEngine
from research.q3.q3_higher_order_method_blind import training


def successor_source(kind):
    if kind=="int":
        def law(x):return max(x-1,0)
        train=(0,1,2,5,8)
        checks=(3,4,9,19)
        goals=((11,0),(17,0))
    elif kind=="set":
        def law(s):return frozenset(s-{min(s)}) if s else s
        train=(frozenset(),frozenset((1,)),
               frozenset((1,2,3)),frozenset((2,7)),
               frozenset((1,3,9)),frozenset((4,5,6)))
        checks=(frozenset((5,8)),frozenset((8,9,10)),
                frozenset((2,4,17)))
        goals=((frozenset((1,2,3,4)),frozenset()),
               (frozenset((3,9)),frozenset()))
    elif kind=="str":
        def law(s):return s.replace("aa","a")
        train=("aaaa","aa","a","baaa","bbaa","baaba")
        checks=("aaaaaa","abaaaa","bbbaaa","abaabb")
        goals=(("aaaaaaa","a"),("bbaaaa","bba"))
    else:
        raise ValueError("unknown source state type")
    return (tuple((x,law(x)) for x in train),
            tuple((x,law(x)) for x in checks),goals)


def target_specs():
    rng=Random(20261109)
    result=[("int",n) for n in range(20,256)]
    for _ in range(110):
        n=rng.randrange(2,151)
        result.append(("set",sorted(rng.sample(range(100,1000),n))))
    for _ in range(150):
        n=rng.randrange(20,221)
        result.append(("str","".join(
            rng.choice("aab") for _ in range(n))))
    return tuple(result)


def decode(kind,value):
    return frozenset(value) if kind=="set" else value


def encode(value):
    if isinstance(value,frozenset):
        return {"type":"set","value":sorted(value)}
    if isinstance(value,str):
        return {"type":"str","value":value}
    if value is None:
        return {"type":"abstain"}
    return {"type":"int","value":value}


def grader(kind,input_value):
    """Reference target gold; the proposer NEVER calls this function."""
    if kind=="int":return 0
    if kind=="set":return frozenset()
    if kind=="str":return re.sub("a+","a",input_value)
    raise ValueError("unknown target input kind")


def propose(out):
    source,long,invariant=training()
    engine=NeumannEngine(None,[],None)
    original=engine.meta_learn_higher_order_method(source)
    intermediate=engine.meta_revise_higher_order_method(long)
    final=engine.meta_revise_higher_order_method(invariant)
    assert original.program.ast[0]=="sequence"
    assert "length" in repr(intermediate.program.ast)
    assert final.program.ast==(
        "while",
        ("not",("equal",("read","current"),
                 ("read","next"))),
        ("apply","transition"))
    programs={}
    compiled={}
    prior={}
    for kind in ("int","set","str"):
        train,checks,source_goals=successor_source(kind)
        t,program=engine.meta_invent_transition_and_solver(
            train,checks,source_goals,
            max_nodes=6,max_source_ms=2500)
        programs[kind]={
            "discovered_transition_ast":repr(t.ast),
            "ast_nodes":t.ast_nodes,
            "source_next_state_examples":len(train),
            "independent_next_state_source_checks":len(checks),
            "independent_terminal_source_checks":len(source_goals),
            "expressions_searched":t.enumerated_expressions}
        compiled[kind]=program
        prior[kind]=original.program.compile(t)
    rows=[]
    for kind,spec in target_specs():
        # No target grader is accessible through any of these API calls.
        x=decode(kind,spec)
        generated=compiled[kind].run(x)
        old=prior[kind].run(x)
        rows.append({
            "type":kind,"source_input":spec,
            "invented_method_prediction":encode(generated.value),
            "invented_status":generated.status,
            "old_method_prediction":encode(old.value)})
    payload={
        "schema":"NEUMANN.Q3.END_TO_END_SOURCE_ONLY.v1",
        "method_source_cases":len(source),
        "method_counterexample_source_cases":len(long)+len(invariant),
        "method_original_ast":original.program.ast,
        "method_revised_ast":final.program.ast,
        "programs":programs,
        "heldout_gold_used_to_generate_predictions":False,
        "rows":rows}
    out.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("END-TO-END Q3 PREDICTIONS FROZEN",
          hashlib.sha256(out.read_bytes()).hexdigest(),
          "tasks",len(rows))


def score(frozen,expected_sha,out):
    digest=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if digest!=expected_sha:raise ValueError("frozen prediction changed")
    p=json.loads(frozen.read_text())
    if p["heldout_gold_used_to_generate_predictions"]:
        raise ValueError("target answer leakage")
    result={}
    for row in p["rows"]:
        kind=row["type"]
        observed=grader(kind,row["source_input"])
        right=row["invented_method_prediction"]==encode(observed)
        old=row["old_method_prediction"]==encode(observed)
        item=result.setdefault(kind,{"tasks":0,"correct":0,
                                     "previous_method_correct":0})
        item["tasks"]+=1
        item["correct"]+=int(right)
        item["previous_method_correct"]+=int(old)
    summary={
        "heldout_tasks":sum(d["tasks"] for d in result.values()),
        "heldout_correct":sum(d["correct"] for d in result.values()),
        "previous_fixed_method_correct":sum(
            d["previous_method_correct"] for d in result.values()),
        "new_transition_programs":len(p["programs"]),
        "method_structural_rewrites":2,
        "no_task_specific_generator_per_state_type":True,
        "target_gold_used_to_synthesize_programs":False,
        "frozen_prediction_sha256":digest,
        "global_Q3_Q6_pass":False,
        "limits":[
            "Synthetic tasks defined by the researcher.",
            "Typed arithmetic/set/string primitive instruction library supplied.",
            "SOURCE successor examples and source terminal examples supplied.",
            "No claim of correct unknown law outside the learned typed DSL.",
            "Meta control is correct only for deterministic fixedpoint convergence.",
            "No strongest-classical or end-to-end Q4 efficiency proof."
        ]}
    out.write_text(json.dumps({
        "schema":"NEUMANN.Q3.END_TO_END_SCORED.v1",
        "summary":summary,
        "by_type":result,
        "invented_ast_details":p["programs"]},indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    a=sub.add_parser("propose")
    a.add_argument("--output",type=Path,required=True)
    b=sub.add_parser("score")
    b.add_argument("--predictions",type=Path,required=True)
    b.add_argument("--expected-sha",required=True)
    b.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="propose":
        propose(args.output)
    else:
        score(args.predictions,args.expected_sha,args.output)
