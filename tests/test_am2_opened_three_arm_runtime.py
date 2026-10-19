"""AM2 executable runner ENGINEERING contract tests only.

No actual model, weights, GPU, original benchmark, frontier or sealed data.
SYNTHETIC test-core results are never promoted to scientific capability.
"""
from __future__ import annotations
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
runtime=importlib.import_module("neumann1.am2_opened_three_arm_runtime")

PUBLIC={"schema":abi.SCHEMA,"question":"3+4?","answer_kind":"integer"}

class FakeCore:
    def __init__(self,raw="<answer>7</answer>",mutate=False):
        self.identity={"evidence_kind":"SYNTHETIC_TEST_ONLY",
                       "weights_frozen":True,"accelerator_class":False}
        self.calls=0
        self.raw=raw
        self.mutate=mutate
    def generate(self,messages,max_tokens,thinking,deadline_ms):
        assert thinking is False
        assert max_tokens==512
        assert deadline_ms>0
        assert all("private_tests" not in x["content"] for x in messages)
        self.calls+=1
        if self.mutate:
            self.identity["weights_frozen"]=False
        return {"raw":self.raw,"input_tokens":14,"output_tokens":4,
                "deadline_reached":False,"peak_accelerator_memory_bytes":0,
                "peak_accelerator_reserved_bytes":0}

def public_tool(view):
    assert set(view)=={"schema","question","answer_kind"}
    return {"context":"Use arithmetic rules to simplify the expression.",
            "tool_id":"TEST_ONLY_NONQUALIFIED_TOOL",
            "internal_calls":1}

def public_structure(view):
    assert "gold" not in view
    return {"representation":"Evaluate the operands then add.",
            "method_id":"TEST_ONLY_NOT_LEARNED_OR_NOVEL"}

def public_certifier(view,proposal):
    return {"valid":True,"proof_sha256":"f"*64,
            "source_sha256":runtime.sha(view),
            "proposal_sha256":runtime.sha(proposal)}

