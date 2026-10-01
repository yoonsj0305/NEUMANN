"""Non-time fixtures and solver-free archive replay; no diagnostic in CI."""
import copy
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from neumann1 import lp_program_parity_v085 as p


class ProgramParityTests(unittest.TestCase):
    def test_retained_diagnostic_replays_without_any_solving(self):
        directory = Path(__file__).resolve().parents[1] / 'docs/experiments/results'
        manifest = json.loads((directory / 'v085_diagnostic.manifest.json').read_text())
        self.assertEqual(manifest['completed']['json_sha256'],
                         'ba29b88cb62dae39b6282d06636fc7ac3903d50c8120915a61c5080a3675e86e')
        original = p.load_source(directory / 'v084_first_audit.manifest.json')
        report = p.load_diagnostic(directory / 'v085_diagnostic.manifest.json')
        with patch.object(p.source, 'lu_factor', side_effect=AssertionError('LU forbidden')), \
             patch.object(p.source, 'linprog', side_effect=AssertionError('optimizer forbidden')), \
             patch.object(p.source.previous, 'generate_case', side_effect=AssertionError('generation forbidden')):
            p.validate_archive(report, original)
        self.assertEqual(report['summary'], {'pairs': 210, 'agreement': 210,
                                             'neumann_accepted': 36, 'direct_accepted': 36,
                                             'decision': p.DECISION, 'q3': 'OPEN', 'q4': 'OPEN'})
        failed = directory / manifest['failed_preflight']['name']
        self.assertEqual(hashlib.sha256(failed.read_bytes()).hexdigest(),
                         manifest['failed_preflight']['sha256'])
        with gzip.open(failed, 'rt') as stream:
            self.assertEqual(json.load(stream), {'execution_failed': "KeyError: 'python_major_minor'",
                                                 'do_not_overwrite': True})

    def raw(self):
        return {'A': np.array([[1., 0., 2.], [0., 1., 2.]]),
                'b': np.ones(2), 'c': np.array([0., 0., 1.])}

    def compare(self, raw, head):
        left = p.structural_route(**raw, head=head, native_fallback=False)
        right = p.direct_tool_program_route(**raw, head=head, native_fallback=False)
        self.assertEqual(left, right)
        return left

    def test_observable_input_only_and_closed_program(self):
        self.assertEqual(list(inspect.signature(p.structural_route).parameters),
                         ['A', 'b', 'c', 'head', 'native_fallback'])
        self.assertEqual(p.decode_tool_program(self.raw(), {'basis': [1, 0]}),
                         {'op': 'solve_basis_checked', 'basis': [1, 0]})
        row = p.execute_tool_program(**self.raw(), program={'op': 'eval', 'source': 'anything'},
                                     native_fallback=False)
        self.assertEqual(row['status'], 'INVALID_HEAD')
        self.assertEqual(row['ledger']['basis_calls'], 0)

    def test_valid_primal_dual_and_actual_call_ledger(self):
        row = self.compare(self.raw(), {'basis': [0, 1]})
        self.assertTrue(row['accepted'])
        self.assertEqual(row['candidate']['witness'], {'x': [1., 1., 0.], 'y': [0., 0.]})
        self.assertEqual(row['ledger'], {'basis_calls': 1, 'native_calls': 0,
                                       'original_certificate_calls': 1, 'decode_rejections': 0})
        self.assertNotIn('_ms', json.dumps(row))

    def test_singular_and_nonoptimal_are_retained_rejections(self):
        singular = {'A': np.array([[1., 1., 0.], [0., 0., 1.]]),
                    'b': np.ones(2), 'c': np.array([2., 1., 0.])}
        row = self.compare(singular, {'basis': [0, 1]})
        self.assertFalse(row['accepted'])
        self.assertEqual(row['ledger']['original_certificate_calls'], 0)
        self.assertIn('Singular', row['candidate']['error'])
        row = self.compare(self.raw(), {'basis': [0, 2]})
        self.assertFalse(row['accepted'])
        self.assertIsNotNone(row['candidate']['witness'])
        self.assertEqual(row['ledger']['original_certificate_calls'], 1)

    def test_malformed_heads_fail_closed_without_solver(self):
        heads = [None, [], {'basis': [0]}, {'basis': [0, 0]}, {'basis': [0, 3]},
                 {'basis': [-1, 0]}, {'basis': [False, 1]}, {'basis': [0., 1]},
                 {'basis': '01'}, {'basis': [0, 1], 'gold': True}, {'abstain': 1}]
        with patch.object(p.source, 'lu_factor', side_effect=AssertionError('solve forbidden')):
            for head in heads:
                row = self.compare(self.raw(), head)
                self.assertEqual(row['status'], 'INVALID_HEAD')
                self.assertEqual(row['ledger']['decode_rejections'], 1)

    def test_abstain_and_verifier_failure_calls_are_counted(self):
        row = self.compare(self.raw(), {'abstain': True})
        self.assertEqual(row['status'], 'ABSTAIN')
        self.assertEqual(sum(row['ledger'].values()), 0)
        with patch.object(p, 'verify_standard_form_certificate', side_effect=ValueError('fixture')):
            row = self.compare(self.raw(), {'basis': [0, 1]})
        self.assertFalse(row['accepted'])
        self.assertEqual(row['ledger']['original_certificate_calls'], 1)

    def test_fallback_integration_in_fresh_process(self):
        script = '''
import json
import numpy as np
from neumann1 import lp_program_parity_v085 as p
raw={'A':np.array([[1.,1.,0.],[0.,0.,1.]]),'b':np.ones(2),'c':np.array([2.,1.,0.])}
rows=[]
for head in ({'basis':[0,1]}, {'basis':[0,0]}, {'abstain':True}):
    left=p.structural_route(**raw,head=head)
    right=p.direct_tool_program_route(**raw,head=head)
    assert left==right
    assert left['accepted'] and left['fallback_used']
    rows.append(left)
print(json.dumps(rows))
'''
        result = subprocess.run([sys.executable, '-c', script], check=True,
                                capture_output=True, text=True, timeout=30)
        rows = json.loads(result.stdout)
        self.assertEqual([r['ledger']['native_calls'] for r in rows], [1, 1, 1])
        self.assertEqual([r['ledger']['basis_calls'] for r in rows], [1, 0, 0])
        self.assertTrue(all(r['ledger']['original_certificate_calls'] == 1 for r in rows))

    def original(self):
        raw = self.raw()
        return {'sources': [{'id': 'fixture', 'rows': 2, 'cols': 3,
                             'raw_sha256': p.source.input_digest(raw),
                             'arrays': {k: p.source.encode_array(v) for k, v in raw.items()}}],
                'records': [{'case_id': 'fixture', 'route_id': route, 'repeat': repeat,
                             'attempts': [{'indices': basis, 'method': f'basis_{i}'}
                                          for i, basis in enumerate(([0, 1], [0, 2]))]}
                            for route in p.protocol()['source_routes'] for repeat in (0, 1)]}

    def report(self):
        original = self.original()
        raw, pairs = p.prepare_pairs(original)
        records = []
        for pair in pairs:
            r = raw[pair['case_id']]
            records.append({**pair, 'direct_program': p.decode_tool_program(r, pair['head']),
                            'neumann': p.structural_route(**r, head=pair['head'], native_fallback=False),
                            'direct': p.direct_tool_program_route(**r, head=pair['head'], native_fallback=False)})
        return original, {'protocol': p.protocol(), 'records': records,
                          'environment': {**p.source.protocol()['runtime'], 'openblas_coretype': 'HASWELL',
                                          'threadpools': [{'num_threads': 1}]},
                          'summary': p.summarize(records)}

    def test_pair_collection_deduplicates_only_first_actual_attempts(self):
        original = self.original()
        _, pairs = p.prepare_pairs(original)
        self.assertEqual(len(pairs), 2)
        self.assertTrue(all(len(row['provenance']) == 2 for row in pairs))
        original['records'].pop(0)
        with self.assertRaises(ValueError): p.prepare_pairs(original)

    def test_runtime_schema_and_diagnostic_on_fixture(self):
        self.assertIn('python_major_minor', p._environment())
        environment = {**p.source.protocol()['runtime'], 'python': '3.11.fixture',
                       'openblas_coretype': 'HASWELL'}
        with patch.object(p.source, 'validate_archive'), \
             patch.object(p, '_environment', return_value=environment):
            report = p.run_diagnostic(self.original())
        p.validate_archive(report, self.original())
        self.assertEqual(report['summary']['agreement'], 2)
        environment['python_major_minor'] = [3, 12]
        with patch.object(p.source, 'validate_archive'), \
             patch.object(p, '_environment', return_value=environment), \
             patch.object(p.source, 'lu_factor', side_effect=AssertionError('solve forbidden')):
            with self.assertRaises(RuntimeError): p.run_diagnostic(self.original())

    def test_solver_free_archive_replays_rejected_and_accepted_witnesses(self):
        original, report = self.report()
        with patch.object(p.source, 'lu_factor', side_effect=AssertionError('LU forbidden')), \
             patch.object(p.source, 'linprog', side_effect=AssertionError('optimizer forbidden')), \
             patch.object(p.source.previous, 'generate_case', side_effect=AssertionError('generation forbidden')):
            p.validate_archive(report, original)
        self.assertEqual(report['summary']['agreement'], 2)
        self.assertEqual(report['summary']['neumann_accepted'], 1)
        self.assertEqual(report['summary']['decision'], p.DECISION)

    def test_archive_negative_controls(self):
        original, report = self.report()
        for mutation in ('witness', 'basis', 'coverage', 'ledger', 'summary', 'program', 'provenance', 'environment'):
            r = copy.deepcopy(report)
            row = r['records'][0]
            if mutation == 'witness': row['direct']['candidate']['witness']['x'][0] += 1.
            elif mutation == 'basis': row['head']['basis'] = [1, 2]
            elif mutation == 'coverage': r['records'].pop()
            elif mutation == 'ledger': row['direct']['ledger']['basis_calls'] = 0
            elif mutation == 'summary': r['summary']['q4'] = 'PASS'
            elif mutation == 'program': row['direct_program']['op'] = 'native_checked'
            elif mutation == 'provenance': row['provenance'].pop()
            else: r['environment']['threadpools'][0]['num_threads'] = 2
            with self.assertRaises(ValueError, msg=mutation): p.validate_archive(r, original)

    def test_changed_direct_witness_changes_agreement(self):
        _, report = self.report()
        report['records'][0]['direct']['candidate']['witness']['x'][0] += 1.
        summary = p.summarize(report['records'])
        self.assertEqual(summary['agreement'], 1)
        self.assertEqual(summary['decision'], 'PARITY_BUG_OR_CONTRACT_MISMATCH')

    def test_runner_reserves_output_before_source_load(self):
        import benchmark_v085
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'first.json.gz'
            path.touch()
            with patch.object(sys, 'argv', ['benchmark_v085.py', str(path)]), \
                 patch.object(benchmark_v085, 'load_source', side_effect=AssertionError('load forbidden')):
                with self.assertRaises(SystemExit): benchmark_v085.main()
            self.assertEqual(path.read_bytes(), b'')

    def test_manifest_and_source_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_text(json.dumps({'json_sha256': '0' * 64}))
            with self.assertRaises(ValueError): p.load_source(path)
            path.write_text(json.dumps({'format': 'neumann.lp-program-parity.archive.v1',
                                       'source_json_sha256': p.SOURCE_JSON_SHA256,
                                       'completed': {'name': '../outside'}}))
            with self.assertRaises(ValueError): p.load_diagnostic(path)

    def test_failed_first_attempt_is_not_erased(self):
        import benchmark_v085
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'first.json.gz'
            with patch.object(sys, 'argv', ['benchmark_v085.py', str(path)]), \
                 patch.object(benchmark_v085, 'load_source', side_effect=ValueError('fixture')):
                with self.assertRaises(ValueError): benchmark_v085.main()
            with gzip.open(path, 'rt') as stream:
                result = json.load(stream)
            self.assertTrue(result['do_not_overwrite'])
            self.assertIn('fixture', result['execution_failed'])


if __name__ == '__main__':
    unittest.main()
