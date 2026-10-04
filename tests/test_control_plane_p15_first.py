"""Synthetic first-run, gate, raw replay, tamper and retention checks."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from neumann1.control_plane_v1 import snapshot, digest
from neumann1.control_plane_p15 import FrozenSketchCompiler, interpret_and_execute, contract
from experiments.control_plane_p14_dev import _executor, _hidden_verifier
from experiments.control_plane_p15_dev import evaluate, totals, run
from experiments.control_plane_p15_registration import registration, check_construction, BOUNDARY
from experiments.control_plane_p15_replay import replay, replay_record
from test_control_plane_p15 import FakeCore

SKETCHES=(
    "ARITHMETIC\nSTART 30\nDIV 5\nSUB 2\nMUL 9\nEND",
    "ARITHMETIC\nSTART 17\nADD 7\nDIV 3\nSUB 5/2\nEND",
    "ARITHMETIC\nSTART 19\nSUB 7\nADD 0.25\nDIV 7\nEND",
    "ARITHMETIC\nSTART 6\nMUL 4\nDIV 8\nSUB 1.5\nEND",
    "CSP\nDOMAIN M 1 2 3 4\nDOMAIN N 1 2 3 4\nDOMAIN O 1 2 3 4\nEQ M 3\nLT N M\nEQ O N\nEND",
    "CSP\nDOMAIN I 0 1 2\nDOMAIN J 0 1 2\nDOMAIN K 0 1 2\nDOMAIN L 0 1 2\nNE I K\nEQ J 2\nEQ K L\nLT I J\nEND",
    "CSP\nDOMAIN S -2 -1 0 1\nDOMAIN T -2 -1 0 1\nLE S T\nEQ T -1\nNE S T\nEND",
    "CSP\nDOMAIN P 0 1 2 3\nDOMAIN Q 0 1 2 3\nDOMAIN R 0 1 2 3\nEQ R 2\nNE P R\nLE Q R\nEQ P Q\nEND",
)


def records(sketches=SKETCHES):
    _,rows,refs=registration(); out=[]
    for row,ref,raw in zip(rows,refs,sketches):
        r=interpret_and_execute(row["view"],FrozenSketchCompiler(FakeCore(raw)),_executor,_hidden_verifier(ref))
        r.update(task_id=row["task_id"],kind=ref["kind"]); out.append(r)
    return out


def fixture(directory,recs=None):
    reg,rows,refs=registration(); recs=records() if recs is None else recs
    write=lambda name,obj:(directory/name).write_text(json.dumps(obj,sort_keys=True,allow_nan=False))
    head="a"*40
    write("study_started.json",{"schema":contract()["schema"],"frozen_head":head,"first_only":True,**BOUNDARY})
    write("manifest.json",{"registration":reg,"public_rows":rows,"frozen_head":head})
    write("core.json",FakeCore().identity)
    for i,(row,r) in enumerate(zip(rows,recs)):
        write("task_%02d_started.json"%i,{"task_id":row["task_id"],"view_sha256":digest(row["view"])})
        write("task_%02d.json"%i,r)
    complete=len(recs)==8
    decision=evaluate(recs,refs,True,complete,1000.0)
    report={"schema":contract()["schema"],"status":"COMPLETE" if complete else "INCOMPLETE",
            "decision":decision,"source_head":head,"core_audit":{"unchanged":True},"observations":len(recs),
            "whole_study_ms":1000.0,"accounting_complete":complete and all(r["accounting_complete"] for r in recs),
            "cost_totals":totals(recs),"frontier_calls":0,"fallback_calls":0,"new_training":False,
            "sealed_data_opened":False,"historical_score_reuse":False,"error":None,**BOUNDARY}
    write("report.json",report)
    write("terminal.json",{"files":{},"complete":complete,"decision":decision["verdict"],"no_replacement":True,**BOUNDARY})
    repin(directory)


def repin(directory):
    path=directory/"terminal.json"; t=json.loads(path.read_bytes())
    t["files"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob("*.json") if p.name!="terminal.json"}
    path.write_text(json.dumps(t,sort_keys=True))


class FirstContracts(unittest.TestCase):
    def test_registration_original_controls_no_model(self):
        r=check_construction()
        self.assertTrue(r["registration_valid"]); self.assertEqual(r["positive_checker_controls"],8)
        self.assertEqual(r["negative_checker_controls"],8); self.assertFalse(r["model_inference"])

    def test_pass_diagnostic_never_admits_p2(self):
        _,_,refs=registration(); r=records(); d=evaluate(r,refs,True,True,1000)
        self.assertEqual(d["verdict"],"PASS"); self.assertEqual(d["raw_semantic_accepted"],8)
        self.assertFalse(d["p2_registration_admitted"]); self.assertFalse(d["decision3_admitted"])
        self.assertEqual(d["cost_totals"]["input_tokens"],320)

    def test_original_capability_floor_still_fails_after_accounting_fix(self):
        _,_,refs=registration(); r=records(("bad","bad")+SKETCHES[2:])
        self.assertTrue(all(x["accounting_complete"] for x in r))
        d=evaluate(r,refs,True,True,1000)
        self.assertEqual(d["verdict"],"FAIL"); self.assertEqual(d["raw_semantic_accepted"],6)
        self.assertEqual(d["raw_math_accepted"],2); self.assertEqual(d["reason"],"SEMANTIC_PATH_CAPABILITY_FAILURE")

    def test_partial_work_never_sums_unknown_tokens_as_zero(self):
        _,_,refs=registration(); r=records(); r[0]["input_tokens"]=None; r[0]["accounting_complete"]=False
        self.assertIsNone(totals(r)["input_tokens"])
        self.assertEqual(evaluate(r,refs,True,True,1000)["reason"],"SEMANTIC_ACCOUNTING_OR_BUDGET_FAILURE")
        self.assertEqual(evaluate(r[:-1],refs,True,False,1000)["verdict"],"NOT_EVALUATED")
        self.assertEqual(evaluate(r,refs,False,True,1000)["verdict"],"NOT_EVALUATED")

    def test_all_raw_records_replay_including_strict_fail_and_abstain(self):
        _,rows,refs=registration()
        for raw in (SKETCHES[0],"bad", "CSP\nDOMAIN X 1 2\nEQ X Z\nEND","ABSTAIN"):
            r=records((raw,)+SKETCHES[1:])[0]
            replay_record(rows[0],refs[0],r)

    def test_replay_reconstructs_from_raw_not_cached_ir(self):
        _,rows,refs=registration(); r=records()[0]
        for key,value in (("accepted",False),("output_tokens",0),("accounting_complete",False),("selected_route","CSP")):
            bad=snapshot(r); bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): replay_record(rows[0],refs[0],bad)
        bad=snapshot(r); bad["proposal"]["public"]["expression"]="36"
        with self.assertRaises(ValueError): replay_record(rows[0],refs[0],bad)

    def test_actual_item_timeout_is_retained_not_replayed_into_success(self):
        _,rows,refs=registration(); r=records()[0]
        r.update(status="FAILED",accepted=False,semantic_budget_valid=False,
                 error="TimeoutError: complete semantic item deadline exceeded",complete_ms=180001.0)
        replay_record(rows[0],refs[0],r)
        r.update(executed=False,tool_calls=0,verifier_calls=0)
        r.pop("execution")
        replay_record(rows[0],refs[0],r)
        r["complete_ms"]=1.0
        with self.assertRaises(ValueError): replay_record(rows[0],refs[0],r)

    def test_complete_archive_replay_and_aggregate_admission_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp); fixture(directory)
            self.assertTrue(replay(directory)["integrity_valid"])
            for key,value in (("p2_admitted",True),("frontier_calls",1),("cost_totals",{})):
                fixture(directory); p=directory/"report.json"; r=json.loads(p.read_bytes()); r[key]=value
                p.write_text(json.dumps(r)); repin(directory)
                with self.subTest(key=key),self.assertRaises(ValueError): replay(directory)

    def test_failed_candidate_cost_replays_and_partial_retains_not_evaluated(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp); fixture(directory,records(("bad",)+SKETCHES[1:]))
            self.assertTrue(replay(directory)["integrity_valid"])
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp); fixture(directory,records()[:2])
            self.assertEqual(replay(directory)["decision"]["verdict"],"NOT_EVALUATED")

    def test_first_directory_is_exclusive_and_wrong_git_head_has_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"first"
            with patch("experiments.control_plane_p15_dev.subprocess.check_output",return_value="b"*40):
                result=run(target,"a"*40)
            self.assertEqual(result["status"],"INCOMPLETE")
            self.assertEqual(result["cost_totals"]["model_calls"],0)
            self.assertTrue((target/"terminal.json").exists()); self.assertTrue(replay(target)["integrity_valid"])
            with self.assertRaises(FileExistsError): run(target,"a"*40)


if __name__ == "__main__": unittest.main()
