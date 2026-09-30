import unittest
from fractions import Fraction
from neumann1.natural_arithmetic_v078 import (
    Unsupported, parse_program, execute, independent_expression_value,
    observable_input, observe, admission,
)


class NaturalArithmeticContracts(unittest.TestCase):
    def test_separate_exact_evaluators_and_precedence(self):
        for expr, expected in (("4-3",1),("2+3*4",14),("20/2/5",2),
                               ("-(2+3)*4",-20),("0.1+0.2",Fraction(3,10)),
                               ("1/3+1/3+1/3",1),("8/(2*2)",2)):
            program=parse_program(expr)
            self.assertEqual(execute(program,share=False)[0],expected)
            self.assertEqual(execute(program,share=True)[0],expected)
            self.assertEqual(independent_expression_value(expr),expected)

    def test_shared_runtime_optimization_is_available_to_direct(self):
        program=parse_program("(2+3)*(2+3)")
        direct,dops=execute(program,share=False)
        shared,sops=execute(program,share=True)
        self.assertEqual(direct,shared)
        self.assertEqual((dops,sops),(3,2))

    def test_untrusted_constructs_and_budgets_fail_closed(self):
        for expr in ("__import__('os')","x+1","True+1","2**8","1e4", "1/0", "1+"*300,
                     "1234567890123456789+1", "2//1", "(2).real"):
            with self.assertRaises(Unsupported):
                execute(parse_program(expr),share=True)
            with self.assertRaises((Unsupported, ValueError)):
                independent_expression_value(expr)

    def test_reference_values_cannot_enter_observable_projection(self):
        row={"Body":"Alice has 4.","Question":"How many?", "Equation":"4-3",
             "Answer":1,"ID":"a","Type":"Subtraction"}
        first=observable_input(row)
        changed=dict(row,Equation="secret",Answer="secret",ID="secret",Type="secret")
        self.assertEqual(first,observable_input(changed))
        self.assertNotIn("secret",first)

    def test_rounding_and_wrong_labels_do_not_become_exact_success(self):
        row={"Body":"There are 1 and 3.","Question":"Divide?", "Equation":"1/3",
             "Answer":0.3333333333333333,"ID":"rounding"}
        self.assertEqual(observe(row)["status"],"ROUNDING_ONLY")
        row["Answer"]=42
        self.assertEqual(observe(row)["status"],"LABEL_DISAGREEMENT")

    def test_gate_does_not_promote_small_arithmetic_or_label_errors(self):
        summary={"exact_label_and_expression_rate":1.0,"gain_incidence":0.5,"median_direct_ms":2.0}
        self.assertEqual(admission(summary),"INVESTIGATE_NUMERIC_COMPRESSION_TARGET")
        for key,value in (("exact_label_and_expression_rate",0.999),
                          ("gain_incidence",0.0),("median_direct_ms",0.05)):
            self.assertEqual(admission(dict(summary,**{key:value})),"REJECT_SVAMP_NUMERIC_COMPRESSION_TARGET")

    def test_first_archive_is_complete_and_preserves_annotation_disagreement(self):
        import json
        from pathlib import Path
        result=json.loads((Path(__file__).resolve().parents[1]/
            "docs/experiments/results/v078_first_audit.json").read_text())
        rows=result["rows"]
        self.assertEqual(len(rows),1000)
        self.assertEqual(len({row["id"] for row in rows}),1000)
        self.assertTrue(all(row["original_expression_verified"] for row in rows))
        self.assertTrue(all(len(row[key])==9 for row in rows for key in ("direct_ms","shared_ms")))
        self.assertEqual(sum(row["status"]=="EXACT_MATCH" for row in rows),999)
        bad=[row for row in rows if row["status"]!="EXACT_MATCH"]
        self.assertEqual([row["id"] for row in bad],["chal-680"])
        self.assertEqual(bad[0]["exact_value"],[5,1])
        self.assertEqual(bad[0]["label_value"],[1,1])
        self.assertEqual(result["summary"]["gain_rows"],0)
        self.assertEqual(result["summary"]["timed_paths"],18000)
        self.assertEqual(result["source"]["exposure"],"all rows opened development only")
        self.assertIsNone(result["summary"]["raw_word_problem_solve_rate"])
        self.assertEqual(admission(result["summary"]),"REJECT_SVAMP_NUMERIC_COMPRESSION_TARGET")


if __name__ == "__main__":
    unittest.main()
