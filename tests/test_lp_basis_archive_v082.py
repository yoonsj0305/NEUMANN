"""v0.0.82 immutable first-audit archive contracts."""
import hashlib
import json
from pathlib import Path
import unittest

from neumann1.lp_basis_headroom_v082 import (
    array_digest,
    generate,
    specifications,
    summarize,
)


ARCHIVE = Path("docs/experiments/results/v082_first_audit.json")
EXPECTED_SHA256 = "2e3b3ca23a27c1d7f8176bf1b33c4c7edb4f077743cc7a2505e58a53fd701149"


class LPBasisArchiveV082Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = ARCHIVE.read_bytes()
        cls.raw = raw
        cls.report = json.loads(raw)
        cls.summary = cls.report["summary"]

    def test_exact_first_audit_bytes_are_frozen(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), EXPECTED_SHA256)

    def test_complete_capability_and_frozen_decision(self):
        self.assertEqual(len(self.report["warmups"]), 48)
        self.assertEqual(len(self.report["rows"]), 240)
        self.assertTrue(all(row["accepted"] for row in self.report["warmups"]))
        self.assertTrue(all(row["accepted"] for row in self.report["rows"]))
        self.assertEqual(
            self.summary["decision"],
            "MECHANISM_HEADROOM_PRESENT_MODEL_TRAINING_NOT_YET_ADMITTED",
        )
        self.assertEqual(self.summary["accepted"], 240)
        self.assertEqual(self.summary["twenty_percent_win_cases"], 12)
        self.assertEqual(self.summary["required_win_cases"], 9)
        self.assertLessEqual(
            self.summary["basis_oracle_vs_direct_per_case_oracle_ratio"], 0.80
        )
        self.assertEqual(self.summary["q3"], "OPEN")
        self.assertEqual(self.summary["q4"], "OPEN")

    def test_archive_summary_recomputes_from_preserved_rows(self):
        recomputed = summarize(self.report["rows"])
        self.assertEqual(recomputed, self.summary)

    def test_source_hashes_reproduce_from_frozen_generator(self):
        archived = {entry["id"]: entry for entry in self.report["source"]}
        self.assertEqual(set(archived), {spec["id"] for spec in specifications()})
        for spec in specifications():
            case = generate(spec)
            expected = archived[spec["id"]]["sha256"]
            self.assertEqual(array_digest(case["A"]), expected["A"])
            self.assertEqual(array_digest(case["b"]), expected["b"])
            self.assertEqual(array_digest(case["c"]), expected["c"])
            self.assertEqual(array_digest(case["basis"]), expected["basis"])


if __name__ == "__main__":
    unittest.main()
