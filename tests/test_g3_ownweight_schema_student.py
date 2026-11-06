"""No external originals in these tests; Q3 remains OPEN."""
import unittest
import numpy as np
from research.g3.ownweight_schema_student import (
    compiled_predicate, compile_from_weights, policy, vector,
    certified_teacher_targets, q_interval
)

SYNTHETIC = """(set-logic HORN)
(declare-fun |main@entry| (Int) Bool)
(declare-fun |main@bb9.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb19.i| (Int Int (Array Int Int) Int) Bool)
(declare-fun |main@bb29.i| (Int (Array Int Int) Int Int) Bool)
(declare-fun |main@verifier.error.split| () Bool)
(assert (forall ((n Int) (i Int) (a (Array Int Int)) (l Int))
    (=> (and (main@bb9.i n i a l) (< i l) (= a (store a i 42))) (main@bb9.i n i a l))))
(assert (forall ((n Int) (i Int) (a (Array Int Int)) (l Int))
    (=> (and (main@bb19.i n i a l) (< i l) (= a (store a i 43))) (main@bb19.i n i a l))))
(assert (=> main@verifier.error.split false))
(check-sat)
"""


class StudentGrammarTests(unittest.TestCase):
    def test_training_program_labels_are_human_preset_not_proof(self):
        self.assertEqual(certified_teacher_targets(0,2),(1,1,0,0))
        self.assertEqual(certified_teacher_targets(1,2),(1,1,2,2))
        self.assertEqual(certified_teacher_targets(2,2),(3,2,0,0))

    def test_quantifier_formula_is_real_typed_ast_not_string_return(self):
        q=q_interval(1,1,1,[42,43])
        self.assertIn("(forall ((j Int))",q)
        self.assertIn("43",q)
        self.assertIn("(< j i)",q)
        with self.assertRaises(ValueError):
            q_interval(0,1,1,[42,43])
        with self.assertRaises(ValueError):
            q_interval(1,2,0,[42,43])

    def test_untrained_zero_weights_are_not_automatically_a_theorem(self):
        W=np.zeros((4,6,4),dtype=np.float64)
        with self.assertRaises(ValueError):
            compile_from_weights(SYNTHETIC,W)

    def test_mock_fixed_weights_compile_all_three_roles(self):
        # This is a hand-constructed test ONLY, NOT an evaluated learned model.
        W=np.zeros((4,6,4),dtype=np.float64)
        for kind in range(3):
            stage={0:0,1:1,2:2}[kind]
            targets=certified_teacher_targets(stage,2)
            for head,v in enumerate(targets):
                W[head,kind+1,v]=10
        self.assertEqual(policy(W,0,2),(1,1,0,0))
        self.assertEqual(policy(W,1,2),(1,1,2,2))
        self.assertEqual(policy(W,2,2),(3,2,0,0))
        program=compile_from_weights(SYNTHETIC,W)
        self.assertEqual(program["num_stages"],2)
        self.assertEqual(program["original_clause_count"],3)
        self.assertIn("(forall ((j Int))",program["prefix"])
        self.assertIn("(define-fun |main@verifier.error.split| () Bool false)",program["prefix"])
        self.assertIn("(define-fun |main@entry| ((n Int)) Bool true)",program["prefix"])

    def test_bad_metadata_and_weights_fail_closed(self):
        with self.assertRaises(ValueError):
            vector(5,2)
        with self.assertRaises(ValueError):
            policy(np.zeros((3,6,4)),0,2)
        with self.assertRaises(ValueError):
            policy(np.full((4,6,4),np.nan),0,2)
        with self.assertRaises(ValueError):
            compiled_predicate(1,2,[42,43],"x",0,(1,1,2,2))


if __name__=="__main__":
    unittest.main()
