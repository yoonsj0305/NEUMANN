"""New preparation boundaries only; no historical studies or model calls."""
import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "colab_receipt", ROOT / "experiments/am2_colab_hardware_receipt.py")
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class Preparation(unittest.TestCase):
    def test_unconfirmed_entitlement_does_not_probe(self):
        with patch.object(R, "load_cp1", side_effect=AssertionError("must not probe")):
            r = R.measure_hardware(False)
        self.assertEqual(r["status"], "BLOCKED_FREE_ENTITLEMENT_UNCONFIRMED")
        self.assertIsNone(r["telemetry"]["free_device_memory_bytes"])
        self.assertEqual(r["model_calls"], 0)

    def test_defaults_are_not_hardware_evidence(self):
        r = R.initial_receipt()
        self.assertIsNone(r["measured_at_utc"])
        self.assertIsNone(r["actual_monetary_charge"])
        self.assertFalse(r["inference_authorized_by_this_receipt"])

    def test_write_once_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "first.json"
            R.write_once(p, {"first": True})
            before = p.read_bytes()
            with self.assertRaises(FileExistsError):
                R.write_once(p, {"first": False})
            self.assertEqual(p.read_bytes(), before)

    def test_cli_no_confirmation_retains_blocked_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "new"
            with patch.object(sys, "argv", ["receipt", "--out", str(out)]):
                self.assertEqual(R.main(), 2)
            r = json.loads((out / "GPU_QUALIFICATION.json").read_text())
            self.assertEqual(r["model_calls"], 0)
            with patch.object(sys, "argv", ["receipt", "--out", str(out)]):
                with self.assertRaises(FileExistsError):
                    R.main()

    def test_no_neural_executor_or_package_install(self):
        tree = ast.parse((ROOT / "experiments/am2_colab_hardware_receipt.py").read_text())
        calls = {n.func.attr for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertFalse(calls & {"generate", "from_pretrained", "snapshot_download", "fit"})

    def test_receipt_uses_original_cp1_function(self):
        cp1 = R.load_cp1()
        self.assertEqual(cp1.MIN_VRAM_BYTES, 14 * 1024**3)
        self.assertTrue(callable(cp1.probe_native_bf16))


if __name__ == "__main__":
    unittest.main()
