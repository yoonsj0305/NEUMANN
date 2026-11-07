"""Parser-only controls for independent HumanEval benchmark; no original read."""
import unittest
from research.q3.learn_grammar_then_humaneval_original_first import (
    extract_original_assertions,parse_humaneval_assert,
)
import ast

class HumanEvalSafeSourceTests(unittest.TestCase):
    def test_parse_literal_original_style_assertions(self):
        code="""
def check(candidate):
    assert candidate([1,2,3,4,5,6]) == [1,3,5]
    assert candidate([0,1,2,3]) == [1,3]
    assert candidate([10,11,12,13]) == [11,13]
    assert candidate([-3,-2,-1,0]) == [-3,-1]
"""
        cases=extract_original_assertions(code)
        self.assertEqual(len(cases),4)
        self.assertEqual(cases[0],([[1,2,3,4,5,6]],[1,3,5]))
        self.assertEqual(cases[-1],([[-3,-2,-1,0]],[-3,-1]))

    def test_refuse_potentially_unsafe_reference_tests_without_execution(self):
        for testcase in [
            "def check(candidate):\n assert candidate(__import__('os').system('pwd')) == 0\n assert True\n assert True\n assert True",
            "def check(candidate):\n assert candidate([1]) == [1]\n exec('x=1')\n assert candidate([2]) == [2]\n assert candidate([3]) == [3]",
            "def check(candidate):\n assert candidate([1]) != [1]\n assert candidate([2]) == [2]\n assert candidate([3]) == [3]\n assert candidate([4]) == [4]",
        ]:
            with self.assertRaises(ValueError):
                extract_original_assertions(testcase)

    def test_requires_multiple_distinct_heldout_author_examples(self):
        with self.assertRaises(ValueError):
            extract_original_assertions(
                "def check(candidate):\n assert candidate([1,2]) == [2]\n assert candidate([3,4]) == [4]")

if __name__=="__main__":
    unittest.main()
