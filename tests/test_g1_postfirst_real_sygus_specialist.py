"""Unit tests with synthetic SyGuS source, no new original target exposure."""
from __future__ import annotations
import unittest
from research.g1.postfirst_real_cvc5_specialist import (
    top_forms,parse_constraint,prepare_original,extract_define,gitblob,ground_verify,
)

SOURCE='''; hello ( not a real parenthesis )
(set-logic SLIA)
(synth-fun f ((name String)) String
    ((Start String (ntString))
     (ntString String (name " " (str.++ ntString ntString)))))
(constraint (= (f "Kara Lee") "Kara"))
(constraint (= (f "Yuna Kim") "Yuna"))
(check-synth)
'''

class G1SpecialistSmoke(unittest.TestCase):
    def test_top_level_original_forms(self):
        f=top_forms(SOURCE)
        self.assertEqual(len(f),5)
        self.assertTrue(f[2][2].startswith("(synth-fun f"))
    def test_exact_heldout_removed_not_training(self):
        p=prepare_original(SOURCE.encode())
        self.assertEqual(p["original_constraint_count"],2)
        self.assertIn('Kara Lee',p["train_source"])
        self.assertNotIn('Yuna Kim',p["train_source"])
        self.assertEqual(p["heldout_args"],['"Yuna Kim"'])
        self.assertEqual(p["heldout_gold"],'"Yuna"')
        self.assertIn("(synth-fun f",p["train_source"])
        self.assertIn("(check-synth)",p["train_source"])
        self.assertEqual(len(p["train_constraints"]),1)
    def test_nested_escaped_quotes_are_not_dropped(self):
        s='(constraint (= (f "A""B") "A""B"))'
        p=parse_constraint(s)
        self.assertEqual(p,(['"A""B"'],'"A""B"'))
    def test_cannot_silently_skip_source_assertion(self):
        text=SOURCE.replace('(constraint (= (f "Yuna Kim") "Yuna"))','')
        with self.assertRaisesRegex(ValueError,"MULTIPLE"):
            prepare_original(text.encode())
    def test_reject_unbalanced_source(self):
        with self.assertRaises(ValueError):
            top_forms('(constraint (= (f "A") "B")))')
    def test_extract_candidate_function_no_oracle(self):
        s='(\n(define-fun f ((name String)) String (str.substr name 0 4))\n)'
        out=extract_define(s)
        self.assertTrue(out.startswith("(define-fun f"))
        self.assertTrue(out.endswith(")"))
    def test_readonly_original_git_blob_digest(self):
        self.assertEqual(gitblob(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
    def test_independent_ground_verification_with_installed_cvc5(self):
        import shutil
        if not shutil.which("cvc5"):
            self.skipTest("CLI not present in local test; CI installs apt cvc5")
        candidate='(define-fun f ((name String)) String (str.substr name 0 4))'
        true=ground_verify(candidate,
             ['(constraint (= (f "Kara Lee") "Kara"))'],
             '(constraint (= (f "Yuna Kim") "Yuna"))',5)
        self.assertEqual(true["status"],"CANDIDATE_TRAIN_AND_HELDOUT_VERIFIED")
        false=ground_verify(candidate,
             ['(constraint (= (f "Kara Lee") "Kara"))'],
             '(constraint (= (f "Yuna Kim") "WRONG"))',5)
        self.assertEqual(false["status"],"CANDIDATE_NOT_INDEPENDENTLY_VERIFIED")

if __name__=="__main__":
    unittest.main()
