"""Native integration uses a fresh process; fixtures are not a timing audit."""
import inspect
import json
import subprocess
import sys
from unittest.mock import patch

import numpy as np
import pytest

from neumann1 import lp_native_warm_start_v086 as p


def raw():
    return {'A': np.array([[1., 1., 0.], [0., 0., 1.]]),
            'b': np.ones(2), 'c': np.array([2., 1., 0.])}


def test_observable_only_signature_and_strict_heads():
    assert list(inspect.signature(p.solve_native_checked).parameters) == [
        'A', 'b', 'c', 'head', 'cold_fallback', 'budget_s']
    for head in ({'basis': [0]}, {'basis': [0, 0]}, {'basis': [0, 3]},
                 {'basis': [-1, 0]}, {'basis': [True, 2]}, {'basis': [0., 2]},
                 {'basis': '02'}, {'basis': [0, 2], 'gold': True},
                 {'abstain': 1}, {'abstain': True, 'gold': 1}, [], None):
        assert p.decode_basis(head, 2, 3) == ('INVALID_HEAD', None)
    assert p.decode_basis({'abstain': True}, 2, 3) == ('ABSTAIN', None)
    assert p.decode_basis({'basis': [2, 0]}, 2, 3) == ('BASIS', [2, 0])


def test_invalid_head_without_fallback_does_no_native_work():
    pytest.importorskip('highspy')
    with patch.object(p, '_attempt', side_effect=AssertionError('native forbidden')):
        row = p.solve_native_checked(**raw(), head={'basis': [0, 0]}, cold_fallback=False)
    assert row['status'] == 'REJECTED' and not row['accepted']
    assert not row['attempts'] and not row['fallback_used']
    assert sum(row['ledger'].values()) == 0


@pytest.mark.parametrize('budget', [0, -1, True, float('nan'), float('inf')])
def test_invalid_budget_rejected_before_work(budget):
    with pytest.raises(ValueError):
        p.solve_native_checked(**raw(), budget_s=budget)


def test_malformed_original_input_is_not_solved():
    pytest.importorskip('highspy')
    for A in (np.ones(2), np.zeros((0, 3)), np.full((2, 3), np.nan)):
        with patch.object(p, '_attempt', side_effect=AssertionError('native forbidden')):
            with pytest.raises(ValueError):
                p.solve_native_checked(A, np.ones(2), np.ones(3))


def _failed_attempt():
    return {'accepted': False, 'ledger': {'native_run_calls': 1,
            'set_basis_calls': 1, 'certificate_calls': 1}}


def test_failed_warm_work_and_cold_rescue_are_both_charged():
    pytest.importorskip('highspy')
    cold = {'accepted': True, 'ledger': {'native_run_calls': 1,
            'set_basis_calls': 0, 'certificate_calls': 1}}
    with patch.object(p, '_attempt', side_effect=[_failed_attempt(), cold]) as attempt:
        row = p.solve_native_checked(**raw(), head={'basis': [1, 2]})
    assert row['accepted'] and row['fallback_used'] and len(row['attempts']) == 2
    assert row['ledger'] == {'native_run_calls': 2, 'set_basis_calls': 1, 'certificate_calls': 2}
    assert attempt.call_args_list[0].args[-1] == attempt.call_args_list[1].args[-1]
    assert attempt.call_args_list[1].args[-2] is None


def test_late_certificate_is_not_success_and_deadline_prevents_extra_run():
    pytest.importorskip('highspy')
    with patch.object(p, 'perf_counter_ns', side_effect=[0, 2_000_000_000, 2_000_000_000]), \
         patch.object(p, '_attempt', return_value=_failed_attempt()) as attempt:
        row = p.solve_native_checked(**raw(), head={'basis': [1, 2]}, budget_s=1)
    assert attempt.call_count == 1 and row['status'] == 'BUDGET_EXCEEDED'
    assert not row['accepted'] and row['ledger']['native_run_calls'] == 1
    with patch.object(p, 'perf_counter_ns', side_effect=[0, 2_000_000_000]), \
         patch.object(p, '_attempt', return_value={'accepted': True, 'ledger':
                     {'native_run_calls': 1, 'set_basis_calls': 0, 'certificate_calls': 1}}):
        row = p.solve_native_checked(**raw(), budget_s=1)
    assert row['status'] == 'BUDGET_EXCEEDED' and not row['accepted']


def test_real_native_repairs_bad_bases_and_original_verifier_retains_authority():
    pytest.importorskip('highspy')
    script = '''
import json
import numpy as np
from unittest.mock import patch
from neumann1 import lp_native_warm_start_v086 as p
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
raw={'A':np.array([[1.,1.,0.],[0.,0.,1.]]),'b':np.ones(2),'c':np.array([2.,1.,0.])}
out=[]
for head in (None, {'basis':[1,2]}, {'basis':[0,2]}, {'basis':[0,1]},
             {'basis':[0,0]}, {'abstain':True}):
    row=p.solve_native_checked(**raw,head=head)
    assert row['accepted'], row
    witness=row['attempts'][-1]['witness']
    assert verify_standard_form_certificate(**raw,**witness)['accepted']
    assert abs(np.array(raw['c'])@witness['x']-1.)<1e-8
    if head is not None and head.get('basis') in ([1,2],[0,2],[0,1]):
        assert row['ledger']['set_basis_calls']==1
    out.append({'head_kind':row['head_kind'],'accepted':row['accepted'],
                'ledger':row['ledger'],'fallback_used':row['fallback_used']})
with patch.object(p,'verify_standard_form_certificate',return_value={'accepted':False}):
    denied=p.solve_native_checked(**raw,head={'basis':[1,2]})
assert not denied['accepted'] and denied['ledger']['certificate_calls']==2
with patch.object(p,'verify_standard_form_certificate',side_effect=ValueError('fixture')):
    failed=p.solve_native_checked(**raw,head={'basis':[1,2]})
assert not failed['accepted'] and failed['ledger']['certificate_calls']==2
assert all('fixture' in a['error'] for a in failed['attempts'])
for bad in ({'A':np.array([[1.]]),'b':np.array([-1.]),'c':np.array([0.])},
            {'A':np.array([[0.]]),'b':np.array([0.]),'c':np.array([-1.])}):
    row=p.solve_native_checked(**bad)
    assert not row['accepted'] and row['ledger']['certificate_calls']==0
print(json.dumps(out))
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True,
                            text=True, check=True, timeout=30)
    rows = json.loads(result.stdout)
    assert len(rows) == 6 and all(row['accepted'] for row in rows)
    assert rows[4]['fallback_used'] and rows[5]['fallback_used']
