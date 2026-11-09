"""Q3: generic SOURCE input/next-state → new T AST → learned method AST.

No complete integer, set or string algorithm supplied to either inventor.
Each source family provides transition examples, independent successor checks,
and independent SOURCE terminal checks. Final task inputs remain unseen.
"""
from random import Random
from math import gcd
import re
import pytest
from neumann1 import NeumannEngine,RegistryEngine
from neumann1.higher_order_method_inventor import SourceCase
from neumann1.typed_transition_inventor import TypedTransitionInventor


def sources_for_control():
    def reach(n):
        adj={i:{i+1} for i in range(n-1)}
        adj[n-1]=set()
        return SourceCase(
            lambda s,g=adj:frozenset(
                set(s)|{v for u in s for v in g[u]}),
            frozenset({0}),frozenset(range(n)))
    def collapse(n):
        return SourceCase(lambda s:s.replace("aa","a"),"a"*n,"a")
    def sort(n):
        def t(a):
            a=list(a)
            for i in range(len(a)-1):
                if a[i]>a[i+1]:
                    a[i],a[i+1]=a[i+1],a[i]
                    break
            return tuple(a)
        return SourceCase(t,tuple(range(n,0,-1)),
                          tuple(range(1,n+1)))
    small=tuple(reach(n) for n in (2,3,3,2))+tuple(
        collapse(n) for n in (2,3,4,2))
    large=tuple(reach(n) for n in (13,17))+tuple(
        collapse(n) for n in (16,23))
    preserving=(sort(6),sort(7))
    return small,large,preserving


def model_for_engine(engine):
    small,large,preserving=sources_for_control()
    engine.meta_learn_higher_order_method(small)
    engine.meta_revise_higher_order_method(large)
    final=engine.meta_revise_higher_order_method(preserving)
    assert final.program.ast[0]=="while"
    assert "length" not in repr(final.program.ast)
    return engine


@pytest.mark.parametrize("engine",[NeumannEngine(None,[],None),
                                   RegistryEngine(None,None)])
def test_end_to_end_autonomous_integer_set_string_program_creation(engine):
    model_for_engine(engine)

    def integer_step(x):return max(x-1,0)
    data=(0,1,2,5,8)
    check=(3,4,9,19)
    integer,program=engine.meta_invent_transition_and_solver(
        [(x,integer_step(x)) for x in data],
        [(x,integer_step(x)) for x in check],
        [(11,0),(17,0)])
    assert "sub" in repr(integer.ast) and integer.ast_nodes>=3
    assert all(integer(x)==integer_step(x) for x in range(-30,201))
    assert all(program.run(x).value==0 for x in (35,57,100,150,200))

    def set_step(s):
        return frozenset(s-{min(s)}) if s else s
    observed=(frozenset(),frozenset((1,)),
              frozenset((1,2,3)),frozenset((2,7)),
              frozenset((1,3,9)),frozenset((4,5,6)))
    held=(frozenset((5,8)),frozenset((8,9,10)),
          frozenset((2,4,17)))
    removal,program=engine.meta_invent_transition_and_solver(
        [(x,set_step(x)) for x in observed],
        [(x,set_step(x)) for x in held],
        [(frozenset((1,2,3,4)),frozenset()),
         (frozenset((3,9)),frozenset())])
    assert "difference" in repr(removal.ast)
    assert "singleton" in repr(removal.ast)
    assert all(program.run(frozenset(range(20,20+n))).value==
               frozenset() for n in (8,23,50,75,125))
    assert all(removal(frozenset(range(i,i+4)))==
               set_step(frozenset(range(i,i+4)))
               for i in range(30))

    def string_step(s):return s.replace("aa","a")
    train=("aaaa","aa","a","baaa","bbaa","baaba")
    checks=("aaaaaa","abaaaa","bbbaaa","abaabb")
    rewriting,program=engine.meta_invent_transition_and_solver(
        [(x,string_step(x)) for x in train],
        [(x,string_step(x)) for x in checks],
        [("aaaaaaa","a"),("bbaaaa","bba")])
    assert "replace" in repr(rewriting.ast)
    rng=Random(3001)
    for _ in range(120):
        x="".join(rng.choice("aab")
                  for _ in range(rng.randrange(10,120)))
        result=program.run(x)
        assert result.status=="HALT_CERTIFIED_FIXED_POINT"
        assert result.value==re.sub("a+","a",x)


def test_no_fabricated_rule_when_source_disagrees_or_budget_exhausted():
    with pytest.raises(ValueError):
        TypedTransitionInventor(max_nodes=3).invent(
            [(1,999),(2,998),(3,997)],
            independent_source_checks=[(4,996),(5,995)])
    engine=model_for_engine(NeumannEngine(None,[],None))
    with pytest.raises(ValueError):
        engine.meta_invent_transition_and_solver(
            [(0,0),(1,0),(2,1),(5,4),(8,7)],
            [(3,2),(4,3),(9,8)],
            [(11,999),(17,999)])
