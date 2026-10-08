"""Soundness and authority guards for the opened certificate diagnostic."""
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
import pytest
from experiments import bp_certificate_diagnostic as d


@pytest.fixture(autouse=True)
def scientific_imports():
    d.science()


def tiny():
    # Optimum x0=1 with only one nonzero, though the original has two rows.
    return {'A': np.array([[1., -1., 1., 0.], [1., -1., 0., 1.]]),
            'b': np.array([1., 1.]), 'c': np.array([1., 1., 2., 2.])}


def test_sparse_below_row_count_is_original_certified():
    r = d.sparse_checked(tiny(), [0], budget_s=2)
    assert r['accepted'] and len(r['indices']) < tiny()['A'].shape[0]
    assert d.checker(**tiny(), **r['witness'])['accepted']
    assert not r['free_dual_used']


def test_inferior_support_is_never_certified():
    r = d.sparse_checked(tiny(), [2, 3], budget_s=2)
    assert not r['accepted']
    assert not d.checker(**tiny(), **r['witness'])['accepted']


def test_full_original_dual_repair_uses_no_oracle():
    raw = {'A': np.array([[1., 2., 0., -1., -2., 0.], [0., 1., 1., 0., -1., -1.]]),
           'b': np.array([1., 0.]), 'c': np.ones(6)}
    r = d.sparse_checked(raw, [0], budget_s=2)
    assert not r['attempts'][0]['certificate']['accepted']
    assert r['attempts'][1]['method'] == 'full_dual_feasibility_LP'
    assert r['accepted'] and not r['free_dual_used']
    assert d.checker(**raw, **r['witness'])['accepted']


def test_invalid_support_and_budget_fail_closed():
    for support in ([], [0, 0], [-1], [4], [True]):
        with pytest.raises(ValueError): d.sparse_checked(tiny(), support, budget_s=2)
    for budget in (0, -1, float('inf'), float('nan')):
        with pytest.raises(ValueError): d.sparse_checked(tiny(), [0], budget_s=budget)


def test_wrong_free_dual_and_payload_mutation_rejected():
    r = d.sparse_checked(tiny(), [0], budget_s=2, free_dual=[0., 0.])
    assert not r['accepted']
    good = d.sparse_checked(tiny(), [0], budget_s=2)
    good['witness']['x'][0] += 1
    assert not d.checker(**tiny(), **good['witness'])['accepted']


def test_native_dual_lp_recovers_original_primal():
    r = d.scipy_direct(tiny(), 'A_DUAL', 2)
    assert r['accepted'] and d.checker(**tiny(), **r['witness'])['accepted']


def test_oracle_authority_only_e_may_use_supplied_dual():
    poison = object()
    with patch.object(d, 'native_result', return_value={'accepted': True}) as f:
        d.execute_path(tiny(), 'A_NATIVE', 2, oracle_support=poison, oracle_dual=poison)
        assert f.call_count == 1
    with patch.object(d, 'sparse_checked', return_value={'accepted': True}) as f:
        d.execute_path(tiny(), 'D_ORACLE_SPARSE', 2, oracle_support=[0], oracle_dual=poison)
        assert f.call_args.kwargs['free_dual'] is None


def test_schedule_warmup_before_timing_and_no_missing_cells():
    rows = d.schedule()
    assert len(rows) == 576 and len(set(rows)) == 576
    assert all(r[2] == -1 for r in rows[:144])
    assert all(r[2] >= 0 for r in rows[144:])


def test_censored_capability_not_removed_from_screen():
    records = [{'case_id': c, 'route': r, 'repeat': i, 'query_ms': 1., 'accepted': True}
               for c, r, i in d.schedule()]
    row = next(x for x in records if x['route'] == 'D_ORACLE_SPARSE')
    row['accepted'] = False
    summary = d.summarize(records, 1000., 100.)
    assert summary['screening']['D_ORACLE_SPARSE']['comparable_originals'] == 15
    assert summary['screening']['D_ORACLE_SPARSE']['screen'] == 'INCOMPLETE'
    with pytest.raises(ValueError): d.summarize(records[:-1], 1000., 100.)


def test_spgl_grammar_never_assumed():
    def forbidden_solve(*args, **kwargs):
        raise AssertionError('invalid signed-pair grammar must be rejected before solving')
    # SPGL1 is an optional comparator dependency, not needed to test grammar.
    with patch.dict('sys.modules', {'spgl1': SimpleNamespace(spg_bp=forbidden_solve)}):
        with pytest.raises(ValueError): d.spgl_direct(tiny(), 2)
