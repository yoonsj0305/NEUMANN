"""Q3 generator acceptance tests. No source-free toy is counted as Q3 proof."""
import hashlib
import json
import unittest

from research.q3.generative_typed_operator_policy import (
    AST, PRODUCTIONS, Generator, check_ast, learn_from_independent_checker,
    novelty_signature
)


class VariableLengthTypedASTTests(unittest.TestCase):
    def test_not_a_fixed_h1_selector(self):
        self.assertNotIn("COPY_PREFIX", str(PRODUCTIONS))
        self.assertNotIn("ADD1", str(PRODUCTIONS))
        self.assertNotIn("MUL2", str(PRODUCTIONS))
        self.assertIn("forall", dict(PRODUCTIONS["Bool"]))
        self.assertIn("read_src", dict(PRODUCTIONS["Int"]))
        self.assertIn("read_dst", dict(PRODUCTIONS["Int"]))

    def test_own_weights_generate_typed_variable_length_programs(self):
        m = Generator(seed=3)
        sizes = set()
        emitted = set()
        for _ in range(128):
            try:
                ast, trace = m.sample(collision=True, failed_proofs=6,
                    max_depth=5, max_nodes=160)
            except ValueError as exc:
                self.assertEqual(str(exc), "AST_NODE_BUDGET_EXCEEDED")
                continue
            self.assertEqual(ast.kind, "Bool")
            sizes.add(check_ast(ast, ceiling=160))
            emitted.add(json.dumps(ast.to_data(), sort_keys=True))
            self.assertGreater(len(trace), 0)
            self.assertIn("(", ast.to_smt())
        self.assertGreater(len(sizes), 1)
        self.assertGreater(len(emitted), 10)

    def test_index_scope_and_type_errors_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "UNBOUND_INDEX"):
            check_ast(AST("Int", "j"))
        with self.assertRaisesRegex(ValueError, "TYPE_MISMATCH"):
            check_ast(AST("Bool", "eq",
                (AST("Bool", "eq", (AST("Int","one"),AST("Int","zero"))),
                 AST("Int","zero"))))
        valid = AST("Bool", "forall", (
            AST("Bool", "eq", (AST("Int", "j"), AST("Int","j"))),))
        self.assertGreater(check_ast(valid), 1)
        self.assertIn("(forall ((j Int))", valid.to_smt())

    def test_proof_reward_updates_real_weights_not_human_labels(self):
        m = Generator(seed=11)
        start = m.parameters_hash()
        seen = []
        def checker(ast):
            seen.append(ast.to_data())
            # UNKNOWN never proves an operator. The purpose of this test is
            # the actual REINFORCE update, not a positive scientific score.
            return {"verdict":"UNKNOWN","validated_fraction":0.0}
        result=learn_from_independent_checker(m,checker,
            episodes=8,collision=True,failed_proofs=3,
            max_depth=3,max_nodes=80,max_seconds=3)
        self.assertNotEqual(start,m.parameters_hash())
        self.assertGreater(result["actual_grad_steps"],0)
        self.assertEqual(result["verified_programs"],0)
        self.assertEqual(result["Q3"],"OPEN")
        self.assertEqual(result["independent_checker_calls"],len(seen))

    def test_refuse_false_proof_or_unvalidated_reward(self):
        m = Generator(seed=17)
        def invalid_checker(ast):
            return {"verdict":"PROVED","validated_fraction":0.5}
        with self.assertRaisesRegex(ValueError,"FALSE_PROOF_REWARD"):
            learn_from_independent_checker(m,invalid_checker,
                episodes=3,collision=True,failed_proofs=1,
                max_depth=2,max_nodes=50,max_seconds=3)

    def test_expressions_are_constructed_not_selected_from_set(self):
        m=Generator(seed=73)
        expressions=[]
        for _ in range(300):
            try:
                ast,_=m.sample(collision=False,failed_proofs=0,
                    max_depth=7,max_nodes=100)
                expressions.append(ast)
            except ValueError:
                pass
        self.assertTrue(expressions)
        self.assertTrue(any(novelty_signature(x)["variable_nodes"]>5
                            for x in expressions))
        self.assertGreater(len(set(x.to_smt() for x in expressions)),15)


if __name__=="__main__":
    unittest.main()