class ThreeArmExecutableBoundary(unittest.TestCase):
    def test_same_core_three_arms_and_original_boolean_checker(self):
        c=FakeCore()
        out=runtime.run_matched_opened(PUBLIC,c,lambda x:x=="7",
            shared_tool=public_tool,proposer=public_structure,
            certifier=public_certifier,production=False)
        rows=out["receipts"]
        self.assertEqual([x["arm"] for x in rows],list(runtime.ARMS))
        self.assertEqual([x["accepted"] for x in rows],[True,True,True])
        self.assertEqual(c.calls,3)
        self.assertTrue(out["shared_tool_context_identical"])
        self.assertFalse(out["actual_opened_model_comparison_admitted"])
        self.assertTrue(all(x["actual_model_generate_calls"]==0 for x in rows))
        self.assertEqual(rows[1]["tool_provider_invocations"],1)
        self.assertEqual(rows[2]["structure_verifications"],1)

    def test_unbound_shared_tool_blocks_tool_plus_and_neumann(self):
        c=FakeCore()
        out=runtime.run_matched_opened(PUBLIC,c,lambda x:x=="7",
            shared_tool=None,proposer=public_structure,
            certifier=public_certifier,production=False)
        self.assertEqual(c.calls,1)
        self.assertTrue(all(not x["accepted"] for x in out["receipts"]))
        self.assertEqual(out["sealed_D3"],"BLOCKED")

    def test_structure_must_be_real_and_certified_before_model(self):
        c=FakeCore()
        row=runtime.run_one_opened(PUBLIC,"NEUMANN",c,lambda x:x=="7",
            shared_tool=public_tool,proposer=public_structure,
            certifier=None,production=False)
        self.assertFalse(row["accepted"])
        self.assertIn("CERTIFIER_REQUIRED",row["reason"])
        self.assertEqual(c.calls,0)

    def test_invalid_structure_certificate_fail_closed(self):
        c=FakeCore()
        row=runtime.run_one_opened(PUBLIC,"NEUMANN",c,lambda x:True,
            shared_tool=public_tool,proposer=public_structure,
            certifier=lambda p,q:{"valid":True,"proof_sha256":"wrong"},
            production=False)
        self.assertFalse(row["accepted"])
        self.assertEqual(c.calls,0)

    def test_private_answers_never_passed_into_tools_or_models(self):
        c=FakeCore()
        dirty={**PUBLIC,"private_tests":["hidden answer"]}
        with self.assertRaises(abi.InterfaceBlocked):
            runtime.run_one_opened(dirty,"DIRECT",c,lambda x:True,production=False)
        self.assertEqual(c.calls,0)

    def test_thought_channel_only_does_not_touch_original_checker(self):
        c=FakeCore("<|channel>thought I think it is seven")
        calls=[]
        row=runtime.run_one_opened(PUBLIC,"DIRECT",c,
            lambda x:(calls.append(x) or True),production=False)
        self.assertFalse(row["accepted"])
        self.assertEqual(row["original_checker_calls"],0)
        self.assertEqual(calls,[])

    def test_tool_context_disagreement_invalidates_whole_matched_result(self):
        count={"n":0}
        def drift(view):
            count["n"]+=1
            return {"context":"version "+str(count["n"]),
                "tool_id":"TEST_ONLY","internal_calls":1}
        out=runtime.run_matched_opened(PUBLIC,FakeCore(),lambda x:True,
            shared_tool=drift,proposer=public_structure,certifier=public_certifier,
            production=False)
        self.assertFalse(out["shared_tool_context_identical"])
        self.assertTrue(all(not x["accepted"] for x in out["receipts"]))
        self.assertEqual(out["receipts"][0]["reason"],"MATCHED_SHARED_TOOL_PARITY_FAILURE")

    def test_synthetic_core_cannot_masquerade_as_real_gpu_model(self):
        with self.assertRaises(abi.InterfaceBlocked):
            runtime.run_one_opened(PUBLIC,"DIRECT",FakeCore(),
                lambda x:True,production=True)

    def test_core_identity_mutation_is_rejected(self):
        c=FakeCore(mutate=True)
        r=runtime.run_one_opened(PUBLIC,"DIRECT",c,lambda x:True,
            production=False)
        self.assertFalse(r["accepted"])
        self.assertIn("IDENTITY_CHANGED",r["reason"])

    def test_strong_tool_not_automatically_attested(self):
        row=runtime.run_one_opened(PUBLIC,"TOOL+",FakeCore(),lambda x:x=="7",
            shared_tool=public_tool,production=False)
        self.assertTrue(row["accepted"])
        self.assertFalse(row["strong_TOOL_qualified"])
        self.assertIsNone(row["model_forward_calls_measured"])
        self.assertIsNone(row["dollar_cost"])
        self.assertIsNone(row["electricity_joules"])
        self.assertEqual(row["global_Q1_Q7"],"OPEN")

    def test_wrong_answer_rejected_by_original(self):
        row=runtime.run_one_opened(PUBLIC,"DIRECT",FakeCore("<answer>8</answer>"),
            lambda x:x=="7",production=False)
        self.assertFalse(row["accepted"])
        self.assertEqual(row["original_checker_calls"],1)
        self.assertEqual(row["status"],"ORIGINAL_CHECKER_REJECT")


    def test_certifier_cannot_reuse_proof_on_another_public_source(self):
        stale_hash=runtime.sha(PUBLIC)
        changed={**PUBLIC,"question":"Another original."}
        def stale_cert(view,proposal):
            return {"valid":True,"proof_sha256":"f"*64,
                    "source_sha256":stale_hash,
                    "proposal_sha256":runtime.sha(proposal)}
        core=FakeCore()
        row=runtime.run_one_opened(changed,"NEUMANN",core,lambda x:True,
            shared_tool=public_tool,proposer=public_structure,
            certifier=stale_cert,production=False)
        self.assertFalse(row["accepted"])
        self.assertEqual(core.calls,0)
        self.assertIn("CERTIFICATION_FAILED",row["reason"])

    def test_frozen_artifact_and_tokenizer_required_for_actual_model(self):
        c=FakeCore()
        c.identity.update({"evidence_kind":"actual_frozen_model",
            "accelerator_class":True,"model_id":"google/gemma-4-E2B-it",
            "model_revision":"3e22461f65e89153144f8adb70e3b8c2cc9845a7",
            "artifact_sha256":"0"*64,"tokenizer_sha256":"1"*64,
            "precision":"bfloat16","deterministic":True,"do_sample":False})
        with self.assertRaises(abi.InterfaceBlocked):
            runtime.run_one_opened(PUBLIC,"DIRECT",c,lambda x:True,
                production=True)
        self.assertEqual(c.calls,0)

    def test_frozen_budgets_validate(self):
        with self.assertRaises(ValueError):
            runtime.OpenedBudget(max_new_tokens=0)
        with self.assertRaises(ValueError):
            runtime.OpenedBudget(wall_ms=1000,provider_ms=1000)

if __name__=="__main__":
    unittest.main()
