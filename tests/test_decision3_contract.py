from neumann1.decision3_contract import evaluate_decision3
from neumann1.decision3_frontier_receipt import validate_frontier_receipt
from experiments.decision3_selection import select_metadata


def resource(v, unit):
    return {"status":"measured","value":v,"unit":unit}


def unavailable(unit):
    return {"status":"unavailable","value":None,"unit":unit}


def role(success, ms, latency, cost=None):
    return {
        "verified_success": success,
        "complete_ms": ms,
        "resources": {
            "complete_latency_ms": resource(latency, "ms"),
            "monetary_cost_usd": resource(cost, "USD") if cost is not None else unavailable("USD"),
            "energy_j": unavailable("J"),
            "compute_units": unavailable("provider_native"),
        },
    }


def good_rows():
    rows=[]
    families=["math","science","coding"]
    # 18 tasks, 6/family. Baseline 6 successes, N 11, frontier 15.
    for i in range(18):
        fam=families[i%3]
        b=i<6
        n=i<11
        f=i<15
        rows.append({
            "task_id":f"t{i:02d}",
            "family":fam,
            "new_family": fam=="science",
            "roles":{
                "BASELINE":role(b,100,100),
                "NEUMANN":role(n,90,40),
                "FRONTIER":role(f,180,120,0.01),
            },
        })
    return rows


def common(rows):
    return evaluate_decision3(
        rows,
        decision2_valid_pass=True,
        architecture_frozen=True,
        task_agnostic_interface=True,
        baseline_arm_frozen="TOOL",
        source_registry_frozen=True,
        sealed_before_admission=True,
    )


def test_decision3_pass_fixture():
    result=common(good_rows())
    assert result["verdict"]=="PASS_ADMIT_EDGE_CLOUD_ENGINEERING"
    assert result["sealed_multiplier"]["persists"]
    assert result["frontier_gap"]["recovery_pass"]
    assert result["frontier_resource_signal"]["pass"]
    assert result["global_questions_closed"]==[]


def test_decision2_must_pass_first():
    result=evaluate_decision3(
        [],
        decision2_valid_pass=False,
        architecture_frozen=True,
        task_agnostic_interface=True,
        baseline_arm_frozen="TOOL",
        source_registry_frozen=True,
        sealed_before_admission=True,
    )
    assert result["verdict"]=="BLOCKED_DECISION2_NOT_PASS"


def test_task_specific_interface_blocks_before_opening_new_family():
    result=evaluate_decision3(
        [],
        decision2_valid_pass=True,
        architecture_frozen=True,
        task_agnostic_interface=False,
        baseline_arm_frozen="TOOL",
        source_registry_frozen=True,
        sealed_before_admission=True,
    )
    assert result["verdict"]=="BLOCKED_TASK_SPECIFIC_INTERFACE"


def test_sealed_multiplier_failure_is_scientific_fail():
    rows=good_rows()
    for row in rows:
        row["roles"]["NEUMANN"]["verified_success"]=row["roles"]["BASELINE"]["verified_success"]
        row["roles"]["NEUMANN"]["complete_ms"]=100
    result=common(rows)
    assert result["verdict"]=="FAIL_SEALED_MULTIPLIER_DID_NOT_PERSIST"


def test_no_sufficient_frontier_gap_is_not_negative_recovery_evidence():
    rows=good_rows()
    for row in rows:
        row["roles"]["BASELINE"]["verified_success"]=True
    result=common(rows)
    assert result["verdict"]=="NOT_EVALUATED_NO_SUFFICIENT_VERIFIED_FRONTIER_GAP"


def test_gap_recovery_failure_is_scientific_fail():
    rows=good_rows()
    # Keep N's aggregate multiplier positive on tasks baseline already solves,
    # but remove recovery on baseline-fail/frontier-success tasks.
    for i,row in enumerate(rows):
        if not row["roles"]["BASELINE"]["verified_success"]:
            row["roles"]["NEUMANN"]["verified_success"]=False
        elif i<6:
            row["roles"]["NEUMANN"]["verified_success"]=True
    # Efficiency path remains via lower total wall.
    for row in rows:
        row["roles"]["NEUMANN"]["complete_ms"]=40
    result=common(rows)
    assert result["sealed_multiplier"]["persists"]
    assert result["verdict"]=="FAIL_FRONTIER_GAP_RECOVERY"


def test_unknown_frontier_resources_never_become_zero_or_pass():
    rows=good_rows()
    for row in rows:
        for arm in ("NEUMANN","FRONTIER"):
            row["roles"][arm]["resources"]["complete_latency_ms"]=unavailable("ms")
            row["roles"][arm]["resources"]["monetary_cost_usd"]=unavailable("USD")
    result=common(rows)
    assert result["verdict"]=="NOT_EVALUATED_FRONTIER_RESOURCE_SIGNAL"


def test_selector_uses_metadata_only_and_diversifies():
    rows=[]
    for i in range(30):
        rows.append({
            "id":f"id-{i}",
            "family":"science" if i%3==0 else "math" if i%3==1 else "coding",
            "raw_subject":f"s{i%10}",
            "category":f"c{i%4}",
            "new_family":i%3==0,
            "eligible":True,
        })
    chosen=select_metadata(rows,source_id="fixture",target_count=18)
    assert len(chosen)==18
    assert len({x["id"] for x in chosen})==18
    assert max(sum(x["raw_subject"]==s for x in chosen) for s in {x["raw_subject"] for x in chosen})<=2


def test_selector_rejects_question_or_answer_content():
    rows=[{"id":"x","family":"science","raw_subject":"s","category":"c","eligible":True,"question":"secret"}]
    try:
        select_metadata(rows,source_id="fixture",target_count=1)
    except ValueError as exc:
        assert "forbidden" in str(exc)
    else:
        raise AssertionError("sealed content influenced selection")


def test_frontier_receipt_requires_explicit_unknown_axes():
    r={
        "provider":"fixture",
        "model_id":"frontier",
        "model_revision":"r1",
        "task_id":"t",
        "request_sha256":"a",
        "response_sha256":"b",
        "trace_sha256":"c",
        "verified_success":True,
        "attempts":1,
        "selection_role":"FROZEN_FRONTIER_REFERENCE",
        "resources":{
            "complete_latency_ms":resource(10,"ms"),
            "monetary_cost_usd":resource(0.01,"USD"),
            "energy_j":unavailable("J"),
            "compute_units":unavailable("provider_native"),
        },
    }
    assert validate_frontier_receipt(r)
    r["resources"]["energy_j"]={"status":"unavailable","value":0,"unit":"J"}
    try:
        validate_frontier_receipt(r)
    except ValueError:
        pass
    else:
        raise AssertionError("UNKNOWN silently became zero")
