"""Frozen objective/legacy-namespace guards, no new scientific observations."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NorthStarFreezeTests(unittest.TestCase):
    def test_all_eleven_user_sections_retained(self):
        text = (ROOT / 'docs/research/frozen_north_star.md').read_text()
        for i in range(1, 12):
            self.assertIn(f'## {i}. ', text)
        self.assertIn('Frontier-level problem solving with minimum necessary computation', text)
        self.assertIn('No component earns permanence', text)
        self.assertIn('Do not learn what can be derived more cheaply', text)

    def test_exact_v104_gate_text_remains_an_immutable_legacy_annex(self):
        raw = (ROOT / 'docs/research/legacy_core_question_gates_v104.md').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'd48101642e48f8878ac35d94a303c5c9fef3bc14d9a3f3a12da2b00f43277c94')

    def test_current_q5_q6_not_historical_closure_flags(self):
        text = (ROOT / 'docs/research/core_question_gates.md').read_text()
        self.assertIn('north_star_2026_10_02', text)
        self.assertIn('archived `global_q5_closed` field denotes LEGACY Q5', text)
        self.assertIn('| Q5 | Complete discovery+execution+verification+retry+routing', text)
        self.assertIn('| Q6 | Gains persist on unseen tasks', text)
        self.assertIn('| Q7 | A small complete NEUMANN system', text)

    def test_primary_frontier_contract_is_not_an_armed_or_paid_run(self):
        text = (ROOT / 'docs/research/frontier_gap_evaluation.md').read_text()
        self.assertIn('CONTRACT ONLY / UNARMED', text)
        self.assertIn('Synthetic unit fixtures are never actual Frontier Gap evidence', text)
        self.assertIn('before the first real run', text)
        readme = (ROOT / 'README.md').read_text()
        self.assertLess(readme.index('Frozen North Star'), readme.index('Historical structural-compression'))


if __name__ == '__main__':
    unittest.main()
