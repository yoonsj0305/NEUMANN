"""Q3 generic program invention, learned grammar, causal and safety tests."""
import math
import unittest

from research.q3.universal_recursive_meta_inventor import (
    InventingLanguage,enumerate_solution,run,safe_eval,generalize_two_programs,
)
from research.q3.codearc_universal_meta_external_first import parse_case,cohort


def pairs(xs,fn):
    return [([x],fn(x)) for x in xs]


class UniversalRecursiveInventionTests(unittest.TestCase):
    def setUp(self):
        self.words=[[1,2,3],[2,4],[3,2,1],[5],[1,6,5]]

    def test_invents_list_reverse_no_named_reverse_primitive(self):
        train=pairs(self.words,lambda x:x[::-1])
        result=enumerate_solution(train,34000)
        self.assertEqual(result["status"],"invented_recursive_operator")
        program=result["program"]
        self.assertEqual(program[0],"recur")
        self.assertNotIn("reverse",str(program))
        self.assertEqual(run(program,[["x",7,"y",9]]),[9,"y",7,"x"])
        self.assertEqual(run(program,[[]]),[])
        baseline=enumerate_solution(train,2000,allow_recursive=False)
        self.assertIsNone(baseline["program"])

    def test_invents_polymorphic_string_reverse(self):
        train=pairs(["cat","cab","z","xy","abb"],lambda x:x[::-1])
        result=enumerate_solution(train,34000)
        self.assertEqual(result["status"],"invented_recursive_operator")
        self.assertEqual(run(result["program"],["orbital"]),"latibro")

    def test_invents_numeric_recursion_and_true_language_expansion(self):
        lang=InventingLanguage()
        nsum=lang.solve(pairs(self.words,sum),34000)
        nprod=lang.solve(pairs(self.words,math.prod),34000)
        self.assertEqual(nsum["status"],"invented_recursive_operator")
        self.assertEqual(nprod["status"],"invented_recursive_operator")
        self.assertGreaterEqual(len(lang.grammar),1)
        template=lang.dump()["grammar"][0]
        self.assertEqual(len(template["sources"]),2)
        target=pairs(self.words,lambda xs:-sum(xs))
        without=enumerate_solution(target,5000)
        self.assertIsNone(without["program"])
        discovered=lang.solve(target,5000)
        self.assertEqual(discovered["status"],"learned_meta_grammar")
        self.assertLessEqual(discovered["attempts"],50)
        self.assertEqual(run(discovered["program"],[[10,-2,3]]),-11)
        self.assertEqual(len(lang.definitions),3)

    def test_learned_not_reused_on_incompatible_type(self):
        lang=InventingLanguage()
        lang.solve(pairs(self.words,sum),34000)
        self.assertEqual(len(lang.definitions),1)
        reverse=pairs(["cat","can","boo"],lambda x:x[::-1])
        result=lang.solve(reverse,34000)
        self.assertEqual(result["status"],"invented_recursive_operator")
        self.assertNotEqual(lang.definitions[0]["program"],result["program"])

    def test_unknown_instruction_and_runtime_invalid_abstain(self):
        ok,v=safe_eval(["invent_free_python_opcode","..."],{"x":1})
        self.assertFalse(ok)
        self.assertIsNone(run(["recur",[],["cat",["v","s"],["c",0]],
                               ["v","s"],"fold"],[[1,2,3]]))
        self.assertIsNone(run(["recur",0,["mul",["v","s"],["c",2]],
                               ["v","s"],"fold"],[[0]*110]))

    def test_real_benchmark_input_parser_strips_function_name_and_prompt(self):
        sample={
            "errored":False,
            "input":"print('Result 1: ' + str(calculate_gcd(48, 18)))",
            "output":"Result 1: 6",
        }
        self.assertEqual(parse_case(sample),([48,18],6))
        another={
            "errored":False,
            "input":"print('Result 1: ' + str(find_shortest_palindrome_start_with('cat')))",
            "output":"Result 1: catac",
        }
        self.assertEqual(parse_case(another),(["cat"],"catac"))

    def test_external_cohort_predeclared_and_early_seen_excluded(self):
        self.assertFalse(any(cohort(i) for i in range(21)))
        self.assertEqual(cohort(134),cohort(134))


if __name__=="__main__":
    unittest.main()
