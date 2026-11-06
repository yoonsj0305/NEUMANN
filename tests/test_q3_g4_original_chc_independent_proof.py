"""Real CHC grammar independent proof tests. NO reserved originals used."""
import unittest
from research.g4.generic_chc_independent_proof import (
 parse,render,source_contract,independent_verify_original_chc_sat,
)

FILL_HORN="""(set-logic HORN)
(declare-fun Entry () Bool)
(declare-fun Inv (Int Int (Array Int Int)) Bool)
(assert Entry)
(assert (forall ((n Int) (A (Array Int Int)))
    (=> (and Entry (>= n 0)) (Inv 0 n A))))
(assert (forall ((i Int) (n Int) (A (Array Int Int)) (A2 (Array Int Int)))
    (=> (and (Inv i n A) (< i n) (= A2 (store A i 7)))
        (Inv (+ i 1) n A2))))
(assert (forall ((i Int) (n Int) (A (Array Int Int)))
    (=> (and (Inv i n A) (= i n))
        (forall ((k Int))
          (=> (and (<= 0 k) (< k n)) (= (select A k) 7))))))
(check-sat)
(exit)
"""
FILL_REL={
  "Entry":{"params":[],"body":"true"},
  "Inv":{"params":["i","n","A"],"body":"""(and (<= 0 i) (<= i n)
     (forall ((k Int))
       (=> (and (<= 0 k) (< k i)) (= (select A k) 7))))"""},
}
COPY_HORN="""(set-logic HORN)
(declare-fun Inv (Int Int (Array Int Int) (Array Int Int)) Bool)
(assert (forall ((n Int) (A (Array Int Int)) (B (Array Int Int)))
    (=> (>= n 0) (Inv 0 n A B))))
(assert (forall ((i Int) (n Int) (A (Array Int Int))
                 (B (Array Int Int)) (B2 (Array Int Int)))
    (=> (and (Inv i n A B) (< i n)
        (= B2 (store B i (select A i))))
        (Inv (+ i 1) n A B2))))
(assert (forall ((i Int) (n Int) (A (Array Int Int)) (B (Array Int Int)))
    (=> (and (Inv i n A B) (= i n))
        (forall ((k Int))
         (=> (and (<= 0 k) (< k n))
             (= (select B k) (select A k)))))))
(check-sat)
"""
COPY_REL={
  "Inv":{"params":["i","n","A","B"],"body":"""(and (<= 0 i) (<= i n)
      (forall ((k Int))
       (=> (and (<= 0 k) (< k i))
           (= (select B k) (select A k)))))"""},
}

class IndependentRealSMTHornProofTests(unittest.TestCase):
 def test_smt_parser_preserves_array_types_and_bar_symbols(self):
    x=parse('(declare-fun |main@bb19.i| (Int (Array Int Int)) Bool) ;comment\n (check-sat)')
    self.assertEqual(len(x),2)
    self.assertEqual(x[0][1],"|main@bb19.i|")
    self.assertEqual(render(x[0]),"(declare-fun |main@bb19.i| (Int (Array Int Int)) Bool)")
    self.assertEqual(source_contract(FILL_HORN)["relations"]["Inv"],
       ["Int","Int",["Array","Int","Int"]])
 def test_original_source_fill_sat_verified_all_four_assertions(self):
    v=independent_verify_original_chc_sat(FILL_HORN,FILL_REL,timeout_ms=4500)
    self.assertTrue(v["verified"],v)
    self.assertEqual(v["original_assertion_count"],4)
    self.assertTrue(all(x["counterexample"]=="unsat" for x in v["independent_checks"]))
 def test_forged_vacuous_true_invariant_rejected_by_original_post(self):
    forged={k:dict(v) for k,v in FILL_REL.items()}
    forged["Inv"]={"params":["i","n","A"],"body":"true"}
    v=independent_verify_original_chc_sat(FILL_HORN,forged,timeout_ms=4500)
    self.assertFalse(v["verified"],v)
    self.assertEqual(v["status"],"NOT_INDEPENDENTLY_PROVED")
 def test_zero_entry_mutation_not_a_valid_safety_certificate(self):
    forged={k:dict(v) for k,v in FILL_REL.items()}
    forged["Entry"]={"params":[],"body":"false"}
    v=independent_verify_original_chc_sat(FILL_HORN,forged,timeout_ms=4500)
    self.assertFalse(v["verified"],v)
 def test_copy_relational_unbounded_array_model_proved(self):
    v=independent_verify_original_chc_sat(COPY_HORN,COPY_REL,timeout_ms=4500)
    self.assertTrue(v["verified"],v)
    self.assertEqual(v["original_assertion_count"],3)
 def test_copy_mutant_wrong_value_relation_rejected(self):
    forged={"Inv":{"params":["i","n","A","B"],"body":
       COPY_REL["Inv"]["body"].replace("(select A k)","(+ 1 (select A k))")}}
    v=independent_verify_original_chc_sat(COPY_HORN,forged,timeout_ms=4500)
    self.assertFalse(v["verified"],v)
 def test_reject_untrusted_candidate_changing_source_or_command(self):
    fake={"Inv":{"params":["i","n","A","B"],"body":"true) (assert true"}}
    with self.assertRaises(ValueError):
       independent_verify_original_chc_sat(COPY_HORN,fake)
 def test_all_original_uninterpreted_relations_must_be_supplied(self):
    with self.assertRaises(ValueError):
       independent_verify_original_chc_sat(FILL_HORN,{"Inv":FILL_REL["Inv"]})
 def test_candidate_original_sort_arity_guard(self):
    fake={"Inv":{"params":["i","A"],"body":"true"}}
    with self.assertRaises(ValueError):
       independent_verify_original_chc_sat(COPY_HORN,fake)
 def test_disallow_cyclic_model_proposal(self):
    fake={"Inv":{"params":["i","n","A","B"],"body":"(Inv i n A B)"}}
    with self.assertRaises(ValueError):
       independent_verify_original_chc_sat(COPY_HORN,fake)


if __name__=="__main__":
 unittest.main()
