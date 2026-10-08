"""Goal semantics and first-evidence tests; zero model construction/solving."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('diagnostic', root / 'probabilistic_native_diagnostic.py')
diagnostic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostic)


class ContractTests(unittest.TestCase):
    def test_max_preserves_all_initial_states(self):
        expression = {'op': 'filter', 'states': {'op': 'initial'}, 'fun': 'max'}
        self.assertEqual(diagnostic.reduce_goal(['1/2', '7/3', '1/6'], expression), '7/3')

    def test_exact_reduction(self):
        expression = {'op': 'filter', 'states': {'op': 'initial'}, 'fun': 'values'}
        self.assertEqual(diagnostic.reduce_goal(['2/6'], expression), '1/3')

    def test_scalar_refuses_multiple_initial_values(self):
        with self.assertRaises(AssertionError):
            diagnostic.reduce_goal(['1', '2'], {'op': 'filter', 'states': {'op': 'initial'}, 'fun': 'values'})

    def test_non_initial_filter_refused(self):
        with self.assertRaises(AssertionError):
            diagnostic.reduce_goal(['1'], {'op': 'filter', 'states': True, 'fun': 'max'})

    def test_unsupported_aggregation_refused(self):
        with self.assertRaises(ValueError):
            diagnostic.reduce_goal(['1'], {'op': 'filter', 'states': {'op': 'initial'}, 'fun': 'avg'})

    def test_empty_initial_set_refused(self):
        with self.assertRaises(AssertionError):
            diagnostic.reduce_goal([], {'op': 'filter', 'states': {'op': 'initial'}, 'fun': 'max'})

    def test_first_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'first.json'
            diagnostic.write_first(p, {'a': 1})
            with self.assertRaises(FileExistsError):
                diagnostic.write_first(p, {'a': 2})
            self.assertEqual(json.loads(p.read_text()), {'a': 1})

    def test_oracle_payload_rejected_before_native_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'request.json'
            p.write_text(json.dumps({'case': {'expected_exact': '1/2'}}))
            with self.assertRaises(AssertionError):
                diagnostic.worker(p)

    def test_cost_blind_manifest_keeps_13_requests_and_9_families(self):
        rows = json.loads((root / 'source-cases-first.json').read_text())['cases']
        self.assertEqual(len(rows), 13)
        self.assertEqual(len({r['family'] for r in rows}), 9)
        self.assertEqual(len({r['case_id'] for r in rows}), 13)


if __name__ == '__main__':
    unittest.main(verbosity=2)
