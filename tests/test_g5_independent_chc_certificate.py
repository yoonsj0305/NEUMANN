"""G5 source-free positive, negative, typed, multi-predicate CHC proof controls.

No G3 hard original problem opened, no neural model or original target.
"""
from __future__ import annotations
import json
import unittest

from research.g5.independent_chc_certificate import (
    prove,contract,forms,tokens,emit
)

INTEGER=b"""(set-logic HORN)
(declare-fun |inv| (Int) Bool)
(assert (forall ((x Int)) (=> (= x 0) (|inv| x))))
(assert (forall ((x Int) (y Int))
  (=> (and (|inv| x) (= y (+ x 1))) (|inv| y))))
(assert (forall ((x Int))
  (=> (and (|inv| x) (< x 0)) false)))
(check-sat)
"""

ARRAY=b"""(set-logic HORN)
(declare-fun R ((Array Int Int)) Bool)
(assert (forall ((A (Array Int Int)))
  (=> (= (select A 0) 0) (R A))))
(assert (forall ((A (Array Int Int)) (B (Array Int Int)) (v Int))
  (=> (and (R A) (= B (store A 1 v))) (R B))))
(assert (forall ((A (Array Int Int)))
  (=> (and (R A) (distinct (select A 0) 0)) false)))
(check-sat)
"""

MULTI=b"""(set-logic HORN)
(declare-fun P (Int) Bool)
(declare-fun Q (Int) Bool)
(assert (forall ((x Int)) (=> (= x 0) (P x))))
(assert (forall ((x Int)) (=> (P x) (Q x))))
(assert (forall ((x Int) (y Int))
  (=> (and (Q x) (= y (+ x 1))) (P y))))
(assert (forall ((x Int))
  (=> (and (P x) (< x 0)) false)))
(assert (forall ((x Int))
  (=> (and (Q x) (< x 0)) false)))
(check-sat)
"""

ADT=b"""(set-logic HORN)
(declare-datatypes ((List 0)) (((nil) (cons (hd Int) (tl List)))))
(declare-fun R (List) Bool)
(assert (R nil))
(assert (forall ((L List)) (=> (R L) (R L))))
(assert (forall ((L List)) (=> (and (R L) (distinct L nil)) false)))
(check-sat)
"""

UNSAFE=INTEGER.replace(b"(< x 0)",b"(> x 0)")

class G5OriginalCHCProofControls(unittest.TestCase):
    def test_lexer_uninterpreted_quote_and_comments(self):
        s='; fake (declare-fun FAIL () Bool)\n(declare-fun |P@bb40.i| ((Array Int Int)) Bool)'
        forms_read=forms(s)
        self.assertEqual(forms_read[0][1],"|P@bb40.i|")
        self.assertIn("(Array Int Int)",emit(forms_read[0]))
        self.assertEqual(len(forms_read),1)

    def test_exact_three_integer_universal_obligations(self):
        r=prove(INTEGER,{"|inv|":"(>= arg0 0)"})
        self.assertTrue(r["proof_pass"],r)
        self.assertEqual(r["checked_original_clauses"],3)
        self.assertEqual(r["original_predicate_count"],1)
        self.assertEqual(r["candidate_predicate_signatures"]["|inv|"],["Int"])
        self.assertEqual([x["counterexample_status"] for x in r["negative_rule_counterexample_checks"]],["unsat"]*3)
        self.assertEqual(r["Q3"],"OPEN")

    def test_mutant_integer_true_fails_original_safety(self):
        r=prove(INTEGER,{"|inv|":"true"})
        self.assertFalse(r["proof_pass"])
        self.assertIn("sat", [x["counterexample_status"] for x in r["negative_rule_counterexample_checks"]])

    def test_mutant_integer_false_fails_original_initial_state(self):
        r=prove(INTEGER,{"|inv|":"false"})
        self.assertFalse(r["proof_pass"])
        self.assertEqual(r["negative_rule_counterexample_checks"][0]["counterexample_status"],"sat")

    def test_exact_array_frame_complete_allstate(self):
        r=prove(ARRAY,{"R":"(= (select arg0 0) 0)"})
        self.assertTrue(r["proof_pass"],r)
        self.assertEqual(r["candidate_predicate_signatures"]["R"],["(Array Int Int)"])
        self.assertEqual(r["checked_original_clauses"],3)

    def test_wrong_array_frame_not_universal(self):
        r=prove(ARRAY,{"R":"true"})
        self.assertFalse(r["proof_pass"])
        self.assertTrue(any(c["counterexample_status"]=="sat" for c in r["negative_rule_counterexample_checks"]))

    def test_multi_predicate_interconnection(self):
        r=prove(MULTI,{"P":"(>= arg0 0)","Q":"(>= arg0 0)"})
        self.assertTrue(r["proof_pass"],r)
        self.assertEqual(r["checked_original_clauses"],5)
        self.assertEqual(r["original_predicate_count"],2)

    def test_multi_predicate_partial_missing_not_silently_allowed(self):
        with self.assertRaisesRegex(ValueError,"CHC_RELATION_WITNESS_COVERAGE_MISMATCH"):
            prove(MULTI,{"P":"(>= arg0 0)"})

    def test_extra_predicate_injected_rejected(self):
        with self.assertRaisesRegex(ValueError,"CHC_RELATION_WITNESS_COVERAGE_MISMATCH"):
            prove(MULTI,{"P":"true","Q":"true","Unknown":"true"})

    def test_adt_datatype_sort_positive(self):
        r=prove(ADT,{"R":"(= arg0 nil)"})
        self.assertTrue(r["proof_pass"],r)
        self.assertEqual(r["checked_original_clauses"],3)

    def test_adt_true_is_not_safety_proof(self):
        r=prove(ADT,{"R":"true"})
        self.assertFalse(r["proof_pass"])

    def test_actual_unsafe_source_has_no_spurious_positive(self):
        self.assertFalse(prove(UNSAFE,{"|inv|":"(>= arg0 0)"})["proof_pass"])
        self.assertFalse(prove(UNSAFE,{"|inv|":"true"})["proof_pass"])
        self.assertFalse(prove(UNSAFE,{"|inv|":"false"})["proof_pass"])

    def test_invalid_body_command_injection_rejected(self):
        with self.assertRaises((ValueError,Exception)):
            prove(INTEGER,{"|inv|":"true) (assert false) ("})

    def test_source_no_definitions_rejected(self):
        with self.assertRaisesRegex(ValueError,"MISSING_SOURCE_RULES_OR_RELATIONS"):
            prove(b"(set-logic HORN) (assert true) (check-sat)",{"R":"true"})

    def test_non_HORN_original_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_ORIGINAL_HORN_SOURCE"):
            prove(INTEGER.replace(b"(set-logic HORN)",b"(set-logic QF_LIA)"),
                  {"|inv|":"true"})

    def test_source_or_witness_sha_changes(self):
        good=prove(INTEGER,{"|inv|":"(>= arg0 0)"})
        good2=prove(INTEGER.replace(b"(|inv| x)","(|inv| x) "),{"|inv|":"(>= arg0 0)"})
        self.assertNotEqual(good["original_source_sha256"],good2["original_source_sha256"])
        bad=prove(INTEGER,{"|inv|":"true"})
        self.assertNotEqual(good["certificate_sha256"],bad["certificate_sha256"])

if __name__=="__main__":
    unittest.main()
