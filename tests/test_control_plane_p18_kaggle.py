"""Bootstrap faults retain evidence without any subprocess/model execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

PATH=Path(__file__).resolve().parents[1]/"scripts/control_plane_p18_kaggle.py"
spec=importlib.util.spec_from_file_location("p18_bootstrap_test",PATH)
bootstrap=importlib.util.module_from_spec(spec); spec.loader.exec_module(bootstrap)


class BootstrapContracts(unittest.TestCase):
    def test_missing_head_does_no_work(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD",""):
            with self.assertRaises(ValueError): bootstrap.run(Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_first_stage_failure_packaged_and_never_replaced(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
            def fail(args,**kw): return 1
            setup,receipt=bootstrap.run(Path(tmp),execute=fail,launcher_wall_ms=1)
            self.assertEqual(setup["status"],"FAILED_OR_INTERRUPTED")
            self.assertFalse(setup["p2_admitted"]); self.assertIsNone(setup["active_child_pid"])
            raw=(Path(tmp)/bootstrap.ARCHIVE).read_bytes()
            with zipfile.ZipFile(Path(tmp)/bootstrap.ARCHIVE) as z:
                self.assertIn("archive_manifest.json",z.namelist())
            with self.assertRaises(RuntimeError): bootstrap.run(Path(tmp),execute=fail)
            with self.assertRaises(RuntimeError): bootstrap.package(Path(tmp))
            self.assertEqual((Path(tmp)/bootstrap.ARCHIVE).read_bytes(),raw)

    def test_recovery_refuses_live_child(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(bootstrap,"RUNTIME_HEAD","a"*40):
            data={"runtime_head":"a"*40,"development_only":True,"bootstrap_sha256":bootstrap.digest_file(PATH),"active_child_pid":123}
            (Path(tmp)/bootstrap.SETUP).write_text(json.dumps(data))
            with patch.object(bootstrap.os,"kill",return_value=None):
                with self.assertRaises(RuntimeError): bootstrap.package_existing(Path(tmp))
            self.assertFalse((Path(tmp)/bootstrap.ARCHIVE).exists())


if __name__ == "__main__": unittest.main()
