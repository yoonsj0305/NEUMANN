"""Q3/Q6 genuinely GENERATED interaction representation; finite exhaustive tests.

The source oracles are synthetic experiment controls. They are never passed as
candidate programs or target gold to the invention procedure except explicitly
when testing the classical-first bypass.
"""
from itertools import combinations
from math import comb
from random import Random
import pytest
from neumann1.causal_representation_inventor import (
    CausalRepresentationInventor,IncompleteInformation,
    invent_with_active_source_queries)


def bitvector(i,n):
    return tuple((i>>j)&1 for j in range(n))


def source_design(n,degree,oracle,checks=50):
    basis=[tuple(int(i in subset) for i in range(n))
           for k in range(degree+1)
           for subset in combinations(range(n),k)]
    observed=set(basis)
    remaining=[bitvector(k,n) for k in range(1<<n)
               if bitvector(k,n) not in observed]
    Random(n*191+degree).shuffle(remaining)
    train=[(x,oracle(x)) for x in basis]
    verification=[(x,oracle(x)) for x in remaining[:checks]]
    assert set(basis).isdisjoint(remaining)
    return train,verification,remaining[checks:]


def numeric_law(x):
    return (x[0]&x[7])^(x[2]&x[9])^(x[3]&x[11])^x[4]


def graph_law(x):
    edges=list(combinations(range(5),2))
    edge={pair:i for i,pair in enumerate(edges)}
    result=0
    for a,b,c in combinations(range(5),3):
        result^=x[edge[a,b]]&x[edge[b,c]]&x[edge[a,c]]
    return result


def symbolic_law(x):
    return sum(x[i]&(1^x[i+1])&x[i+2]
               for i in range(len(x)-2))&1


@pytest.mark.parametrize("family,width,degree,oracle,checks",[
    ("numeric_arithmetic",12,2,numeric_law,70),
    ("graph_triangle_parity",10,3,graph_law,50),
    ("symbolic_substring_pattern",12,3,symbolic_law,90),
])
def test_exhaustive_fixed_width_proof_of_generated_latent_features(
        family,width,degree,oracle,checks):
    train,verified,unseen=source_design(width,degree,oracle,checks)
    inventor=CausalRepresentationInventor(max_degree=3,max_source_ms=5000)
    r=inventor.invent(train,independent_source_checks=verified)
    assert r.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
    program=r.program
    assert program.degree==degree
    assert program.proof_rank==sum(comb(width,k) for k in range(degree+1))
    assert program.latent_dimension>0
    assert "source_inferred_interaction_mask" in repr(program.ast)
    assert all(program.apply(x)==oracle(x) for x in unseen)
    assert all(program.apply(bitvector(i,width))==oracle(bitvector(i,width))
               for i in range(1<<width))
    if family=="graph_triangle_parity":
        # Without naming 'triangle' to the inventor it discovers exactly
        # ten distinct cubic motifs for K5 edges.
        assert len(program.latent_features)==10
        assert all(m.bit_count()==3 for m in program.latent_features)
    print(family,"source",len(train),"verified",len(verified),
          "unseen",len(unseen),"degree",program.degree,
          "latent",program.latent_dimension)


def test_old_linear_representation_cannot_express_source_discovered_quadratic():
    train,check,_=source_design(12,2,numeric_law)
    old=CausalRepresentationInventor(max_degree=1).invent(
        train,independent_source_checks=check)
    assert old.status=="ABSTAIN_OUTSIDE_LANGUAGE"
    new=CausalRepresentationInventor(max_degree=2).invent(
        train,independent_source_checks=check)
    assert new.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"


def test_known_classical_solution_preempts_any_invention_work():
    train,check,hold=source_design(12,2,numeric_law)
    r=CausalRepresentationInventor().invent(
        train,independent_source_checks=check,
        classical_solvers=(numeric_law,))
    assert r.status=="CLASSICAL_VERIFIED"
    assert not r.degrees_tried and r.program is None
    assert all(r.apply(x)==numeric_law(x) for x in hold)


def test_independent_source_rank_shortfall_requires_abstention():
    train,check,_=source_design(12,2,numeric_law)
    r=CausalRepresentationInventor(max_degree=2).invent(
        train[:12],independent_source_checks=check)
    assert r.status=="ABSTAIN_UNIDENTIFIABLE"
    assert r.program is None


def test_new_verifier_counterexample_not_used_to_refit_model():
    train,check,_=source_design(12,2,numeric_law)
    x,y=check[0]
    check[0]=x,1-y
    r=CausalRepresentationInventor().invent(
        train,independent_source_checks=check)
    assert r.status=="ABSTAIN_VERIFIER_COUNTEREXAMPLE"


def test_arbitrary_unseen_one_point_exception_is_a_real_falsifier():
    train,check,hold=source_design(12,2,numeric_law)
    r=CausalRepresentationInventor().invent(
        train,independent_source_checks=check)
    x=hold[0]
    alternate=lambda z:numeric_law(z)^int(z==x)
    assert all(alternate(z)==out for z,out in train+check)
    assert r.apply(x)!=alternate(x)


@pytest.mark.parametrize("width,degree,oracle,checks",[
    (12,2,numeric_law,70),(10,3,graph_law,50),(12,3,symbolic_law,90)])
def test_active_source_design_and_no_target_answer_exposure(
        width,degree,oracle,checks):
    queried=[]
    def source_oracle(x):
        queried.append(x)
        return oracle(x)
    result=invent_with_active_source_queries(
        source_oracle,width=width,max_degree=degree,
        independent_checks=checks)
    assert result.discovery.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
    assert result.source_probes==sum(comb(width,k)
                                    for k in range(degree+1))
    assert len(queried)==result.source_probes+checks
    assert len(set(queried))==len(queried)
    assert result.source_probe_fraction<.35
    program=result.discovery.program
    assert all(program.apply(bitvector(i,width))==oracle(bitvector(i,width))
               for i in range(1<<width))


def test_unsound_source_reuse_and_invalid_budget_rejected():
    train,check,_=source_design(12,2,numeric_law)
    with pytest.raises(IncompleteInformation):
        CausalRepresentationInventor().invent(
            train,independent_source_checks=train[:1])
    with pytest.raises(IncompleteInformation):
        CausalRepresentationInventor().invent(
            train,independent_source_checks=[((2,)*12,0)])
    with pytest.raises(ValueError):
        CausalRepresentationInventor(max_features=0)
    with pytest.raises(IncompleteInformation):
        invent_with_active_source_queries(
            lambda x:0,width=2,max_degree=2,independent_checks=1)
