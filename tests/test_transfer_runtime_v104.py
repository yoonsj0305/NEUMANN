"""Tiny explicit mathematical fixtures; never generate the registered corpus."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from experiments import q5_transfer_admission as audit
from neumann1.lp_certificate_v081 import verify_standard_form_certificate
from neumann1 import lp_portfolio_v084 as storage


def fixture():
    return {"A":audit.assignment_matrix(2),"b":np.ones(3),"c":np.array([4.,1.,2.,3.])}


class TransferRuntimeTests(unittest.TestCase):
    def test_specialized_direct_has_original_primal_dual_certificate(self):
        raw=fixture();result=audit.assignment_checked(raw)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["witness"]["x"],[0.,1.,1.,0.])
        self.assertTrue(verify_standard_form_certificate(**raw,**result["witness"])["accepted"])

    def test_same_shape_wrong_grammar_is_not_authority(self):
        for field in ("A","b"):
            raw=fixture();raw[field].flat[0]+=1
            with self.assertRaises(ValueError):audit.assignment_checked(raw)

    def test_oracle_support_keeps_degenerate_primal_support(self):
        raw=fixture();w=audit.assignment_checked(raw)["witness"]
        indices=audit.oracle_support(w,3)
        self.assertEqual(indices,[1,2])

    def test_signed_pair_exact_support_without_planted_ground_truth_access(self):
        I=np.eye(4)
        raw={"A":np.concatenate((I,-I),axis=1),"b":np.array([1.,-2.,0.,3.]),"c":np.ones(8)}
        w={"x":[1.,0.,0.,3.,0.,2.,0.,0.],"y":[1.,-1.,1.,1.]}
        indices=audit.oracle_support(w,4)
        self.assertEqual(indices,[0,3,5])

    def test_original_certificate_rejects_changed_answer(self):
        raw=fixture();w=audit.assignment_checked(raw)["witness"]
        w["x"][0]=1.
        self.assertFalse(verify_standard_form_certificate(**raw,**w)["accepted"])

    @unittest.skipUnless(importlib.util.find_spec("highspy"),"native runtime unavailable locally; required in exact-runtime CI")
    def test_native_oracle_accepts_fewer_support_entries_than_rows(self):
        raw=fixture();w=audit.assignment_checked(raw)["witness"]
        with patch.object(audit,"generate",side_effect=AssertionError("no registered source generation")):
            result=audit.oracle_checked(raw,[1,2],w["y"],5.)
        self.assertTrue(result["accepted"],result)
        self.assertEqual(result["witness"]["x"],w["x"])
        self.assertLess(len(result["indices"]),raw["A"].shape[0])
        from experiments.q5_replay import check_cost,native_checked
        small={"A":raw["A"][:,[1,2]],"b":raw["b"],"c":raw["c"][[1,2]]}
        native_checked(small,result["native"])
        check_cost(result["total_ms"],result["solve_ms"]+result["verify_ms"])

    @unittest.skipUnless(importlib.util.find_spec("highspy"),"exact runtime required in dedicated CI")
    def test_all_four_fresh_workers_ready_without_any_source(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/"sources.json").write_text(json.dumps({"cases":[]}))
            for route in ("NATIVE","IPM","ASSIGNMENT","ORACLE"):
                w=audit.Worker(directory,route)
                try:
                    self.assertTrue(w.ready["ready"])
                    self.assertGreater(w.cold_ms,0)
                    pools=w.ready["environment"]["threadpools"]
                    self.assertTrue(pools)
                    self.assertTrue(all(p["num_threads"]==1 for p in pools))
                finally:w.close()

    def test_retained_native_record_and_late_receipt(self):
        raw=fixture();answer=audit.assignment_checked(raw)
        spec={"id":"fixture","family":"assignment","level":2,"replicate":0,"rows":3,"cols":4,"seed":0}
        source={"metadata":spec,"arrays":{k:storage.encode_array(v) for k,v in raw.items()},
            "input_sha256":storage.input_digest(raw),"oracle":answer}
        ledger={"native_run_calls":1,"set_basis_calls":0,"certificate_calls":1}
        attempt={"warm_start":False,"basis":None,"accepted":True,
            "witness":answer["witness"],"certificate":answer["certificate"],"error":None,
            "stages":[{"stage":name,"ms":1.} for name in ("model_setup","native_solve","original_verification")],"ledger":ledger}
        native={"accepted":True,"head_kind":"COLD","fallback_used":False,"budget_s":5.,
            "total_ms":3.5,"status":"VERIFIED","ledger":ledger,"attempts":[attempt]}
        source["native_label"]=native;source["oracle"]["indices"]=[1,2]
        record={"case_id":"fixture","route":"NATIVE","repeat":0,"execution":native,
            "witness":answer["witness"],"error":None,"accepted":True,
            "total_ms":5.,"worker_total_ms":4.,"transport_and_receipt_ms":1.,
            "proposal_ms":0.,"post_ms":5.,"peak_rss_kib":1000}
        manifest={"cases":[{"metadata":spec,"identity":{}}]}
        ev=audit.evidence_module()
        with patch.object(audit.contract,"specs",return_value=[spec]),patch.object(ev,"unpack_case",return_value=source):
            checked=audit.validate_records("fixture",manifest,[copy.deepcopy(record)])
            self.assertTrue(checked[0]["accounted"])
            late=copy.deepcopy(record);late["total_ms"]=5001.;late["post_ms"]=5001.;late["transport_and_receipt_ms"]=4997.;late["accepted"]=False
            self.assertTrue(audit.validate_records("fixture",manifest,[late])[0]["accounted"])
            bad=copy.deepcopy(record);bad["witness"]=None
            with self.assertRaises(ValueError):audit.validate_records("fixture",manifest,[bad])


if __name__=="__main__":unittest.main()
