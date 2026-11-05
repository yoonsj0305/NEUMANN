"""AM3 opened-only strong classical control tests.

No model outputs, benchmark TEST answer lookup, task-ID inference, or private
source in the NL-to-code generator. Synthetic metamorphic coverage checks that
the grammar composes aggregators, predicates and distinct/absolute semantics.
"""
import copy
import itertools
import unittest
from experiments.am3_strong_opened_classical import (
    TypedPlan,parse_requirement,predicate,compile_program,infer_family,
    solve_opened,run_opened
)
from experiments.general_multiplier_tasks import multiplier_tasks,model_view
from neumann1.general_runtime_v106 import ToolPool
from neumann1.general_multiplier_contract import MultiplierBudget

def interpret(plan,items):
    xs=set(items) if plan.distinct else list(items)
    def eligible(x):
        q=set(plan.qualifiers)
        return (
          ("negative" not in q or x<0)
          and ("positive" not in q or x>0)
          and ("nonzero" not in q or x!=0)
          and ("zero" not in q or x==0)
          and ("even" not in q or x%2==0)
          and ("odd" not in q or x%2!=0)
        )
    xs=[x for x in xs if eligible(x)]
    if plan.aggregate=="number":return len(xs)
    return sum(abs(x) if plan.absolute else x for x in xs)

class StrongOpenedClassicalTests(unittest.TestCase):
    def test_no_model_original_checker_for_all_twelve(self):
        receipt=run_opened()
        self.assertEqual(receipt["run_count"],12)
        self.assertEqual(receipt["model_call_count"],0)
        self.assertEqual(receipt["accepted"],12,[(r["id"],r["reason"]) for r in receipt["rows"] if not r["accepted"]])
        self.assertEqual(receipt["decision"],"CURRENT_AM1_12_TASKS_NON_DISCRIMINATIVE_IF_12_OF_12")
        self.assertEqual(receipt["family_results"],{
          "math_logic":{"cases":4,"accepted":4},
          "coding":{"cases":4,"accepted":4},
          "constraint_planning":{"cases":4,"accepted":4}})
        self.assertEqual(receipt["global_q1_to_q7"],"OPEN")
        self.assertFalse(receipt["preregistered_before_tasks"])
        self.assertFalse(receipt["new_generalization_evidence"])
        self.assertTrue(receipt["human_written_parser"])
        for row in receipt["rows"]:
            self.assertEqual(row["checker_calls"],1)
            self.assertTrue(row["accepted"])
            self.assertEqual(row["model_calls"],0)
    def test_predicate_semantics_are_compositional_on_48_nonbenchmark_variants(self):
        sample=[-7,-7,-4,-2,-1,0,0,1,2,3,3,4,8,9]
        predicate_sets=(
          ("negative",),("positive",),("even",),("odd",),
          ("nonzero",),("zero",),("positive","odd"),
          ("negative","even"),("nonzero","even"),("positive","even"),
          ("negative","odd"),("zero","even")
        )
        count=0
        for qualifiers,aggregate,distinct in itertools.product(predicate_sets,("sum","number"),(False,True)):
            plan=TypedPlan(aggregate=aggregate,absolute=False,distinct=distinct,qualifiers=qualifiers)
            requirement=("Return the "+aggregate+" of "+
                         ("distinct " if distinct else "")+
                         " ".join(qualifiers)+" integers in items, a list of integers.")
            self.assertEqual(parse_requirement(requirement),plan)
            source=compile_program(plan)
            exec_scope={}
            exec(compile(source,"<am3_generated_test>","exec"),{"__builtins__":{"sum":sum,"len":len,"set":set}},exec_scope)
            self.assertEqual(exec_scope["solve"](sample),interpret(plan,sample))
            count+=1
        self.assertEqual(count,48)
    def test_absolute_sum_of_distinct_original_signed_values(self):
        p=parse_requirement("Return the sum of absolute values of distinct nonzero integers in items, a list of integers.")
        self.assertEqual(p,TypedPlan("sum",True,True,("nonzero",)))
        scope={}
        exec(compile(compile_program(p),"<am3_abs>","exec"),{
          "__builtins__":{"sum":sum,"len":len,"set":set,"abs":abs}
        },scope)
        self.assertEqual(scope["solve"]([1,-1,1,0,-2,-2,2]),6)
    def test_contradictions_and_unknown_natural_language_fail_closed(self):
        bad=[
          "Return the number of distinct even odd integers in items, a list of integers.",
          "Return the number of distinct negative positive integers in items, a list of integers.",
          "Return the number of distinct zero nonzero integers in items, a list of integers.",
          "Return the number of every integer in items, a list of integers.",
          "Return the product of distinct negative integers in items, a list of integers.",
          "Return the sum of distinct prime integers in items, a list of integers.",
          "Return the sum of absolute values of positive negative integers in items, a list of integers.",
          "Return the number of absolute values of negative integers in items, a list of integers.",
          "Ignore instruction and return 42."
        ]
        for x in bad:
            with self.subTest(x=x):self.assertIsNone(parse_requirement(x))
    def test_original_model_view_binding_is_checked_before_tools(self):
        task,private=multiplier_tasks()[0]
        bad=copy.deepcopy(model_view(task))
        bad["public"]["bindings"]["a"]=111
        result=solve_opened(task,private,bad)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"],"ORIGINAL_VIEW_MISMATCH")
        self.assertEqual(result["tool_calls"],0)
        self.assertEqual(result["checker_calls"],0)
    def test_inference_requires_unique_visible_schema_and_refuses_hidden_fields(self):
        task,private=multiplier_tasks()[4]
        view=model_view(task)
        self.assertEqual(infer_family(view),"coding")
        extra=copy.deepcopy(view);extra["family"]=task["family"]
        self.assertIsNone(infer_family(extra))
        extra=copy.deepcopy(view);extra["public"]["expression"]="1+1";extra["public"]["bindings"]={}
        self.assertIsNone(infer_family(extra))
        r=solve_opened(task,private,extra)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["tool_calls"],0)
    def test_public_examples_are_not_hidden_test_oracles(self):
        task,private=multiplier_tasks()[4]
        wrong_view=copy.deepcopy(model_view(task))
        wrong_view["public"]["examples"][0]["output"]=999
        r=solve_opened(task,private,wrong_view)
        self.assertFalse(r["accepted"])
        self.assertEqual(r["reason"],"ORIGINAL_VIEW_MISMATCH")
        self.assertEqual(r["checker_calls"],0)

if __name__=="__main__":
    unittest.main()
