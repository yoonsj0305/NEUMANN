"""Strong-tool admission against ORIGINAL opened 12, never model evidence."""
import copy
import unittest
from experiments.am2_strong_matched_baseline_admission import (
    evaluate,strong_one,check_compiler_identity,REFERENCE_COMPILER_GIT_BLOB
)
from experiments.general_multiplier_tasks import multiplier_tasks
from neumann1.am2_classical_code_compiler import compile_public_requirement,UnsupportedSpec

class StrongMatchedBaselineAdmission(unittest.TestCase):
    def test_unchanged_2026_10_19_baseline_source_blob(self):
        self.assertEqual(len(REFERENCE_COMPILER_GIT_BLOB),40)
        self.assertTrue(check_compiler_identity())
    def test_actual_opened_original_12_of_12(self):
        r=evaluate()
        self.assertEqual(r["result"],"STRONG_MATCHED_BASELINE_12_OF_12_AND_CAPABILITY_GATE_SATURATED")
        self.assertTrue(r["stronger_tool_catalogue_added"])
        self.assertFalse(r["plus_two_accuracy_gate_possible"])
        self.assertEqual(r["max_extra_accuracy_with_this_toolbox"],0)
        self.assertEqual(r["efficiency_gate"],"NOT_EVALUATED")
        self.assertEqual(r["global_Q1_Q7"],"OPEN")
        for a in ("TOOL","NEUMANN"):
            s=r["statistics"][a]
            self.assertEqual(s["terminal"],12)
            self.assertEqual(s["original_solved"],12)
            self.assertEqual(s["model_calls"],0)
            self.assertEqual(s["checker_calls"],12)
            self.assertEqual(s["by_family"],{
                "math_logic":4,"constraint_planning":4,"coding":4})
        self.assertEqual(sum(r["public_example_count"]>0 for r in r["rows"]),8)
        self.assertEqual(r["statistics"]["TOOL"]["tool_calls"],12)
        self.assertEqual(r["statistics"]["NEUMANN"]["tool_calls"],24)
    def test_stronger_compiler_responds_to_semantics_not_task_id(self):
        spec="Return the sum of distinct even integers in items, a list of integers."
        changed="Return the sum of distinct odd integers in items, a list of integers."
        self.assertNotEqual(compile_public_requirement(spec)["source"],
                            compile_public_requirement(changed)["source"])
    def test_unknown_or_inconsistent_specs_fail_closed(self):
        for spec in (
            "Return the sum of distinct prime integers in items, a list of integers.",
            "Return the sum of distinct negative even odd integers in items, a list of integers.",
            "Return the number of distinct positive negative integers in items, a list of integers.",
        ):
            with self.subTest(spec=spec),self.assertRaises(UnsupportedSpec):
                compile_public_requirement(spec)
    def test_private_gold_cannot_be_used_as_proposal_hint(self):
        task,private=multiplier_tasks()[4]
        x=strong_one(task,private,"TOOL")
        wrong=copy.deepcopy(private)
        wrong["tests"][0]["output"]=8123
        y=strong_one(task,wrong,"TOOL")
        self.assertEqual(x["candidate_sha256"],y["candidate_sha256"])
        self.assertTrue(x["accepted"])
        self.assertFalse(y["accepted"])
        self.assertEqual(y["checker_calls"],1)
    def test_mutated_original_requirement_not_always_compilable(self):
        task,private=multiplier_tasks()[4]
        bad=copy.deepcopy(task)
        bad["public"]["requirement"]="Return the median of primes in items."
        with self.assertRaises(UnsupportedSpec):
            strong_one(bad,private,"NEUMANN")

if __name__=="__main__":
    unittest.main()
