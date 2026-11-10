"""Q3 new executable program via periodic quotient and causal residual.

Synthetic tests never qualify as first-seen original or learned C-exclusive.
"""
import pytest
from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_periodic_residual_invention import (
    _apply,induce_periodic_residual_rules)
from neumann1.q3_single_discovery_core import SingleDiscoveryCore
from neumann1.q3_structural_invention import StructuralInventionPolicy
from neumann1.q3_coordinate_morphisms import induce_coordinate_morphisms


def make(r,c,symbol,h=6,w=7):
    a=[[0]*w for _ in range(h)]
    a[r][c]=symbol
    a[(r+2)%h][(c+2)%w]=symbol
    return a,_apply(a,3,2,-1,-1,9)


def test_periodic_quotient_and_unseen_residual_relation_invented_together():
    train=[make(1,2,1),make(2,3,4)]
    checks=[make(3,0,7)]
    # Pure periodic-index morphism CANNOT explain newly created 9 values:
    # the residual is a new semantic dependency.
    assert not induce_coordinate_morphisms(train)
    rules=induce_periodic_residual_rules(train)
    assert rules
    assert any("new_symbol=9" in m.program for m in rules)
    runner=IsolatedPython(max_seconds=8)
    for rule in rules:
        result=runner.evaluate(rule.program,[x for x,y in checks])
        assert result.status=="EXECUTED"
        assert all(source_same_value(z,y)
                   for z,(_,y) in zip(result.outputs,checks))
    core=StructuralInventionPolicy(max_candidates=12)
    outcome=SingleDiscoveryCore(
        core,runner,max_proposals=12).discover(
            train,checks,reuse_memory=False).discovery
    assert outcome.verified
    assert "new_symbol=9" in outcome.program
    assert "dr=-1" in outcome.program
    assert "dc=-1" in outcome.program


def test_causal_residual_rule_generalizes_to_new_size_and_category():
    train=[make(1,2,1),make(2,3,4)]
    independent=[make(2,1,8,h=5,w=6)]
    rules=induce_periodic_residual_rules(train)
    assert rules
    runner=IsolatedPython(max_seconds=8)
    assert any(
        r.status=="EXECUTED" and source_same_value(
            r.outputs[0],independent[0][1])
        for m in rules
        for r in [runner.evaluate(m.program,[independent[0][0]])]
    )


def test_independent_source_counterexample_must_refute_wrong_residual_symbol():
    train=[make(1,2,1),make(2,3,4)]
    wrong_source=[(
        make(3,0,7)[0],
        _apply(make(3,0,7)[0],3,2,-1,-1,5),
    )]
    policy=StructuralInventionPolicy(max_candidates=12)
    result=SingleDiscoveryCore(
        policy,IsolatedPython(max_seconds=8),
        max_proposals=12).discover(
            train,wrong_source,reuse_memory=False).discovery
    assert not result.verified
    assert result.program is None


def test_no_repeated_lattice_no_causal_relation_or_bad_source():
    train=[make(1,2,1),make(2,3,4)]
    with pytest.raises(ValueError,match="bounded"):
        induce_periodic_residual_rules(train,max_candidates=100)
    ordinary=[([[1,2],[3,4]],[[1,2],[3,4]])]*2
    assert induce_periodic_residual_rules(ordinary)==()
    changed=[
        (x,[row[:-1] for row in y])
        for x,y in train
    ]
    assert induce_periodic_residual_rules(changed)==()


def test_compiled_program_contains_inferred_offsets_not_original_answers():
    methods=induce_periodic_residual_rules(
        [make(1,2,1),make(2,3,4)])
    assert methods
    for item in methods:
        assert "def transform(x):" in item.program
        assert len(item.program)<6000
        assert item.source_examples==2
        assert "test" not in item.program
        assert "TARGET" not in item.program
