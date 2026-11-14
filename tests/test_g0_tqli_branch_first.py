"""Software-only soundness controls; NO hard original body/answer opened here."""
import unittest
import z3

from research.g0.tqli_branch_first import branch_solver,git_blob,direct_solver,native_original_exact_model


class SemanticBranchGate(unittest.TestCase):
    def test_git_blob_identity(self):
        self.assertEqual(git_blob(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertNotEqual(git_blob(b"a"),git_blob(b"b"))

    def test_choose_only_original_or_disjuncts(self):
        a,b=z3.Bools("g0_test_a g0_test_b")
        f=[z3.Or(a,b),z3.Not(a)]
        direct_status,_,_=direct_solver(f,1)
        self.assertEqual(direct_status,"sat")
        result,model=branch_solver(f,2,0.25,2)
        self.assertEqual(result["status"],"sat")
        self.assertIsNotNone(model)
        self.assertTrue(all(z3.is_true(model.eval(c,model_completion=True)) for c in f))

    def test_under_budget_not_wrong_unsat(self):
        a,b=z3.Bools("g0_test_a g0_test_b")
        f=[z3.Or(a,b),z3.Not(a),z3.Not(b)]
        result,model=branch_solver(f,1,0.1,2)
        self.assertIsNone(model)
        self.assertNotEqual(result["status"],"sat")

    def test_cannot_assume_remaining_or_branches_false(self):
        a,b=z3.Bools("g0_test_a g0_test_b")
        f=[z3.Or(a,b),z3.Not(a)]
        result,model=branch_solver(f,1,0.1,1)
        self.assertIsNone(model)
        self.assertNotEqual(result["status"],"sat")
        # A restricted original OR branch subset cannot establish UNSAT.
        self.assertEqual(result["status"],"unknown_exhausted_or_unsat")

    def test_model_original_assertions_checked(self):
        a=z3.Int("g0_test_x")
        f=[z3.Or(a==1,a==2),a==2]
        s=z3.Solver();s.add(*f)
        self.assertEqual(s.check(),z3.sat)
        _,assign=native_original_exact_model(s.model(),
            "(declare-fun g0_test_x () Int)\n(check-sat)",f)
        self.assertEqual(assign["g0_test_x"],2)

    def test_false_claim_rejected_under_original(self):
        a=z3.Int("g0_test_y")
        f=[a>10]
        s=z3.Solver();s.add(a==2)
        self.assertEqual(s.check(),z3.sat)
        valid,assignment=native_original_exact_model(s.model(),
            "(declare-fun g0_test_y () Int)\n(check-sat)",f)
        self.assertFalse(valid)
        self.assertEqual(assignment["g0_test_y"],2)

if __name__=="__main__":
    unittest.main()
