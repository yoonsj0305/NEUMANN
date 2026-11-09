"""Q3 source-first first proposal: active terminal CEGIS on THREE state types.

The source inputs, training labels and generated SOURCE experiment oracle are
available to the learner; fresh target labels remain inaccessible until score.
Researcher-created synthetic benchmark. No independent-author or frontier claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

from neumann1 import NeumannEngine
from research.q3.q3_higher_order_method_blind import training
from research.q3.q3_terminal_only_blind_first import (
    source_endpoints, encode)


def _source_oracle(kind):
    if kind=="int":
        return lambda n: min(n,0)
    if kind=="set":
        return lambda s: frozenset()
    if kind=="str":
        return lambda s: re.sub("b+","b",s)
    raise TypeError(kind)


def _cases():
    rng=random.Random(314159265)
    examples=[]
    for n in range(100,300):
        examples.append(("int",n))
    for n in range(-300,-100):
        examples.append(("int",n))
    for _ in range(200):
        examples.append(("set",frozenset(
            rng.sample(range(100,2000),rng.randrange(4,120)))))
    for _ in range(200):
        examples.append(("str","".join(
            rng.choice("aabbb") for i in range(rng.randrange(25,161)))))
    return tuple(examples)


def _encode_input(x):
    return sorted(x) if type(x) is frozenset else x


def propose(outpath: Path):
    engine=NeumannEngine(None,[],None)
    a,b,c=training()
    engine.meta_learn_higher_order_method(a)
    engine.meta_revise_higher_order_method(b)
    engine.meta_revise_higher_order_method(c)
    source=source_endpoints()
    processes={}
    stats={}
    for kind,(train,checks) in source.items():
        # The SIGN-PRESERVING negative SOURCE law is never shown via original
        # positive-only integer endpoints. Its first evidence is a proposed
        # experiment from an AST built by the generator.
        oracle=_source_oracle(kind)
        learned=engine.meta_invent_active_terminal_process(
            train,checks,oracle,max_nodes=8,max_expressions=150000,
            max_source_ms=25000,max_oracle_queries=512,
            max_rounds=5)
        if learned.program is None:
            raise RuntimeError(kind+" failed source invention: "+learned.status)
        old=engine.meta_invent_terminal_only_process(
            train,checks,max_nodes=8,max_expressions=150000,
            max_source_ms=25000)
        processes[kind]=(old,learned.program)
        stats[kind]={
            "status":learned.status,
            "source_queries":learned.source_oracle_queries,
            "source_experiment_programs":learned.source_experiment_programs,
            "source_experiment_inputs":learned.source_experiment_inputs,
            "revisions":[{
                "counterexample_input":_encode_input(r.counterexample_input),
                "expected_terminal":_encode_input(r.expected_terminal),
                "predicted_terminal":_encode_input(r.predicted_terminal),
                "old_ast":repr(r.old_ast),
                "new_ast":repr(r.new_ast)}
                for r in learned.revisions],
            "old_ast":repr(old.transition_ast),
            "new_ast":repr(learned.program.transition_ast),
            "source_endpoints":learned.source_endpoints}
    rows=[]
    for kind,x in _cases():
        old,new=processes[kind]
        baseline=old.compile(max_steps=1024).run(x)
        improved=new.compile(max_steps=1024).run(x)
        rows.append({
            "kind":kind,"input":_encode_input(x),
            "baseline":encode(baseline.value),
            "baseline_status":baseline.status,
            "prediction":encode(improved.value),
            "status":improved.status})
    payload={
        "schema":"NEUMANN.Q3.ACTIVE-TERMINAL.SOURCE-FIRST.v1",
        "human_authored_synthetic":True,
        "target_labels_seen_during_proposal":False,
        "target_successor_labels_seen":0,
        "source_only_experiment_feedback":True,
        "source_programs":stats,
        "rows":rows}
    outpath.write_text(json.dumps(
        payload,sort_keys=True,separators=(",",":"))+"\n")
    print("SOURCE_ONLY_800_FIRST_SHA256",
          hashlib.sha256(outpath.read_bytes()).hexdigest())
    print("REVISIONS",json.dumps(stats,sort_keys=True))


def score(frozen:Path,sha:str,outpath:Path):
    actual=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if actual!=sha:
        raise ValueError("proposal SHA was not frozen")
    data=json.loads(frozen.read_text())
    if data["target_labels_seen_during_proposal"] or data[
            "target_successor_labels_seen"]!=0:
        raise ValueError("target leakage")
    totals={}
    errors=[]
    for i,row in enumerate(data["rows"]):
        kind=row["kind"]
        x=frozenset(row["input"]) if kind=="set" else row["input"]
        expected=encode(_source_oracle(kind)(x))
        good=(row["prediction"]==expected and
              row["status"]=="HALT_CERTIFIED_FIXED_POINT")
        baseline=(row["baseline"]==expected and
                  row["baseline_status"]=="HALT_CERTIFIED_FIXED_POINT")
        tally=totals.setdefault(kind,{
            "n":0,"before":0,"after":0})
        tally["n"]+=1
        tally["before"]+=int(baseline)
        tally["after"]+=int(good)
        if not good:errors.append({"index":i,"kind":kind})
    report={
        "frozen_sha256":actual,"totals":totals,
        "first_proposal_tasks":len(data["rows"]),
        "exact_before":sum(v["before"] for v in totals.values()),
        "exact_after":sum(v["after"] for v in totals.values()),
        "all_correct":not errors,
        "new_grammar_from_human_supplied_primitives":False,
        "independent_author_original":False,
        "unrestricted_q3_q6_pass":False,
        "scientific_boundary":"synthetic, source-oracle-active, typed DSL"}
    outpath.write_text(json.dumps(
        {"report":report,"errors":errors},indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if errors:
        raise AssertionError("frozen output was not uniformly correct")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("propose");p.add_argument("--output",type=Path,required=True)
    s=sub.add_parser("score")
    s.add_argument("--predictions",type=Path,required=True)
    s.add_argument("--sha",required=True)
    s.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=="propose": propose(args.output)
    else: score(args.predictions,args.sha,args.output)
