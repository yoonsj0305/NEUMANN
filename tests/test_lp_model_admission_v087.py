"""Contract fixtures only. No timing audit, training or generated final data."""
import copy
import inspect
from unittest.mock import patch

import numpy as np
import pytest

from neumann1 import lp_model_admission_v087 as p


def fixture_records():
    sources = [{'id': str(i), 'expanded': i < 12} for i in range(24)]
    records = []
    for s in sources:
        for route in p.ROUTES:
            for repeat in (-1, 0, 1, 2):
                records.append({'case_id': s['id'], 'route': route, 'repeat': repeat,
                    'accepted': True, 'total_ms': 2. if route.startswith('perfect_') else 10.,
                    'forward_ms': 1. if route == 'perfect_compact16' else 2.,
                    'execution': {'candidate': {'accepted': False}}})
    return records, sources


def test_admission_is_not_q3_q4_closure():
    rows, sources = fixture_records()
    result = p.summarize(rows, sources)
    assert result['decision'] == 'ADMIT_BOUNDED_MODEL_FITTING_NOT_Q3_Q4_PASS'
    assert result['q3'] == result['q4'] == 'OPEN'
    assert not p.protocol()['trained']


@pytest.mark.parametrize('fault', ['slow', 'cheap', 'forward', 'failed'])
def test_preregistered_negative_gates(fault):
    rows, sources = fixture_records()
    for r in rows:
        if fault == 'slow' and r['route'] == 'perfect_compact16':
            r['total_ms'] = 6.
        if fault == 'cheap' and r['route'] == 'centred_residual':
            r['execution']['candidate']['accepted'] = True
        if fault == 'forward' and r['route'] == 'perfect_compact16':
            r['forward_ms'] = 2.
    if fault == 'failed':
        rows[0]['accepted'] = False
    assert p.summarize(rows, sources)['decision'] == (
        'CAPABILITY_UNREACHED' if fault == 'failed' else 'REJECT_THIS_MODEL_TASK_BEFORE_FITTING')


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'nonfinite', 'bool', 'sources'])
def test_archive_coverage_and_cost_faults(fault):
    rows, sources = fixture_records()
    if fault == 'missing': rows.pop()
    if fault == 'duplicate': rows.append(copy.deepcopy(rows[0]))
    if fault == 'nonfinite': rows[0]['total_ms'] = float('nan')
    if fault == 'bool': rows[0]['accepted'] = 1
    if fault == 'sources': sources.pop()
    with pytest.raises(ValueError):
        p.summarize(rows, sources)


def test_paid_features_and_policy_observe_only_original_problem():
    assert list(inspect.signature(p.features).parameters) == ['A', 'b', 'c']
    rng = np.random.default_rng(87001)
    A = rng.normal(size=(3, 12))
    b, c = rng.normal(size=3), rng.normal(size=12)
    D, rows, cols = p.features(A, b, c)
    assert D.shape == (3, 12) and rows.shape == (3, 8) and cols.shape == (12, 8)
    order = rng.permutation(12)
    _, rows2, cols2 = p.features(A[:, order], b, c[order])
    np.testing.assert_allclose(rows, rows2, atol=1e-12)
    np.testing.assert_allclose(cols[order], cols2, atol=1e-12)


def test_failed_basis_and_native_repair_share_remaining_deadline():
    raw = {'A': np.eye(2), 'b': np.ones(2), 'c': np.ones(2)}
    failed = {'accepted': False, 'witness': None, 'total_ms': 1.}
    native = {'accepted': True, 'attempts': [{'witness': {'x': [1., 1.], 'y': [1., 1.]}}]}
    with patch.object(p.storage, 'candidate_once', return_value=failed), \
         patch.object(p, 'solve_native_checked', return_value=native) as solve, \
         patch.object(p, 'perf_counter_ns', side_effect=[0, 1000000, 2000000]):
        row = p.checked_head(raw, [0, 1], budget_s=.01)
    assert row['accepted'] and row['fallback_used']
    assert solve.call_args.kwargs['budget_s'] == pytest.approx(.009)
    assert row['candidate'] == failed and row['native'] == native


