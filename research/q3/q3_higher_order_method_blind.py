"""Q3 higher-order method invention, SHA-frozen source-first experiment.

The meta method sees two source families and separate falsifiers; no target
outputs from the new families are read before the proposal file is frozen.
New operands are existing classical transitions, not invented primitive math.
Researcher-designed tasks, not untouched independent ARC problems.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from math import gcd
from random import Random

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from neumann1.higher_order_method_inventor import (
    HigherOrderMethodInventor,SourceCase,conditional_proof)


def graph(n):
    edge={k:{k+1} for k in range(n-1)}
    edge[n-1]=set()
    def step(s):
        return frozenset(set(s)|{v for u in s for v in edge[u]})
    return SourceCase(step,frozenset({0}),frozenset(range(n)),"graph")


def collapsing(n):
    return SourceCase(lambda s:s.replace("aa","a"),"a"*n,"a","symbolic")


def sorting(n):
    def step(s):
        v=list(s)
        for i in range(len(v)-1):
            if v[i]>v[i+1]:
                v[i],v[i+1]=v[i+1],v[i]
                break
        return tuple(v)
    return SourceCase(step,tuple(range(n,0,-1)),
                      tuple(range(1,n+1)),"sort")


def training():
    first=tuple(graph(n) for n in (2,3,3,2))+tuple(
        collapsing(n) for n in (2,3,4,2))
    length_feedback=tuple(graph(n) for n in (13,17))+tuple(
        collapsing(n) for n in (16,23))
    state_feedback=tuple(sorting(n) for n in (6,7))
    return first,length_feedback,state_feedback


def catalog():
    rng=Random(20261109)
    tasks=[]
    for _ in range(60):
        tasks.append(("euclid",[rng.randrange(1000,100000),
                                rng.randrange(1,1000)]))
    for _ in range(60):
        tasks.append(("dedup",[rng.randrange(12)
                    for _ in range(rng.randrange(8,40))]))
    tasks.extend(("sort",n) for n in range(8,15))
    tasks.extend(("graph",n) for n in range(19,44))
    tasks.extend(("cycle",n) for n in range(2,12))
    for _ in range(100):
        n=rng.randrange(1024,10000000)
        tasks.append(("interval",[n,rng.randrange(n)]))
    return tuple(tasks)


def transition(family,spec):
    if family=="euclid":
        def step(s):
            a,b=s
            return s if b==0 else (b,a%b)
        return step,tuple(spec)
    if family=="dedup":
        def step(s):
            for i in range(len(s)-1,-1,-1):
                if s[i] in s[:i]:
                    return s[:i]+s[i+1:]
            return s
        return step,tuple(spec)
    if family=="sort":
        t=sorting(spec)
        return t.transition,t.initial
    if family=="graph":
        t=graph(spec)
        return t.transition,t.initial
    if family=="cycle":
        return lambda x,n=spec:(x+1)%n,0
    if family=="interval":
        size,answer=spec
        def step(s):
            lo,hi=s
            if lo==hi:return s
            mid=(lo+hi)//2
            return ((mid+1,hi) if mid<answer else (lo,mid))
        return step,(0,size-1)
    raise ValueError("unsupported finite source family")


def target_oracle(family,spec):
    """Only score() calls this for heldout catalog task IDs."""
    if family=="euclid":return gcd(*spec),0
    if family=="dedup":return tuple(dict.fromkeys(spec))
    if family=="sort":return tuple(range(1,spec+1))
    if family=="graph":return frozenset(range(spec))
    if family=="interval":return spec[1],spec[1]
    if family=="cycle":return None
    raise ValueError("unknown target")


def encode(value):
    if isinstance(value,frozenset):
        return {"type":"set","value":sorted(value)}
    if isinstance(value,tuple):
        return {"type":"tuple","value":list(value)}
    if value is None:
        return {"type":"abstain"}
    return {"type":"scalar","value":value}


def verify_source_method(method):
    rng=Random(4233)
    verifiers=[]
    for i in range(3):
        a,b=rng.randrange(1000,100000),rng.randrange(1,1000)
        verifiers.append(("euclid",[a,b]))
        verifiers.append(("dedup",[rng.randrange(10) for _ in range(23)]))
        verifiers.append(("sort",15+i))
        verifiers.append(("graph",44+i))
        n=50000000+i
        verifiers.append(("interval",[n,n//3]))
    # These 15 SOURCE cases are disjoint from all final target seeds/specs;
    # they verify the frozen method but are never used to refit it.
    for family,spec in verifiers:
        step,initial=transition(family,spec)
        result=method.compile(step).run(initial)
        if result.value!=target_oracle(family,spec):
            raise ValueError("new family source verifier falsified method")
    return len(verifiers)


def propose(output):
    first,length_feedback,state_feedback=training()
    learner=HigherOrderMethodInventor(max_unroll=3,max_steps=256)
    one=learner.discover(first)
    two=learner.discover(first+length_feedback,old=one)
    three=learner.discover(
        first+length_feedback+state_feedback,old=two)
    if (one.program.ast!=("sequence",2,("apply","transition"))
            or "length" not in repr(two.program.ast)
            or three.program.ast!=(
                "while",
                ("not",("equal",("read","current"),
                         ("read","next"))),
                ("apply","transition"))):
        raise ValueError("method did not self-invent two required rewrites")
    source_check_count=verify_source_method(three.program)
    records=[]
    for family,spec in catalog():
        step,initial=transition(family,spec)
        # Never read target_oracle for these IDs in propose().
        guess=three.program.compile(step).run(initial)
        baseline=one.program.compile(step).run(initial)
        records.append({
            "family":family,"spec":spec,
            "method_answer":encode(guess.value),
            "method_status":guess.status,
            "initial_method_answer":encode(baseline.value),
            "method_transition_calls":guess.transition_calls})
    payload={
        "schema":"NEUMANN.Q3.HIGHER_ORDER.BLIND.v1",
        "initial_method_ast":one.program.ast,
        "middle_method_ast":two.program.ast,
        "final_method_ast":three.program.ast,
        "initial_source_training":len(first),
        "first_source_counterexamples":two.counterexamples,
        "second_source_counterexamples":three.counterexamples,
        "heldout_family_source_verifiers":source_check_count,
        "target_gold_used_in_propose":False,
        "records":records}
    output.write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print("Q3 HIGHER-ORDER PREDICTIONS FROZEN",
          hashlib.sha256(output.read_bytes()).hexdigest(),
          "unseen cases",len(records))


def score(frozen,expected_sha,output):
    digest=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if digest!=expected_sha:
        raise ValueError("prediction file changed after source freeze")
    source=json.loads(frozen.read_text())
    if source["target_gold_used_in_propose"]:
        raise ValueError("original-target leakage")
    by_domain={}
    for row in source["records"]:
        family,spec=row["family"],row["spec"]
        target=target_oracle(family,spec)
        if family=="cycle":
            passed=(row["method_status"]=="ABSTAIN_BUDGET"
                    and row["method_answer"]==encode(None))
            old=False
        else:
            passed=row["method_answer"]==encode(target)
            old=row["initial_method_answer"]==encode(target)
        metrics=by_domain.setdefault(family,{
            "tasks":0,"new_correct":0,"old_correct":0})
        metrics["tasks"]+=1
        metrics["new_correct"]+=int(passed)
        metrics["old_correct"]+=int(old)
    positive=[x for k,x in by_domain.items() if k!="cycle"]
    summary={
        "convergent_heldout_tasks":sum(x["tasks"] for x in positive),
        "convergent_heldout_correct":sum(x["new_correct"] for x in positive),
        "previous_method_correct":sum(x["old_correct"] for x in positive),
        "unseen_euclid_dedup_interval_cases":sum(
            by_domain[k]["tasks"] for k in ("euclid","dedup","interval")),
        "unseen_euclid_dedup_interval_correct":sum(
            by_domain[k]["new_correct"]
            for k in ("euclid","dedup","interval")),
        "nonconvergent_cases":by_domain["cycle"]["tasks"],
        "nonconvergent_safe_abstains":by_domain["cycle"]["new_correct"],
        "independent_source_verifiers":
            source["heldout_family_source_verifiers"],
        "method_rewrites":2,
        "final_method_ast":source["final_method_ast"],
        "frozen_prediction_sha256":digest,
        "conditional_proof":conditional_proof(),
        "meta_language_primitives_predefined":True,
        "transition_operators_classical_supplied":True,
        "independent_author_original":False,
        "global_Q3_Q6_pass":False}
    output.write_text(json.dumps({
        "schema":"NEUMANN.Q3.HIGHER_ORDER.SCORED.v1",
        "summary":summary,"by_domain":by_domain},indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("propose")
    p.add_argument("--output",type=Path,required=True)
    q=sub.add_parser("score")
    q.add_argument("--predictions",type=Path,required=True)
    q.add_argument("--expected-sha",required=True)
    q.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="propose":propose(args.output)
    else:score(args.predictions,args.expected_sha,args.output)
