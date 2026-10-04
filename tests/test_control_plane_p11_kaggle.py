"""Model-free bootstrap orchestration tests; never evidence from real Gemma."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/control_plane_p11_kaggle.py"
spec = importlib.util.spec_from_file_location("p11_kaggle", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def fake(self, working, verdict="PASS", fail=None, terminal=True, replay_code=0):
        calls = []
        def execute(args, *, cwd, log, timeout, on_started):
            calls.append(args)
            on_started(12345678)
            with log.open("ab") as out:
                out.write(b"synthetic command log\n")
            if fail is not None and fail[0] in args:
                if isinstance(fail[1], BaseException):
                    raise fail[1]
                return fail[1]
            if args[:2] == ["git", "clone"]:
                (working / bootstrap.CHECKOUT).mkdir()
            if "experiments.control_plane_p11_dev" in args and "--directory" in args:
                output = working / bootstrap.OUTPUT
                output.mkdir()
                (output / "task_00_started.json").write_bytes(b'{"partial":true}\n')
                report = {"development_only": True, "decision": {
                    "verdict": verdict, "p2_admitted": False, "decision3_admitted": False}}
                (output / "report.json").write_text(json.dumps(report))
                if terminal:
                    (output / "terminal.json").write_text("{}\n")
                return 0 if verdict == "PASS" else 2
            if "experiments.control_plane_p11_replay" in args:
                return replay_code
            return 0
        return execute, calls

    def assert_archive(self, working):
        archive = working / bootstrap.ARCHIVE
        receipt = json.loads((working / bootstrap.HASH_RECEIPT).read_bytes())
        self.assertEqual(receipt["archive_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        with zipfile.ZipFile(archive) as z:
            manifest = json.loads(z.read("archive_manifest.json"))
            self.assertEqual(set(z.namelist()), set(manifest["members"]) | {"archive_manifest.json"})
            for name, pin in manifest["members"].items():
                raw = z.read(name)
                self.assertEqual(pin, {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
            self.assertFalse(manifest["p2_admitted"])
            self.assertFalse(manifest["decision3_admitted"])
        return archive.read_bytes()

    def test_pinned_execution_and_no_old_p1_or_capability_path(self):
        with tempfile.TemporaryDirectory() as root:
            working = Path(root)
            execute, calls = self.fake(working)
            data, _ = bootstrap.run(working, execute)
            self.assertEqual(data["status"], "FINISHED")
            self.assertEqual(data["runtime_head"], "4e6db9926a27c94f63c8d539d0c6e57c34b49336")
            self.assertEqual(data["bootstrap_sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
            self.assertTrue(all(s["wall_ms"] >= 0 for s in data["stages"]))
            runner = next(c for c in calls if "--directory" in c and "experiments.control_plane_p11_dev" in c)
            self.assertEqual(runner[-2:], ["--frozen-head", bootstrap.RUNTIME_HEAD])
            self.assertNotIn("experiments.control_plane_p1_first", str(calls))
            pip = next(c for c in calls if "install" in c)
            self.assertIn("-c", pip)
            self.assertNotIn("torch==2.11.0+cu128", pip)
            self.assert_archive(working)

    def test_environment_failure_preserved_before_clone_and_no_retry(self):
        with tempfile.TemporaryDirectory() as root:
            working = Path(root)
            execute, calls = self.fake(working, fail=("-c", 1))
            data, _ = bootstrap.run(working, execute)
            self.assertEqual(data["status"], "FAILED_OR_INTERRUPTED")
            self.assertEqual(len(calls), 1)
            original = self.assert_archive(working)
            setup = (working / bootstrap.SETUP).read_bytes()
            with self.assertRaises(RuntimeError):
                bootstrap.run(working, execute)
            self.assertEqual((working / bootstrap.ARCHIVE).read_bytes(), original)
            self.assertEqual((working / bootstrap.SETUP).read_bytes(), setup)
            self.assertEqual(len(calls), 1)

    def test_nonpass_still_replayed_and_packaged(self):
        with tempfile.TemporaryDirectory() as root:
            working = Path(root)
            execute, calls = self.fake(working, verdict="FAIL")
            data, _ = bootstrap.run(working, execute)
            self.assertEqual(data["status"], "FINISHED_NONPASS")
            self.assertEqual(data["runner_exit_code"], 2)
            self.assertEqual(data["replay_exit_code"], 0)
            self.assertFalse(data["p2_admitted"])
            self.assert_archive(working)

    def test_timeout_and_keyboard_interrupt_package_first_bytes(self):
        for exc in (subprocess.TimeoutExpired("synthetic", 1), KeyboardInterrupt()):
            with self.subTest(exc=type(exc).__name__), tempfile.TemporaryDirectory() as root:
                working = Path(root)
                execute, calls = self.fake(working, fail=("--check-registration", exc))
                data, _ = bootstrap.run(working, execute)
                self.assertEqual(data["status"], "FAILED_OR_INTERRUPTED")
                self.assertIsNone(data["active_child_pid"])
                self.assertFalse(any("--directory" in c for c in calls))
                self.assert_archive(working)

    def test_missing_terminal_and_replay_failure_do_not_report_finished(self):
        for options in ({"terminal": False}, {"replay_code": 1}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as root:
                working = Path(root)
                execute, _ = self.fake(working, **options)
                data, _ = bootstrap.run(working, execute)
                self.assertEqual(data["status"], "FAILED_OR_INTERRUPTED")
                self.assert_archive(working)

    def test_receipt_or_checkout_blocks_all_commands(self):
        for name in (bootstrap.HASH_RECEIPT, bootstrap.CHECKOUT, bootstrap.OUTPUT):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as root:
                working = Path(root)
                (working / name).write_bytes(b"retained original")
                execute, calls = self.fake(working)
                with self.assertRaises(RuntimeError):
                    bootstrap.run(working, execute)
                self.assertEqual(calls, [])
                self.assertEqual((working / name).read_bytes(), b"retained original")

    def test_evidence_only_recovery_and_live_child_block(self):
        with tempfile.TemporaryDirectory() as root:
            working = Path(root)
            bootstrap.write_json(working / bootstrap.SETUP, {"runtime_head": bootstrap.RUNTIME_HEAD,
                                 "development_only": True, "active_child_pid": 123,
                                 "bootstrap_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest()}, exclusive=True)
            with patch.object(bootstrap.os, "kill", return_value=None):
                with self.assertRaises(RuntimeError):
                    bootstrap.package_existing(working)
            self.assertFalse((working / bootstrap.ARCHIVE).exists())
            with patch.object(bootstrap.os, "kill", side_effect=ProcessLookupError):
                bootstrap.package_existing(working)
            original = self.assert_archive(working)
            with self.assertRaises(RuntimeError):
                bootstrap.package(working)
            self.assertEqual((working / bootstrap.ARCHIVE).read_bytes(), original)

    def test_real_subprocess_timeout_retains_log_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as root:
            log = Path(root) / "timeout.log"
            pids = []
            with self.assertRaises(subprocess.TimeoutExpired):
                bootstrap.command([bootstrap.sys.executable, "-u", "-c",
                                  "import time; print('retained'); time.sleep(10)"],
                                  cwd=Path(root), log=log, timeout=0.2, on_started=pids.append)
            self.assertIn(b"retained", log.read_bytes())
            with self.assertRaises(ProcessLookupError):
                bootstrap.os.kill(pids[0], 0)

    def test_false_admission_is_blocked_even_if_replay_exits_zero(self):
        with tempfile.TemporaryDirectory() as root:
            working = Path(root)
            execute, _ = self.fake(working)
            def corrupt(*args, **kwargs):
                code = execute(*args, **kwargs)
                if "experiments.control_plane_p11_replay" in args[0]:
                    path = working / bootstrap.OUTPUT / "report.json"
                    data = json.loads(path.read_bytes())
                    data["decision"]["p2_admitted"] = True
                    path.write_text(json.dumps(data))
                return code
            data, _ = bootstrap.run(working, corrupt)
            self.assertEqual(data["status"], "FAILED_OR_INTERRUPTED")
            self.assert_archive(working)


if __name__ == "__main__":
    unittest.main()
