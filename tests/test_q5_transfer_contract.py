"""Synthetic admission fixtures, not new problem generation or measurements."""
import copy
import importlib
import math
import subprocess
import sys
import unittest
from pathlib import Path

from experiments import q5_transfer_contract as c


def records():
    return [{"case_id":case, "route":route, "repeat":repeat,
             "total_ms":10. if route == "ORACLE" else (40. if route == "ASSIGNMENT" else 100.),
             "accepted":True, "accounted":True} for case,route,repeat in c.schedule()]


def cold():
    return {r:1000. for r in ("NATIVE","IPM","ASSIGNMENT","ORACLE")}


class TransferContractTests(unittest.TestCase):
    def test_metadata_and_scope(self):
        self.assertEqual(len(c.specs()),32)
        self.assertEqual([r["seed"] for r in c.specs()],list(range(104000,104032)))
        self.assertEqual(len(c.schedule()),448)
        self.assertTrue(all(r[2]==-1 for r in c.schedule()[:112]))
        self.assertTrue(all(r[2]>=0 for r in c.schedule()[112:]))
        self.assertFalse(c.protocol()["global_q5_closed"])
        self.assertFalse(c.protocol()["cross_domain_pass"])

    def test_imports_do_not_open_scientific_runtime(self):
        root=Path(__file__).resolve().parents[1]
        p=subprocess.run([sys.executable,"-c","import sys; import experiments.q5_transfer_admission; assert not any(n in sys.modules for n in ('numpy','scipy','torch','highspy'))"],cwd=root,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_oracle_headroom_only_admits_frozen_transfer(self):
        result=c.summarize(records(),cold())
        self.assertEqual(set(result["decisions"].values()),{"ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING"})
        self.assertFalse(result["global_q5_closed"])
        self.assertEqual(result["model_forwards"],0)

    def test_strong_specialized_baseline_cannot_be_ignored(self):
        rows=records()
        for r in rows:
            if r["route"]=="ASSIGNMENT": r["total_ms"]=1.
        self.assertEqual(c.summarize(rows,cold())["decisions"]["assignment"],"STOP_FAMILY_NO_ORACLE_HEADROOM")

    def test_warmup_capability_failure_never_dropped(self):
        rows=records(); rows[0]["accepted"]=False
        result=c.summarize(rows,cold())
        family=next(s["family"] for s in c.specs() if s["id"]==rows[0]["case_id"])
        self.assertEqual(result["decisions"][family],"CAPABILITY_UNREACHED_NO_TRANSFER_BUDGET")

    def test_missing_or_reordered_records_rejected(self):
        rows=records()
        with self.assertRaises(ValueError): c.summarize(rows[:-1],cold())
        rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaises(ValueError): c.summarize(rows,cold())

    def test_one_favorable_size_cannot_rescue_other_cells(self):
        rows=records()
        target=next(s["id"] for s in c.specs() if s["family"]=="basis_pursuit" and s["level"]==16)
        for r in rows:
            if r["case_id"]==target and r["route"]=="ORACLE":r["total_ms"]=1000.
        self.assertEqual(c.summarize(rows,cold())["decisions"]["basis_pursuit"],"STOP_FAMILY_NO_ORACLE_HEADROOM")

    def test_all_costs_and_cold_routes_required(self):
        for value in (-1,math.nan,True):
            rows=records();rows[0]["total_ms"]=value
            with self.assertRaises(ValueError):c.summarize(rows,cold())
        rows=records(); rows[0]["accounted"]=False
        with self.assertRaises(ValueError):c.summarize(rows,cold())
        with self.assertRaises(ValueError):c.summarize(records(),{})

    def test_protocol_is_not_mutable_global_state(self):
        p=c.protocol();p["levels"].clear()
        self.assertEqual(c.protocol()["levels"],[8,16,32,64])

    def test_unregistered_spec_rejected_before_generation(self):
        module=importlib.import_module("experiments.q5_transfer_admission")
        with self.assertRaises(ValueError):module.generate({"seed":1})


if __name__=="__main__":unittest.main()
