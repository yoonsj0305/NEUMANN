"""Compiler and accounting faults with synthetic cores only; no model weights."""
from fractions import Fraction
import unittest

from neumann1.control_plane_v1 import snapshot, digest
from neumann1.control_plane_p1_contract import MODEL
from neumann1.general_runtime_v106 import sha
from neumann1.control_plane_p15 import (
    number, parse_sketch, compile_sketch, semantic_prompt, FrozenSketchCompiler,
    interpret_and_execute, validate_receipt, SketchProposalFailure, contract,
)
from experiments.control_plane_p14_dev import _executor

VIEW={"instruction":"Return exact.","public":{"query":"Divide 21 by 7, add 5, then multiply the result by 4."}}
SEQUENTIAL="ARITHMETIC\nSTART 21\nDIV 7\nADD 5\nMUL 4\nEND"


class FakeCore:
    def __init__(self,raw=SEQUENTIAL,**overrides):
        self.identity=dict(MODEL); self.raw=raw; self.overrides=overrides; self.calls=[]
    def audit(self): return {"unchanged":True}
    def generate(self,messages,max_tokens,thinking,deadline_ms):
        self.calls.append((snapshot(messages),max_tokens,thinking,deadline_ms))
        return {"raw":self.raw,"input_tokens":40,"output_tokens":20,"generation_ms":5.0,
                "deadline_reached":False,"peak_accelerator_memory_bytes":1234,
                "core_sha256":sha(self.identity),**self.overrides}


def run(raw=SEQUENTIAL,check=None,core=None):
    core=core or FakeCore(raw)
    record=interpret_and_execute(VIEW,FrozenSketchCompiler(core),_executor,
                                 check or (lambda original,answer:Fraction(answer)==32))
    return record,core


