"""Constructed mechanism checks, NOT independent-author Q3 evidence."""
import pytest

from neumann1.open_program_inventor import IsolatedPython,source_same_value
from neumann1.q3_relational_predicate_invention import (
    induce_relational_comprehensions,_learn_dnf)


def scene(a,b,h=12,w=13,first=8,second=2,fill=4):
    x=[[0]*w for _ in range(h)]
    ra,ca=a;rb,cb=b
    x[ra][ca]=first
    x[rb][cb]=second
    y=[row[:] for row in x]
    for r in range(min(ra,rb),max(ra,rb)+1):
        if y[r][ca]==0:y[r][ca]=fill
    for c in range(min(ca,cb),max(ca,cb)+1):
        if y[rb][c]==0:y[rb][c]=fill
    return x,y


def test_source_invents_heldout_relational_law_not_stored_solution():
    train=[
        scene((1,8),(5,1)),
        scene((2,1),(8,9)),
        scene((9,10),(3,2)),
    ]
    heldout=scene((10,2),(1,7))
    methods=induce_relational_comprehensions(
        train,max_candidates=4)
    assert methods,"a relational DNF must be induced from SOURCE changes"
    runner=IsolatedPython(max_seconds=8)
    assert any(
        (result.status=="EXECUTED"
         and len(result.outputs)==1
         and source_same_value(result.outputs[0],heldout[1]))
        for result in (
            runner.evaluate(m.program,[heldout[0]]) for m in methods))


def test_transferable_role_parameters_new_palette():
    train=[scene((2,6),(7,1),first=3,second=9,fill=7),
           scene((6,1),(2,7),first=3,second=9,fill=7)]
    heldout=scene((1,9),(8,3),first=3,second=9,fill=7)
    runner=IsolatedPython(max_seconds=8)
    methods=induce_relational_comprehensions(train)
    assert any(
        res.status=="EXECUTED" and
        source_same_value(res.outputs[0],heldout[1])
        for res in (runner.evaluate(m.program,[heldout[0]])
                    for m in methods))


def test_unsupported_training_requires_abstention():
    with pytest.raises(ValueError,match="bounded"):
        induce_relational_comprehensions([])
    assert not induce_relational_comprehensions([
        ([[0,1],[0,2]],[[0,1],[0,2]]),
        ([[0,1],[0,2]],[[0,1],[0,2]]),
    ])
