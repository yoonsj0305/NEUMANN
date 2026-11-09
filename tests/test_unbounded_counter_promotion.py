"""New learned nonregular operator becomes a first-class instruction in engines.

Demonstrate genuine expressivity delta (old grammar fails, promoted unbounded
state instruction solves), with independent source checks beyond all prior
source-query lengths and heldout far-size transfer.
"""
import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.induced_grammar import eval_ast
from neumann1.unbounded_counter_inventor import UnboundedCounterInventor


def oracle(w):
    if not w:return 1
    half=len(w)//2
    return int(len(w)%2==0 and w=="a"*half+"b"*half)


def cases():
    train=tuple((x,oracle(x)) for x in (
        "a","b","ab","ba","aabb","aaabbb","aba","abab",
        "aab","abb","aaaabbbb","baba","aaabb","aababb",
        "aabbb","aaa","bbbb"))
    independent=tuple((w,oracle(w)) for w in (
        "a"*10+"b"*10,
        "a"*11+"b"*11,
        "a"*12+"b"*12,
        "ab"*11,
        "b"*13+"a"*13))
    targets=tuple((w,oracle(w)) for w in (
        "a"*40+"b"*40,"a"*70+"b"*70,
        "ab"*75,"a"*50+"b"*49,"b"*71+"a"*71,
        "a"*101+"b"*101))
    return train,independent,targets


@pytest.mark.parametrize("engine_type",[NeumannEngine,RegistryEngine])
def test_inferred_unbounded_counter_changes_actual_program_language(engine_type):
    train,checks,targets=cases()
    engine=engine_type(None,[],None) if engine_type is NeumannEngine \
        else engine_type(None,None)
    old=engine.synthesize_with_invented_grammar(train)
    assert not old.solved
    invented=engine.invent_unbounded_counter_operator(
        oracle,alphabet=("a","b"))
    assert invented.status=="SOURCE_VERIFIED_UNBOUNDED_COUNTER"
    assert invented.program.source_horizon==14
    engine.promote_unbounded_counter_operator(
        "invented:counter:balanced_blocks",invented.program,
        independent_source_checks=checks)
    new=engine.synthesize_with_invented_grammar(train)
    assert new.solved
    assert "invented:counter:balanced_blocks" in repr(new.expression)
    for x,y in targets:
        got=eval_ast(
            new.expression,x,
            dynamic_primitives=engine._invented_grammar.dynamic_primitives)
        assert got==y


def test_counter_promotion_refuses_reused_or_falsified_source_checks():
    engine=NeumannEngine(None,[],None)
    invented=UnboundedCounterInventor().invent(oracle)
    assert invented.program is not None
    _,checks,_=cases()
    reused=(("aaabbb",1),)+checks[1:]
    with pytest.raises(ValueError):
        engine.promote_unbounded_counter_operator(
            "invented:counter:reused",invented.program,
            independent_source_checks=reused)
    false_checks=(checks[0][0],1-checks[0][1]),*checks[1:]
    with pytest.raises(ValueError):
        engine.promote_unbounded_counter_operator(
            "invented:counter:false",invented.program,
            independent_source_checks=false_checks)
    assert engine._invented_grammar.dynamic_primitives=={}
