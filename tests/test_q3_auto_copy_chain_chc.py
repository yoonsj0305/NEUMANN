"""No-source structural compiler contracts: fail closed on graph/layout mismatch."""
import unittest

from research.q3.auto_copy_chain_chc import (
    generated_body, recognize_stage_types, compile_candidate, ARR
)

class CopyChainGeneratorTest(unittest.TestCase):
    def test_three_stage_relation_is_generically_assembled(self):
        stage0=generated_body(0, 3, False)
        stage1=generated_body(1, 3, False)
        stage2=generated_body(2, 3, False)
        self.assertIn("(COPY_PREFIX x3 x1 x5 x4 x2)", stage0)
        self.assertIn("(COPY_PREFIX x1 x0 x3 x2 x7)", stage1)
        self.assertIn("(COPY_PREFIX x6 x5 x3 x2 x4)", stage1)
        self.assertIn("(COPY_PREFIX x1 x0 x3 x2 x5)", stage2)
        self.assertNotIn("x6", stage2)

    def test_four_stage_extra_future_arrays(self):
        stage0=generated_body(0,4,False)
        stage1=generated_body(1,4,False)
        stage2=generated_body(2,4,False)
        self.assertIn("(> x8 0)", stage0)
        self.assertIn("(> x8 0)", stage1)
        self.assertNotIn("(> x8 0)", stage2)
        self.assertIn("(COPY_PREFIX x6 x5 x3 x2 x4)", stage2)

    def test_no_target_stage_names_hardcoded(self):
        stage_sorts={
            "arbitrary_one":["Int","Int","Int",ARR,"Int",ARR,"Int","Int",ARR],
            "arbitrary_two":["Int",ARR,"Int",ARR,"Int","Int",ARR,"Int"],
            "arbitrary_three":["Int",ARR,"Int",ARR,"Int","Int"]
        }
        self.assertEqual(recognize_stage_types(stage_sorts,list(stage_sorts)),3)

    def test_drift_inferred_layout_raises(self):
        signatures={
            "a":["Int","Int","Int",ARR,"Int",ARR,"Int","Int",ARR],
            "b":["Int",ARR,"Int",ARR,"Int","Int",ARR,"Int"],
            "c":["Int",ARR,"Int",ARR,"Int","Int"],
        }
        signatures["b"][4]="Bool"
        with self.assertRaisesRegex(ValueError,"LAYOUT"):
            recognize_stage_types(signatures,["a","b","c"])

    def test_wrong_mutant_differs_only_copy_step(self):
        left=generated_body(1,4,False)
        right=generated_body(1,4,True)
        self.assertNotEqual(left,right)
        self.assertIn("COPY_PREFIX_WRONG",right)
        self.assertNotIn("COPY_PREFIX_WRONG",left)

    def test_parser_rejects_non_chain(self):
        source="""(set-logic HORN)
(declare-fun |main@entry| ( Int Int ) Bool)
(declare-fun |main@verifier.error.split| () Bool)
(assert (=> (main@entry 0 0) main@verifier.error.split))"""
        with self.assertRaises(ValueError):
            compile_candidate(source)

if __name__ == "__main__":
    unittest.main()
