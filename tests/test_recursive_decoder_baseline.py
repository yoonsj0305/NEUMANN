"""Soundness and counterexamples for the opened native symbolic control."""
from copy import deepcopy
import pytest
import z3

from neumann1.recursive_decoder_baseline import binary,normal,templates,propose
from neumann1.recursive_summary import CertifiedSummary,SummaryError,program,reference,check_summary,validate_program
from experiments.recursive_summary_cases import tree
from experiments.recursive_summary_replay import z3_expression,independent_obligations


def problem(empty,outputs):
    return {'semantics':'integer_list_right_fold','empty':empty,
            'step':program(['head']+[f'r{i}' for i in range(len(empty))],outputs)}


def preserved(public,cases):
    result=propose(public)
    assert result['accepted'] and not result['Oracle_used'] and not result['learning_performed']
    engine=CertifiedSummary(public,result['proposal'])
    for theorem in independent_obligations(public,result['proposal']).values():
        solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(theorem))
        assert solver.check()==z3.unsat
    for values in cases:
        for shape in ['left','right','balanced']:
            assert engine.run(tree(values,shape))==reference(public,values)
    return result


@pytest.mark.parametrize('term',[
    ['sub',['add','x','y'],['sub','z','x']],
    ['sub',0,['max',['add','x','y'],['min','y','z']]],
    ['ite',['gt','x',0],['add','y',['add',2,'x']],['add','y',7]],
    ['and',['ge','x',0],['and',['lt','y',3],['eq','z',0]]],
    ['or',['gt','x',0],['or',['lt','y',3],False]],
    ['ite',['not',['not',['gt','x',0]]],['sub','x','y'],['sub','x','y']],
])
def test_normalization_preserves_all_integer_inputs_and_binary_boolean_arity(term):
    converted=binary(normal(term));original=program(['x','y','z'],[term])
    assert validate_program(original)==validate_program(program(['x','y','z'],[converted]))
    env={v:z3.Int(v) for v in ['x','y','z']}
    solver=z3.Solver();solver.add(z3_expression(term,env)!=z3_expression(converted,env))
    assert solver.check()==z3.unsat


def test_weighted_extension_preserves_the_original_boolean_catalogue():
    ts=templates();names=[t['name'] for t in ts]
    assert names.count('boolean_run_lengths')==names.count('weighted_segment_monoid')==1
    original=next(t for t in ts if t['name']=='boolean_run_lengths')
    weighted=next(t for t in ts if t['name']=='weighted_segment_monoid')
    assert '$increment' not in str(original) and '$increment' in str(weighted)
    weighted['empty'][0]=99
    assert original['empty'][0]==0 and templates()!=ts


def test_balance_generates_a_new_decoder_from_known_prefix_and_sum_states():
    total=['ite',['gt','head',0],['add','r0',1],['sub','r0',1]]
    p=problem([0,0,1],[total,['min','r1',total],
              ['ite',['and',['eq','r2',1],['ge',total,0]],1,0]])
    result=preserved(p,[[],[1,-1],[-1,1],[1,1,-1,-1],[1,-1,-1,1],[1]*50+[-1]*49])
    assert len(result['proposal']['empty'])==2
    assert result['proposal']['decode']['outputs'][1]==['sub','z1','z0']
    assert result['proposal']['decode']['outputs'][2][0]=='ite'


def peak(strict=False):
    active=['gt' if strict else 'ge','head',0]
    suffix_active=['and',['eq','r1',1],['ge','head',0]]
    prefix=['ite',active,['add','r0','head'],0]
    return problem([0,1,0,0],[prefix,['ite',suffix_active,1,0],
        ['ite',suffix_active,['add','r2','head'],'r2'],['max','r3',prefix]])


@pytest.mark.parametrize('strict',[False,True])
def test_weighted_segments_preserve_zero_barriers_and_large_weights(strict):
    p=peak(strict);cases=[[],[2,0,3],[2,-1,3],[2,0,0,3],[-1,0],
                        [10**50,0,3,-1,10**51],[3,0,-1,4,0,5]]
    result=preserved(p,cases)
    if strict:assert len(result['proposal']['empty'])==8 and 'direct_product' in result['origin']
    else:assert result['origin']['template']=='weighted_segment_monoid'
    # Zero is a barrier only for strict-prefix/max-run, while suffix uses >=0.
    assert reference(p,[2,0,3])==([2,1,5,3] if strict else [5,1,5,5])


def test_length_and_suffix_predicate_are_not_confused_by_short_samples():
    flag=['and',['not',['gt','head',0]],['eq','r2',1]]
    p=problem([0,0,1],[['add','r0',1],['ite',flag,['add','r0',1],'r1'],['ite',flag,1,0]])
    result=preserved(p,[[],[-1]*50,[1]+[-1]*50,[-1]*50+[1],[-1,0,1,0,-2]])
    assert len(result['proposal']['empty'])==3
    assert reference(p,[-1,0,1,0,-2])==[5,2,0]


def test_suffix_argmax_uses_shortest_tie_and_preserves_position():
    candidate=['add','r1','head']
    p=problem([0,0,0,0],[['max','r0',candidate],candidate,
       ['ite',['gt',candidate,'r0'],['add','r3',1],'r2'],['add','r3',1]])
    result=preserved(p,[[],[0],[1,-1,1],[-3,-2],[5,-1,4],[10**50,-10**50,2]])
    assert reference(p,[1,-1,1])==[1,1,1,3]
    assert reference(p,[5,-1,4])==[8,8,3,3]
    bad=deepcopy(result['proposal'])
    bad['merge']['outputs'][2][1][0]='ge'
    assert check_summary(p,bad)['status']=='REFUTED'


def test_sample_equivalent_but_false_decoder_never_authorizes_execution():
    p=problem([0,0],[['add','r0',1],['ite',['ge','r0',3],1,0]])
    result=propose(p,max_unifications=500,max_pool=8,max_checks=8)
    assert not result['accepted'] and result['proposal'] is None
    assert any(c['certificate']['status']=='REFUTED' for c in result['checks'])


def test_public_schema_and_search_budgets_block_privilege_and_unbounded_search():
    p=peak()
    for budget in [0,True,100001]:
        with pytest.raises(SummaryError):propose(p,max_unifications=budget)
    with pytest.raises(SummaryError):propose(p,max_pool=33)
    with pytest.raises(SummaryError):propose(p,max_checks=65)
    p['Oracle']='hidden'
    with pytest.raises(SummaryError):propose(p)


def test_counterexample_rejects_an_unsafe_weighted_invariant():
    # A known nonnegative-run invariant is unsuitable when active weights can
    # be negative. The native proposal must be checked rather than trusted.
    p=problem([0],[['ite',['ge','head',-10],['add','r0','head'],0]])
    result=propose(p,max_unifications=300,max_pool=8,max_checks=8)
    assert not result['accepted']
    assert any(c['certificate']['status']=='REFUTED' for c in result['checks'])
