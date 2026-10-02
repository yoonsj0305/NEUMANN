"""First-byte authority tests only: no new inputs, models, solves or timing."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.q5_first_archive import DECISION, SOURCE_HEAD, result_pin, source_pin
from experiments.q5_register import evidence_module

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs/experiments/results/q5_first_sources"
RESULTS = ROOT / "docs/experiments/results/q5_first_evaluation"


class Q5FirstArchiveTests(unittest.TestCase):
    def test_first_result_metadata_and_receipts(self):
        report, rows = result_pin(RESULTS)
        self.assertEqual(report["summary"]["decision"], DECISION)
        self.assertEqual(report["summary"]["observations"], 1536)
        self.assertEqual(report["summary"]["failures_including_warmup"], 32)
        self.assertEqual(sum(r["kind"] == "observation" for r in rows), 1536)
        self.assertFalse(report["global_q5_closed"])

    def test_first_report_reserialization_is_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            report = json.loads((RESULTS / "report.json").read_text())
            (target / "report.json").write_text(json.dumps(report, indent=2))
            with self.assertRaisesRegex(ValueError, "report replacement"):
                result_pin(target)

    def test_first_source_metadata_and_receipts(self):
        manifest = source_pin(SOURCES)
        self.assertEqual(manifest["frozen_head"], SOURCE_HEAD)
        self.assertEqual(len(manifest["cases"]), 96)
        self.assertFalse(manifest["rerun"])
        self.assertFalse(manifest["model_access"])
        self.assertFalse(manifest["route_evaluation"])

    def test_manifest_replacement_rejected_before_scientific_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            # Even a semantically identical reserialization is not first bytes.
            manifest = json.loads((SOURCES / "manifest.json").read_text())
            (target / "manifest.json").write_text(json.dumps(manifest, indent=2))
            with self.assertRaisesRegex(ValueError, "manifest replacement"):
                source_pin(target)

    def test_terminal_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in ("manifest.json", "events.jsonl", "terminal.json"):
                shutil.copyfile(SOURCES / name, target / name)
            terminal = json.loads((target / "terminal.json").read_text())
            terminal["last_sha256"] = "0" * 64
            (target / "terminal.json").write_text(json.dumps(terminal))
            with self.assertRaises(ValueError):
                source_pin(target)

    def test_authority_import_is_execution_free(self):
        process = subprocess.run([sys.executable, "-c",
            "import sys; import experiments.q5_first_archive; "
            "assert not any(n in sys.modules for n in ('numpy','scipy','torch','highspy'))"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_internally_valid_rehashed_chain_is_not_first_authority(self):
        ev = evidence_module()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copyfile(SOURCES / "manifest.json", target / "manifest.json")
            rows, terminal = ev.read_events(SOURCES)
            rows[0]["payload"]["replacement_fixture"] = True
            previous = "0" * 64
            rewritten = []
            for row in rows:
                core = {k: row[k] for k in ("index", "previous", "kind", "payload")}
                core["previous"] = previous
                previous = ev.digest(ev.canonical(core))
                rewritten.append({**core, "sha256": previous})
            (target / "events.jsonl").write_bytes(b"".join(ev.canonical(r) + b"\n" for r in rewritten))
            terminal["last_sha256"] = previous
            (target / "terminal.json").write_bytes(ev.canonical(terminal) + b"\n")
            ev.read_events(target)  # Internally valid is insufficient.
            with self.assertRaisesRegex(ValueError, "receipt replacement"):
                source_pin(target)


if __name__ == "__main__":
    unittest.main()
