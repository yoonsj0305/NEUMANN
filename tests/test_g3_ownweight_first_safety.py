"""No target-source fetch in these negative-control tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from research.g3.ownweight_schema_original_first import (
    FREEZE, run, native_original, verify_compiler
)


class FrozenQuantifierFirstSafety(unittest.TestCase):
    def test_registered_targets_and_exact_original_checkpoint_sha(self):
        f=json.loads(FREEZE.read_text())
        self.assertEqual(f["training_first"]["run_id"],42198111692)
        self.assertEqual(
            f["training_first"]["checkpoint_sha256"],
            "982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc"
        )
        self.assertEqual(
            [row["file"] for row in f["target_registry"]],
            ["standard_init2_true-unreach-call_ground_000.smt2",
             "standard_init3_true-unreach-call_ground_000.smt2"])
        self.assertEqual(f["original_eval_budget"]["native_z3_seconds_per_original"],15)
        self.assertTrue(f["human_designed_grammar_is_reused"])

    def test_wrong_checkpoint_refuses_before_any_source_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"wrong.json"
            p.write_text("{}")
            with patch("research.g3.ownweight_schema_original_first.source") as forbidden:
                with self.assertRaises(ValueError):
                    run(p)
                forbidden.assert_not_called()

    def test_untrained_zero_tensor_cannot_be_called_a_proof(self):
        synthetic="""(set-logic HORN)
(declare-fun |main@entry| (Int) Bool)
(declare-fun |main@bb9.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb19.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb29.i| (Int (Array Int Int) Int Int) Bool)
(declare-fun |main@verifier.error.split| () Bool)
(assert (forall ((a (Array Int Int)) (i Int)) (= a (store a i 17))))
(assert (forall ((a (Array Int Int)) (i Int)) (= a (store a i 18))))
(assert (=> main@verifier.error.split false))
(check-sat)
"""
        test=verify_compiler(synthetic,np.zeros((4,6,4)),7)
        self.assertEqual(test["status"],"FAIL_CLOSED_NO_PROVEN_ORIGINAL")
        self.assertEqual(test["original_independently_proven"],0)

    def test_unknown_native_response_is_not_verified(self):
        with patch("research.g3.ownweight_schema_original_first.subprocess.run") as subprocess_call:
            subprocess_call.return_value=SimpleNamespace(returncode=0,stdout="unknown\n",stderr="")
            out=native_original(b"(set-logic HORN)\n(check-sat)\n",15)
            self.assertEqual(out["status"],"UNKNOWN_OR_ERROR")
            self.assertIsNone(out["verdict"])

    def test_error_native_response_is_not_verified(self):
        with patch("research.g3.ownweight_schema_original_first.subprocess.run") as subprocess_call:
            subprocess_call.return_value=SimpleNamespace(returncode=2,stdout="sat\n",stderr="error")
            out=native_original(b"(set-logic HORN)\n(check-sat)\n",15)
            self.assertEqual(out["status"],"UNKNOWN_OR_ERROR")


if __name__=="__main__":
    unittest.main()
