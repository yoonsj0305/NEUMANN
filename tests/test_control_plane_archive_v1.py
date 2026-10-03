import json
import tempfile
import unittest
from pathlib import Path
import shutil

from experiments.control_plane_p0_v1 import ARCHIVE, replay_failure


class FirstFailureBytes(unittest.TestCase):
    def test_original_complete_failure_replays_without_model(self):
        result = replay_failure()
        self.assertTrue(result["valid"])
        self.assertEqual(result["model_calls"], 72)
        self.assertFalse(result["model_inference_performed"])

    def test_single_original_byte_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "archive"
            shutil.copytree(ARCHIVE, directory)
            with (directory / "query_00.json").open("ab") as out:
                out.write(b" ")
            with self.assertRaisesRegex(ValueError, "byte drift"):
                replay_failure(directory)


if __name__ == "__main__":
    unittest.main()
