import copy
import inspect
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from neumann1 import lp_discovery_v083 as discovery
from neumann1.lp_certificate_v081 import verify_standard_form_certificate


class DiscoveryTests(unittest.TestCase):
    def retained(self):
        path = Path(__file__).resolve().parents[1] / 'docs/experiments/results/v083_first_audit.json.gz'
        raw = gzip.decompress(path.read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'a9693593bf1869b6148edf1f06e1ec5e7c5d641da439b592735b90980d42b09f')
        return json.loads(raw)

    def test_retained_first_archive_integrity_without_cross_blas_regeneration(self):
        report = self.retained()
        discovery.validate_archive(report, regenerate_sources=False)
        self.assertEqual(len(report['records']), 576)
        self.assertEqual(sum(x['accepted'] for x in report['records']), 576)
        self.assertTrue(report['summary']['normalization_sensitive'])

    def test_retained_archive_rejects_cost_coverage_and_acceptance_tampering(self):
        original = self.retained()
        route_index = next(i for i,r in enumerate(original['records']) if r['route_id']=='norm_discovery')
        for mutation in ('missing', 'cost', 'acceptance', 'summary', 'source'):
            report = copy.deepcopy(original)
            if mutation == 'missing': report['records'].pop()
            elif mutation == 'cost': report['records'][route_index]['total_ms'] = 0.
            elif mutation == 'acceptance': report['records'][route_index]['accepted'] = False
            elif mutation == 'summary': report['summary']['decision'] = 'Q4_PASS'
            else: report['sources'][0]['seed'] += 1
            with self.assertRaises(ValueError):
                discovery.validate_archive(report, regenerate_sources=False)

    def test_observable_only_signature_and_candidate_sets(self):
        self.assertEqual(list(inspect.signature(discovery.propose).parameters), ['A', 'b', 'c'])
        A = np.array([[1., 0., 2.], [0., 1., 2.]])
        candidates = discovery.propose(A, np.ones(2), np.array([0., 0., 1.]))
        self.assertEqual(len(candidates), 1)
        np.testing.assert_array_equal(candidates[0][1], [0, 1])

    def test_valid_discovered_basis_checks_original_without_fallback(self):
        A, b, c = np.array([[1., 0., 2.], [0., 1., 2.]]), np.ones(2), np.array([0., 0., 1.])
        with patch.object(discovery.base, 'oracle_basis_once', wraps=discovery.base.oracle_basis_once) as spy:
            row = discovery.discovery_once(A, b, c)
        self.assertTrue(row['accepted'])
        self.assertFalse(row['fallback_used'])
        self.assertEqual(set(spy.call_args.args[0]), {'A', 'b', 'c'})
        self.assertGreaterEqual(row['total_ms'], row['discovery_ms'] + sum(a['total_ms'] for a in row['attempts']))

    def test_singular_proposal_retains_cost_then_verified_native_fallback(self):
        # HiGHS owns a process-global thread scheduler. Earlier unrelated tests
        # can initialize it with different settings; the audit runs fresh.
        script = """
import json
import numpy as np
from neumann1.lp_discovery_v083 import discovery_once
print(json.dumps(discovery_once(np.array([[1.,1.,0.],[0.,0.,1.]]),
                               np.ones(2), np.array([2.,1.,0.]))))
"""
        completed = subprocess.run([sys.executable, '-c', script], check=True,
                                   capture_output=True, text=True, timeout=30)
        row = json.loads(completed.stdout)
        self.assertTrue(row['accepted'])
        self.assertTrue(row['fallback_used'])
        self.assertFalse(row['attempts'][0]['accepted'])
        self.assertIsNone(row['attempts'][0]['verify_ms'])
        charged = row['discovery_ms'] + sum(a['total_ms'] for a in row['attempts']) + row['fallback']['total_ms']
        self.assertGreaterEqual(row['total_ms'], charged)

    def test_normalized_coordinate_transform_preserves_certificate(self):
        A = np.array([[2., 0., 3.], [0., 4., 2.]])
        x, y = np.array([1., 2., 0.]), np.array([.5, .25])
        b, c = A @ x, A.T @ y + np.array([0., 0., 1.])
        d = np.linalg.norm(A, axis=0)
        self.assertTrue(verify_standard_form_certificate(A, b, c, x, y)['accepted'])
        self.assertTrue(verify_standard_form_certificate(A / d, b, c / d, x * d, y)['accepted'])

    def test_grid_fresh_seeds_matched_forms_and_protocol(self):
        specs = discovery.specifications()
        self.assertEqual(len(specs), 48)
        self.assertEqual(len({s['id'] for s in specs}), 48)
        self.assertEqual({s['seed'] for s in specs}, set(range(83100, 83112)))
        self.assertEqual({s['form'] for s in specs}, {'raw', 'normalized'})

    def fixtures(self):
        rows, warm = [], []
        for s in discovery.specifications():
            for route in discovery.ROUTES:
                r = {'case_id': s['id'], 'route_id': route, 'accepted': True,
                     'total_ms': 1. if route == 'norm_discovery' else 10.,
                     'fallback_used': s['form'] == 'normalized'}
                if route == 'norm_discovery' and s['form'] == 'normalized':
                    r['total_ms'] = 12.
                warm.append(r)
                rows.extend({**r, 'repeat': i} for i in range(discovery.REPEATS))
        return rows, warm

    def test_summary_separates_raw_shortcut_and_normalized_sensitivity(self):
        rows, warm = self.fixtures()
        report = discovery.summarize(rows, warm)
        self.assertEqual(report['decision'], 'CHEAP_DISCOVERY_CONSUMES_RAW_FAMILY_HEADROOM')
        self.assertTrue(report['normalization_sensitive'])
        self.assertEqual(report['q3'], 'OPEN')
        self.assertEqual(report['q4'], 'OPEN')

    def test_coverage_and_capability_fail_closed(self):
        rows, warm = self.fixtures()
        for bad in (rows[:-1], rows[:-1] + [rows[0]]):
            with self.assertRaises(ValueError):
                discovery.summarize(bad, warm)
        changed = copy.deepcopy(rows)
        changed[0]['repeat'] = False
        with self.assertRaises(ValueError):
            discovery.summarize(changed, warm)
        rows[3]['accepted'] = False
        # One native failure need not fail coverage if another native succeeds.
        for r in rows:
            if r['route_id'] == 'norm_discovery':
                r['accepted'] = False
        self.assertEqual(discovery.summarize(rows, warm)['decision'], 'CAPABILITY_UNREACHED')

    def test_nonfinite_proposal_rejected(self):
        with self.assertRaises(ValueError):
            discovery.propose(np.array([[float('nan')]]), np.ones(1), np.ones(1))
