"""Zero source/model execution tests for frozen symbolic-stage extrapolation."""
import json
import math
import unittest

from research.g3.ownweight_symbolic_n_readonly import (
    PREREG, digest, target, independent_score, original_native_censored_readonly
)


class SymbolicNReadonlyContracts(unittest.TestCase):
    def test_frozen_registered_denominator_and_sha(self):
        c=json.loads(PREREG.read_text())
        self.assertEqual(c["registered_n_range"]["min"],2)
        self.assertEqual(c["registered_n_range"]["max_inclusive"],128)
        self.assertEqual(sum(n+1 for n in range(2,129)),8382)
        self.assertEqual(c["frozen_checkpoint"]["checkpoint_sha256"],
                         "982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc")

    def test_first_middle_and_final_have_distinct_typed_syntax(self):
        for n in (2,7,128):
            self.assertEqual(target(0,n),(1,1,0,0))
            self.assertEqual(target(1,n),(1,1,2,2))
            self.assertEqual(target(n,n),(3,2,0,0))
        with self.assertRaises(ValueError):
            target(129,128)

    def test_independent_pure_python_fourhead_weight_scorer(self):
        weights=[[[0.0]*4 for _ in range(6)] for _ in range(4)]
        for position,vec in enumerate(((1,1,0,0),(1,1,2,2),(3,2,0,0))):
            for head,c in enumerate(vec):
                weights[head][position+1][c]=50.0
        for n,stage in ((2,0),(2,1),(2,2),(128,0),(128,63),(128,128)):
            prediction,margins=independent_score(weights,stage,n)
            self.assertEqual(prediction,target(stage,n))
            self.assertTrue(all(x>=0.0 for x in margins))

    def test_untrained_never_magic_theorem(self):
        blank=[[[0.0]*4 for _ in range(6)] for _ in range(4)]
        for n in (2,3,5,10,128):
            for k in range(n+1):
                predicted,_=independent_score(blank,k,n)
                self.assertNotEqual(predicted,target(k,n))

    def test_bad_weights_refuse_processing(self):
        with self.assertRaises(ValueError):
            independent_score([[[0.0]*4 for _ in range(6)] for _ in range(3)],1,3)
        bad=[[[0.0]*4 for _ in range(6)] for _ in range(4)]
        bad[0][0][1]=float("nan")
        with self.assertRaises(ValueError):
            independent_score(bad,1,3)

    def test_native_sha_means_literal_censored_timeout_not_checker_error(self):
        c=json.loads(PREREG.read_text())
        code=digest(b"timeout\n")
        rows=[]
        for name in ("standard_init2_true-unreach-call_ground_000.smt2",
                     "standard_init3_true-unreach-call_ground_000.smt2"):
            rows.append({"name":name,"original_source_strong_native":{
                "bounded_native_verdict":"CHECKER_ERROR",
                "exit":0,"stdout_sha256":code,
                "native_time_cap_s":15,"wall_ms":15002.4
            }})
        first={"checkpoint_SHA256":c["frozen_checkpoint"]["checkpoint_sha256"],
               "train_source_only_actual_run":42198111692,"rows":rows}
        audit=original_native_censored_readonly(first,c)
        self.assertEqual(audit["timeout_censored_corrections"],2)
        self.assertTrue(all(x["postfirst_readonly_qualified_label"]==
                            "TIMEOUT_CENSORED_15_SECONDS" for x in audit["rows"]))
        first["rows"][0]["original_source_strong_native"]["stdout_sha256"]="0"*64
        with self.assertRaises(ValueError):
            original_native_censored_readonly(first,c)


if __name__=="__main__":
    unittest.main()
