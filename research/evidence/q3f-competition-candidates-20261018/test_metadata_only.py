"""No-leak metadata audit controls: no original SMT2 reads in tests."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("q3f_first",HERE/"first_metadata_only_escrow.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CompetitionMetadataControls(unittest.TestCase):
    def test_2025_absent_expected(self):
        yml=b"input_files: p.smt2\nproperties:\n- property_file: ../properties/check-sat.prp\n"
        self.assertEqual(m.parse_metadata(yml,"2025"),"p.smt2")
    def test_2025_any_decision_excluded(self):
        yml=b"input_files: p.smt2\nproperties:\n- property_file: ../properties/check-sat.prp\n  expected_verdict: true\n"
        with self.assertRaises(ValueError):m.parse_metadata(yml,"2025")
    def test_2026_placeholder_is_not_a_solved_result(self):
        yml=b"input_files: p.smt2\nproperties:\n- property_file: ../properties/check-sat.prp\n  expected_verdict: true\n  # placeholder verdict (auto-added)\n"
        self.assertEqual(m.parse_metadata(yml,"2026"),"p.smt2")
        for marker in ("  majority_vote_verdict: sat\n","  sat:\n  - solver\n"):
            with self.subTest(marker=marker):
                with self.assertRaises(ValueError):
                    m.parse_metadata(yml+marker.encode(),"2026")
    def test_2026_no_placeholder_is_not_accepted(self):
        yml=b"input_files: p.smt2\nproperties:\n- property_file: ../properties/check-sat.prp\n  expected_verdict: true\n"
        with self.assertRaises(ValueError):m.parse_metadata(yml,"2026")
    def test_no_two_input_files(self):
        yml=b"input_files: one.smt2\ninput_files: two.smt2\nproperties:\n- property_file: ../properties/check-sat.prp\n"
        with self.assertRaises(ValueError):m.parse_metadata(yml,"2025")

if __name__=="__main__":unittest.main()
