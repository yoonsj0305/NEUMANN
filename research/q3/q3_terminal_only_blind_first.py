"""Q3 blind-FIRST final-endpoint-only latent execution invention.

The proposer sees exactly (initial, final) SOURCE examples for the three
state types and a PREVIOUSLY source-learned higher-order control AST.
It receives NO one-step successor examples and calls NO target grader.
A separate invocation scores cryptographically frozen predictions.

These are researcher-authored finite synthetic problems. We do not claim
to recover the unique hidden successor law from final endpoints alone.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from neumann1 import NeumannEngine
from research.q3.q3_higher_order_method_blind import training


def encode(x):
    if isinstance(x,frozenset):
        return {"type":"set","value":sorted(x)}
    if isinstance(x,str):
        return {"type":"str","value":x}
    if type(x) is int:
        return {"type":"int","value":x}
    return {"type":"abstain"}


def source_endpoints():
    numbers=tuple((x,0) for x in (0,1,2,3,5,8,13,17))
    number_checks=tuple((x,0) for x in (4,7,11,19))
    source_sets=(
        frozenset(),frozenset((3,)),
        frozenset((2,5)),frozenset((1,3,9)),
        frozenset((2,6,7,15)),
        frozenset((4,8,12,16,20)),
        frozenset((5,9,13,14)),
    )
    ref_set=lambda s:frozenset()
    sets=tuple((s,ref_set(s)) for s in source_sets)
    set_checks=tuple((s,ref_set(s)) for s in (
        frozenset((7,11)),frozenset((4,9,23)),
        frozenset((2,8,14,18,25)),
        frozenset((16,22,31,39))))
    words=("bbbbbbbb","abbba","bbabb","aabbbbaa",
           "bbbbbabb","abbabbbaa","abbbbbabbbb","aabbb")
    source_regex=lambda x:re.sub("b+","b",x)
    strings=tuple((s,source_regex(s)) for s in words)
    string_checks=tuple((s,source_regex(s)) for s in (
        "abbbbbba","bbaabbbba","abbbbbbabbb","bbbaabbabb"))
    return {"int":(numbers,number_checks),
            "set":(sets,set_checks),
            "str":(strings,string_checks)}


def fresh_specifications():
    rng=random.Random(738001)
    result=[]
    for _ in range(100):
        result.append(("int",rng.randrange(20,230)))
    for _ in range(100):
        result.append(("set",sorted(
            rng.sample(range(101,5000),rng.randrange(3,120)))))
    for _ in range(100):
        result.append(("str","".join(
            rng.choice("aabbb") for _ in range(
                rng.randrange(30,221)))))
    return tuple(result)


def decode(kind,raw):
    return frozenset(raw) if kind=="set" else raw


def hidden_target_gold(kind,raw):
    """REFERENCE; only the independent score() function may call this."""
    if kind=="int":return 0
    if kind=="set":return frozenset()
    if kind=="str":return re.sub(r"b+","b",raw)
    raise ValueError("unknown target state type")


def propose(path):
    first,feedback,invariance=training()
    engine=NeumannEngine(None,[],None)
    base=engine.meta_learn_higher_order_method(first)
    second=engine.meta_revise_higher_order_method(feedback)
    final=engine.meta_revise_higher_order_method(invariance)
    assert base.program.ast[0]=="sequence"
    assert "length" in repr(second.program.ast)
    assert final.program.ast[0]=="while"
    assert "length" not in repr(final.program.ast)
    process={}
    for kind,(train,checks) in source_endpoints().items():
        program=engine.meta_invent_terminal_only_process(
            train,checks,max_nodes=6,max_expressions=60000,
            max_source_ms=20000)
        if program is None:
            raise ValueError("unexpected classical-first selection")
        process[kind]=program
    rows=[]
    for kind,spec in fresh_specifications():
        original=decode(kind,spec)
        execution=process[kind].compile().run(original)
        rows.append({
            "kind":kind,"initial":spec,
            "prediction":encode(execution.value),
            "status":execution.status,
            "transition_calls":execution.transition_calls})
    output={
        "schema":"NEUMANN.Q3.TERMINAL-ONLY-FIRST.SOURCE-FROZEN.v1",
        "source_endpoint_pairs":{
            kind:len(train) for kind,(train,checks) in source_endpoints().items()},
        "independent_endpoint_checks":{
            kind:len(checks) for kind,(train,checks) in source_endpoints().items()},
        "successor_source_pairs_provided":0,
        "target_gold_used_in_proposer":False,
        "invented_control_ast":final.program.ast,
        "invented_state_processes":{
            k:{"ast":repr(p.transition_ast),"ast_nodes":p.transition_nodes,
               "source_candidate_expressions":p.candidate_expressions,
               "source_terminal_checks":p.final_endpoint_checks,
               "source_multistep_witness":p.max_observed_transition_calls}
            for k,p in process.items()},
        "rows":rows}
    path.write_text(json.dumps(output,separators=(",",":"))+"\n")
    print("Q3 TERMINAL-ONLY 300 PREDICTIONS FROZEN",
          hashlib.sha256(path.read_bytes()).hexdigest())


def score(predictions,sha,output):
    actual=hashlib.sha256(predictions.read_bytes()).hexdigest()
    if actual!=sha:
        raise ValueError("predictions changed after freeze")
    data=json.loads(predictions.read_text())
    if data["successor_source_pairs_provided"]!=0 or data[
            "target_gold_used_in_proposer"]:
        raise ValueError("terminal-only input or source-first gate violated")
    groups={}
    failures=[]
    for i,row in enumerate(data["rows"]):
        kind=row["kind"]
        gold=hidden_target_gold(kind,decode(kind,row["initial"]))
        good=(row["prediction"]==encode(gold) and
              row["status"]=="HALT_CERTIFIED_FIXED_POINT")
        entry=groups.setdefault(kind,{"tasks":0,"correct":0})
        entry["tasks"]+=1
        entry["correct"]+=int(good)
        if not good:failures.append({
            "index":i,"kind":kind,"initial":row["initial"],
            "status":row["status"]})
    summary={
        "selected":len(data["rows"]),
        "correct":sum(x["correct"] for x in groups.values()),
        "by_state_type":groups,
        "unseen_terminal_source_successor_examples":0,
        "source_verified_composed_control":True,
        "source_verified_latent_state_updates":len(
            data["invented_state_processes"]),
        "heldout_target_gold_used_in_learning":False,
        "no_claim_of_unique_true_hidden_transition":True,
        "frozen_prediction_sha256":actual,
        "synthetic_research_tasks":True,
        "global_q3_pass":False,
        "limitations":[
            "All source and heldout problems are researcher-authored synthetic.",
            "The conditional loop and typed atomic instruction library are supplied.",
            "Original hidden step law is not uniquely identifiable from final states.",
            "The test deliberately requires at least one source trajectory with three transition calls.",
            "This cannot replace matched frontier or strongest classical evaluation."
        ]}
    output.write_text(json.dumps({"summary":summary,"failures":failures},
                                 indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("propose")
    p.add_argument("--output",type=Path,required=True)
    s=sub.add_parser("score")
    s.add_argument("--predictions",type=Path,required=True)
    s.add_argument("--expected-sha",required=True)
    s.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="propose":
        propose(args.output)
    else:
        score(args.predictions,args.expected_sha,args.output)
