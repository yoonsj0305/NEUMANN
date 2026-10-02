"""Synthetic retained-receipt fault fixtures, not model evidence."""
from dataclasses import asdict
import pytest
import math
from experiments.general_development_v106 import boot2_tasks
from experiments.general_evidence_v106 import check_record, check_latency_sum
from neumann1.general_runtime_v106 import Limits, sha


def fixture():
    task,private = boot2_tasks()[0]
    core = {"fixture_only":True,"artifact_sha256":"fixture"}
    receipt = {"input_tokens":20,"output_tokens":1,"output_token_ids":[7],"core_sha256":sha(core)}
    events = [{"kind":"model_start"},{"kind":"model_result","receipt":receipt},
              {"kind":"verification","accepted":True}]
    record = {"task_id":task["id"],"task_sha256":sha(task),"family":task["family"],
              "arm":"B0","core":core,"limits":asdict(Limits()),
              "evidence_kind":"actual_frozen_model","new_fitting":False,
              "events":events,"trace_sha256":sha(events),"model_calls":1,"tool_calls":0,
              "token_accounting_complete":True,"input_tokens":20,"output_tokens":1,
              "complete_ms":1.,"accepted":True,"verification_errors":[],"answer":"26"}
    return record,task,private,core,asdict(Limits())


def test_original_checker_rejects_forged_acceptance_even_with_valid_trace_hash():
    args = fixture()
    check_record(*args)
    args[0]["answer"] = "27"
    with pytest.raises(AssertionError):
        check_record(*args)


def test_actual_token_ids_must_match_receipt_count():
    args = fixture()
    args[0]["events"][1]["receipt"]["output_token_ids"].append(8)
    args[0]["trace_sha256"] = sha(args[0]["events"])
    with pytest.raises(AssertionError):
        check_record(*args)


def test_over_budget_original_correctness_cannot_become_success():
    args = fixture()
    args[0]["complete_ms"] = args[-1]["wall_ms"]+1
    with pytest.raises(AssertionError):
        check_record(*args)


def test_missing_model_receipt_cannot_claim_complete_token_accounting():
    args = fixture()
    args[0]["events"].pop(1)
    args[0]["trace_sha256"] = sha(args[0]["events"])
    with pytest.raises(AssertionError):
        check_record(*args)


def test_neumann_requires_retained_certified_representation():
    args = fixture()
    args[0]["arm"] = "N"
    with pytest.raises(AssertionError):
        check_record(*args)


def test_successful_repair_preserves_prior_checker_error():
    args = fixture()
    args[0]["events"].insert(2,{"kind":"verification","accepted":False,"error":"retained prior error"})
    args[0]["verification_errors"] = ["retained prior error"]
    args[0]["trace_sha256"] = sha(args[0]["events"])
    check_record(*args)
    assert args[0]["verification_errors"] == ["retained prior error"]


def test_latency_sum_is_portable_without_allowing_material_cost_change():
    values = [120452.2817,120413.361069,120181.548313]
    expected = math.fsum(values)
    check_latency_sum(math.nextafter(expected,math.inf),values)
    with pytest.raises(AssertionError):
        check_latency_sum(expected+0.000001,values)
