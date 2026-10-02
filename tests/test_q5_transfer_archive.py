"""First v104 byte/receipt guards, never new registered sources or timing."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.q5_transfer_first_archive import pin,DECISIONS,FIRST_HEAD
from experiments.q5_register import evidence_module

ROOT=Path(__file__).resolve().parents[1]
FIRST=ROOT/'docs/experiments/results/v104_transfer_admission_first'


def copy_receipts(directory):
    for name in ('sources.json','report.json','events.jsonl','terminal.json','reservation.json'):
        shutil.copyfile(FIRST/name,Path(directory)/name)


class TransferFirstArchiveTests(unittest.TestCase):
    def test_original_first_decision_and_scope(self):
        manifest,report,events=pin(FIRST)
        self.assertEqual(manifest['frozen_head'],FIRST_HEAD)
        self.assertEqual(len(manifest['cases']),32)
        self.assertEqual(report['summary']['decisions'],DECISIONS)
        self.assertEqual(sum(r['kind']=='observation' for r in events),448)
        self.assertEqual(report['summary']['failed_observations'],0)
        self.assertFalse(report['summary']['global_q5_closed'])

    def test_semantically_identical_report_reserialization_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_receipts(directory)
            report=json.loads((FIRST/'report.json').read_text())
            (Path(directory)/'report.json').write_text(json.dumps(report,indent=2))
            with self.assertRaisesRegex(ValueError,'raw archive replacement'):pin(directory)

    def test_semantically_identical_source_reserialization_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_receipts(directory)
            source=json.loads((FIRST/'sources.json').read_text())
            (Path(directory)/'sources.json').write_text(json.dumps(source,indent=2))
            with self.assertRaisesRegex(ValueError,'raw archive replacement'):pin(directory)

    def test_changed_reservation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_receipts(directory)
            reservation=json.loads((FIRST/'reservation.json').read_text());reservation['rerun']=True
            (Path(directory)/'reservation.json').write_text(json.dumps(reservation))
            with self.assertRaisesRegex(ValueError,'receipt/decision replacement'):pin(directory)

    def test_rehashed_internal_chain_cannot_replace_first(self):
        ev=evidence_module()
        with tempfile.TemporaryDirectory() as directory:
            copy_receipts(directory);rows,terminal=ev.read_events(FIRST)
            rows[0]['payload']['changed_fixture']=True
            previous='0'*64;rewritten=[]
            for row in rows:
                core={k:row[k] for k in ('index','previous','kind','payload')};core['previous']=previous
                previous=ev.digest(ev.canonical(core));rewritten.append({**core,'sha256':previous})
            (Path(directory)/'events.jsonl').write_bytes(b''.join(ev.canonical(r)+b'\n' for r in rewritten))
            terminal['last_sha256']=previous
            (Path(directory)/'terminal.json').write_bytes(ev.canonical(terminal)+b'\n')
            ev.read_events(directory)
            with self.assertRaisesRegex(ValueError,'receipt/decision replacement'):pin(directory)

    def test_import_opens_no_scientific_execution_runtime(self):
        p=subprocess.run([sys.executable,'-c',"import sys; import experiments.q5_transfer_first_archive; assert not any(n in sys.modules for n in ('numpy','scipy','torch','highspy'))"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)


if __name__=='__main__':unittest.main()
