"""Q3 autonomous executable compositions; synthetic mechanics, not global Q3."""
import pytest

from neumann1.open_program_inventor import (
    IsolatedPython,source_same_value,validate_code)
from neumann1.q3_residual_composition import (
    induce_source_compositions,induce_residual_guided_compositions)
from neumann1.q3_source_residual_probes import induce_source_residual_probes
from neumann1.q3_single_discovery_core import SingleDiscoveryCore
from neumann1.q3_structural_invention import StructuralInventionPolicy


TRAIN=[
    ([[1,0,3],[0,1,3]],[[2,0,4],[0,2,4]]),
    ([[0,3,1],[3,0,1]],[[0,4,2],[4,0,2]]),
]
CHECK=[
    ([[3,1,0],[0,1,3]],[[4,2,0],[0,2,4]]),
]


def test_two_partially_correct_programs_invent_new_executable_joint_method():
    runner=IsolatedPython(max_seconds=8)
    atomic=induce_source_residual_probes(TRAIN,max_probes=8)
    assert len(atomic)>=2
    for p in atomic:
        response=runner.evaluate(p.program,[x for x,y in CHECK])
        assert response.status=="EXECUTED"
        assert not source_same_value(response.outputs[0],CHECK[0][1])

    composed=induce_source_compositions(TRAIN,max_candidates=6)
    assert composed
    assert any(p.representation=="source-composition/parallel-atomic-relation"
               for p in composed)
    exact=[]
    for method in composed:
        got=runner.evaluate(method.program,[x for x,y in CHECK])
        if got.status=="EXECUTED" and source_same_value(
                got.outputs[0],CHECK[0][1]):
            exact.append(method)
    assert exact
    assert any("mapping=" in method.program for method in exact)
    assert all("def transform(x):" in method.program for method in exact)
    # The single common discovery core must independently certify, rather
    # than trusting the synthesis program's SOURCE-fit report.
    policy=StructuralInventionPolicy(max_candidates=12)
    discovered=SingleDiscoveryCore(
        policy,runner,max_proposals=12).discover(
        TRAIN,CHECK,reuse_memory=False).discovery
    assert discovered.verified
    assert discovered.program not in [p.program for p in atomic]


def test_compositional_invention_abstains_when_unseen_SOURCE_refutes_mapping():
    runner=IsolatedPython(max_seconds=8)
    candidate=induce_source_compositions(TRAIN,max_candidates=6)
    assert candidate
    withheld=[
        ([[1,3,0],[0,1,3]],[[5,4,0],[0,5,4]]),
    ]
    # Do not trust 100%-SOURCE-train fit as an original scientific PASS:
    # here a conflicting independent SOURCE relation must reject it.
    for method in candidate:
        r=runner.evaluate(method.program,[x for x,y in withheld])
        if r.status=="EXECUTED":
            assert not source_same_value(r.outputs[0],withheld[0][1])
    policy=StructuralInventionPolicy(max_candidates=12)
    result=SingleDiscoveryCore(
        policy,runner,max_proposals=12).discover(
        TRAIN,withheld,reuse_memory=False).discovery
    assert result.verified is False


def test_safe_bounded_program_algebra_and_no_target_oracle():
    with pytest.raises(ValueError,match="bounded"):
        induce_source_compositions(TRAIN,max_candidates=10000)
    methods=induce_source_compositions(TRAIN,max_candidates=6)
    assert len(methods)<=6
    assert all(len(m.program)<=6000 and validate_code(m.program)
               for m in methods)
    for m in methods:
        assert m.source_examples==2
        assert "TARGET" not in m.program
        assert "eval(" not in m.program
        assert "exec(" not in m.program


def test_second_stage_is_invented_from_first_stage_residual_not_memorized_answer():
    """A movement followed by relabeling is absent from original atomic probes.

    The new algorithm must first invent how to move a token, observe the
    remaining SOURCE discrepancy, then invent a fresh second method.
    """
    def source(r,c):
        x=[[0]*7 for _ in range(5)]
        y=[[0]*7 for _ in range(5)]
        x[r][c]=1
        y[r][c+1]=2
        return x,y
    train=[source(1,1),source(2,3)]
    independent=[source(3,4)]
    runner=IsolatedPython(max_seconds=8)
    originals=induce_source_residual_probes(train,max_probes=8)
    assert originals
    assert all(not source_same_value(
        runner.evaluate(p.program,[independent[0][0]]).outputs[0],
        independent[0][1]) for p in originals)
    synthesized=induce_residual_guided_compositions(train,max_candidates=6)
    assert synthesized
    successes=[]
    for candidate in synthesized:
        result=runner.evaluate(
            candidate.program,[x for x,y in independent])
        if result.status=="EXECUTED" and source_same_value(
                result.outputs[0],independent[0][1]):
            successes.append(candidate)
    assert successes
    assert any("stage2(stage1(x))" in p.program for p in successes)
    assert all(p.program not in [base.program for base in originals]
               for p in successes)
    # Same original single core makes the final independent certification.
    policy=StructuralInventionPolicy(max_candidates=12)
    outcome=SingleDiscoveryCore(
        policy,runner,max_proposals=12).discover(
        train,independent,reuse_memory=False).discovery
    assert outcome.verified


def test_new_residual_guided_invention_rejected_by_independent_counterexample():
    def source(r,c,target):
        x=[[0]*7 for _ in range(5)]
        y=[[0]*7 for _ in range(5)]
        x[r][c]=1
        y[r][c+1]=target
        return x,y
    train=[source(1,1,2),source(2,3,2)]
    check=[source(3,4,5)]
    produced=induce_residual_guided_compositions(train,max_candidates=6)
    assert produced
    runner=IsolatedPython(max_seconds=8)
    assert all(
        not source_same_value(
            runner.evaluate(p.program,[check[0][0]]).outputs[0],
            check[0][1])
        for p in produced)
    p=StructuralInventionPolicy(max_candidates=12)
    result=SingleDiscoveryCore(
        p,runner,max_proposals=12).discover(
        train,check,reuse_memory=False).discovery
    assert result.verified is False
