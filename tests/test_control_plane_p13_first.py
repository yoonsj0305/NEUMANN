"""First-only CPU diagnostic fixtures; actual fresh rows are not routed here."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from neumann1.control_plane_v1 import snapshot
from experiments.control_plane_p13_catalog import catalog
from experiments.control_plane_p13_first import (IDS, ROOT, PUBLIC, REFERENCES, REGISTRATION,
    check_construction, registration, run, replay, package, decision, write_new)
from tests.test_control_plane_p13 import math_view, mixed_view

HEAD="a"*40


def fixtures():
    rows=[]; refs=[]
    for i,task_id in enumerate(IDS):
        if i<12: v=math_view(); status="SELECTED"; eligible=["ARITHMETIC"]; selected="ARITHMETIC"
        elif i<20: v=math_view(); del v["public"]["bindings"]; status="REJECTED"; eligible=[]; selected=None
        elif i<22: v=mixed_view(); status="NEEDS_SEMANTIC_FALLBACK"; eligible=["ARITHMETIC","CSP"]; selected=None
        else:
            v={"instruction":"Synthetic raw obligation","public":{"query":"Synthetic query"}}
            status="NEEDS_SEMANTIC_INTERPRETATION"; eligible=["DIRECT"]; selected=None
        rows.append({"task_id":task_id,"view":v})
        refs.append({"task_id":task_id,"status":status,"admissible_routes":eligible,"selected_route":selected})
    return rows,refs


def repin(path):
    terminal=json.loads((path/"terminal.json").read_bytes())
    terminal["files"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.glob("*.json") if p.name!="terminal.json"}
    (path/"terminal.json").write_text(json.dumps(terminal))


class FirstContracts(unittest.TestCase):
    def test_catalog_hashes_and_construction_only_no_candidate_route_run(self):
        rows,refs=catalog()
        self.assertEqual(rows,json.loads(PUBLIC.read_bytes())["rows"])
        self.assertEqual(refs,json.loads(REFERENCES.read_bytes())["rows"])
        with patch("experiments.control_plane_p13_first.route",side_effect=AssertionError("no route run in construction")):
            receipt=check_construction()
        self.assertEqual(receipt["positive_construction_controls"],12)
        self.assertEqual(receipt["negative_checker_controls"],12)
        self.assertEqual(receipt["compared_prior_rows"],27)
        self.assertFalse(receipt["routing_diagnostic_run"])
        self.assertFalse(registration()[0]["provenance"]["first_diagnostic_seen_at_registration"])

    def test_source_drift_is_not_silently_repaired(self):
        reg=json.loads(REGISTRATION.read_bytes()); reg["source_sha256"]["neumann1/control_plane_p13.py"]="0"*64
        with patch("experiments.control_plane_p13_first.REGISTRATION") as p:
            p.read_bytes.return_value=json.dumps(reg).encode()
            with self.assertRaises(ValueError): registration()

    def test_first_complete_fixture_replay_and_exclusive_directory(self):
        rows,refs=fixtures()
        with tempfile.TemporaryDirectory() as tmp, patch("experiments.control_plane_p13_first.registration",return_value=({"fixture":True},rows)), \
             patch("experiments.control_plane_p13_first.REFERENCES") as reference, \
             patch("experiments.control_plane_p13_first.subprocess.check_output",return_value=HEAD), \
             patch("experiments.control_plane_p13_first.subprocess.run"):
            reference.read_bytes.return_value=json.dumps({"rows":refs}).encode()
            path=Path(tmp)/"first"; result=run(path,HEAD)
            self.assertEqual(result["decision"]["verdict"],"PASS")
            self.assertTrue(replay(path)["integrity_valid"])
            self.assertEqual(result["neural_forward_calls"],0)
            for k in ("p2_registration_admitted","p2_admitted","decision3_admitted"):
                self.assertFalse(result["decision"][k])
            with self.assertRaises(FileExistsError): run(path,HEAD)

    def test_git_mismatch_retains_incomplete_first_and_blocks_admission(self):
        rows,refs=fixtures()
        with tempfile.TemporaryDirectory() as tmp, patch("experiments.control_plane_p13_first.registration",return_value=({},rows)), \
             patch("experiments.control_plane_p13_first.subprocess.check_output",return_value="b"*40):
            path=Path(tmp)/"first"; result=run(path,HEAD)
            self.assertEqual(result["status"],"INCOMPLETE")
            self.assertEqual(result["decision"]["verdict"],"NOT_EVALUATED")
            self.assertTrue((path/"terminal.json").exists())
            with self.assertRaises(FileExistsError): run(path,HEAD)

    def test_replacement_ci_attempt_and_invalid_source_pin_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): run(Path(tmp)/"bad","main")
            with patch.dict("os.environ",{"GITHUB_RUN_ATTEMPT":"2"}):
                with self.assertRaises(ValueError): run(Path(tmp)/"rerun",HEAD)

    def test_replay_rejects_rehashed_cached_route_and_admission_counter_cost_tamper(self):
        rows,refs=fixtures()
        for fault in ("route","admission","counter","cost","nan","manifest","forbidden","coverage"):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp, \
                 patch("experiments.control_plane_p13_first.registration",return_value=({"fixture":True},rows)), \
                 patch("experiments.control_plane_p13_first.REFERENCES") as reference, \
                 patch("experiments.control_plane_p13_first.subprocess.check_output",return_value=HEAD), \
                 patch("experiments.control_plane_p13_first.subprocess.run"):
                reference.read_bytes.return_value=json.dumps({"rows":refs}).encode()
                path=Path(tmp)/"first"; run(path,HEAD)
                file=path/("task_00.json" if fault in ("route","nan","coverage") else "manifest.json" if fault=="manifest" else "report.json")
                v=json.loads(file.read_bytes())
                if fault=="route": v["selected_route"]="CSP"
                elif fault=="admission": v["decision"]["p2_registration_admitted"]=True
                elif fault=="counter": v["neural_forward_calls"]=1
                elif fault=="cost": v["route_wall_sum_ms"]+=1
                elif fault=="nan": v["complete_ms"]=float("nan")
                elif fault=="manifest": v["public_rows"][0]["view"]["public"]["bindings"]["a"]=9
                elif fault=="forbidden": v["weights_loaded"]=True
                else: v["task_id"]="different"
                file.write_text(json.dumps(v)); repin(path)
                with self.assertRaises(ValueError): replay(path)


if __name__=="__main__": unittest.main()
