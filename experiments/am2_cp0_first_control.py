"""First AM2-CP0 opened control-plane and exact original checker experiment.
NO real model inference, no Architecture Multiplier decision.
Preregistered GitHub Issue #243.
"""
from __future__ import annotations
from collections import Counter
import argparse
import json
from pathlib import Path
from experiments.general_multiplier_tasks import (
    TASK_SHA256, MODEL_VIEW_SHA256, model_view, multiplier_tasks
)
from neumann1.am2_typed_control_pivot import (
    RejectControl, execute_model_free, infer_kind_from_public_only,
    source_candidate_syntax_only
)
from neumann1.general_runtime_v106 import verify_original, sha


def first_original_control_study():
    cases=[]
    for task,private in multiplier_tasks():
        view=model_view(task)
        planned=infer_kind_from_public_only(view)
        for arm in ("TOOL","NEUMANN"):
            result=execute_model_free(task,private,view,arm)
            result["original_task_id"]=task["id"]  # reporting ONLY, never model input
            result["original_task_sha256"]=sha(task)
            result["model_view_sha256"]=sha(view)
            result["expected_kind_for_analysis"]=task["family"]
            assert planned==task["family"]
            cases.append(result)
    assert len(cases)==24
    assert len({(r["original_task_id"],r["arm"]) for r in cases})==24
    counts={}
    for arm in ("TOOL","NEUMANN"):
        rows=[r for r in cases if r["arm"]==arm]
        counts[arm]=dict(Counter(r["status"] for r in rows))
        assert len(rows)==12
        assert sum(r["model_calls"] for r in rows)==0
        assert sum(r["original_checker_called"] for r in rows)==8
        assert sum(r["accepted"] for r in rows)==8
        assert counts[arm]["ORIGINAL_CHECKER_PASS"]==8
        assert counts[arm]["NEEDS_ACTUAL_FROZEN_MODEL"]==4
        assert all(r["status"]=="ORIGINAL_CHECKER_PASS" for r in rows
                   if r["public_schema"]!="coding")
        assert all(r["status"]=="NEEDS_ACTUAL_FROZEN_MODEL" for r in rows
                   if r["public_schema"]=="coding")
    for arm in ("TOOL","NEUMANN"):
        assert sum(r["tool_calls"] for r in cases if r["arm"]==arm)==(
            8 if arm=="TOOL" else 16
        )
    # Original safety checks may NOT be bypassed by a wrong answer.
    ts={t["id"]:(t,p) for t,p in multiplier_tasks()}
    t,p=ts["am_math_01"]
    assert verify_original(t,"0",p,2000) is False
    t,p=ts["am_plan_01"]
    assert verify_original(t,{k:0 for k in t["public"]["domains"]},p,2000) is False
    # Altered model-visible payload MUST fail identity before ANY execution.
    t,p=ts["am_math_01"]
    view=model_view(t)
    view["id"]=t["id"]
    try:
        execute_model_free(t,p,view,"NEUMANN")
    except RejectControl as e:
        assert str(e)=="PRIVATE_TASK_VIEW_OR_ORIGINAL_MISMATCH"
    else:
        raise AssertionError("private id tamper accepted")
    # Untrusted free-form code must NOT be executed or treated as a result.
    for raw in ("not-python-at-all",
                "def solve(items):\n    import os\n    return 0"):
        try:
            source_candidate_syntax_only(raw)
        except RejectControl:
            pass
        else:
            raise AssertionError("malformed or unsafe source accepted")
    # Syntax-only acceptance never certifies correctness.
    assert source_candidate_syntax_only(
        "def solve(items):\n    return 0"
    )=="def solve(items):\n    return 0"
    return {
      "study":"AM2_CP0_FIRST_OPENED_MODEL_FREE_TYPED_CONTROL_PIVOT",
      "status":"SCOPED_CONTROL_PLANE_PASS",
      "preregistered_issue":243,
      "task_sha256":TASK_SHA256,
      "model_view_sha256":MODEL_VIEW_SHA256,
      "original_development_tasks":12,
      "arms":["TOOL","NEUMANN"],
      "cases":cases,
      "per_arm_outcomes":counts,
      "four_independent_adversarial_categories":{
        "tampered_model_view":"REJECTED",
        "incorrect_rational_candidate":"REJECTED_ORIGINAL_CHECKER",
        "incorrect_csp_assignment":"REJECTED_ORIGINAL_CHECKER",
        "unsafe_or_invalid_source":"REJECTED"},
      "model_calls_total":0,
      "matched_TOOL_has_same_deterministic_rights":True,
      "cpu_smoke_not_accelerator_evidence":True,
      "am1_frozen_first_accelerator_verdict":"FAIL_UNCHANGED",
      "am2_architecture_multiplier":"NOT_EVALUATED",
      "learned_Q3":"OPEN",
      "full_Q1_Q7":"OPEN",
      "no_10x_or_frontier_claim":True,
      "frontier_calls":0,
      "gpu_model_calls":0,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    res=first_original_control_study()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print("AM2_CP0_FIRST_STATUS",res["status"])
    print("AM2_CP0_PER_ARM",json.dumps(res["per_arm_outcomes"],sort_keys=True))
    print("AM2_CP0_GAP_VERDICT",res["am2_architecture_multiplier"])
    print("AM2_CP0_GLOBAL",res["full_Q1_Q7"])

if __name__=="__main__":
    main()
