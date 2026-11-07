"""Q3 source-memory coordinate expression -> new argument-role AST causal tests."""
import itertools
import unittest
from research.q3.discover_index_relation_constructor import discover
from research.q3.learn_argument_roles_for_prior_relation import (
    search,run_role_program,score,acceptable
)


class NewInputRoleMemoryTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old=[([""],True),(["aba"],True),(["aaaa"],True),
             (["abc"],False),(["xyzyx"],True),(["abac"],False)]
        learned=discover(old,budget=1200)
        assert learned["status"]=="INVENTED_EXECUTABLE_RELATION",learned
        cls.prior=learned["program"]

    def test_prior_observation_synthesizes_new_two_input_program(self):
        train=[
            ([[1,2,3],[3,2,1]],True),
            ([[4,5],[5,4]],True),
            ([[5,6],[6,6]],False),
            ([[6,7,8],[8,6,7]],False),
            ([[1,1],[1,1]],True),
            ([[9],[9]],True),
            ([[1,2],[2]],False),
            ([[],[]],True),
        ]
        self.assertTrue(acceptable(train))
        warm=search(train,prior_program=self.prior,budget=64)
        self.assertEqual(warm["status"],"TRANSFERRED_NEW_INPUT_ROLE_BINDING")
        self.assertLessEqual(warm["attempts"],16)
        cold=search(train,prior_program=None,budget=64)
        self.assertGreaterEqual(cold["attempts"],warm["attempts"])
        self.assertNotIn("mirror",str(warm["program"]))
        self.assertNotIn("palindrome",str(warm["program"]))
        test=[
            ([[7,8,9],[9,8,7]],True),
            ([[4,5],[4,5]],False),
            ([[-1,-2],[-2,-1]],True),
            ([[0,1],[1,0]],True),
            ([[0,1],[1,1]],False),
            ([[],[]],True),
        ]
        self.assertTrue(score(warm["program"],test)["exact"])

    def test_new_input_roles_polymorphic_tuple_string(self):
        train=[
            (["abc","cba"],True),
            (["xy","yx"],True),
            (["xyz","xyz"],False),
            (["abba","abba"],True),
            (["z","z"],True),
            (["abc","cab"],False),
        ]
        found=search(train,prior_program=self.prior,budget=64)
        self.assertIsNotNone(found["program"])
        self.assertTrue(score(found["program"],[
            (["hello","olleh"],True),
            (["hello","hello"],False),
            (["aba","aba"],True),
            (["x","x"],True)])["exact"])

    def test_independent_exhaustive_reference_semantics(self):
        train=[
            (["ab","ba"],True),(["abc","cba"],True),
            (["xy","xy"],False),(["abb","bab"],False),
            (["p","p"],True),(["aa","aa"],True),
        ]
        p=search(train,prior_program=self.prior,budget=64)["program"]
        self.assertIsNotNone(p)
        # Exhaust all length 0..6 pairs of 2-symbol strings. The external
        # original problem is NOT used as the reference oracle here.
        checked=0
        for n in range(7):
            vals=["".join(bits) for bits in itertools.product("ab",repeat=n)]
            for a in vals:
                for b in vals:
                    expected=a==b[::-1]
                    self.assertEqual(run_role_program(p,[a,b]),expected,
                                     (a,b,p))
                    checked+=1
        self.assertEqual(checked,sum(4**n for n in range(7)))

    def test_abstain_for_noncausal_unsupported_input_contract(self):
        self.assertEqual(search([
            ([[1,2]],3),([[3,4]],7),([[4]],4),
            ([[5]],5),([[6]],6),([[7]],7)
        ])["status"],"ABSTAIN_TYPE_OR_INSUFFICIENT_EVIDENCE")
        self.assertIsNone(run_role_program(
            {"kind":"arbitrary_code_execution"},[[1],[1]]))

if __name__=="__main__":
    unittest.main()
