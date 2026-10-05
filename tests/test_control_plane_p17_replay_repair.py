"""Post-result regression tests for P1.7 replay repair."""
import unittest

from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p17_registration import registration
from experiments.control_plane_p17_replay_repair import replay_record_repaired
from neumann1.control_plane_p17 import interpret_and_execute


class ReplayRepairContracts(unittest.TestCase):
    def test_execution_timer_is_not_semantic_identity(self):
        _, rows, refs = registration()
        row, ref = rows[0], refs[0]

        def forbidden():
            raise AssertionError("unique path must not construct selector")

        record = interpret_and_execute(
            row["view"], _executor, _hidden_verifier(ref), forbidden
        )
        self.assertTrue(record["accepted"])
        self.assertIsNotNone(record["execution"])

        record["execution"]["complete_ms"] += 12345.0
        replay_record_repaired(row, ref, record)

    def test_execution_answer_corruption_still_fails(self):
        _, rows, refs = registration()
        row, ref = rows[0], refs[0]

        def forbidden():
            raise AssertionError("unique path must not construct selector")

        record = interpret_and_execute(
            row["view"], _executor, _hidden_verifier(ref), forbidden
        )
        record["execution"]["answer"] = "not-the-original-answer"
        with self.assertRaises(ValueError):
            replay_record_repaired(row, ref, record)


if __name__ == "__main__":
    unittest.main()
