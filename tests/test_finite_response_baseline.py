from itertools import product
import pytest
from neumann1.recursive_summary import (program, check_summary, CertifiedSummary,
                                      reference, SummaryError)
from neumann1.finite_response_baseline import propose


def public(empty,outputs):
    return {'semantics':'integer_list_right_fold','empty':empty,
            'step':program(['head']+[f'r{i}' for i in range(len(empty))],outputs)}


def tree(values):
    if not values:return ['nil']
    cut=len(values)//2
    if len(values)==1:return ['single',values[0]]
    return ['concat',tree(values[:cut]),tree(values[cut:])]


def test_generated_response_preserves_order_sensitive_pattern_without_label():
    seen=['eq','r0',1];found=['eq','r1',1];head=['gt','head',0]
    p=public([0,0],[['ite',['or',seen,head],1,0],
                    ['ite',['or',['and',seen,['not',head]],found],1,0]])
    r=propose(p)
    assert r and len(r['proposal']['empty'])==3
    engine=CertifiedSummary(p,r['proposal'])
    for length in range(7):
        for xs in product([-3,7],repeat=length):
            assert engine.run(tree(list(xs)))==reference(p,list(xs))
    assert engine.run(tree([-3,7]))!=engine.run(tree([7,-3]))


def test_new_parity_summary_is_generated_without_catalogue():
    p=public([0],[['ite',['gt','head',0],['sub',1,'r0'],'r0']])
    r=propose(p);assert r and len(r['response_candidates'])==2
    engine=CertifiedSummary(p,r['proposal'])
    for xs in [[],[1,2,3],[0,-4,8],[10**80,-10**70]]:
        assert engine.run(tree(xs))==[sum(x>0 for x in xs)%2]


def test_sampled_state_closure_never_authorizes_unsampled_heads():
    p=public([0],[['ite',['eq','head',13],13,['sub',1,'r0']]])
    r=propose(p);assert r
    checked=check_summary(p,r['proposal'])
    assert not checked['accepted'] and checked['status']=='REFUTED'
    with pytest.raises(SummaryError):CertifiedSummary(p,r['proposal'])


def test_unbounded_counter_exploration_abstains():
    assert propose(public([0],[['add','head','r0']])) is None


def test_response_closure_limit_prevents_partial_acceptance():
    assert propose(public([0],[['ite',['gt','head',0],['sub',1,'r0'],'r0']]),max_responses=1) is None


@pytest.mark.parametrize('kwargs',[{'max_states':0},{'max_states':9},{'max_responses':0},
                                  {'exploration_heads':[True]},{'exploration_heads':[]}])
def test_bounds_are_enforced(kwargs):
    with pytest.raises(SummaryError):propose(public([0],['r0']),**kwargs)


def test_oracle_fields_rejected_by_public_schema():
    p=public([0],['r0']);p['oracle_state']=42
    with pytest.raises(SummaryError):propose(p)
