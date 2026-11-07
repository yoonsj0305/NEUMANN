"""Scientific regression for Q3 local proof credit; not new-original success."""
import unittest

from research.q3.behavioral_proof_reward_first import (
    IndependentChecker, observe,
)
from research.q3.generative_typed_operator_policy import AST
from research.q3.local_credit_inverse_repair_postfirst import (
    FILLERS, mean_absolute_distance, residual_repair,signature,
    strong_classical_inverse,walk_subtrees,trainable_local_credit,
)


class LocalCounterexampleCreditTests(unittest.TestCase):
    def test_exact_match_bias_incorrect_even_on_valid_subtree(self):
        p=observe("source_plus_one")
        src=AST("Int","read_src",(AST("Int","j"),))
        z=AST("Int","zero")
        goal=tuple(y for x,y in p.observations)
        self.assertEqual(sum(a==b for a,b in zip(signature(src,p.observations),goal)),0)
        self.assertEqual(sum(a==b for a,b in zip(signature(z,p.observations),goal)),1)
        self.assertLess(mean_absolute_distance(signature(src,p.observations),goal),
                        mean_absolute_distance(signature(z,p.observations),goal))

    def test_no_hardcoded_target_macro_in_sibling_library(self):
        self.assertTrue(FILLERS)
        self.assertTrue(all(not e.children for e in FILLERS))
        self.assertFalse(any(e.name=="add" or e.name=="sub" for e in FILLERS))

    def test_source_subtree_can_be_completed_without_gold_ast(self):
        probe=AST("Int","read_src",(AST("Int","j"),))
        for target in ("source_plus_one","one_minus_source"):
            p=observe(target)
            ck=IndependentChecker(target,p)
            metrics={"observed_candidate_signatures":0,"full_Z3_candidates":0}
            proof=residual_repair(probe,p.observations,ck,metrics)
            self.assertIsNotNone(proof)
            self.assertEqual(proof["checker"]["verdict"],"PROVED")
            self.assertEqual(proof["checker"]["proof_verdict"],"unsat")
            self.assertEqual(proof["via"],"ONE_INVERSE_COMPLETION")
            self.assertEqual(ck.solver_calls,1)

    def test_all_subtree_spans_correspond_to_preorder_events(self):
        root=AST("Int","sub",(
            AST("Int","one"),
            AST("Int","read_src",(AST("Int","j"),))
        ))
        paths=list(walk_subtrees(root))
        self.assertEqual([(a,b) for node,a,b in paths],[(0,4),(1,2),(2,4),(3,4)])

    def test_strong_same_rights_inverse_classical_is_not_disabled(self):
        for target in ("source_plus_one","one_minus_source"):
            r=strong_classical_inverse(target,max_candidates=128)
            self.assertIsNotNone(r["proof_witness"])
            self.assertGreater(r["metrics"]["observed_candidate_signatures"],0)

    def test_learned_actor_runs_with_local_credit(self):
        r=trainable_local_credit("source_plus_one",episodes=24,seed=83,learn=True)
        self.assertGreater(r["metrics"]["observed_candidate_signatures"],0)
        self.assertEqual(r["metrics"]["subtree_credit_updates"],r["gradient_steps"])
        self.assertLessEqual(r["gradient_steps"],24)
        # The outcome is not hard-coded as PASS; either Z3 genuinely proved it
        # or it remains missing, never overwritten.
        if r["proof_witness"]:
            self.assertEqual(r["proof_witness"]["candidate"]["checker"]["proof_verdict"],"unsat")


if __name__=="__main__":
    unittest.main()
