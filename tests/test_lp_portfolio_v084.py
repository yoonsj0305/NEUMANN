"""Fixtures only; no generated v084 solve/timing and no performance evidence."""
import copy
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from neumann1 import lp_portfolio_v084 as p
from neumann1.lp_certificate_v081 import verify_standard_form_certificate


class PortfolioTests(unittest.TestCase):
    def test_retained_first_archive_reassembles_and_replays_without_solving(self):
        path = Path(__file__).resolve().parents[1] / 'docs/experiments/results/v084_first_audit.manifest.json'
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest['json_sha256'],
                         '10ad3cad8ad5c7f2543c333ce72f484f6747767828dc76e842795940603177c9')
        report = p.load_retained_archive(path)
        with patch.object(p, 'linprog', side_effect=AssertionError('optimizer forbidden')), \
             patch.object(p.previous, 'generate_case', side_effect=AssertionError('generation forbidden')), \
             patch.object(p, 'propose', side_effect=AssertionError('new discovery forbidden')):
            p.validate_archive(report)
        self.assertEqual(sum(r['accepted'] for r in report['records']), 720)
        self.assertEqual(sum(r['accepted'] for r in report['warmups']), 240)
        self.assertEqual(report['summary']['decision'], 'RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION')
        self.assertTrue(all(not x['gate_pass'] for x in report['summary']['forms'].values()))

    def fixture(self):
        return {'A': np.array([[1., 0., 2.], [0., 1., 2.]]),
                'b': np.ones(2), 'c': np.array([0., 0., 1.])}

    def test_observable_only_signature_and_bounded_build(self):
        self.assertEqual(list(inspect.signature(p.propose).parameters), ['A', 'b', 'c'])
        raw = self.fixture()
        with patch.object(p, 'lstsq', wraps=p.lstsq) as spy:
            proposals = p.propose(**raw)
        self.assertEqual(spy.call_count, 6)
        self.assertTrue(all(c.kwargs['lapack_driver'] == 'gelsy' and c.kwargs['cond'] == 1e-12
                            for c in spy.call_args_list))
        self.assertTrue(1 <= len(proposals) <= 7)
        self.assertEqual(len({tuple(x) for _, x in proposals}), len(proposals))

    def test_positive_column_scale_cancels_before_proposal(self):
        rng = np.random.default_rng(12)
        A, b, c = rng.normal(size=(3, 10)), rng.normal(size=3), rng.normal(size=10)
        d = np.array([.5, 2., 4., .25, 8., 16., .125, 1., 32., .0625])
        before, after = p.normalized(A, b, c), p.normalized(A * d, b, c * d)
        for x, y in zip(before, after):
            np.testing.assert_array_equal(x, y)
        original, scaled = p.propose(A, b, c), p.propose(A * d, b, c * d)
        self.assertEqual([name for name, _ in original], [name for name, _ in scaled])
        for (_, x), (_, y) in zip(original, scaled):
            np.testing.assert_array_equal(x, y)

    def test_zero_nonfinite_and_dimension_fail_closed(self):
        raw = self.fixture()
        for mutation in ('zero', 'nan', 'shape'):
            r = copy.deepcopy(raw)
            if mutation == 'zero': r['A'][:, 0] = 0
            elif mutation == 'nan': r['c'][0] = np.nan
            else: r['b'] = np.ones(3)
            with self.assertRaises(ValueError): p.propose(**r)

    def test_original_certificate_and_witness_retained(self):
        raw = self.fixture()
        with patch.object(p, 'propose', return_value=[('fixture', np.array([0, 1]))]), \
             patch.object(p, 'direct_once', side_effect=AssertionError('unexpected fallback')):
            row = p.discovery_once(**raw)
        self.assertTrue(row['accepted'])
        self.assertFalse(row['fallback_used'])
        self.assertTrue(verify_standard_form_certificate(**raw, **row['witness'])['accepted'])
        p._check_record(row, raw)
        self.assertGreaterEqual(row['total_ms'], row['proposal_ms'] + row['attempts'][0]['total_ms'])

    def test_singular_attempt_and_native_fallback_in_fresh_process(self):
        script = '''
import json
from unittest.mock import patch
import numpy as np
from neumann1 import lp_portfolio_v084 as p
raw={'A':np.array([[1.,1.,0.],[0.,0.,1.]]),'b':np.ones(2),'c':np.array([2.,1.,0.])}
with patch.object(p,'propose',return_value=[('singular',np.array([0,1]))]):
    row=p.discovery_once(**raw)
p._check_record(row,raw)
print(json.dumps(row))
'''
        result = subprocess.run([sys.executable, '-c', script], check=True,
                                capture_output=True, text=True, timeout=30)
        row = json.loads(result.stdout)
        self.assertTrue(row['accepted'])
        self.assertTrue(row['fallback_used'])
        self.assertFalse(row['attempts'][0]['accepted'])
        self.assertIn('Singular', row['attempts'][0]['error'])
        self.assertIsNotNone(row['fallback']['witness'])

    def test_proposal_exception_cost_survives_fallback(self):
        raw = self.fixture()
        witness = {'x': [1., 1., 0.], 'y': [0., 0.]}
        fallback = {'method': 'highs', 'accepted': True, 'witness': witness,
                    'certificate': verify_standard_form_certificate(**raw, **witness),
                    'total_ms': 0., 'solve_ms': 0., 'verify_ms': 0., 'error': None}
        with patch.object(p, 'propose', side_effect=RuntimeError('fixture')), \
             patch.object(p, 'direct_once', return_value=fallback):
            row = p.discovery_once(**raw)
        self.assertIn('fixture', row['proposal_error'])
        self.assertTrue(row['fallback_used'])
        self.assertEqual(row['proposed_count'], 0)
        p._check_record(row, raw)

    def test_exact_input_roundtrip_and_shape_rejection(self):
        A = np.array([[1., np.nextafter(1., 2.)], [-0., .125]])
        encoded = p.encode_array(A)
        self.assertEqual(p.decode_array(encoded, A.shape).tobytes(), A.tobytes())
        with self.assertRaises(ValueError): p.decode_array(encoded, (4,))
        encoded['data'] = encoded['data'][:-4]
        with self.assertRaises(ValueError): p.decode_array(encoded, A.shape)

    def archive_fixture(self):
        specs = []
        sources, records, warmups = [], [], []
        raw = self.fixture()
        witness = {'x': [1., 1., 0.], 'y': [0., 0.]}
        certificate = verify_standard_form_certificate(**raw, **witness)
        for form in p.FORMS:
            for i in range(12):
                spec = {'id': f'{form}_{i}', 'form': form, 'width_factor': 16,
                        'rows': 2, 'cols': 3, 'seed': i}
                specs.append(spec)
                sources.append({**spec, 'raw_sha256': p.input_digest(raw), 'setup_ms': 1.,
                                'arrays': {k: p.encode_array(v) for k, v in raw.items()}})
                for route in p.ROUTES:
                    row = {'case_id': spec['id'], 'route_id': route, 'method': route,
                           'accepted': True, 'witness': witness, 'certificate': certificate,
                           'solve_ms': 8., 'verify_ms': 1., 'total_ms': 10., 'error': None}
                    if route not in p.base.DIRECT_METHODS:
                        attempt = {'method': 'fixture', 'indices': [0, 1], 'accepted': True,
                                   'witness': witness, 'certificate': certificate,
                                   'solve_ms': .5, 'verify_ms': .5, 'total_ms': 1., 'error': None}
                        row = {'case_id': spec['id'], 'route_id': route, 'method': route,
                               'accepted': True, 'witness': witness, 'certificate': certificate,
                               'proposal_ms': 1., 'proposal_error': None, 'proposed_count': 1,
                               'attempts': [attempt], 'fallback_used': False, 'fallback': None,
                               'total_ms': 3.}
                    warmups.append(copy.deepcopy(row))
                    records.extend({**copy.deepcopy(row), 'repeat': r} for r in range(p.REPEATS))
        with patch.object(p, 'specifications', return_value=tuple(specs)):
            summary = p.summarize(records, warmups)
        return specs, {'protocol': p.protocol(), 'environment': {
            **p.protocol()['runtime'], 'declared_single_thread': True,
            'openblas_coretype': 'HASWELL', 'threadpools': [{'num_threads': 1}]},
            'sources': sources, 'records': records, 'warmups': warmups, 'summary': summary}

    def test_offline_archive_checks_witness_without_optimizer_or_generation(self):
        specs, report = self.archive_fixture()
        with patch.object(p, 'specifications', return_value=tuple(specs)), \
             patch.object(p, 'linprog', side_effect=AssertionError('optimizer forbidden')), \
             patch.object(p.previous, 'generate_case', side_effect=AssertionError('generation forbidden')):
            p.validate_archive(report)
        self.assertEqual(report['summary']['decision'], 'CLASSICAL_PORTFOLIO_CONSUMES_MATCHED_HEADROOM')

    def test_archive_rejects_input_witness_cost_coverage_and_summary_tampering(self):
        specs, original = self.archive_fixture()
        for mutation in ('input', 'witness', 'cost', 'coverage', 'summary', 'nested', 'pool', 'setup'):
            report = copy.deepcopy(original)
            if mutation == 'input': report['sources'][0]['raw_sha256'] = '0' * 64
            elif mutation == 'witness': report['records'][0]['witness']['x'][0] += 1.
            elif mutation == 'cost': report['records'][0]['total_ms'] = .1
            elif mutation == 'coverage': report['records'].pop()
            elif mutation == 'summary': report['summary']['q4'] = 'PASS'
            elif mutation == 'nested':
                next(r for r in report['records'] if r['route_id'] == 'scale_portfolio')['attempts'][0]['witness']['y'][0] = 10.
            elif mutation == 'pool': report['environment']['threadpools'][0]['num_threads'] = 2
            else: report['sources'][0]['setup_ms'] = -1.
            with patch.object(p, 'specifications', return_value=tuple(specs)):
                with self.assertRaises(ValueError, msg=mutation): p.validate_archive(report)

    def test_capability_failure_cannot_become_speedup(self):
        specs, report = self.archive_fixture()
        next(r for r in report['warmups'] if r['route_id'] == 'scale_portfolio')['accepted'] = False
        with patch.object(p, 'specifications', return_value=tuple(specs)):
            summary = p.summarize(report['records'], report['warmups'])
        self.assertEqual(summary['decision'], 'CAPABILITY_UNREACHED')
        self.assertNotIn('forms', summary)

    def test_full_grid_fresh_seeds_and_record_counts(self):
        specs = p.specifications()
        self.assertEqual(len(specs), 48)
        self.assertEqual({s['seed'] for s in specs}, set(range(84100, 84112)))
        self.assertEqual(len(specs) * len(p.ROUTES) * p.REPEATS, 720)
        self.assertEqual(p.protocol()['max_candidates'], 7)

    def test_runner_reservation_refuses_overwrite_before_audit(self):
        import benchmark_v084
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'first.json.gz'
            path.touch()
            with patch.object(sys, 'argv', ['benchmark_v084.py', str(path)]), \
                 patch.object(benchmark_v084, 'run_audit', side_effect=AssertionError('audit forbidden')):
                with self.assertRaises(SystemExit): benchmark_v084.main()
            self.assertEqual(path.read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
