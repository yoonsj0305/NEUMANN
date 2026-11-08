"""Q3 operator invention tests: unseen cells, algebra transfer and refusal."""
from __future__ import annotations
import itertools
import pytest
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.monoid_operator_inventor import EvidenceInsufficient, invent_operator


def check(elements, identity, generators, law):
    observations = [(a,b,law(a,b)) for a in {identity,*generators}
                    for b in elements]
    model = invent_operator(observations)
    for a,b in itertools.product(elements,repeat=2):
        assert model.apply(a,b) == law(a,b)
    assert model.unobserved_predictions > 0
    return model


def test_symbolic_cycle_31_infers_899_never_seen_pairs():
    elements=tuple("u"+str(i) for i in range(31))
    ids={x:i for i,x in enumerate(elements)}
    model=check(elements,elements[0],(elements[1],),
                lambda a,b:elements[(ids[a]+ids[b])%31])
    assert model.source_observations==62
    assert model.unobserved_predictions==899
    assert len(model.generators)==1
    assert len(model.representation(elements[30]))==30


def test_noncommutative_s3_permutation_group():
    elements=tuple(itertools.permutations(range(3)))
    composition=lambda a,b:tuple(a[b[i]] for i in range(3))
    model=check(elements,(0,1,2),((1,0,2),(1,2,0)),composition)
    a,b=(1,0,2),(1,2,0)
    assert model.apply(a,b) != model.apply(b,a)
    assert len(model.generators)==2


def test_noninvertible_transformation_monoid():
    e=(0,1,2); g1=(1,2,0); g2=(0,0,0)
    composition=lambda a,b:tuple(a[b[i]] for i in range(3))
    elements={e}; todo=[e]
    while todo:
        x=todo.pop()
        for gen in (g1,g2):
            y=composition(gen,x)
            if y not in elements:
                elements.add(y);todo.append(y)
    assert check(elements,e,(g1,g2),composition).universe_size==6


def test_semilattice_without_inverses():
    model=check(range(16),0,(1,2,4,8),lambda a,b:a|b)
    assert len(model.generators)==4
    assert all(model.apply(i,i)==i for i in range(16))


def test_duplicate_contradiction_fails_closed():
    facts=[(0,i,i) for i in range(5)]+[(1,i,(1+i)%5) for i in range(5)]
    with pytest.raises(EvidenceInsufficient):
        invent_operator(facts+[(1,3,1)])


def test_incomplete_source_and_unseen_symbol_refused():
    facts=[(0,i,i) for i in range(5)]+[(1,i,(1+i)%5) for i in range(4)]
    with pytest.raises(EvidenceInsufficient):
        invent_operator(facts)
    facts.append((1,4,0))
    model=invent_operator(facts)
    with pytest.raises(EvidenceInsufficient):
        model.apply(2,"unknown_symbol")


def test_missing_identity_and_malformed_source():
    with pytest.raises(EvidenceInsufficient):
        invent_operator([(1,i,(1+i)%5) for i in range(5)])
    with pytest.raises(EvidenceInsufficient):
        invent_operator([([1],2,3)])
    with pytest.raises(EvidenceInsufficient):
        invent_operator([(1,2)])


def test_source_fitted_wrong_row_entry_is_rejected():
    facts=[(0,i,i) for i in range(5)]+[(1,i,(1+i)%5) for i in range(5)]
    assert invent_operator(facts+[(2,3,0)]).apply(2,3)==0
    with pytest.raises(EvidenceInsufficient):
        invent_operator(facts+[(2,3,4)])


def test_both_live_engines_use_generated_operator_not_static_router():
    facts=[(0,i,i) for i in range(7)]+[(1,i,(1+i)%7) for i in range(7)]
    a=NeumannEngine(None,[],None).synthesize_binary_operator(facts,[(3,5),(6,6)])
    b=RegistryEngine(None,None).synthesize_binary_operator(facts,[(3,5),(6,6)])
    for result in (a,b):
        assert result["predictions"]==(1,5)
        assert result["operator"].unobserved_predictions==35
        assert len(result["representation"][6])==6
