"""Q3 self-repairing finite relational IR: third mathematical superfamily."""
from fractions import Fraction
from random import Random
import pytest
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.active_rank_inventor import invent_rank_operator, EvidenceInsufficient, BudgetExhausted


def make(n=45,m=54,r=3,seed=0):
    rng=Random(seed)
    left=[[rng.randint(-5,5) for k in range(r)] for i in range(n)]
    right=[[rng.randint(-5,5) for j in range(m)] for k in range(r)]
    return list(range(n)),list(range(m)),lambda i,j:sum(left[i][k]*right[k][j] for k in range(r))


def test_induce_coordinates_without_full_table():
    rows,cols,f=make()
    model=NeumannEngine(None,[],None).synthesize_relational_operator_active(
        rows,cols,f,query_budget=2430,seed=0,patience=6,
        validation_queries=32,trusted_rank_upper_bound=3)
    observed={(a,b) for a,b,_ in model.source_facts}
    heldout=[(i,j) for i in rows for j in cols if (i,j) not in observed]
    assert model.rank==3 and model.conditional_on_rank_bound
    assert len(heldout)>1600 and len(observed)<800
    assert all(model.apply(i,j)==f(i,j) for i,j in heldout)
    with pytest.raises(EvidenceInsufficient):
        model.apply(1,2,require_exhaustive=True)


def test_bipartite_graph_edges_no_monoid_or_polynomial_assumption():
    rows=list(range(60));cols=list(range(65))
    groups=[i%2 for i in rows];kinds=[(j+1)%2 for j in cols]
    edge=lambda i,j:int(groups[i]!=kinds[j])
    model=RegistryEngine(None,None).synthesize_relational_operator_active(
        rows,cols,edge,query_budget=3900,seed=3,
        patience=6,validation_queries=32)
    assert model.rank==2
    assert all(model.apply(i,j)==edge(i,j) for i in rows for j in cols)
    assert len(model.source_facts)<1000


def test_hidden_component_is_found_and_representation_rebuilt():
    rows=list(range(45));cols=list(range(54));seed=1
    special=set(Random(seed).sample(rows,7))
    f=lambda i,j:2+i%5 if j%3==0 else (int(i in special)*(1+j%7))
    model=invent_rank_operator(rows,cols,f,query_budget=2430,
                               seed=seed,patience=6,validation=32)
    assert model.repairs>=1 and model.rank==2
    assert all(model.apply(i,j)==f(i,j) for i in rows for j in cols)


def test_budget_never_exceeded():
    rows,cols,f=make(n=12,m=13)
    calls=[]
    def oracle(i,j):
        calls.append((i,j))
        return f(i,j)
    with pytest.raises(BudgetExhausted):
        invent_rank_operator(rows,cols,oracle,query_budget=3)
    assert len(calls)==3 and len(set(calls))==3


def test_unsupported_structure_and_nonrational_output_fail_closed():
    with pytest.raises(EvidenceInsufficient):
        invent_rank_operator(range(8),range(9),lambda i,j:0,query_budget=72)
    with pytest.raises(EvidenceInsufficient,match="rational"):
        invent_rank_operator(range(8),range(9),lambda i,j:0.1,query_budget=72)


def test_adversarial_single_unseen_exception_remains_undetectable():
    rows,cols,base=make(n=20,m=23,r=2,seed=9)
    model=invent_rank_operator(rows,cols,base,query_budget=460,seed=0,
                               patience=6,validation=24)
    observed={(i,j) for i,j,_ in model.source_facts}
    pair=next((i,j) for i in rows for j in cols if (i,j) not in observed)
    false_friend=lambda i,j:base(i,j)+1 if (i,j)==pair else base(i,j)
    learner=invent_rank_operator(rows,cols,false_friend,query_budget=460,
                                 seed=0,patience=6,validation=24)
    assert pair not in {(i,j) for i,j,_ in learner.source_facts}
    assert learner.apply(*pair)!=false_friend(*pair)
    assert not learner.verified_exhaustively
    assert not learner.conditional_on_rank_bound


def test_rank_upper_bound_is_external_contract_not_oracle_proof():
    rows,cols,f=make(n=20,m=23,r=2,seed=9)
    model=invent_rank_operator(rows,cols,f,query_budget=460,seed=1,
                               patience=6,validation=20,rank_upper_bound=2)
    assert model.rank==2 and model.conditional_on_rank_bound
    assert not model.verified_exhaustively
