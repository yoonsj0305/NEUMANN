"""P0.9: source/solver independence and typed scope discovery tests."""
from copy import deepcopy
from itertools import product

import numpy as np
import pytest

from experiments.prh_structure_inference_p09 import (
    CONTRACT, LocalOperator, Reject, execute_1d, execute_2d, infer,
    load_ast, negative_controls, reference_1d, run, source_tasks,
)


def test_all_boundary_reference_models_small_exhaustive():
    # Check both independently implemented stepping paths against all binary
    # inputs of length five for all 256 radius-1 rules.
    for byte in range(256):
        table = tuple((byte >> j)&1 for j in range(8))
        for boundary in ('periodic','zero-pad'):
            op=LocalOperator(1,boundary,table)
            for row in product((0,1),repeat=5):
                seq=list(row)
                assert execute_1d(op,seq) == reference_1d(seq,1,boundary,list(table))


def test_radius_two_reference_independence():
    rng=np.random.default_rng(13001)
    for boundary in ('periodic','zero-pad'):
        for _ in range(20):
            table=rng.integers(0,2,size=32).astype(int).tolist()
            seq=rng.integers(0,2,size=29).astype(int).tolist()
            op=LocalOperator(2,boundary,tuple(table))
            assert execute_1d(op,seq)==reference_1d(seq,2,boundary,table)


def test_all_source_conditioned_rules_representable():
    cases=list(source_tasks())
    assert len(cases)==20
    assert [(c['reference_radius'],c['reference_boundary']) for c in cases] == (
        [(0,'none')]*4+[(1,'periodic')]*4+[(1,'zero-pad')]*4+
        [(2,'periodic')]*4+[(2,'zero-pad')]*4
    )
    for case in cases:
        fitted=infer(case['train'])
        assert fitted['status']=='INFERRED_UNIQUE_LOCAL_STRUCTURE'
        op=load_ast(fitted['ast'])
        assert (op.radius,op.boundary,list(op.table)) == (
            case['reference_radius'],case['reference_boundary'],case['reference_table']
        )


def test_holdout_answers_are_not_observed_by_learner():
    case=list(source_tasks())[9]
    original=infer(case['train'])['ast']
    mutated=deepcopy(case)
    mutated['test_1d'][0]['output']=[999]
    mutated['test_2d'][1]['output']=[[999]]
    assert original==infer(mutated['train'])['ast']


def test_invalid_boolean_radius_and_boundary_are_rejected():
    for ast in [
        {'kind':'LOCAL_CA','radius':True,'boundary':'none','table':[0,1]},
        {'kind':'LOCAL_CA','radius':1,'boundary':'reflect','table':[0]*8},
        {'kind':'LOCAL_CA','radius':2,'boundary':'none','table':[0]*32},
        {'kind':'LOCAL_CA','radius':1,'boundary':'periodic','table':[0]*31},
    ]:
        with pytest.raises(Reject):
            load_ast(ast)


def test_source_scope_rejections():
    first=list(source_tasks())[0]
    results=negative_controls(first)
    assert len(results)==7
    assert all(status.startswith('ABSTAIN_') for status in results.values())


def test_not_evidence_of_frontier_global_q3():
    output=run()
    assert output['first_local_gate']=='P09_BOUNDED_SCOPE_DISCOVERY_PASS'
    assert output['global_Q1_to_Q7']=='OPEN'
    assert output['JEPA']=='NOT_RUN'
    assert output['metrics']['exact_structure_and_table']==20
    assert output['metrics']['heldout_1d_exact']==40
    assert output['metrics']['heldout_2d_exact']==40
    assert output['metrics']['negative_controls_rejected']==7