class CompilerContracts(unittest.TestCase):
    def test_compiler_parentheses_entire_accumulator(self):
        p=compile_sketch(parse_sketch(SEQUENTIAL))
        self.assertEqual(p["public"]["expression"],"(((21/7)+5)*4)")
        self.assertEqual(_executor(p["route"],p["public"]),"32")
        self.assertFalse(p["certificate"]["natural_language_equivalence_proved"])

    def test_decimal_atom_is_exact_not_binary_float_or_rational_guess(self):
        for value,expected in (("0.5",Fraction(1,2)),("-0.125",Fraction(-1,8)),("0.333333",Fraction(333333,1000000))):
            self.assertEqual(number(value),expected)
            p=compile_sketch(parse_sketch("ARITHMETIC\nSTART "+value+"\nEND"))
            self.assertEqual(Fraction(_executor(p["route"],p["public"])),expected)
        for bad in (0.5,"nan","inf","1e2","1/0","1+2","9"*33):
            with self.subTest(value=bad),self.assertRaises((ValueError,ZeroDivisionError)): number(bad)

    def test_csp_atom_relations_become_strict_list_ir(self):
        p=compile_sketch(parse_sketch("CSP\nDOMAIN X 1 2 3\nDOMAIN Y 1 2 3\nEQ X 1\nNE X Y\nEND"))
        self.assertEqual(p["public"]["constraints"],[["eq","X",1],["ne","X","Y"]])
        answer=_executor(p["route"],p["public"])
        self.assertEqual(answer["X"],1); self.assertNotEqual(answer["X"],answer["Y"])

    def test_bad_csp_cannot_enter_execution(self):
        for bad in (
            "DOMAIN X 1 1\nEQ X 1", "DOMAIN X 1 2\nEQ X Z",
            "DOMAIN X 1 2\nDOMAIN X 1\nEQ X 1", "DOMAIN X 1 2\nEQ X 1\nDOMAIN Y 1 2",
            "DOMAIN X 0.5 1\nEQ X 1", "DOMAIN X 1 2\nEQ X 1 2",
        ):
            with self.subTest(value=bad),self.assertRaises(ValueError): compile_sketch(parse_sketch("CSP\n"+bad+"\nEND"))

    def test_executable_text_and_extra_answers_are_not_atoms(self):
        for bad in ('{"route":"ARITHMETIC","expression":"21/7+5*4"}',
                    "ARITHMETIC\nSTART 1+2\nEND", "ARITHMETIC\nSTART 1\nEND\nANSWER 1",
                    "ARITHMETIC\nADD 1\nEND", "ABSTAIN\nEND"):
            with self.subTest(value=bad),self.assertRaises(ValueError): parse_sketch(bad)

    def test_valid_wrong_order_is_still_rejected_by_original_query(self):
        r,core=run("ARITHMETIC\nSTART 21\nDIV 7\nMUL 4\nADD 5\nEND")
        self.assertEqual(r["execution"]["answer"],"17")
        self.assertEqual(r["status"],"REJECTED_BY_ORIGINAL_VERIFIER")
        self.assertFalse(r["accepted"]); self.assertTrue(r["accounting_complete"])
        self.assertEqual(len(core.calls),1)

    def test_original_public_obligation_not_compiled_view_reaches_verifier(self):
        def check(original,answer):
            self.assertEqual(original,VIEW); self.assertEqual(answer,"32"); return True
        r,_=run(check=check)
        self.assertTrue(r["accepted"]); self.assertEqual(r["verifier_calls"],1)

    def test_completed_invalid_sketch_preserves_charged_cost(self):
        for raw in ("bad sketch", "CSP\nDOMAIN X 1 2\nEQ X UNDECLARED\nEND"):
            r,core=run(raw)
            self.assertEqual(r["status"],"FAILED"); self.assertTrue(r["accounting_complete"])
            self.assertTrue(r["semantic_budget_valid"]); self.assertFalse(r["executed"])
            self.assertEqual((r["model_calls"],r["input_tokens"],r["output_tokens"]),(1,40,20))
            self.assertEqual(r["tool_calls"],0); self.assertEqual(len(core.calls),1)

    def test_abstention_is_charged_no_executor(self):
        r,_=run("ABSTAIN")
        self.assertEqual(r["status"],"ABSTAINED"); self.assertTrue(r["accounting_complete"])
        self.assertFalse(r["executed"]); self.assertEqual(r["tool_calls"],0)

    def test_single_bounded_greedy_call_never_generates_ir_or_control_json(self):
        r,core=run(); messages,cap,thinking,wall=core.calls[0]
        self.assertEqual(cap,192); self.assertIs(thinking,False); self.assertLessEqual(wall,120000)
        self.assertIn("Do not write JSON",messages[0]["content"])
        self.assertEqual(r["semantic_receipt"]["raw"],SEQUENTIAL)

    def test_telemetry_and_identity_faults_fail_closed_preserving_known_work(self):
        for overrides in ({"deadline_reached":True},{"peak_accelerator_memory_bytes":None},
                          {"input_tokens":4097},{"output_tokens":193},{"generation_ms":120001},
                          {"core_sha256":"wrong"},{"generation_ms":-1}):
            with self.subTest(overrides=overrides):
                r,_=run(core=FakeCore(**overrides))
                self.assertFalse(r["accounting_complete"]); self.assertFalse(r["accepted"])
                self.assertFalse(r["executed"]); self.assertEqual(r["model_calls"],1)
                self.assertIn("semantic_receipt",r)
        bad=FakeCore(); bad.identity["model_revision"]="wrong"
        with self.assertRaises(ValueError): FrozenSketchCompiler(bad)

    def test_backend_partial_failure_is_unknown_not_zero_and_no_retry(self):
        class Broken(FakeCore):
            def generate(self,*args): self.calls.append(args); raise RuntimeError("backend partial failure")
        r,core=run(core=Broken())
        self.assertFalse(r["accounting_complete"]); self.assertIsNone(r["input_tokens"])
        self.assertIsNone(r["output_tokens"]); self.assertEqual(len(core.calls),1)

    def test_executor_failure_retains_generation_cost(self):
        r,_=run("ARITHMETIC\nSTART 1\nDIV 0\nEND")
        self.assertEqual(r["status"],"EXECUTION_FAILED"); self.assertTrue(r["accounting_complete"])
        self.assertEqual(r["tool_calls"],1); self.assertEqual(r["verifier_calls"],0)
        self.assertFalse(r["accepted"])

    def test_hidden_field_or_typed_state_is_rejected_before_model(self):
        for view in ({**VIEW,"answer":"32"},{"instruction":"Exact","public":{"expression":"1+2","bindings":{}}},
                     {"instruction":"Exact","public":{"query":"q","family":"math_logic"}}):
            with self.subTest(view=view),self.assertRaises(ValueError): semantic_prompt(view)
        self.assertFalse(contract()["p2_registration_admitted"])
        self.assertEqual(contract()["global_questions_closed"],[])


if __name__ == "__main__": unittest.main()
