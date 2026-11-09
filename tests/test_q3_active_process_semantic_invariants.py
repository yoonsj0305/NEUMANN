"""Q3 generated-program semantics: bounded exhaustive checks and invariants.

The program ASTs come from the live source-only learner.  Assertions here
validate their semantics after synthesis; these are NOT blind, independent-
author original problem wins or a claim of unbounded runtime correctness.
"""
from functools import lru_cache
from itertools import combinations, product
import re

from neumann1 import NeumannEngine
from research.q3.q3_higher_order_method_blind import training
from research.q3.q3_terminal_only_blind_first import source_endpoints


@lru_cache(maxsize=1)
def learned():
    engine=NeumannEngine(None,[],None)
    a,b,c=training()
    engine.meta_learn_higher_order_method(a)
    engine.meta_revise_higher_order_method(b)
    engine.meta_revise_higher_order_method(c)
    outcome={}
    gold={
        "int":lambda n:min(n,0),
        "set":lambda s:frozenset(),
        "str":lambda s:re.sub(r"b+","b",s)}
    for kind,(source,checks) in source_endpoints().items():
        result=engine.meta_invent_active_terminal_process(
            source,checks,gold[kind],max_nodes=8,
            max_expressions=150000,max_source_ms=25000,
            max_oracle_queries=512,max_rounds=5)
        assert result.status=="SOURCE_PROBE_CONSISTENT"
        assert result.program is not None
        outcome[kind]=result.program
    return outcome


def test_signed_integer_discovered_transition_carries_piecewise_invariant():
    program=learned()["int"]
    step=program.transition
    executable=program.compile(max_steps=1024)
    for n in range(-256,257):
        expected_step=n-1 if n>0 else n
        assert step(n)==expected_step
        out=executable.run(n)
        assert out.status=="HALT_CERTIFIED_FIXED_POINT"
        assert out.value==min(n,0)
        assert out.transition_calls==(n+1 if n>=0 else 1)
    # No unjustified extrapolation beyond the explicit execution budget.
    assert program.compile(max_steps=256).run(300).status=="ABSTAIN_BUDGET"


def test_finite_set_discovered_transition_exhaustive_six_element_universe():
    program=learned()["set"]
    atoms=(2,3,5,7,11,13)
    executable=program.compile(max_steps=1024)
    examined=0
    for count in range(len(atoms)+1):
        for group in combinations(atoms,count):
            state=frozenset(group)
            expected_step=state-frozenset((min(state),)) if state else state
            assert program.transition(state)==expected_step
            out=executable.run(state)
            assert out.status=="HALT_CERTIFIED_FIXED_POINT"
            assert out.value==frozenset()
            assert out.transition_calls==len(state)+1
            examined+=1
    assert examined==64


def test_string_discovered_transition_exhaustive_binary_strings_length_0_to_10():
    program=learned()["str"]
    executable=program.compile(max_steps=1024)
    examined=0
    for n in range(11):
        for chars in product("ab",repeat=n):
            value="".join(chars)
            successor=program.transition(value)
            assert successor==value.replace("bb","b")
            if "bb" in value:
                assert len(successor)<len(value)
            else:
                assert successor==value
            out=executable.run(value)
            assert out.status=="HALT_CERTIFIED_FIXED_POINT"
            assert out.value==re.sub(r"b+","b",value)
            examined+=1
    assert examined==2047


def test_endpoint_observations_cannot_identify_the_hidden_process():
    # Even if the terminal map is known for ALL signed integer inputs,
    # process dynamics are not recoverable without successor evidence.
    first=lambda n:max(0,n-1)
    second=lambda n:max(0,n-2)
    assert first(13)!=second(13)
    for n in range(0,513):
        a=n
        b=n
        while first(a)!=a:a=first(a)
        while second(b)!=b:b=second(b)
        assert a==b==0
