"""Q3 one learned compositional discovery policy and actual Docker verifier.

These fixtures test algorithm invention mechanics, not the scientific Q3 gate.
Never use fixture results as independent-author original achievements.
"""
import pytest

from neumann1.open_program_inventor import (
    IsolatedPython,GenerativeProgramInventor,source_same_value)
from neumann1.q3_single_discovery_core import (
    SourceMethodMemory,SingleDiscoveryCore)
from neumann1.q3_structural_invention import (
    LearnedDiscoveryPolicy, StructuralInventionPolicy)


def training_memory(runner):
    m=SourceMethodMemory(runner)
    m.admit(
        "prior-mod",[(9,True),(18,True),(8,False)],
        [(27,True)],"def transform(x):\n    return x % 9 == 0")
    m.admit(
        "prior-sum",[([1,2],3),([7,8],15)],
        [([4,5],9)],"def transform(x):\n    return sum(x)")
    m.admit(
        "prior-mul",[([3,5],15),([5,7],35)],
        [([6,9],54)],"def transform(x):\n    return x[0] * x[1]")
    m.freeze()
    return m


@pytest.mark.parametrize("train,check",[
    (
        [([None,2],True),([1,None,3],True),([1,2,3],False),
         ([],False),([None],True),([3,4],False)],
        [([9,None],True)],
    ),
    (
        [([1,2],1),([7,5],5),([-1,2],-1),
         ([10,4],4),([3,3],3),([-3,-7],-7)],
        [([11,8],8)],
    ),
    (
        [("PPALLP",True),("PPALLL",False),("PAPALL",False),
         ("LLALP",True),("PLLPLP",True),("PPALLA",False)],
        [("ALLP",True)],
    ),
    (
        [([[1,2,3,2],2],2),([[7,8,7],7],2),
         ([[0,0,0],0],3),([[3,2,1],4],0),
         ([[5,6,5,6],6],2),([[4,4],4],2)],
        [([[8,9,8,9],9],2)],
    ),
])
def test_source_only_fresh_program_invention_across_semantics(train,check):
    runner=IsolatedPython(max_seconds=8)
    memory=training_memory(runner)
    learned=LearnedDiscoveryPolicy.fit(memory.episodes)
    assert learned.provenance
    p=StructuralInventionPolicy(
        learned,max_states=6500,max_evaluations=250000,max_candidates=12,
        prior_method_count=len(memory.episodes))
    discovery=SingleDiscoveryCore(
        p,runner,memory=memory,max_proposals=12).discover(
        train,check,reuse_memory=False).discovery
    assert p.receipt is not None
    assert p.receipt.evaluated_expressions<=250000
    assert p.receipt.unique_semantics<=6500
    assert p.receipt.learned_policy
    assert discovery.verified
    assert discovery.program not in {m.program for m in memory.episodes}
    assert discovery.status=="SOURCE_VERIFIED_OPEN_PROGRAM"
    output=runner.evaluate(discovery.program,[x for x,y in check])
    assert output.status=="EXECUTED"
    assert all(source_same_value(a,y) for a,(_,y) in zip(output.outputs,check))


def test_on_same_task_policy_does_not_receive_independent_source_gold():
    class Withheld:
        def __init__(self): self.seen=None
        def prepare(self,train):self.seen=train
        def propose(self,prompt):return "def transform(x):\n    return x + 1"
    policy=Withheld()
    actual=SingleDiscoveryCore(
        policy,IsolatedPython(max_seconds=8),max_proposals=1).discover(
        [(2,3),(5,6)],[(99,100)],reuse_memory=False)
    assert actual.discovery.verified
    assert policy.seen==((2,3),(5,6))
    assert (99,100) not in policy.seen


def test_frozen_learning_contract_and_bounded_no_target_search():
    runner=IsolatedPython(max_seconds=8)
    memory=training_memory(runner)
    learned=LearnedDiscoveryPolicy.fit(memory.episodes)
    assert learned.weight("mod","int","bool")>=1
    assert learned.weight("mul","list","int")>=1
    assert learned.weight("mod","str","bool")==0
    with pytest.raises(ValueError,match="bounded"):
        StructuralInventionPolicy(learned,max_states=500000)
    p=StructuralInventionPolicy(learned,max_states=6500)
    p.prepare([(123,True),(2020,False),(5,True),
               (321,True),(122,True),(1024,False)])
    assert p.receipt
    assert not p.receipt.source_constant
    assert p.receipt.candidates
    assert any(" % " in item for item in p.receipt.candidates)
    assert p.receipt.elapsed_seconds>=0
