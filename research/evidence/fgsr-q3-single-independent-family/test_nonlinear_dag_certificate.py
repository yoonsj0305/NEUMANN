"""Reproducible no-network test: learned-advisor proof authority must fail closed.

Tiny mathematical proof-DAG positive/negative controls test **the checker**.
They are explicitly NOT new authentic-original benchmark successes.
"""
import copy
import sys
import unittest

from full_nonlinear_dag_one import attempt, check_replay, read_rules

def example(error_target=2):
    x=" ".join(["Int"]*8)
    z=lambda n:f"(Inv {n} 0 0 0 0 0 0 0)"
    return f"""(set-logic HORN)
(declare-fun Inv ({x}) Bool)
(declare-fun CHC_COMP_FALSE () Bool)
(assert (forall ((x Int)) (=> (= x 0) {z("x")})))
(assert (forall ((x Int)) (=> (and {z("x")} (= x 0)) {z(1)})))
(assert (forall ((a Int)(b Int)) (=> (and {z("a")} {z("b")} (= a 0) (= b 1)) {z(2)})))
(assert (forall ((x Int)) (=> (and {z("x")} (= x {error_target})) CHC_COMP_FALSE)))
(assert (forall ((u Bool)) (=> CHC_COMP_FALSE false)))
"""

class NonlinearProofDagContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=read_rules(example(),expected_count=5)
        cls.result=attempt(cls.rules,3,9000)
        assert cls.result["verdict"]=="sat", cls.result

    def test_genuinely_nonlinear_join_derivation(self):
        p=self.result["certificate"]
        self.assertEqual(len(p["nodes"]),3)
        self.assertEqual(len(p["nodes"][-1]["parents"]),2)
        self.assertEqual(p["nodes"][-1]["state"][0],2)
        self.assertTrue(p["certificate"]["independently_replayed"])
        self.assertEqual(p["certificate"]["terminal_false_rule"],5)

    def test_each_proof_step_replay(self):
        p=self.result["certificate"]
        result=check_replay(self.rules,p)
        self.assertEqual(result["checked_nodes"],3)

    def test_prevent_parent_from_future(self):
        p=copy.deepcopy(self.result["certificate"])
        p["nodes"][-1]["parents"][0]=2
        with self.assertRaisesRegex(ValueError,"REPLAY_TOPOLOGICAL_FAILURE"):
            check_replay(self.rules,p)

    def test_prevent_omitted_nonlinear_parent(self):
        p=copy.deepcopy(self.result["certificate"])
        p["nodes"][-1]["parents"].pop()
        with self.assertRaisesRegex(ValueError,"REPLAY_WRONG_PARENT_COUNT"):
            check_replay(self.rules,p)

    def test_prevent_corrupted_head_state(self):
        p=copy.deepcopy(self.result["certificate"])
        p["nodes"][-1]["state"][0]=999
        with self.assertRaisesRegex(ValueError,"REPLAY_STEP"):
            check_replay(self.rules,p)

    def test_falsified_original_goal_never_accepted(self):
        changed=read_rules(example(error_target=999),expected_count=5)
        with self.assertRaisesRegex(ValueError,"REPLAY_NO_ORIGINAL_ERROR_RULE"):
            check_replay(changed,self.result["certificate"])

    def test_wrong_clause_identity_rejected(self):
        p=copy.deepcopy(self.result["certificate"])
        p["nodes"][-1]["rule"]=2
        with self.assertRaises(ValueError):
            check_replay(self.rules,p)

    def test_source_rule_count_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"ORIGINAL_CLAUSE_COUNT_MISMATCH"):
            read_rules(example(),expected_count=48)

    def test_unrelated_depth_no_unsafety_proof(self):
        r=attempt(self.rules,2,9000)
        self.assertEqual(r["verdict"],"unsat")

if __name__=="__main__":
    unittest.main(verbosity=2)
