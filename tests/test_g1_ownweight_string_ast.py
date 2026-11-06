"""G1 smoke controls, only synthetic strings; no external source access."""
from __future__ import annotations
import random
import unittest
import numpy as np
from research.g1.ownweight_string_ast import (
  ATOMS,atom,features,run_ast,synthetic_task,make_data,
)


class G1SyntheticOnlyTests(unittest.TestCase):
 def test_compiled_two_token_ast(self):
  a=ATOMS.index("FIRST_WORD")
  b=ATOMS.index("DOT")
  self.assertEqual(run_ast((a,b),"Nadia Kim"),"Nadia.")

 def test_digit_prefix_and_suffix(self):
  self.assertEqual(atom("BEFORE_DIGIT","Honda125"),"Honda")
  self.assertEqual(atom("DIGIT_SUFFIX","Honda125"),"125")
  self.assertEqual(atom("DIGIT_SUFFIX","Kara"),"")

 def test_features_ignore_future_original_source(self):
  examples=[("Nadia Kim","Nadia"),("Kara Lee","Kara")]
  f=features(examples)
  self.assertEqual(f.shape,(96,))
  self.assertTrue(np.isfinite(f).all())
  # Features are deterministic and consume only TRAIN I/O.
  self.assertTrue(np.array_equal(f,features(list(examples))))

 def test_own_weight_targets_are_ast_tokens_not_program_ids(self):
  X,Y,observations=make_data(32,random.Random(41677))
  self.assertEqual(X.shape,(32,96))
  self.assertEqual(Y.shape,(32,2))
  self.assertTrue(np.all((Y>=0)&(Y<len(ATOMS))))
  for (train,heldout),tokens in zip(observations,Y):
   a,b=map(int,tokens)
   self.assertTrue(all(run_ast((a,b),x)==y for x,y in train))
   self.assertEqual(run_ast((a,b),heldout[0]),heldout[1])

 def test_heldout_synthetic_input_unexposed_to_model_features(self):
  training,tokens,hold=synthetic_task(random.Random(343))
  before=features(training)
  hold=("changed_unseen_identifier",hold[1])
  self.assertTrue(np.array_equal(before,features(training)))

 def test_original_syugus_eval_targets_are_not_imported(self):
  import inspect
  from research.g1 import ownweight_string_ast
  code=inspect.getsource(ownweight_string_ast)
  self.assertNotIn("SyGuS-Org/benchmarks",code)
  self.assertNotIn("phone-1.sl",code)
  self.assertNotIn("lastname.sl",code)


if __name__=="__main__":
 unittest.main()
