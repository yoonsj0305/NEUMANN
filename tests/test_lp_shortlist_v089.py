import pytest
import numpy as np
from unittest.mock import patch
from neumann1.lp_shortlist_v089 import solve_shortlist_checked


@pytest.mark.parametrize('indices', [[0,1], [1,2]])
def test_reduced_optimum_cannot_hide_omitted_original_dual_constraint(indices):
    pytest.importorskip('highspy')
    A=np.ones((1,3)); b=np.array([1.]); c=np.array([2.,3.,1.])
    row=solve_shortlist_checked(A,b,c,indices)
    assert row['accepted']
    assert row['witness']['x'][2]==pytest.approx(1.)
    if indices==[0,1]:
        assert row['restricted']['accepted']
        assert not row['original_certificate']['accepted']
        assert row['fallback_used'] and not row['subset_accepted']
    else:
        assert row['subset_accepted'] and not row['fallback_used']


def test_restricted_infeasibility_pays_cold_rescue():
    pytest.importorskip('highspy')
    row=solve_shortlist_checked(np.array([[1.,0.,0.],[0.,1.,1.]]),
                               np.ones(2),np.array([1.,1.,2.]),[1,2])
    assert not row['restricted']['accepted']
    assert row['fallback_used'] and row['accepted']


@pytest.mark.parametrize('indices',[[0,0],[True],[4],[],[0.0]])
def test_invalid_shortlist_is_advisory_not_authority(indices):
    pytest.importorskip('highspy')
    row=solve_shortlist_checked(np.ones((1,3)),np.ones(1),np.array([2.,3.,1.]),indices)
    assert not row['valid_shortlist'] and row['restricted'] is None
    assert row['fallback_used'] and row['accepted']


@pytest.mark.parametrize('budget',[0,-1,float('nan'),True])
def test_invalid_deadline_rejected(budget):
    with pytest.raises(ValueError): solve_shortlist_checked(np.ones((1,3)),np.ones(1),np.ones(3),[0],budget_s=budget)


def test_late_valid_witness_cannot_pass_complete_deadline():
    with patch('neumann1.lp_shortlist_v089.perf_counter_ns',side_effect=[0,1,2,6_000_000_000]), \
         patch('neumann1.lp_shortlist_v089.solve_native_checked',return_value={
             'accepted':True,'attempts':[{'witness':{'x':[1.],'y':[1.]}}]}):
        row=solve_shortlist_checked(np.ones((1,1)),np.ones(1),np.ones(1),[0])
    assert row['subset_accepted'] and not row['accepted']
