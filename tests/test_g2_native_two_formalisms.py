"""G2 synthetic, no selected original task bodies."""
import unittest
from research.g2.native_residual import (
  top_forms, form_name,first_define,prepare_bv_train,
  original_invariant_signature,prove_inv,prove_bv
)

SYN_BV="""(set-logic BV)
(define-fun helper ((x (_ BitVec 8))) (_ BitVec 8) (bvadd x #x01))
(synth-fun f ((x (_ BitVec 8))) (_ BitVec 8)
 ((Start (_ BitVec 8) (x (helper x) #x00))))
(constraint (= (f #x01) #x02))
(constraint (= (f #x02) #x03))
(check-synth)
"""

SYN_INV="""(set-logic LIA)
(synth-inv inv-f ((x Int)))
(declare-primed-var x Int)
(define-fun pre-f ((x Int)) Bool (= x 0))
(define-fun trans-f ((x Int) (x! Int)) Bool (= x! (+ x 1)))
(define-fun post-f ((x Int)) Bool (>= x 0))
(inv-constraint inv-f pre-f trans-f post-f)
(check-synth)
"""

class NativeTwoFormalismTests(unittest.TestCase):
 def test_train_only_heldout_exactly_one(self):
  v=prepare_bv_train(SYN_BV)
  self.assertTrue(v["ok"])
  self.assertEqual(v["constraint_count"],2)
  self.assertNotIn("(f #x02)",v["train"])
  self.assertIn("(f #x01)",v["train"])
  self.assertEqual(len(v["train_constraints"]),1)
 def test_invalid_same_ground_no_holdout(self):
  v=prepare_bv_train(SYN_BV.replace('(constraint (= (f #x02) #x03))',''))
  self.assertFalse(v["ok"])
 def test_original_invariant_and_safety_schema(self):
  i=original_invariant_signature(SYN_INV)
  self.assertTrue(i["ok"],i)
  self.assertEqual(i["name"],"inv-f")
  self.assertEqual(i["params"],[("x","Int")])
  self.assertEqual((i["pre"],i["trans"],i["post"]),("pre-f","trans-f","post-f"))
 def test_original_inv_verified_universal(self):
  # Source-free synthetic universal positive and negative invariant.
  v=original_invariant_signature(SYN_INV)
  good=prove_inv("(define-fun inv-f ((x Int)) Bool (>= x 0))",v)
  self.assertTrue(good["verified"],good)
  bad=prove_inv("(define-fun inv-f ((x Int)) Bool (= x 0))",v)
  self.assertFalse(bad["verified"],bad)
  self.assertEqual(bad["reason"],"INV_STEP_NOT_PROVEN")
 def test_original_BV_source_helper_ground_proved(self):
  v=prepare_bv_train(SYN_BV)
  good=prove_bv("(define-fun f ((x (_ BitVec 8))) (_ BitVec 8) (helper x))",v)
  self.assertTrue(good["verified"],good)
  bad=prove_bv("(define-fun f ((x (_ BitVec 8))) (_ BitVec 8) x)",v)
  self.assertFalse(bad["verified"],bad)
 def test_first_define_wrap_and_no_forge(self):
  s="(\n(define-fun inv-f ((x Int)) Bool (>= x 0))\n)"
  self.assertEqual(first_define(s,"inv-f"),"(define-fun inv-f ((x Int)) Bool (>= x 0))")
  self.assertIsNone(first_define(s,"f"))
 def test_exact_s_expression_constraints(self):
  fs=top_forms('; a comment ( is not a form\n'+SYN_INV)
  self.assertEqual(len([x for x in fs if form_name(x)=="inv-constraint"]),1)
  self.assertTrue(top_forms('(define-fun f ((s String)) String "Hello""(x)")'))

if __name__=="__main__":
 unittest.main()