def test_late_valid_witness_is_retained_but_not_accepted():
    raw = {'A': np.eye(2), 'b': np.ones(2), 'c': np.ones(2)}
    candidate = {'accepted': True, 'witness': {'x': [1., 1.], 'y': [1., 1.]}}
    with patch.object(p.storage, 'candidate_once', return_value=candidate), \
         patch.object(p, 'solve_native_checked', side_effect=AssertionError('extra run')), \
         patch.object(p, 'perf_counter_ns', side_effect=[0, 2000000]):
        row = p.checked_head(raw, [0, 1], budget_s=.001)
    assert not row['accepted'] and row['witness'] == candidate['witness']


def test_runner_refuses_overwriting_first_evidence(tmp_path):
    import benchmark_v087 as runner
    target = tmp_path / 'first.json.gz'
    target.write_bytes(b'original')
    with patch('sys.argv', ['benchmark_v087.py', str(target)]), \
         patch.object(runner, 'run_audit', side_effect=AssertionError('audit forbidden')):
        with pytest.raises(SystemExit): runner.main()
    assert target.read_bytes() == b'original'


def test_runner_preserves_partial_failed_observations(tmp_path):
    import gzip
    import json
    import benchmark_v087 as runner
    target = tmp_path / 'failed.json.gz'
    partial = {'records': [{'accepted': False, 'total_ms': 4.}]}
    with patch('sys.argv', ['benchmark_v087.py', str(target)]), \
         patch.object(runner, 'load_source', return_value={}), \
         patch.object(runner, 'run_audit', side_effect=p.AuditInterrupted(ValueError('fixture'), partial)):
        with pytest.raises(p.AuditInterrupted): runner.main()
    with gzip.open(target, 'rt') as stream: saved = json.load(stream)
    assert saved['partial'] == partial and saved['do_not_overwrite']


def retained_report():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'docs/experiments/results'
    return p.load_admission(root / 'v087_admission.manifest.json'), p.load_source(
        root / 'v084_first_audit.manifest.json')


def test_retained_correction_replays_without_solver_or_model():
    report, original = retained_report()
    with patch.object(p, 'prepare', side_effect=AssertionError('oracle setup forbidden')), \
         patch.object(p.storage, 'candidate_once', side_effect=AssertionError('solve forbidden')), \
         patch.object(p, 'solve_native_checked', side_effect=AssertionError('native forbidden')):
        p.validate_archive(report, original)
    assert report['summary']['decision'] == 'ADMIT_BOUNDED_MODEL_FITTING_NOT_Q3_Q4_PASS'
    assert len(report['records']) == 864


@pytest.mark.parametrize('fault', ['witness', 'source', 'cost', 'runtime', 'state', 'summary'])
def test_retained_archive_rejects_evidence_faults(fault):
    report, original = retained_report()
    if fault == 'witness': report['records'][0]['witness']['x'][0] += 100.
    if fault == 'source': report['sources'][0]['expanded'] = not report['sources'][0]['expanded']
    if fault == 'cost':
        r = next(r for r in report['records'] if 'execution' in r)
        r['total_ms'] = 0.
    if fault == 'runtime': report['environment']['numpy'] = 'wrong'
    if fault == 'state':
        next(r for r in report['records'] if r['route'].startswith('perfect_'))['state_columns'] += 1
    if fault == 'summary': report['summary']['perfect_complete_best_direct_geomean'] = 0.
    with pytest.raises(ValueError): p.validate_archive(report, original)


def test_missing_first_archive_cannot_be_used_as_measurement():
    from pathlib import Path
    manifest = Path(__file__).resolve().parents[1] / 'docs/experiments/results/v087_admission.manifest.json'
    with pytest.raises(ValueError, match='unavailable'): p.load_admission(manifest, 'first')
