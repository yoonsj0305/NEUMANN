"""Post-first universal fold controls, across formerly unsupported output types."""
import unittest
from research.q3.universal_typed_state_fold_postfirst import (
    synthesis,run,expression,
)

def examples(inputs,fn):return [([x],fn(x)) for x in inputs]

class TypedUniversalFoldTests(unittest.TestCase):
    def test_list_to_integer_sum_and_product_not_predefined(self):
        rows=[[1,2,3],[2,3,4],[4,1,3],[5,6],[-2,7,8]]
        total=synthesis(examples(rows,sum))
        self.assertEqual(total["status"],"GENERATED_GENERIC_FOLD_AST")
        self.assertEqual(run(total["program"],[[4,-3,7]]),8)
        self.assertNotIn("sum",str(total["program"]))
        import math
        prod=synthesis(examples(rows,math.prod))
        self.assertEqual(prod["status"],"GENERATED_GENERIC_FOLD_AST")
        self.assertEqual(run(prod["program"],[[2,5,7]]),70)
        self.assertNotIn("prod",str(prod["program"]))

    def test_sequence_to_int_len_across_string_and_list(self):
        e=examples(["alpha","x","neumann","", "xyzz"],len)
        x=synthesis(e)
        self.assertEqual(run(x["program"],["orbit"]),5)
        p=synthesis(examples([[1,2],[2],[3,4,5],[8,9,1,1]],len))
        self.assertEqual(run(p["program"],[[1,1,1,1,1]]),5)

    def test_bool_state_aggregation_from_number_list(self):
        examples_values=[[1,2,3],[2,4],[3,5],[4,6,7],[7,1]]
        train=examples(examples_values,lambda a:7 in a)
        found=synthesis(train)
        self.assertEqual(found["status"],"GENERATED_GENERIC_FOLD_AST")
        self.assertEqual(run(found["program"],[[3,9,7,2]]),True)
        self.assertEqual(run(found["program"],[[3,9,2]]),False)

    def test_list_to_list_copy_and_generic_symbol_omit(self):
        x=synthesis(examples([[1,2,3],[3,4],[5,6,7]],lambda a:a))
        self.assertEqual(run(x["program"],[[8,10]]),[8,10])
        y=synthesis(examples([[1,0,2],[3,0],[0,6,0,7]],
                             lambda a:[z for z in a if z!=0]))
        self.assertEqual(run(y["program"],[[8,0,9]]),[8,9])

    def test_unknown_program_and_safe_boundaries_abstain(self):
        self.assertIsNone(run(["arbitrary_shell","exec"],[[1,2,3]]))
        self.assertIsNone(run(["fold_state",0,["mod",["s"],["lit",0]]],[[1]]))
        self.assertEqual(synthesis([([object()],1),([object()],1)])["status"],
                         "ABSTAIN_INPUT")

if __name__=="__main__":
    unittest.main()
