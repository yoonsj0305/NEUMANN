"""Independent universal candidate verifier: truly separate SMT proof tests.

No CHC native synthesizer is run. No NEUMANN weights. Demonstrate a
single verifier handles two distinct mathematical sorts and rejects
counterexamples, unsupported source, prompt-like forged extra clauses,
wrong sorts and missing solver rather than emitting false PASS.
"""
import unittest

from research.q3.independent_horn_model_verifier import (
    sexps,validate_model,verify
)

INT_SOURCE="""(set-logic HORN)
(declare-fun Inv (Int) Bool)
(assert (forall ((x Int)) (=> (= x 0) (Inv x))))
(assert (forall ((x Int) (y Int))
    (=> (and (Inv x) (= y (+ x 1))) (Inv y))))
(assert (forall ((x Int)) (=> (and (Inv x) (< x 0)) false)))
(check-sat)
(exit)
"""
ARRAY_SOURCE="""(set-logic HORN)
(declare-fun Inv ((Array Int Int) Int) Bool)
(assert (forall ((a (Array Int Int)) (i Int))
    (=> (= (select a i) 0) (Inv a i))))
(assert (forall ((a (Array Int Int)) (i Int) (b (Array Int Int)))
    (=> (and (Inv a i) (= b (store a i 0))) (Inv b i))))
(assert (forall ((a (Array Int Int)) (i Int))
    (=> (and (Inv a i) (not (= (select a i) 0))) false)))
(check-sat)
"""
GOOD_INT="(define-fun Inv ((x Int)) Bool (>= x 0))"
BAD_INT="(define-fun Inv ((x Int)) Bool (= x 0))"
GOOD_ARRAY="(define-fun Inv ((a (Array Int Int)) (i Int)) Bool (= (select a i) 0))"
BAD_ARRAY="(define-fun Inv ((a (Array Int Int)) (i Int)) Bool true)"


class SourceIndependentHornProofTests(unittest.TestCase):
    def test_exact_original_integer_universal_all_three(self):
        result=verify(INT_SOURCE,GOOD_INT,"Inv")
        self.assertEqual(result["proof_status"],"ALL_ORIGINAL_HORN_ASSERTIONS_PROVED",result)
        self.assertEqual(result["original_source_assertions"],3)
        self.assertEqual(result["clauses_checked"],3)
        self.assertEqual(result["relation_arity"],1)
        self.assertTrue(result["all_clause_violations_unsat"])
        self.assertFalse(result["trained_NEUMANN_weights"])
        self.assertEqual(result["Q3_learned_invention"],"NOT_PROVEN")

    def test_original_integer_bad_invariant_inductive_counterexample(self):
        result=verify(INT_SOURCE,BAD_INT,"Inv")
        self.assertEqual(result["proof_status"],"REFUTED_BY_ORIGINAL_SOURCE",result)
        self.assertEqual(result["first_failed_assertion"],1)
        self.assertEqual(result["evidence"][-1]["verdict"],"REFUTED_SAT")

    def test_generic_array_index_quantifier_proof_all_three(self):
        result=verify(ARRAY_SOURCE,GOOD_ARRAY,"Inv")
        self.assertEqual(result["proof_status"],"ALL_ORIGINAL_HORN_ASSERTIONS_PROVED",result)
        self.assertEqual(result["original_source_assertions"],3)
        self.assertEqual(result["relation_arity"],2)

    def test_array_mutant_true_refuted_without_claim_of_Q3(self):
        result=verify(ARRAY_SOURCE,BAD_ARRAY,"Inv")
        self.assertEqual(result["proof_status"],"REFUTED_BY_ORIGINAL_SOURCE",result)
        self.assertEqual(result["evidence"][-1]["verdict"],"REFUTED_SAT")

    def test_extra_candidate_injected_false_assertion_not_accepted(self):
        bad=GOOD_INT+"\n(assert false)"
        out=verify(INT_SOURCE,bad,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")
        self.assertIn("SINGLE_DEFINE_FUN",out["error"])

    def test_wrong_parameter_sort_fails_closed(self):
        bad="(define-fun Inv ((x Bool)) Bool true)"
        out=verify(INT_SOURCE,bad,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")
        self.assertIn("PARAMETER_SORT",out["error"])

    def test_wrong_array_arity_fails_closed(self):
        bad="(define-fun Inv ((a (Array Int Int))) Bool true)"
        out=verify(ARRAY_SOURCE,bad,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")
        self.assertIn("ARITY",out["error"])

    def test_candidate_recursion_not_source_witness(self):
        bad="(define-fun Inv ((x Int)) Bool (Inv x))"
        out=verify(INT_SOURCE,bad,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")
        self.assertIn("SELF_REFERENTIAL",out["error"])

    def test_no_original_assertions_is_not_proved(self):
        src="(set-logic HORN)\n(declare-fun Inv (Int) Bool)\n(check-sat)"
        out=verify(src,GOOD_INT,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")

    def test_original_source_runtime_command_not_allowed(self):
        src=INT_SOURCE.replace("(check-sat)","(check-sat)\n(get-model)")
        out=verify(src,GOOD_INT,"Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")
        self.assertIn("UNAPPROVED",out["error"])

    def test_missing_solver_is_open_not_pass(self):
        out=verify(INT_SOURCE,GOOD_INT,"Inv",solver="NEUMANN_TEST_MISSING_SOLVER_INVALID")
        self.assertEqual(out["proof_status"],"OPEN_OR_INFRA_NO_PROOF",out)
        self.assertFalse(out.get("all_clause_violations_unsat",False))

    def test_quoted_literals_comments_preserve_s_expression(self):
        items=sexps(';(ignore (foo))\n(define-fun g ((s String)) String "hello""world")')
        self.assertEqual(len(items),1)
        self.assertEqual(items[0][0],"define-fun")
        self.assertEqual(items[0][4],'"hello""world"')

    def test_lexical_unbalanced_fails_closed(self):
        out=verify(INT_SOURCE,GOOD_INT+"(","Inv")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")

    def test_mismatched_relation_name_not_accepted(self):
        out=verify(INT_SOURCE,GOOD_INT,"Other")
        self.assertEqual(out["proof_status"],"INVALID_CANDIDATE_OR_SOURCE")

    def test_control_metadata_has_source_and_candidate_hashes(self):
        src=validate_model(ARRAY_SOURCE,GOOD_ARRAY,"Inv")
        self.assertEqual(src["source_assertions"],3)
        self.assertEqual(len(src["source_sha256"]),64)
        self.assertEqual(len(src["candidate_sha256"]),64)


if __name__=="__main__":
    unittest.main()
