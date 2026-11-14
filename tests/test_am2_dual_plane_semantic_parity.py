"""AM2 dual-plane scientific no-go: semantic parity under matched deterministic core.
This is an ORIGINAL opened task fixture, not new model evidence.
"""
import copy
import unittest

from experiments.am2_dual_plane_runtime import run_observation, coding_prompt
from experiments.general_multiplier_tasks import multiplier_tasks, model_view

class DeterministicFixtureCore:
    def __init__(self, source):
        self.source=source
        self.prompts=[]
        self.identity={"weights_frozen":True,"accelerator_class":True,
                       "revision":"fixture-NOT-GEMMA","artifact_sha256":"fixture"}
    def count_tokens(self,messages,thinking):
        assert thinking is False
        return 50
    def generate(self,messages,max_tokens,thinking,deadline_ms):
        assert thinking is False
        self.prompts.append(copy.deepcopy(messages))
        return {
            "raw":self.source,
            "input_tokens":50,
            "output_tokens":20,
            "thinking_enabled":False,
            "deadline_reached":False,
            "peak_accelerator_memory_bytes":2048,
        }

class AM2MatchedSemanticParityTests(unittest.TestCase):
    def test_tool_neumann_same_original_semantics_on_all_twelve(self):
        for task,private in multiplier_tasks():
            view=model_view(task)
            dummy_code="def solve(items):\n    return 0"
            core_a=DeterministicFixtureCore(dummy_code)
            core_b=DeterministicFixtureCore(dummy_code)
            a=run_observation(task,private,view,"TOOL",core_a)
            b=run_observation(task,private,view,"NEUMANN",core_b)
            self.assertEqual(a["accepted"],b["accepted"],task["id"])
            self.assertEqual(a["answer"],b["answer"],task["id"])
            self.assertEqual(a["checker_calls"],b["checker_calls"],task["id"])
            self.assertEqual(a["model_calls"],b["model_calls"],task["id"])
            self.assertEqual(a["tool_calls"],b["tool_calls"],task["id"])
            if task["family"]=="coding":
                self.assertEqual(core_a.prompts,core_b.prompts)
                self.assertEqual(core_a.prompts[0],coding_prompt(view))
                self.assertEqual(a["model_calls"],1)
            else:
                self.assertEqual(a["model_calls"],0)
                self.assertEqual(a["accepted"],True)
                self.assertEqual(core_a.prompts,[])
                self.assertEqual(core_b.prompts,[])
            self.assertFalse(a["representation_certified"])
            self.assertEqual(b["representation_certified"],task["family"]!="coding" or b["model_calls"]==1)

    def test_changed_visible_problem_rejected_before_model_calls(self):
        task,private=multiplier_tasks()[4]
        view=copy.deepcopy(model_view(task))
        view["public"]["requirement"]="Return another function."
        model=DeterministicFixtureCore("def solve(items):\n    return 0")
        for arm in ("TOOL","NEUMANN"):
            obs=run_observation(task,private,view,arm,model)
            self.assertFalse(obs["accepted"])
            self.assertEqual(obs["model_calls"],0)
            self.assertEqual(obs["error"],"ABSTAIN_MODEL_VIEW_ORIGINAL_MISMATCH")
        self.assertEqual(model.prompts,[])

    def test_thought_channel_output_stays_fail_closed(self):
        task,private=multiplier_tasks()[4]
        view=model_view(task)
        model=DeterministicFixtureCore("<|channel>thought\nNever reaches final")
        for arm in ("TOOL","NEUMANN"):
            obs=run_observation(task,private,view,arm,model)
            self.assertFalse(obs["accepted"])
            self.assertIn("ABSTAIN_THOUGHT_CHANNEL",obs["error"])

    def test_coding_prompt_contains_no_private_targets_or_task_identity(self):
        task,private=multiplier_tasks()[4]
        prompt=str(coding_prompt(model_view(task)))
        self.assertNotIn(task["id"],prompt)
        self.assertNotIn(str(private["tests"]),prompt)

if __name__=="__main__":
    unittest.main()
