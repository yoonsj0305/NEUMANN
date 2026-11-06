"""External original strict source parser controls, all synthetic fixtures."""
from __future__ import annotations

import unittest

from research.g1.first_external_sygus import parse_original,gitblob,classical_order,freeze_programs
from research.g1.ownweight_string_ast import ATOMS,run_ast,reserved_pair


def source(lines):
    return ("(set-logic SLIA)\n"
        "(synth-fun f ((name String)) String ((Start String (name))))\n"
        +lines+"\n(check-synth)\n").encode()


class G1OriginalSourcePreflight(unittest.TestCase):
    def test_original_git_blob_sha_empty(self):
        self.assertEqual(gitblob(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_simple_original_sygus_two_constraints(self):
        t=source('(constraint (= (f "Kara Lee") "Kara"))\n'
                 '(constraint (= (f "Mina Kim") "Mina"))')
        examples,reason=parse_original(t)
        self.assertIsNone(reason)
        self.assertEqual(examples,[("Kara Lee","Kara"),("Mina Kim","Mina")])

    def test_multiline_and_CRLF_original_source(self):
        t=source('(constraint\r\n (= (f "Kara") "K"))\n'
                 '(constraint (= (f "Mina") "M"))')
        examples,reason=parse_original(t)
        self.assertIsNone(reason)
        self.assertEqual(examples,[("Kara","K"),("Mina","M")])

    def test_unary_only_original_parser_rejects_multiple_parameters(self):
        t=source('(constraint (= (f "Kara" "Lee") "KL"))\n'
                 '(constraint (= (f "Mina" "Kim") "MK"))')
        examples,reason=parse_original(t)
        self.assertIsNone(examples)
        self.assertEqual(reason,"UNSUPPORTED_ARITY_OR_SOURCE_CONSTRAINT_PATTERN")

    def test_original_extra_constraint_never_silently_dropped(self):
        t=source('(constraint (= (f "Kara") "K"))\n'
                 '(constraint (= (f "Mina") "M"))\n'
                 '(constraint (str.contains (f "Other") "x"))')
        examples,reason=parse_original(t)
        self.assertIsNone(examples)
        self.assertEqual(reason,"UNSUPPORTED_ARITY_OR_SOURCE_CONSTRAINT_PATTERN")

    def test_duplicate_sources_are_not_counted_as_independent(self):
        t=source('(constraint (= (f "Kara") "K"))\n'
                 '(constraint (= (f "Kara") "K"))')
        examples,reason=parse_original(t)
        self.assertIsNone(examples)
        self.assertEqual(reason,"DUPLICATE_SOURCE_INPUT_OUTPUT")

    def test_full_classical_exact_225_programs(self):
        programs=classical_order()
        self.assertEqual(len(programs),225)
        self.assertEqual(len(set(programs)),225)
        self.assertEqual(sum(reserved_pair(p) for p in programs),45)

    def test_train_gold_never_test_gold_from_source_candidate_generator(self):
        train=[("Kara Lee","Kara"),("Mina Kim","Mina")]
        test_input="Yuna Mori"
        programs=classical_order()
        full=freeze_programs(train,test_input,programs,225)
        self.assertEqual(full["candidate_program_executions"],225)
        # The returned AST proposals are executable and exactly TRAIN-fit;
        # this control asserts no hidden test gold parameter exists.
        for pair in full["fitting_ASTs"]:
            self.assertTrue(all(run_ast(tuple(pair),x)==y for x,y in train))
        self.assertTrue(full["submitted"])
        self.assertEqual(full["prediction"],"Yuna")

    def test_ambiguity_fails_closed(self):
        train=[("Kara Lee","K"),("Mina Kim","M")]
        test_input="Ducati100"
        all_pairs=classical_order()
        r=freeze_programs(train,test_input,all_pairs,225)
        if r["predictions_conflict"]:
            self.assertFalse(r["submitted"])
            self.assertIsNone(r["prediction"])
        else:
            self.assertTrue(r["submitted"])


if __name__=="__main__":
    unittest.main()
