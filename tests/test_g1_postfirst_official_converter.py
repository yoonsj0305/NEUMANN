"""Official SyGuS IF1→IF2 source conservation negative controls. No target files."""
from __future__ import annotations
import unittest

from research.g1.postfirst_official_converter_cvc5 import (
    strict_original_train_examples,verify_exact_train_conservation
)
from research.g1.postfirst_real_cvc5_specialist import prepare_original

SRC='''(set-logic SLIA)
(synth-fun f ((name String)) String
  ((Start String (ntString))
   (ntString String (name " " (str.++ ntString ntString)))))
(declare-var name String)
(constraint (= (f "Kara Lee") "Kara"))
(constraint (= (f "Yuna Kim") "Yuna"))
(check-synth)
'''
CONVERTED='''(set-logic SLIA)
(synth-fun f ((name String)) String
    ((Start String) (ntString String))
    ((Start String (ntString))
    (ntString String (name " " (str.++ ntString ntString)))))
(declare-var name String)
(constraint (= (f "Kara Lee") "Kara"))
(check-synth)
'''


class G1OfficialFormatControls(unittest.TestCase):
 def test_last_gold_not_passed_to_converted_train(self):
  p=prepare_original(SRC.encode())
  examples=strict_original_train_examples(p)
  self.assertEqual(examples,[(('"Kara Lee"',),'"Kara"')])
  self.assertNotIn('"Yuna Kim"',p["train_source"])
  self.assertNotIn('"Yuna"',p["train_source"])
  self.assertEqual(p["heldout_gold"],'"Yuna"')
  self.assertTrue(verify_exact_train_conservation(examples,CONVERTED)["pass"])

 def test_forbid_changed_training_gold(self):
  p=prepare_original(SRC.encode())
  examples=strict_original_train_examples(p)
  tampered=CONVERTED.replace('(f "Kara Lee") "Kara"','(f "Kara Lee") "Other"')
  a=verify_exact_train_conservation(examples,tampered)
  self.assertFalse(a["pass"])
  self.assertEqual(a["error"],"TRAIN_EXAMPLES_CHANGED_DURING_CONVERSION")

 def test_forbid_deleted_training_constraint(self):
  p=prepare_original(SRC.encode())
  examples=strict_original_train_examples(p)
  tampered=CONVERTED.replace('(constraint (= (f "Kara Lee") "Kara"))','')
  a=verify_exact_train_conservation(examples,tampered)
  self.assertFalse(a["pass"])

 def test_different_argument_arity_cannot_pass(self):
  p=prepare_original(SRC.encode())
  examples=strict_original_train_examples(p)
  tampered=CONVERTED.replace('(f "Kara Lee")','(f "Kara" "Lee")')
  a=verify_exact_train_conservation(examples,tampered)
  self.assertFalse(a["pass"])

 def test_different_constraint_order_cannot_pass(self):
  train='''(set-logic SLIA)
    (synth-fun f ((name String)) String ((Start String) (ntString String)) ((Start String (ntString)) (ntString String (name))))
    (constraint (= (f "B") "B"))
    (constraint (= (f "A") "A"))
    (check-synth)'''
  a=verify_exact_train_conservation(
      [(('"A"',),'"A"'),(('"B"',),'"B"')],train)
  self.assertFalse(a["pass"])

if __name__=="__main__":
 unittest.main()
