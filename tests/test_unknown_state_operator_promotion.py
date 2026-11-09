"""Q3 new semantic instruction promoted into a real program synthesizer.

Tests the actual ability delta: cold source-program grammar cannot express a
binary modular predicate; source-discovered hidden-state operator extends that
grammar and then solves later tasks with independently validated semantics.
"""
import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.induced_grammar import eval_ast


def _oracle(word):
    return int(int(word or "0",2)%5==0)


def _sources():
    checks=tuple((w,_oracle(w)) for w in (
        "110101010101","100110101101","111001101110",
        "110010110001"))
    sample=tuple((format(n,"b"),int(n%5==0)) for n in (
        3,5,10,12,15,19,24,31,40,61,73,100,118,125))
    heldout=tuple((format(n,"b"),int(n%5==0)) for n in (
        512,1023,2047,12345,50005,99991,123456,1048575))
    return sample,checks,heldout


@pytest.mark.parametrize("engine_type",[NeumannEngine,RegistryEngine])
def test_source_invented_new_operator_is_reusable_in_real_program_synthesis(
        engine_type):
    engine=engine_type(None,[],None) if engine_type is NeumannEngine \
        else engine_type(None,None)
    train,source_checks,heldout=_sources()
    before=engine.synthesize_with_invented_grammar(train)
    assert not before.solved, "old DSL must fail before introducing new semantics"

    discovery=engine.invent_unknown_state_operator(
        _oracle,max_states=5,alphabet=("0","1"),
        independent_source_checks=source_checks)
    assert discovery.status=="SOURCE_CERTIFIED_CONDITIONAL_DFA"
    assert discovery.program.state_count==5
    engine.promote_unknown_state_operator(
        "invented:state:binary_mod5",discovery.program,
        independent_source_checks=source_checks)

    after=engine.synthesize_with_invented_grammar(train)
    assert after.solved
    assert "invented:state:binary_mod5" in repr(after.expression)
    for x,y in heldout:
        assert eval_ast(
            after.expression,x,
            dynamic_primitives=engine._invented_grammar.dynamic_primitives)==y


def test_reject_bad_promotion_and_unverified_source_grammar():
    train,checks,_=_sources()
    engine=NeumannEngine(None,[],None)
    learned=engine.invent_unknown_state_operator(
        _oracle,max_states=5,independent_source_checks=checks)
    assert learned.program is not None
    corrupt=list(checks)
    corrupt[0]=(corrupt[0][0],1-corrupt[0][1])
    with pytest.raises(ValueError,match="falsifies"):
        engine.promote_unknown_state_operator(
            "invented:state:bad",learned.program,
            independent_source_checks=tuple(corrupt))
    with pytest.raises(ValueError):
        engine.promote_unknown_state_operator(
            "dangerously_unscoped_primitive",learned.program,
            independent_source_checks=checks)
    assert not engine._invented_grammar.dynamic_primitives


def test_no_promoted_primitive_without_source_independent_evidence():
    learned=NeumannEngine(None,[],None).invent_unknown_state_operator(
        _oracle,max_states=5)
    assert learned.program
    engine=RegistryEngine(None,None)
    with pytest.raises(ValueError):
        engine.promote_unknown_state_operator(
            "invented:state:missing_independent",
            learned.program,independent_source_checks=())
