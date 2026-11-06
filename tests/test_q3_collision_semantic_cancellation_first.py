"""No training, original source access or Z3 in the contract tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.q3.collision_semantic_cancellation_first import (
    CONTRACT, first_readonly
)
from research.q3.counterexample_representation_grower import count_source_reads,task_from


class FrozenSemanticRelevanceTests(unittest.TestCase):
    def test_original_FIRST_sha_and_new_cohort_frozen(self):
        cfg=json.loads(CONTRACT.read_text())
        self.assertEqual(cfg["original_first"]["run"],42204120156)
        self.assertEqual(cfg["original_first"]["checkpoint_sha256"],
            "0e8f31b31e89f211455634fa460605df6d6f53aa67bdf75629b692320f20d276")
        self.assertEqual(len(cfg["preregistered_heldout_not_in_initial_first"]),6)
        self.assertTrue(cfg["model_frozen_no_retraining"])
        self.assertEqual(cfg["actual_run"],"NOT_RUN")
        self.assertEqual(cfg["global_Q3"],"OPEN")

    def test_lexical_source_mention_is_not_semantic_relevance(self):
        cfg=json.loads(CONTRACT.read_text())
        for row in cfg["preregistered_heldout_not_in_initial_first"]:
            self.assertGreater(count_source_reads(task_from(row)["expr"]),0)
        # Z3 determines semantic irrelevance; no expected H1 label in student.

    def test_wrong_first_fails_before_any_retrain_or_oracle(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"wrong.json"
            p.write_text("{}")
            with patch("research.q3.collision_semantic_cancellation_first.solver") as forbidden:
                with self.assertRaises(ValueError):
                    first_readonly(p,Path(folder)/"report.json")
                forbidden.assert_not_called()


if __name__=="__main__":
    unittest.main()
