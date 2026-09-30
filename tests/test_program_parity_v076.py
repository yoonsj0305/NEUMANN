import ast
from pathlib import Path

import unittest

from benchmark_v076 import run
from neumann1.program_parity_v076 import (Opcode, decode_tool_program,
    direct_tool_program_route, execute_tool_program, structural_route)


def _source_gate_matches_witness_without_torch_import():
    source = Path(__file__).parents[1] / "experiments/v031_sequence_challenger.py"
    nodes = ast.parse(source.read_text()).body
    gate = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == "structural_accepts")
    expected = ast.parse("def structural_accepts(class_id):\n return int(class_id) == STRUCTURAL_LINEAR_CLASS").body[0]
    assert ast.dump(gate.body[0], include_attributes=False) == ast.dump(expected.body[0], include_attributes=False)
    assignments = [n for n in nodes if isinstance(n, ast.Assign)]
    value = next(n.value for n in assignments if any(isinstance(t, ast.Name) and
                 t.id == "STRUCTURAL_LINEAR_CLASS" for t in n.targets))
    assert isinstance(value, ast.Constant) and value.value == 0


def _full_frozen_parity_contract():
    result = run()
    assert result["decision"] == "POST_HEAD_EQUIVALENCE_ONLY_NOT_Q4_PASS"
    assert result["paired_post_head_checks"] == 39852
    assert result["texts"] == 486 and result["mismatches"] == 0
    assert result["positive_head0_verified_known_matches"] == 243
    assert result["negative_head0_compiler_rejections"] == 243
    assert result["model_inferences"] == result["new_training_runs"] == result["timing_measurements"] == 0


def _program_vocabulary_and_untrusted_outputs_fail_closed(testcase):
    for head in (True, -1, 82, "0", 0.0, None):
        with testcase.assertRaises(ValueError):
            decode_tool_program(head)
    for opcode in ("solve_controlled_linear", "import os", None, 0):
        with testcase.assertRaises(ValueError):
            execute_tool_program("x+y=2; x-y=0", opcode)
    assert decode_tool_program(0) == Opcode.SOLVE_CONTROLLED_LINEAR
    for head in range(1, 82):
        assert decode_tool_program(head) == Opcode.ABSTAIN
        assert structural_route("invalid", head) == direct_tool_program_route("invalid", head)


class ProgramParityTests(unittest.TestCase):
    def test_source_gate_matches_witness(self):
        _source_gate_matches_witness_without_torch_import()

    def test_frozen_parity_contract(self):
        _full_frozen_parity_contract()

    def test_untrusted_outputs_fail_closed(self):
        _program_vocabulary_and_untrusted_outputs_fail_closed(self)
