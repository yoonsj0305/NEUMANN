"""Q3 unrelated numeric function construction, exact heldout, and abstention."""
from fractions import Fraction
from random import Random
import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.active_numeric_inventor import invent_numeric_function
from neumann1.active_law_inventor import BudgetExhausted, EvidenceInsufficient


def verify(f,arity,degree,seed=5,budget=120,engine=None):
    if engine is None:
        model=invent_numeric_function(f,arity=arity,max_degree=degree+1,
                                     budget=budget,seed=seed,validation=8)
    else:
        model=engine.synthesize_numeric_function_active(
            f,arity=arity,max_degree=degree+1,query_budget=budget,
            seed=seed,validation_queries=8)
    assert model.degree==degree
    training={x for x,y in model.source_facts}
    random=Random(9128)
    tests=[]
    while len(tests)<200:
        xs=tuple(Fraction(random.randint(-100,100)) for _ in range(arity))
        if xs not in training:tests.append(xs)
    assert all(model.apply(*x)==f(*x) for x in tests)
    return model


def test_univariate_cubic_exact_ir_via_neumann():
    f=lambda x:7*x**3-2*x**2+5*x-11
    m=verify(f,1,3,engine=NeumannEngine(None,[],None))
    assert len(m.nonzero_terms)==4
    assert m.apply(Fraction(1,2))==f(Fraction(1,2))


def test_quadratic_multivariate_interactions_via_registry():
    f=lambda x,y:2*x*x+3*x*y-7*y*y+4*x-13
    m=verify(f,2,2,engine=RegistryEngine(None,None))
    assert (1,1) in [p for p,c in m.nonzero_terms]


def test_multivariate_cubic_with_nontrivial_cross_terms():
    f=lambda x,y,z:3*x*y*z+5*x*x-2*y*z+4*z-17
    m=verify(f,3,3,budget=170)
    assert len(m.nonzero_terms)==5


def test_affine_four_independent_dimensions():
    f=lambda a,b,c,d:9*a-11*b+3*c+2*d+17
    verify(f,4,1)


def test_nonpolynomial_under_bound_abstains():
    with pytest.raises(EvidenceInsufficient):
        invent_numeric_function(lambda x:2**abs(int(x)),arity=1,
                                max_degree=2,budget=80,seed=4)


def test_floating_oracle_refused_exact_arithmetic_only():
    with pytest.raises(EvidenceInsufficient,match="exact numerical"):
        invent_numeric_function(lambda x:float(x),arity=1)


def test_numeric_source_query_limit_enforced():
    queries=[]
    def f(x,y):
        queries.append((x,y))
        return x*x+2*y
    with pytest.raises(BudgetExhausted):
        invent_numeric_function(f,arity=2,max_degree=3,budget=3,seed=0)
    assert len(queries)==3
