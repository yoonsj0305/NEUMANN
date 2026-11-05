"""No learned/model scores, private test answers, or sealed tasks are used in this assay."""
import copy
import unittest
from experiments.am2_opened_control_dominance import visible_family, _solver, evaluate_opened
from experiments.general_multiplier_tasks import multiplier_tasks, model_view
from neumann1.general_multiplier_contract import MultiplierBudget

class AM2ControlDominanceTests(unittest.TestCase):
    def test_all_original_opened_tasks_are_classified_from_public_input_only(self):
        tasks=multiplier_tasks()
        self.assertEqual(len(tasks),12)
        for task,private in tasks:
            view=model_view(task)
            self.assertEqual(visible_family(view),task["family"])
            self.assertNotIn("id",view)
            self.assertNotIn("family",view)
    def test_strong_model_free_tool_matches_neumann_on_eight_tasks(self):
        receipt=evaluate_opened()
        self.assertEqual(receipt["totals"]["TOOL"]["accepted"],8)
        self.assertEqual(receipt["totals"]["NEUMANN"]["accepted"],8)
        self.assertEqual(receipt["totals"]["TOOL"]["model_calls"],0)
        self.assertEqual(receipt["totals"]["NEUMANN"]["model_calls"],0)
        self.assertEqual(receipt["totals"]["NEUMANN"]["degraded_coding"],4)
        self.assertEqual(receipt["totals"]["TOOL"]["degraded_coding"],4)
        self.assertTrue(all(r["representation_certified"] for r in receipt["rows"] if r["arm"]=="NEUMANN" and r["accepted"]))
        self.assertTrue(all(not r["accepted"] for r in receipt["rows"] if r["inferred_family"]=="coding"))
        self.assertEqual(receipt["result"],"OPENED_8_OF_12_MODEL_FREE_MATCHED_TOOL_BASELINE")
    def test_fail_closed_on_unknown_ambiguous_or_external_metadata(self):
        self.assertIsNone(visible_family({}))
        self.assertIsNone(visible_family({"instruction":"?","public":{}}))
        self.assertIsNone(visible_family({"instruction":"?","public":{"requirement":"x","expression":"1","bindings":{}}}))
        self.assertIsNone(visible_family({"instruction":"?","public":{"expression":"1","bindings":{}}, "family":"math_logic"}))
    def test_original_math_checker_refuses_mutated_model_visible_problem(self):
        task,private=multiplier_tasks()[0]
        view=copy.deepcopy(model_view(task))
        view["public"]["bindings"]["a"]=19
        budget=MultiplierBudget()
        tool=_solver(task,private,view,"TOOL",budget)
        neumann=_solver(task,private,view,"NEUMANN",budget)
        self.assertFalse(tool["accepted"])
        self.assertFalse(neumann["accepted"])
        self.assertEqual(tool["checker_calls"],1)
        self.assertEqual(neumann["checker_calls"],0)
        self.assertIn("ValueError",neumann["error"])
    def test_no_program_source_is_invented_for_coding(self):
        task,private=multiplier_tasks()[4]
        view=model_view(task)
        r=_solver(task,private,view,"NEUMANN",MultiplierBudget())
        self.assertFalse(r["accepted"])
        self.assertEqual(r["tool_calls"],0)
        self.assertEqual(r["checker_calls"],0)
        self.assertIn("ABSTAIN_PROGRAM_SEMANTICS",r["error"])
if __name__=="__main__":
    unittest.main()
