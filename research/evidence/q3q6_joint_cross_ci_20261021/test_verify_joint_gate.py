"""Synthetic fault injection ONLY, never a research benchmark result."""
import copy,unittest
from research.evidence.q3q6_joint_cross_ci_20261021.verify_joint_gate import dual,one
def proof(s):
    return {"expected":s,"Z3":s,"cvc5":s,"cvc5_exit":0,"dual_pass":True}
def source():
    return {
      "source":"SYNTHETIC_FALSIFICATION_NOT_BENCHMARK",
      "actual_original_SHA_authenticated":True,
      "dynamic_arity_original_canonical_success":True,
      "original_source_dynamic_arity":3,
      "all_three_alpha_signature_digests_identical_to_original":True,
      "original_source_and_renamed_3x_full_dual_equivalence_tests_passed":9,
      "negative_post_mutation_real_semantics_dual_SAT":True,
      "negative_post_mutation_canonical_sha_differs":True,
      "negative_original_source_dual_check_receipt":proof("sat"),
      "three_synthetic_renamed_semantic_source_test_cases":[{
        "renaming_seed":i,
        "source_canonical_alpha_name_order_sha_equal":True,
        "independent_dual_original_Pre_Trans_Post_pass_count":3,
        "independent_source_3_math_grammars_semantics_dual_equivalence":{
          k:{"original_vs_alpha_native_XOR_dual_proved_UNSAT":True,
             "independent_z3_cvc5_original_source_receipt":proof("unsat")}
          for k in ("pre","trans","post")}
      } for i in (1,2,3)]
    }
class FailClosed(unittest.TestCase):
    def test_positive_control(self):self.assertEqual(one(source()),9)
    def test_z3_forged(self):
        r=source();r["three_synthetic_renamed_semantic_source_test_cases"][0]["independent_source_3_math_grammars_semantics_dual_equivalence"]["pre"]["independent_z3_cvc5_original_source_receipt"]["Z3"]="sat"
        with self.assertRaises(AssertionError):one(r)
    def test_cvc5_forged(self):
        r=source();r["three_synthetic_renamed_semantic_source_test_cases"][0]["independent_source_3_math_grammars_semantics_dual_equivalence"]["post"]["independent_z3_cvc5_original_source_receipt"]["cvc5"]="unknown"
        with self.assertRaises(AssertionError):one(r)
    def test_missing_formula(self):
        r=source();del r["three_synthetic_renamed_semantic_source_test_cases"][0]["independent_source_3_math_grammars_semantics_dual_equivalence"]["post"]
        with self.assertRaises(AssertionError):one(r)
    def test_negative_mutation_disabled(self):
        r=source();r["negative_original_source_dual_check_receipt"]["cvc5_exit"]=1
        with self.assertRaises(AssertionError):one(r)
    def test_false_model_result_fails_dual(self):
        with self.assertRaises(AssertionError):dual({"expected":"unsat","Z3":"unsat","cvc5":"unknown","cvc5_exit":0,"dual_pass":True},"unsat")
if __name__=="__main__":unittest.main()
