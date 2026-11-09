"""Q3 terminal-only process invention: NO ONE-STEP SOURCE examples.

Run the previously invented control AST against novel latent state-update
expressions fitted from only (initial_state, final_state) SOURCE pairs.
Researcher-defined classical independent reference outcomes are never passed
as source successor labels or whole task programs to the inventor.
"""
from random import Random
import re
import pytest

from neumann1 import NeumannEngine,RegistryEngine
from neumann1.terminal_only_process_inventor import (
    TerminalOnlyProcessInventor)
from research.q3.q3_higher_order_method_blind import training


def learn_control(engine):
    small,long,state=training()
    engine.meta_learn_higher_order_method(small)
    engine.meta_revise_higher_order_method(long)
    method=engine.meta_revise_higher_order_method(state).program
    assert method.ast[0]=="while"
    assert "length" not in repr(method.ast)
    return method


def endpoint_cases():
    # These are ENDPOINT pairs only, NOT successor step labels!
    # Integer process needs multiple unobserved steps to reach 0.
    numbers=tuple((x,0) for x in (0,1,2,3,5,8,13,17))
    number_checks=tuple((x,0) for x in (4,7,11,19))
    # Set process removes elements until it reaches empty; this is
    # multi-step unless the source set contains <=1 item.
    sets=(
        frozenset(),frozenset((3,)),
        frozenset((2,5)),
        frozenset((1,3,9)),
        frozenset((2,6,7,15)),
        frozenset((4,8,12,16,20)),
        frozenset((5,9,13,14)),
    )
    final_set=lambda s:frozenset()
    set_source=tuple((s,final_set(s)) for s in sets)
    set_checks=tuple((s,final_set(s)) for s in (
        frozenset((7,11)),frozenset((4,9,23)),
        frozenset((2,8,14,18,25)),
        frozenset((16,22,31,39))))
    # New symbolic rule removes duplicate b's. The control learner's
    # earlier training saw 'aa' collapsing, not this target law.
    words=("bbbbbbbb","abbba","bbabb","aabbbbaa","bbbbbabb",
           "abbabbbaa","abbbbbabbbb","aabbb")
    shrink=lambda s:re.sub(r"b+","b",s)
    word_source=tuple((s,shrink(s)) for s in words)
    word_checks=tuple((s,shrink(s)) for s in (
        "abbbbbba","bbaabbbba","abbbbbbabbb","bbbaabbabb"))
    return ((numbers,number_checks),
            (set_source,set_checks),(word_source,word_checks))


@pytest.mark.parametrize("family",["int","set","str"])
def test_synthesizes_nontrivial_latent_process_without_successor_examples(family):
    engine=NeumannEngine(None,[],None)
    method=learn_control(engine)
    data=dict(zip(("int","set","str"),endpoint_cases()))
    source,checks=data[family]
    found=engine.meta_invent_terminal_only_process(
        source,checks,max_nodes=6,max_expressions=60000,
        max_source_ms=20000)
    assert found is not None
    assert found.transition_type==family
    assert found.max_observed_transition_calls>=3
    assert found.source_examples==len(source)
    assert found.independent_checks==len(checks)
    assert found.ast[0]=="source_invented_process_from_terminal_only"
    compiled=found.compile()
    rng=Random(19010)
    for _ in range(100):
        if family=="int":
            x=rng.randrange(0,180)
            answer=0
        elif family=="set":
            x=frozenset(rng.sample(range(10,999),rng.randrange(1,100)))
            answer=frozenset()
        else:
            x="".join(rng.choice("aabbb")
                      for i in range(rng.randrange(12,180)))
            answer=re.sub(r"b+","b",x)
        out=compiled.run(x)
        assert out.status=="HALT_CERTIFIED_FIXED_POINT"
        assert out.value==answer


def test_both_production_engines_share_terminal_only_invention_interface():
    source,checks=endpoint_cases()[0]
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        learn_control(engine)
        method=engine.meta_invent_terminal_only_process(
            source,checks,max_nodes=6,max_source_ms=20000)
        assert method is not None
        assert method.compile().run(127).value==0


def test_known_classical_solution_bypasses_new_invention():
    engine=NeumannEngine(None,[],None)
    learn_control(engine)
    source,checks=endpoint_cases()[0]
    assert engine.meta_invent_terminal_only_process(
        source,checks,known_classical=lambda x:0) is None


def test_invalid_source_independence_and_non_source_color_abstain():
    engine=NeumannEngine(None,[],None)
    control=learn_control(engine)
    source,checks=endpoint_cases()[2]
    with pytest.raises(ValueError):
        TerminalOnlyProcessInventor().invent(
            source,independent_terminal_checks=source[:3],
            control=control)
    bad_checks=(("bbbabbb","cannot_be_constructed"),)+checks[1:]
    with pytest.raises(ValueError,match="ABSTAIN"):
        TerminalOnlyProcessInventor(
            max_nodes=5,max_source_ms=10000).invent(
                source,independent_terminal_checks=bad_checks,
                control=control)


def test_endpoint_information_does_not_identify_true_trajectory():
    # Two physically different hypothetical processes agree on ALL
    # initial -> terminal pairs. Their intermediate trajectories differ.
    minus_one=lambda x:max(x-1,0)
    minus_two=lambda x:max(x-2,0)
    for x in range(100):
        a,b=x,x
        while minus_one(a)!=a:a=minus_one(a)
        while minus_two(b)!=b:b=minus_two(b)
        assert a==b==0
    assert minus_one(11)!=minus_two(11)
