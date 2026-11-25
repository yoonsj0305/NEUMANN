"""Q3 law hypothesis discovery -> active experiments -> generated IR."""
from __future__ import annotations
import itertools
from random import Random

import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.active_law_inventor import (
    invent_with_oracle, EvidenceInsufficient, BudgetExhausted)


def cycle(n=31):
    xs=list(range(n))
    Random(887).shuffle(xs)
    index={x:i for i,x in enumerate(xs)}
    return xs,lambda a,b:xs[(index[a]+index[b])%n]


def verify(xs,op,budget,engine=None):
    if engine is None:
        model=invent_with_oracle(xs,op,budget=budget,seed=0,validation=12)
    else:
        model=engine.synthesize_binary_operator_active(
            xs,op,query_budget=budget,seed=0,validation_queries=12)
    observed={(a,b) for a,b,c in model.source_facts}
    unseen=[(a,b) for a in xs for b in xs if (a,b) not in observed]
    assert unseen and len(observed)+len(unseen)==len(xs)**2
    assert all(model.apply(a,b)==op(a,b) for a,b in unseen)
    assert model.strategy=="generator_word"
    assert model.conditional_associativity
    assert not model.verified_exhaustively
    assert any(set(eq)=={"((x*y)*z)","(x*(y*z))"} for eq in model.equations)
    return model


def test_cyclic_31_creates_ir_without_supplied_generators():
    xs,op=cycle()
    model=verify(xs,op,budget=450)
    assert len(model.source_facts)<220
    assert len(model.model.generators)==1


def test_noncommutative_s3_times_z5_via_live_neumann_engine():
    ps=list(itertools.permutations(range(3)))
    xs=[(p,k) for p in ps for k in range(5)]
    Random(456).shuffle(xs)
    op=lambda a,b:(tuple(a[0][b[0][i]] for i in range(3)),(a[1]+b[1])%5)
    model=verify(xs,op,budget=700,engine=NeumannEngine(None,[],None))
    assert model.apply(((1,0,2),0),((1,2,0),0)) != model.apply(((1,2,0),0),((1,0,2),0))


def test_noninvertible_transform_times_z7_via_registry_engine():
    e=(0,1,2);rotation=(1,2,0); const=(0,0,0)
    composition=lambda a,b:tuple(a[b[i]] for i in range(3))
    states={e};todo=[e]
    while todo:
        x=todo.pop()
        for g in (rotation,const):
            y=composition(g,x)
            if y not in states:states.add(y);todo.append(y)
    xs=[(p,k) for p in states for k in range(7)]
    Random(444).shuffle(xs)
    op=lambda a,b:(composition(a[0],b[0]),(a[1]+b[1])%7)
    verify(xs,op,budget=1000,engine=RegistryEngine(None,None))


def test_union_semilattice_works_without_inverse():
    xs=list(range(32));Random(77).shuffle(xs)
    verify(xs,lambda a,b:a|b,budget=800)


def test_bounded_string_concatenation_is_inferred_not_built_in():
    xs=['']
    for k in range(4):
        xs.extend([s+ch for s in [w for w in xs if len(w)==k] for ch in 'ab'])
    Random(88).shuffle(xs)
    verify(xs,lambda a,b:(a+b)[:4],budget=850)


def test_nonassociative_operator_abstains():
    xs,op=cycle()
    index={v:i for i,v in enumerate(xs)}
    nonassoc=lambda a,b:xs[(index[a]+2*index[b])%len(xs)]
    with pytest.raises(EvidenceInsufficient,match="associativity"):
        invent_with_oracle(xs,nonassoc,budget=450,seed=0)


def test_missing_identity_abstains():
    xs,_=cycle()
    with pytest.raises(EvidenceInsufficient,match="identity"):
        invent_with_oracle(xs,lambda a,b:a,budget=450,seed=0)


def test_hard_query_budget_exactly_enforced():
    xs,op=cycle()
    calls=[]
    def tracked(a,b):
        calls.append((a,b))
        return op(a,b)
    with pytest.raises(BudgetExhausted):
        invent_with_oracle(xs,tracked,budget=15,seed=0)
    assert len(calls)==len(set(calls))==15


def test_explicit_degraded_full_table_is_exact_but_not_generalization():
    xs=list(range(5))
    law=lambda a,b:(a+2*b)%5
    model=invent_with_oracle(xs,law,budget=25,seed=0,allow_full_table=True)
    assert model.strategy=="full_table"
    assert model.verified_exhaustively
    assert len(model.source_facts)==25
    assert all(model.apply(a,b)==law(a,b) for a,b in itertools.product(xs,repeat=2))


def test_adversarial_one_cell_exception_escapes_sparse_probing():
    xs,law=cycle()
    base=invent_with_oracle(xs,law,budget=450,seed=0,validation=12)
    seen={(a,b) for a,b,c in base.source_facts}
    a,b=next((a,b) for a,b in itertools.product(xs,repeat=2) if (a,b) not in seen)
    index={v:i for i,v in enumerate(xs)}
    corrupted=xs[(index[law(a,b)]+1)%len(xs)]
    false_friend=lambda x,y:corrupted if (x,y)==(a,b) else law(x,y)
    model=invent_with_oracle(xs,false_friend,budget=450,seed=0,validation=12)
    assert (a,b) not in {(x,y) for x,y,z in model.source_facts}
    assert model.apply(a,b)!=false_friend(a,b)
    assert not model.verified_exhaustively
