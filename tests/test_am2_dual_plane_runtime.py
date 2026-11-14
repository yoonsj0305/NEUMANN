"""AM2 transport/authority tests. Fixture model answers are NOT model capability evidence."""
import copy
import json
import unittest
from experiments.am2_dual_plane_runtime import (
    ARMS,plain_final,parse_source,coding_prompt,run_observation
)
from experiments.general_multiplier_tasks import multiplier_tasks,model_view
from neumann1.general_multiplier_contract import MultiplierBudget

CODING_PROGRAMS=(
    "def solve(items):\n    return len(set(x for x in items if x < 0))",
    "def solve(items):\n    return sum(set(x for x in items if x % 2 == 0))",
    "def solve(items):\n    return len(set(x for x in items if x > 0 and x % 2 == 1))",
    "def solve(items):\n    return sum(abs(x) for x in set(items) if x != 0)",
)

class FakeCore:
    def __init__(self,raw,wrong_thinking=False,change_identity=False):
        self.raw=raw
        self.identity={"weights_frozen":True,"accelerator_class":True,"revision":"fixture"}
        self.wrong_thinking=wrong_thinking
        self.change_identity=change_identity
        self.calls=[]
    def count_tokens(self,messages,thinking):
        assert thinking is False
        self.calls.append({"kind":"count","messages":messages,"thinking":thinking})
        return 97
    def generate(self,messages,max_tokens,thinking,deadline_ms):
        assert thinking is False
        self.calls.append({"kind":"generate","messages":messages,"thinking":thinking})
        if self.change_identity:self.identity["revision"]="mutated"
        return {
          "raw":self.raw,"input_tokens":97,"output_tokens":min(24,max_tokens),
          "thinking_enabled":self.wrong_thinking,"generation_ms":1.0,
          "deadline_reached":False,"peak_accelerator_memory_bytes":1024
        }

class AM2DualPlaneTests(unittest.TestCase):
    def test_decoder_rejects_thought_channel_and_unsafe_source(self):
        self.assertEqual(plain_final("<|channel>final def solve(items):\n    return 0<eos>"),
                         "def solve(items):\n    return 0")
        self.assertEqual(parse_source("def solve(items):\n    return 0"),
                         "def solve(items):\n    return 0")
        bad=[
            "<|channel>thought x <|channel>final def solve(items):\n return 0",
            "Here is the solution: def solve(items):\n return 0",
            chr(96)*3+"python\ndef solve(items):\n return 0\n"+chr(96)*3,
            "import os\ndef solve(items):\n return 0",
            "def solve(items):\n import os\n return 0",
            "def solve(items):\n return 0\nprint(1)",
            "def solve(x):\n return 0",
            "def solve(items):\n return eval('1')\n" if False else "def solve(items):\n return 0\n\ndef f():\n return 0"
        ]
        for b in bad:
            with self.subTest(b=b[:22]),self.assertRaises(ValueError):parse_source(b)
    def test_same_tool_rights_and_actual_original_verification_for_eight(self):
        records=[]
        for task,private in multiplier_tasks():
            if task["family"]=="coding":continue
            for arm in ("TOOL","NEUMANN"):
                x=run_observation(task,private,model_view(task),arm)
                self.assertTrue(x["accepted"],x["error"])
                self.assertEqual(x["model_calls"],0)
                self.assertEqual(x["tool_calls"],1)
                self.assertEqual(x["checker_calls"],1)
                self.assertEqual(x["representation_certified"],arm=="NEUMANN")
                records.append(x)
        self.assertEqual(len(records),16)
    def test_coding_fixture_executes_without_json_action_or_thinking(self):
        tasks=multiplier_tasks()[4:8]
        for i,(task,private) in enumerate(tasks):
            for arm in ARMS:
                fake=FakeCore(CODING_PROGRAMS[i])
                result=run_observation(task,private,model_view(task),arm,fake)
                self.assertTrue(result["accepted"],str((arm,i,result["error"])))
                self.assertEqual(result["model_calls"],1)
                self.assertEqual(result["checker_calls"],1)
                self.assertEqual(result["thinking_enabled"],False)
                self.assertEqual(result["tool_calls"],0 if arm=="DIRECT" else 1)
                self.assertEqual(result["representation_certified"],arm=="NEUMANN")
                called=[x for x in fake.calls if x["kind"]=="generate"]
                self.assertEqual(len(called),1)
                prompt=json.dumps(called[0]["messages"])
                self.assertNotIn("am_code_",prompt)
                self.assertNotIn('"family"',prompt)
                self.assertNotIn('"tests"',prompt)
    def test_model_is_not_invoked_for_tool_math_or_planning(self):
        task,private=multiplier_tasks()[0]
        fake=FakeCore("invalid result")
        for arm in ("TOOL","NEUMANN"):
            x=run_observation(task,private,model_view(task),arm,fake)
            self.assertTrue(x["accepted"])
        self.assertEqual(fake.calls,[])
    def test_direct_model_is_not_free(self):
        task,private=multiplier_tasks()[0]
        core=FakeCore("18")
        x=run_observation(task,private,model_view(task),"DIRECT",core)
        self.assertTrue(x["accepted"],x["error"])
        self.assertEqual(x["model_calls"],1)
        self.assertEqual(x["tool_calls"],0)
        self.assertEqual(x["checker_calls"],1)
    def test_thinking_contract_drift_and_identity_mutation_fail_closed(self):
        task,private=multiplier_tasks()[4]
        for fake in (FakeCore(CODING_PROGRAMS[0],wrong_thinking=True),
                     FakeCore(CODING_PROGRAMS[0],change_identity=True)):
            x=run_observation(task,private,model_view(task),"TOOL",fake)
            self.assertFalse(x["accepted"])
            self.assertEqual(x["checker_calls"],0)
            self.assertEqual(x["model_calls"],1)
    def test_model_visible_mismatch_cannot_fall_through_to_hidden_original(self):
        task,private=multiplier_tasks()[0]
        x=copy.deepcopy(model_view(task))
        x["public"]["bindings"]["a"]+=1
        for arm in ARMS:
            fake=FakeCore("18")
            result=run_observation(task,private,x,arm,fake)
            self.assertFalse(result["accepted"])
            self.assertEqual(result["model_calls"],0)
            self.assertEqual(result["checker_calls"],0)
            self.assertIn("ABSTAIN_MODEL_VIEW_ORIGINAL_MISMATCH",result["error"])
            self.assertEqual(fake.calls,[])
    def test_coding_without_core_abstains_not_fabricate(self):
        task,private=multiplier_tasks()[4]
        for arm in ARMS:
            result=run_observation(task,private,model_view(task),arm)
            self.assertFalse(result["accepted"])
            self.assertEqual(result["checker_calls"],0)
            self.assertEqual(result["model_calls"],0)
    def test_public_example_replay_rejects_wrong_program_before_private_checker(self):
        task,private=multiplier_tasks()[4]
        x=run_observation(task,private,model_view(task),"NEUMANN",
                          FakeCore("def solve(items):\n    return 123"))
        self.assertFalse(x["accepted"])
        self.assertEqual(x["checker_calls"],0)
        self.assertIn("PUBLIC_EXAMPLE_REPLAY_FAILED",x["error"])
    def test_compilation_prompt_is_narrow_public_only(self):
        task,_=multiplier_tasks()[4]
        view=model_view(task)
        p=coding_prompt(view)
        self.assertEqual(len(p),2)
        self.assertNotIn(task["id"],json.dumps(p))
        self.assertNotIn("tests",json.dumps(p))
        self.assertIn("requirement",p[1]["content"])

if __name__=="__main__":
    unittest.main()
