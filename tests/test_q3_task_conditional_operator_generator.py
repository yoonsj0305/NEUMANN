"""Q3 actual information-bottleneck regression and semantically conditioned actor."""
import json
import unittest

from research.q3.generative_typed_operator_policy import Generator
from research.q3.task_conditional_operator_generator import (
    ObservedProblem, TaskConditionalGenerator,
    certify_original_blindness_pair, public_rhs_tree
)


class Q3TaskInformationGate(unittest.TestCase):
    def test_old_proposer_is_informationally_blind(self):
        result=certify_original_blindness_pair()
        self.assertTrue(result["original_identical_first_24_proposals"])
        self.assertEqual(result["original_task_mutual_information_given_same_metadata"],0)
        self.assertGreater(result["conditional_semantic_feature_difference_max"],0)
        self.assertEqual(result["Q3"],"OPEN")

    def test_ordered_semantics_not_token_bag(self):
        a=ObservedProblem("(- (select src cursor) 1)",True,0)
        b=ObservedProblem("(- 1 (select src cursor))",True,0)
        self.assertNotEqual(a.sha(),b.sha())
        self.assertEqual(a.vector()[:16],b.vector()[:16])
        self.assertNotEqual(a.vector()[16:],b.vector()[16:])
        self.assertEqual(public_rhs_tree(a.transition_rhs)[1][0],"select")
        self.assertEqual(public_rhs_tree(b.transition_rhs)[1],"1")

    def test_reject_unsupported_operator_instead_of_guess(self):
        with self.assertRaisesRegex(ValueError,"UNSUPPORTED_OBSERVED"):
            ObservedProblem("(xor src dst)",True,0)
        p=ObservedProblem("(xor src dst)",True,0) if False else None
        with self.assertRaisesRegex(ValueError,"INVALID_PUBLIC_TRANSITION_ARITY"):
            public_rhs_tree("(select src)")

    def test_learned_sampler_generates_int_value_expressions(self):
        p=ObservedProblem("(+ (select src cursor) 1)",True,0)
        m=TaskConditionalGenerator(seed=12)
        n=0
        samples=set()
        for i in range(80):
            try:
                ast,trace=m.sample_observed(p,root_kind="Int",bound_index=True,
                                            max_depth=5,max_nodes=80)
            except ValueError as err:
                self.assertEqual(str(err),"AST_NODE_BUDGET_EXCEEDED")
                continue
            n+=1
            self.assertEqual(ast.kind,"Int")
            self.assertTrue(trace)
            samples.add(ast.to_smt())
        self.assertGreater(n,50)
        self.assertGreater(len(samples),10)

    def test_training_updates_actual_contextual_weights(self):
        p=ObservedProblem("(select src cursor)",True,0)
        m=TaskConditionalGenerator(seed=14)
        initial=m.parameters_hash()
        calls=[]
        def checker(ast):
            calls.append(ast.to_data())
            return {"verdict":"UNKNOWN","validated_fraction":0}
        outcome=m.learn_observed(p,checker,episodes=14,max_depth=3,
                                  max_nodes=40,max_seconds=4)
        self.assertNotEqual(initial,m.parameters_hash())
        self.assertEqual(outcome["independent_checker_calls"],len(calls))
        self.assertEqual(outcome["verified_programs"],0)
        self.assertTrue(outcome["task_semantic_features_in_logits"])
        self.assertEqual(outcome["semantic_observation_sha256"],p.sha())

    def test_no_task_context_is_error(self):
        m=TaskConditionalGenerator(seed=12)
        with self.assertRaisesRegex(ValueError,"TASK_SEMANTICS_REQUIRED"):
            m.sample(collision=True,failed_proofs=0,max_depth=3,max_nodes=40)


if __name__=="__main__":
    unittest.main()
