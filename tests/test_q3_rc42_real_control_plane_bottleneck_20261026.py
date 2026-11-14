"""Run directly on retained real 36 original Gemini/Gemma accelerator receipts."""
import pytest
from research.q3.rc42.am1_control_plane_diagnostic import diagnose,_math_value_mentioned

def test_immutable_original_accelerator_gate_and_control_failure():
    d=diagnose()
    assert d["original_status"]=="FAIL_UNMODIFIED"
    assert d["original_receipts"]==36
    assert d["actual_model_calls"]==72
    assert d["thought_only_calls"]==72
    assert d["json_action_rejections"]==72
    assert d["actual_tool_calls"]==0
    assert d["original_accepted"]==0
    assert d["new_model_calls"]==0
    assert not d["global_q1_q7_closed"]

def test_correct_fraction_is_thought_mention_not_accepted_answer():
    d=diagnose()
    assert d["math_records"]==12
    assert d["math_correct_fraction_text_mentioned"]==9
    assert d["math_mentioned_by_original_arm"]=={"DIRECT":2,"TOOL":4,"NEUMANN":3}
    assert d["retroactive_task_passes_authorized"]==0

def test_unrelated_numbers_and_invalid_latex_not_accidentally_counted():
    assert _math_value_mentioned("Intermediate 218 = 20 + 198", "18") is False
    assert _math_value_mentioned("The result 18", "18") is True
    assert _math_value_mentioned("19 / 6", "19/6") is True
    assert _math_value_mentioned(r"\frac{89}{11}","89/11") is True
    assert _math_value_mentioned("119/600","19/6") is False

def test_task_family_admission_is_not_rewritten():
    d=diagnose()
    assert len(d["math_diagnostic_per_task"])==36
    assert sum(x["math_correct_fraction_text_present"] is not None
               for x in d["math_diagnostic_per_task"])==12
    assert not any(x["actual_original_accepted"] for x in d["math_diagnostic_per_task"])
