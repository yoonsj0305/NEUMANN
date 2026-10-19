"""AM2 typed SMT output formatting controls, old answer paths unchanged."""
import importlib
import sys
import types
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
if "neumann1" not in sys.modules:
    pkg=types.ModuleType("neumann1")
    pkg.__path__=[str(ROOT/"neumann1")]
    sys.modules["neumann1"]=pkg
abi=importlib.import_module("neumann1.am2_generic_qa_abi")

class SMTAnswerEnvelope(unittest.TestCase):
    def setUp(self):
        self.public={"schema":abi.SCHEMA,
           "question":"Find an inductive invariant for this public SyGuS task.",
           "answer_kind":"smt_invariant"}

    def test_multiline_smt_inequality_and_comparison_operator(self):
        term="(and (>= x 0)\n(<= x 12)\n(< y 5))"
        self.assertEqual(abi.extract_answer("<answer>"+term+"</answer>",self.public),term)

    def test_explicit_final_channel_allowed(self):
        self.assertEqual(abi.extract_answer("<|channel>final<answer>(= x 3)</answer><|end|>",self.public),
                         "(= x 3)")

    def test_short_text_keeps_legacy_newline_rejection(self):
        view={**self.public,"answer_kind":"short_text"}
        with self.assertRaises(abi.InterfaceBlocked):
            abi.extract_answer("<answer>two\nlines</answer>",view)

    def test_integer_canonical_gate_unchanged(self):
        view={**self.public,"answer_kind":"integer"}
        with self.assertRaises(abi.InterfaceBlocked):
            abi.extract_answer("<answer>03</answer>",view)

    def test_smt_nested_answer_blocks_refused(self):
        with self.assertRaises(abi.InterfaceBlocked):
            abi.extract_answer("<answer>(and true <answer>false</answer>)</answer>",self.public)

    def test_extraneous_text_refused(self):
        with self.assertRaises(abi.InterfaceBlocked):
            abi.extract_answer("My proof: <answer>true</answer>",self.public)

    def test_thought_only_cannot_promote_proof(self):
        with self.assertRaisesRegex(abi.InterfaceBlocked,"NO_FINAL_CHANNEL"):
            abi.extract_answer("<|channel>thought<answer>true</answer>",self.public)

    def test_output_size_cap_for_smt_only(self):
        with self.assertRaises(abi.InterfaceBlocked):
            abi.extract_answer("<answer>"+"x"*4100+"</answer>",self.public)

    def test_source_private_fields_not_allowed(self):
        with self.assertRaises(abi.InterfaceBlocked):
            abi.validate_public({**self.public,"checker":"ORIGINAL_SOLVER_OUTPUT"})

    def test_typed_prompt_never_contains_private_authority(self):
        msgs=abi.format_public_messages(self.public)
        self.assertEqual(msgs[1]["role"],"user")
        self.assertIn("smt_invariant",msgs[1]["content"])
        self.assertNotIn("ORIGINAL_SOLVER_OUTPUT",str(msgs))

if __name__=="__main__":
    unittest.main()
