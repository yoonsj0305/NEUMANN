"""Synthetic receipt controls only; no scores or capability evidence from a model."""
import json
import pytest
from experiments.control_plane_p113 import (
    ARMS, registration, run_item, replay, write, sha,
)
from experiments.control_plane_p113_audit import evaluate
from test_control_plane_p113 import SyntheticJudge


def synthetic_archive(out):
    reg,rows,refs = registration()
    records = [run_item(row,ref,SyntheticJudge(arm,ref["expected_candidate"]))
               for arm in ARMS for row,ref in zip(rows,refs)]
    costs = {arm:{"complete_ms":10.0} for arm in ARMS}
    # Both oracle fixtures pass; strict paired gain is absent, so the gate FAILs.
    report = {"arm_costs":costs,"result":evaluate(records,reg,costs)}
    write(out/"preregister.json",reg)
    write(out/"public.json",rows)
    write(out/"references.json",refs)
    write(out/"records.json",records)
    report["reg_sha256"] = sha(out/"preregister.json")
    write(out/"report.json",report)
    return records,reg,costs


def test_independent_replay_and_no_automatic_gain_from_equal_capability(tmp_path):
    synthetic_archive(tmp_path)
    result = replay(tmp_path)
    assert result["integrity"] and result["model_loaded"] is False
    assert result["result"]["verdict"] == "FAIL"
    assert result["result"]["accepted"] == {"baseline":12,"nli":12}


@pytest.mark.parametrize("kind",["scores","model_input","witness","status","verdict"])
def test_independent_replay_rejects_modified_evidence(tmp_path,kind):
    synthetic_archive(tmp_path)
    if kind == "verdict":
        p = tmp_path/"report.json"
        value = json.loads(p.read_bytes())
        value["result"]["verdict"] = "PASS"
    else:
        p = tmp_path/"records.json"
        value = json.loads(p.read_bytes())
        if kind == "scores": value[0]["selector_receipt"]["scores"][0] += 10
        elif kind == "model_input": value[0]["selector_receipt"]["pairs"][0][0] += " expected answer is B"
        elif kind == "witness": value[0]["answer"]["A"] = 999999
        else: value[0]["status"] = "REJECTED_BY_ORIGINAL_VERIFIER"
    write(p,value)
    with pytest.raises(ValueError): replay(tmp_path)


@pytest.mark.parametrize("field,value",[("neural_forward_calls",2),("generated_calls",1),
    ("feasibility_calls",0),("input_rows",99),("input_tokens",None)])
def test_incomplete_work_accounting_cannot_be_evaluated(tmp_path,field,value):
    records,reg,costs = synthetic_archive(tmp_path)
    records[0][field] = value
    assert evaluate(records,reg,costs)["verdict"] == "NOT_EVALUATED"


def test_timing_budget_cannot_be_hidden_by_good_answers(tmp_path):
    records,reg,costs = synthetic_archive(tmp_path)
    records[0]["complete_ms"] = reg["gate"]["per_item_wall_ms"]+1
    assert evaluate(records,reg,costs)["reason"] == "COST_CAP"
