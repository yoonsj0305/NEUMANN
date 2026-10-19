"""Software-only AM2 generic public QA interface controls.

No AI model is loaded, no sealed task content is accessed. This checks ONLY the
new answer-neutral input/output checker boundary, not the research multiplier.
"""
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/"neumann1"/"am2_generic_qa_abi.py"
spec=importlib.util.spec_from_file_location("am2_generic_qa_abi",path)
abi=importlib.util.module_from_spec(spec)
spec.loader.exec_module(abi)

class GenericQAABI(unittest.TestCase):
    def setUp(self):
        self.view={"schema":abi.SCHEMA,
            "question":"If x=3, find x+4.","answer_kind":"integer"}
    def test_public_only(self):
        self.assertEqual(abi.validate_public(self.view)["question"],self.view["question"])
        self.assertNotIn("private",str(abi.format_public_messages(self.view)))
    def test_private_fields_do_not_enter_model_input(self):
        for name in ("answer","private_tests","gold","solution","checker","reference_answer"):
            with self.subTest(name=name),self.assertRaises(abi.InterfaceBlocked):
                abi.validate_public({**self.view,name:"7"})
    def test_am1_thought_only_cannot_be_rescued(self):
        with self.assertRaisesRegex(abi.InterfaceBlocked,"NO_FINAL_CHANNEL"):
            abi.extract_answer("<|channel>thought I think 7",self.view)
    def test_final_only_strict(self):
        self.assertEqual(abi.extract_answer("<answer>7</answer>",self.view),"7")
        self.assertEqual(abi.extract_answer(
            "<|channel>final<answer>7</answer><|end|>",self.view),"7")
    def test_original_checker_remains_authoritative(self):
        seen=[]
        receipt=abi.verify_candidate(self.view,"<answer>7</answer>",
            lambda answer:(seen.append(answer) or answer=="7"))
        self.assertTrue(receipt["accepted"])
        self.assertEqual(seen,["7"])
        self.assertEqual(receipt["model_work_in_this_function"],0)
        wrong=abi.verify_candidate(self.view,"<answer>0</answer>",lambda x:x=="7")
        self.assertFalse(wrong["accepted"])
    def test_nonboolean_or_failed_checker_is_not_accepted(self):
        result=abi.verify_candidate(self.view,"<answer>7</answer>",lambda x:1)
        self.assertEqual(result["status"],"ABSTAIN")
    def test_choices_and_malformed_model_outputs(self):
        v={"schema":abi.SCHEMA,"question":"Choose one.","answer_kind":"choice",
           "choices":["A","B","C"]}
        self.assertEqual(abi.extract_answer("<answer>B</answer>",v),"B")
        for text in ("<answer>Z</answer>","B","<answer>B</answer> extra",
                     "<answer>ABC</answer>"):
            with self.subTest(output=text),self.assertRaises(abi.InterfaceBlocked):
                abi.extract_answer(text,v)
    def test_generic_novel_family_not_filename_routed(self):
        v={"schema":abi.SCHEMA,"question":"Prove or disprove any general statement.",
            "answer_kind":"short_text"}
        self.assertEqual(abi.validate_public(v)["question"],v["question"])

if __name__=="__main__":
    unittest.main()
