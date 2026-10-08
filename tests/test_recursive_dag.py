from copy import deepcopy
import random
import pytest
from neumann1.recursive_summary import program,reference,SummaryError
from neumann1.recursive_library_baseline import propose
from neumann1.recursive_dag import CertifiedDagSummary,validate_dag


def prefix():
    return {'semantics':'integer_list_right_fold','empty':[0],
            'step':program(['head','r0'],[['max',['add','head','r0'],0]])}


def dag(nodes,roots):return {'semantics':'ordered_integer_list_dag','nodes':nodes,'roots':roots}


def unfold(d,index):
    n=d['nodes'][index]
    return [] if n[0]=='nil' else [n[1]] if n[0]=='single' else unfold(d,n[1])+unfold(d,n[2])


def test_dag_sharing_and_input_order_preserve_original_goal():
    p=prefix();engine=CertifiedDagSummary(p,propose(p)['proposal'])
    d=dag([['single',-4],['single',7],['concat',0,1],['concat',1,0],['concat',2,2]], [2,3,4])
    r=engine.run_dag(d)
    assert r['outputs']==[[3],[7],[6]]
    assert r['expanded_root_lengths']==[2,2,4]
    assert r['evaluated_nodes']==5


def test_huge_implicit_list_is_not_materialized_or_reported_as_speedup():
    p=prefix();engine=CertifiedDagSummary(p,propose(p)['proposal'])
    nodes=[['single',3]]
    for i in range(60):nodes.append(['concat',i,i])
    r=engine.run_dag(dag(nodes,[60]))
    assert r['outputs']==[[3*2**60]]
    assert r['expanded_root_lengths']==[2**60] and r['evaluated_nodes']==61
    assert not r['expanded_length_is_speedup_claim']


def test_goal_conditioned_reachability_avoids_unneeded_evaluation():
    p=prefix();engine=CertifiedDagSummary(p,propose(p)['proposal'])
    d=dag([['single',2],['single',999],['concat',1,1],['concat',0,0]],[3,0])
    r=engine.run_dag(d)
    assert r['outputs']==[[4],[2]] and r['input_nodes']==4 and r['evaluated_nodes']==2


def test_generated_random_dags_match_independent_unrolling():
    p=prefix();engine=CertifiedDagSummary(p,propose(p)['proposal']);rng=random.Random(81721)
    for _ in range(60):
        nodes=[['nil'],['single',rng.randint(-10,10)]]
        for index in range(2,12):
            nodes.append(['single',rng.randint(-10,10)] if rng.random()<0.3 else ['concat',rng.randrange(index),rng.randrange(index)])
        d=dag(nodes,[11,10,5])
        result=engine.run_dag(d)
        assert result['outputs']==[reference(p,unfold(d,r)) for r in d['roots']]


@pytest.mark.parametrize('nodes,roots',[([['concat',0,0]],[0]),([['nil'],['concat',0,2]],[1]),
    ([['single',True]],[0]),([['nil']],[True]),([['nil']],[1]),([['nil'],['concat',0,-1]],[1])])
def test_invalid_or_cyclic_dags_reject(nodes,roots):
    with pytest.raises(SummaryError):validate_dag(dag(nodes,roots))


def test_binding_and_bit_budgets_prevent_unverified_execution():
    p=prefix();proposal=propose(p)['proposal'];engine=CertifiedDagSummary(p,proposal)
    with pytest.raises(SummaryError):engine.run_dag(dag([['single',9]],[0]),max_state_bits=3)
    with pytest.raises(SummaryError):validate_dag(dag([['single',2**4096]],[0]))
    with pytest.raises(SummaryError):validate_dag(dag([['single',1],['concat',0,0]],[1]),max_length_bits=1)
    engine._proposal['empty'][0]=1
    with pytest.raises(SummaryError):engine.run_dag(dag([['nil']],[0]))


def test_public_dag_and_proposal_do_not_accept_answer_flags():
    p=prefix();proposal=propose(p)['proposal'];proposal['accepted']=True
    with pytest.raises(SummaryError):CertifiedDagSummary(p,proposal)
    d=dag([['nil']],[0]);d['answers']=[0]
    with pytest.raises(SummaryError):validate_dag(d)
