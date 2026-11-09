"""Q3: the DISCOVERY METHOD (control AST) is invented and twice revised."""
from math import gcd
from random import Random
import pytest
from neumann1 import NeumannEngine,RegistryEngine
from neumann1.higher_order_method_inventor import (
    HigherOrderMethodInventor,SourceCase,conditional_proof)


def reach(n):
    edges={i:{i+1} for i in range(n-1)}
    edges[n-1]=set()
    def t(s):
        return frozenset(set(s)|{v for u in s for v in edges[u]})
    return SourceCase(t,frozenset((0,)),frozenset(range(n)),"graph")


def collapse(n):
    return SourceCase(lambda s:s.replace("aa","a"),"a"*n,"a","symbolic")


def bubble(n):
    def t(a):
        a=list(a)
        for i in range(len(a)-1):
            if a[i]>a[i+1]:
                a[i],a[i+1]=a[i+1],a[i]
                break
        return tuple(a)
    return SourceCase(t,tuple(range(n,0,-1)),
                      tuple(range(1,n+1)),"sort")


def source_families():
    first=tuple(reach(n) for n in (2,3,3,2))+tuple(
        collapse(n) for n in (2,3,4,2))
    long=tuple(reach(n) for n in (13,17))+tuple(
        collapse(n) for n in (16,23))
    preserving=tuple(bubble(n) for n in (6,7))
    return first,long,preserving


def euclid(a,b):
    def step(s):
        x,y=s
        return s if y==0 else (y,x%y)
    return SourceCase(step,(a,b),(gcd(a,b),0),"euclid")


def remove_duplicate(values):
    def step(s):
        for i in range(len(s)-1,-1,-1):
            if s[i] in s[:i]:return s[:i]+s[i+1:]
        return s
    return SourceCase(step,values,tuple(dict.fromkeys(values)),
                      "constraint_projection")


def unseen_source_and_test_cases():
    rng=Random(20261109)
    fresh=[euclid(rng.randrange(1000,100000),
                  rng.randrange(1,1000)) for _ in range(60)]
    fresh.extend(remove_duplicate(tuple(
        rng.randrange(12) for _ in range(rng.randrange(8,40))))
                 for _ in range(60))
    fresh.extend(bubble(n) for n in range(8,15))
    fresh.extend(reach(n) for n in range(19,44))
    assert len(fresh)==152
    return tuple(fresh)


def assert_generated_revisions(engine):
    first,long,preserving=source_families()
    a=engine.meta_learn_higher_order_method(first)
    assert a.program.ast==("sequence",2,("apply","transition"))
    assert a.source_cases==8
    b=engine.meta_revise_higher_order_method(long)
    assert b.counterexamples==4
    assert b.program.ast[0]=="while" and "length" in repr(b.program.ast)
    c=engine.meta_revise_higher_order_method(preserving)
    assert c.counterexamples==2
    assert c.program.ast==(
        "while",
        ("not",("equal",("read","current"),("read","next"))),
        ("apply","transition"))
    return a,b,c


@pytest.mark.parametrize("engine",[
    NeumannEngine(None,[],None),RegistryEngine(None,None)])
def test_live_engines_autonomously_invent_two_higher_order_rewrites(engine):
    old,partial,final=assert_generated_revisions(engine)
    assert final.program.ast not in [
        r.program.ast for r in old.meta_records
        if r.program.ast[0]=="sequence"]
    assert len(final.meta_records)==75
    assert all(r.passed<final.source_cases
               for r in final.meta_records
               if r.program.ast[0]=="sequence")
    outcomes={}
    before=0
    for task in unseen_source_and_test_cases():
        prediction=engine.meta_compile_higher_order_method(
            task.transition).run(task.initial)
        assert prediction.value==task.expected
        assert prediction.status=="HALT_CERTIFIED_FIXED_POINT"
        outcomes[task.group]=outcomes.get(task.group,0)+1
        previous=old.program.compile(task.transition).run(task.initial)
        before+=previous.value==task.expected
    assert outcomes=={
        "euclid":60,"constraint_projection":60,"sort":7,"graph":25}
    assert before==2
    assert "deterministic" in conditional_proof()


def test_looping_nonconvergent_problems_do_not_fake_answers():
    learner=HigherOrderMethodInventor(max_steps=64)
    a,b,c=source_families()
    m=learner.discover(a+b+c)
    for n in range(2,12):
        model=m.program.compile(lambda x,n=n:(x+1)%n)
        outcome=model.run(0)
        assert outcome.status=="ABSTAIN_BUDGET"
        assert outcome.value is None


def test_classical_algorithm_is_verified_and_not_reinvented():
    a,b,c=source_families()
    method=HigherOrderMethodInventor().discover(a+b+c).program
    def prohibited(x):
        raise AssertionError("should never execute invented transition")
    direct=method.compile(
        prohibited,known_classical=lambda n:n+1,
        independent_source_checks=((3,4),(7,8)))
    assert direct.run(9).value==10
    assert direct.run(9).transition_calls==0
    with pytest.raises(ValueError):
        method.compile(prohibited,known_classical=lambda n:n+2,
                       independent_source_checks=((3,4),))


def test_meta_policy_ignores_domain_names_and_requires_real_counterexamples():
    a,b,c=source_families()
    learner=HigherOrderMethodInventor()
    first=learner.discover(a)
    with pytest.raises(ValueError):
        learner.discover(a,old=first)
    renamed=tuple(SourceCase(v.transition,v.initial,v.expected,
                             "intentionally_wrong_domain_label")
                  for v in a+b+c)
    assert learner.discover(renamed).program.ast==learner.discover(
        a+b+c).program.ast
