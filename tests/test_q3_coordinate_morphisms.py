"""One generic coordinate grammar, SOURCE-only induction, real Docker verification.

These are synthetic scientific *contracts*, not new external-original Q3 wins.
The same candidate generator is used for unlearned A and learned C.
"""
import pytest

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_coordinate_morphisms import (
    _apply,induce_coordinate_morphisms)
from neumann1.q3_single_discovery_core import SingleDiscoveryCore
from neumann1.q3_structural_invention import StructuralInventionPolicy


def mirror(x):
    return _apply(x,"alternate_reverse_first",2,
                  "alternate_reverse_first",2)


def test_source_only_discovers_2d_inverted_repetition_not_named_benchmark_task():
    train=[
        ([[1,2,3],[4,5,6]],mirror([[1,2,3],[4,5,6]])),
        ([["a","b"],["c","d"],["e","f"]],
         mirror([["a","b"],["c","d"],["e","f"]])),
    ]
    withheld=[
        ([[8,7,6,5],[0,1,2,3]],mirror([[8,7,6,5],[0,1,2,3]]))
    ]
    candidates=induce_coordinate_morphisms(train,max_candidates=4)
    assert candidates
    assert all(c.source_examples==2 for c in candidates)
    assert any("alternate_reverse_first+alternate_reverse_first"
               in c.representation for c in candidates)
    runner=IsolatedPython(max_seconds=8)
    for candidate in candidates:
        run=runner.evaluate(candidate.program,[x for x,y in withheld])
        assert run.status=="EXECUTED"
        assert all(source_same_value(got,y)
                   for got,(_,y) in zip(run.outputs,withheld))
    policy=StructuralInventionPolicy(max_candidates=12)
    res=SingleDiscoveryCore(
        policy,runner,max_proposals=12).discover(
            train,withheld,reuse_memory=False).discovery
    assert res.verified
    assert "row_mode" in res.program and "col_mode" in res.program


def test_new_coordinate_grammar_supports_variable_input_size_and_types():
    train=[
        ([[0,1],[2,3]],mirror([[0,1],[2,3]])),
        ([[5,6,7],[8,9,10],[11,12,13]],
         mirror([[5,6,7],[8,9,10],[11,12,13]])),
    ]
    check=[
        ([["x","y"],["z","w"],["t","u"]],
         mirror([["x","y"],["z","w"],["t","u"]]))
    ]
    methods=induce_coordinate_morphisms(train)
    assert methods
    runner=IsolatedPython(max_seconds=8)
    for m in methods:
        response=runner.evaluate(m.program,[check[0][0]])
        assert response.status=="EXECUTED"
        assert source_same_value(response.outputs[0],check[0][1])


def test_abstain_when_independent_source_refutes_a_fitting_coordinate_rule():
    train=[
        ([[1,2],[3,4]],mirror([[1,2],[3,4]])),
        ([[1,4,7],[2,5,8]],mirror([[1,4,7],[2,5,8]])),
    ]
    held=[([[1,2],[3,4]],[[1,2],[3,4]])]
    methods=induce_coordinate_morphisms(train)
    assert methods
    policy=StructuralInventionPolicy(max_candidates=12)
    outcome=SingleDiscoveryCore(
        policy,IsolatedPython(max_seconds=8),max_proposals=12).discover(
            train,held,reuse_memory=False).discovery
    assert not outcome.verified
    assert outcome.program is None


def test_duplicate_or_unbounded_source_fails_closed():
    with pytest.raises(ValueError,match="bounded"):
        induce_coordinate_morphisms([],max_candidates=4)
    with pytest.raises(ValueError,match="bounded"):
        induce_coordinate_morphisms([([[1]],[[1]])]*2,max_candidates=400)
    assert not induce_coordinate_morphisms(
        [([[1,2]],[[1,2]]),([[3,4]],[[3,4]])])
    assert not induce_coordinate_morphisms(
        [("str","str"),("text","text")])


def test_one_compiled_program_has_no_discrete_answer_or_target_gold():
    source=[
        ([[1,2],[3,4]],mirror([[1,2],[3,4]])),
        ([[5,6],[7,8]],mirror([[5,6],[7,8]])),
    ]
    methods=induce_coordinate_morphisms(source)
    assert methods
    for m in methods:
        assert len(m.program)<6000
        assert "def transform(x):" in m.program
        assert "TARGET" not in m.program
        assert "test" not in m.program
        assert "source" not in m.program
