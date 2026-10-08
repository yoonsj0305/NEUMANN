from copy import deepcopy
import pytest

from neumann1.recursive_summary import (CertifiedSummary, SummaryError, check_summary,
                                      program, reference)
from neumann1.recursive_library_baseline import propose, replace


def problem(empty, outputs):
    return {'semantics':'integer_list_right_fold','empty':empty,
            'step':program(['head']+[f'r{i}' for i in range(len(empty))],outputs)}


def tree(values):
    if not values:return ['nil']
    if len(values)==1:return ['single',values[0]]
    cut=len(values)//2
    return ['concat',tree(values[:cut]),tree(values[cut:])]


def assert_preserved(public, cases):
    found=propose(public)
    assert found is not None
    engine=CertifiedSummary(public,found['proposal'])
    for values in cases:
        assert engine.run(tree(values))==reference(public,values)
    return found


def test_known_prefix_adds_sufficient_auxiliary_state():
    p=problem([0],[['max',['add','r0','head'],0]])
    found=assert_preserved(p,[[],[-5,4],[4,-5],[3,-9,8]])
    assert found['template']=='prefix_lift' and len(found['proposal']['empty'])==2


def test_mapped_weights_are_generated_from_public_input_only():
    weight=['sub',3,'head']
    p=problem([0],[['max',['add','r0',weight],0]])
    found=assert_preserved(p,[[],[5,0,9],[-2,4],[10**70,-10**70]])
    assert found['input_map']==weight


def test_associative_flattened_input_map_is_retained():
    weight=['add','head',['add',2,'head']]
    p=problem([0],[['max',['add',weight,'r0'],0]])
    assert_preserved(p,[[],[-10,1,20],[3,0,-9],[10**30]])


def test_reference_state_permutation_preserves_full_ordered_output():
    p=problem([0,0],[['add','r0','head'],['max',['add','head','r1'],0]])
    found=assert_preserved(p,[[],[2,-8,3],[0],[-4,9]])
    assert found['template']=='prefix_with_sum' and found['state_order']==[1,0]


@pytest.mark.parametrize('op,other',[('max','min'),('min','max')])
def test_zero_padded_order_statistics_use_correct_multiset_semantics(op,other):
    p=problem([0,0],[[op,'head','r0'],[op,'r1',[other,'head','r0']]])
    assert_preserved(p,[[],[-9],[-9,-1],[4,4,3],[10**60,-10**61,2]])


def test_first_two_retains_distinct_empty_and_single_defaults():
    p=problem([0,1],['head','r0'])
    found=assert_preserved(p,[[],[5],[5,-3],[5,-3,99],[0],[-1,0]])
    assert len(found['proposal']['empty'])==3


def test_partial_subarray_goal_requires_known_additional_state():
    p=problem([0,0],[['max',['add','r0','head'],0],
                     ['max','r1',['max',['add','r0','head'],0]]])
    found=assert_preserved(p,[[],[-5,4],[4,-5],[3,-8,9,-2]])
    assert found['template']=='prefix_subarray_lift' and len(found['proposal']['empty'])==4


def test_independent_blocks_are_composed_without_oracle_lookup():
    p=problem([0,0],[['add','r0','head'],['max','r1',['sub',0,'head']]])
    found=assert_preserved(p,[[],[-5,4],[4,-5],[1,2,3]])
    assert found['mechanism']=='KNOWN_DIRECT_PRODUCT_REUSE_NOT_LEARNING'
    assert len(found['blocks'])==2


def test_native_reuse_bounds_composed_state_size():
    p=problem([0]*8,[['max',['add',f'r{i}','head'],0] for i in range(8)])
    assert propose(p) is None


def test_coupled_unknown_recurrence_abstains():
    p=problem([0,0],[['add','r0','head'],['add','r1','r0']])
    assert propose(p) is None


def test_near_match_is_recognized_only_under_actual_validation():
    p=problem([0],[['max',['add','r0','head'],0]])
    found=propose(p)
    false=deepcopy(found['proposal'])
    false['decode']['outputs']=['z1']
    assert not check_summary(p,false)['accepted']
    p['oracle_label']='prefix'
    with pytest.raises(SummaryError):propose(p)
