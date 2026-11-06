"""Fail-closed synthetic-only controls; no benchmark input or first evaluation."""
import unittest
from research.q3.proof_reward_relational_student import (
    CANDIDATES, OPS, actual_source_delta, argmax, predicate, script, task
)


class ProofRewardStructureTests(unittest.TestCase):
    def test_grammar_expands_from_unary_H0_to_binary_H1(self):
        self.assertNotIn("select S",predicate(None))
        self.assertIn("select S",predicate(0))
        self.assertIn("forall",predicate(0))
        self.assertEqual(CANDIDATES,(None,-2,-1,0,1,2))

    def test_proof_tasks_use_source_and_dest_index_shift(self):
        t=task("ADD1",[17,-11])
        s=script(t,0,"STEP")
        self.assertIn("(+ base 17)",s)
        self.assertIn("(+ base -11)",s)
        self.assertIn("(store dst (+ a cursor)",s)
        self.assertIn("(select src (+ b cursor)) 1",s)

    def test_zero_weights_h0_not_a_learned_new_operator(self):
        self.assertEqual(argmax([0.0]*len(CANDIDATES)),0)
        self.assertIsNone(CANDIDATES[argmax([0.0]*len(CANDIDATES))])

    def test_real_source_semantics_not_sent_as_label(self):
        self.assertEqual(actual_source_delta("COPY"),0)
        self.assertEqual(actual_source_delta("ADD1"),1)
        self.assertEqual(actual_source_delta("SUB1"),-1)
        with self.assertRaises(ValueError):
            actual_source_delta("TRAIN_LABEL_LEAK")

    def test_unknown_proposal_or_unsupported_ast_fails_closed(self):
        for op in ("DROP","INFER","DISABLE"):
            with self.assertRaises(ValueError):
                script({"op":op,"src_shift":1,"dst_shift":3},0,"STEP")
        with self.assertRaises(ValueError):
            script(task("COPY",[0,0]),17,"STEP")
        with self.assertRaises(ValueError):
            argmax([float("nan")]*6)
        with self.assertRaises(ValueError):
            script(task("COPY",[0,0]),None,"BAD_CHECK")

    def test_preregistered_6_train_12_heldout_different_addresses(self):
        from research.q3.proof_reward_relational_student import MANIFEST
        import json
        c=json.loads(MANIFEST.read_text())
        self.assertEqual(c["training_cases"]["n"],6)
        self.assertEqual(c["heldout_cases"]["n"],12)
        self.assertTrue(c["origin"].startswith("AUTHOR_CONSTRUCTED"))
        self.assertEqual(len(c["H0_frozen"]),1)
        self.assertEqual(len(c["H1_proposals_by_generic_typed_composition"]),6)


if __name__=="__main__":
    unittest.main()
