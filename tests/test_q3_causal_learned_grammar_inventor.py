"""Q3 generic grammar invention causal controls, no HumanEval source accessed."""
import unittest
from research.q3.causal_learned_grammar_inventor import (
    source_lowering,learn_production,solve,run_operator,
    scorable,antiunify,substitute,decompose_examples,pred_eval,
)

def prior(task,remainder):
    return {
        "task_id":task,
        "original_heldout_exact":True,
        "program":{
            "kind":"DefineGeneratedOperator",
            "predicate":["mod_equals",2,remainder],
            "ast":["fold",["arg",0],["empty_like",["arg",0]],
                   ["if",["ApplyGeneratedBooleanExpression",
                          ["mod_equals",2,remainder],["item"]],
                    ["acc"],["append",["acc"],["item"]]]],
        },
    }

class CausalMetaGrammarTests(unittest.TestCase):
    def setUp(self):
        self.old=[prior(554,0),prior(629,1)]

    def test_meta_discovers_new_named_grammar_production(self):
        result=learn_production(self.old)
        self.assertEqual(result["type"],"DefineNewGrammarProduction")
        self.assertEqual(result["source_operator_programs"],[554,629])
        self.assertEqual(result["variable_parameters"],1)
        self.assertEqual(result["pattern_ast"],[
            "fold","keep_if_false",
            ["eq",["mod",["item"],["lit",2]],["hole",0]]])
        self.assertTrue(result["name"].startswith("invented_grammar_"))
        self.assertFalse(result["base_vm_modified"])

    def test_bounded_causal_advantage_same_core_same_budget(self):
        grammar=learn_production(self.old)
        train=[([list(range(0,32))],[x for x in range(0,32) if x%2]),
               ([list(range(11,37))],[x for x in range(11,37) if x%2])]
        first=solve(train,rule=grammar,budget=16)
        cold=solve(train,rule=None,budget=16)
        unlimited=solve(train,rule=None,budget=150)
        self.assertIsNotNone(first["program"])
        self.assertEqual(first["status"],"INVENTED_GRAMMAR_PRODUCTION")
        self.assertEqual(first["attempts"],1)
        self.assertIsNone(cold["program"])
        self.assertEqual(cold["attempts"],16)
        self.assertIsNotNone(unlimited["program"])
        self.assertGreater(unlimited["attempts"],first["attempts"])
        test=[-9,-8,-7,-6,-5,-4,-3,-2,-1,0,1,2,3,4,77,78,99]
        self.assertEqual(run_operator(first["program"],[test]),
                         [x for x in test if x%2])

    def test_other_parity_value_and_container_properly_generalize(self):
        grammar=learn_production(self.old)
        train=[([list(range(0,30))],[x for x in range(30) if x%2==0]),
               ([list(range(10,40))],[x for x in range(10,40) if x%2==0])]
        result=solve(train,rule=grammar,budget=16)
        self.assertEqual(result["attempts"],2)
        self.assertEqual(run_operator(result["program"],
                         [(11,12,13,14,-15,-16)]),(12,14,-16))

    def test_wrong_semantics_and_bad_types_abstain(self):
        grammar=learn_production(self.old)
        self.assertIsNone(solve([
            (["abc"],"cba"),(["hello"],"olleh")],
            rule=grammar,budget=16)["program"])
        self.assertIsNone(decompose_examples([
            ([list([1,1])],[1]),([[1]],[1])]))
        with self.assertRaises(ValueError):
            learn_production([self.old[0],{
                **self.old[1],"original_heldout_exact":False}])
        self.assertIsNone(run_operator(
            ["fold","keep_if_false",["eq",["mod",["item"],["lit",0]],
                                     ["lit",1]]],[[1,2,3]]))

    def test_base_vm_no_named_predicate_mod_equals(self):
        a=source_lowering(self.old[0]["program"])
        self.assertNotIn("mod_equals",str(a))
        self.assertEqual(pred_eval(["eq",["mod",["item"],["lit",2]],
                                    ["lit",1]],-9),True)
        self.assertEqual(pred_eval(["eq",["mod",["item"],["lit",2]],
                                    ["lit",0]],-9),False)

if __name__=="__main__":
    unittest.main()
