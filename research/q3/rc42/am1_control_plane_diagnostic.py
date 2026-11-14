"""RC42: ZERO inference. Audit ORIGINAL 2026-10-03 AM1 real model receipts.
The private original gold does NOT supply any candidate answer to model.
A correct answer STRING APPEARING IN THOUGHT is NOT a solved/accepted task!
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re

from experiments.general_multiplier_tasks import (
    TASK_SHA256, MODEL_VIEW_SHA256, model_view, multiplier_tasks
)
from neumann1.general_runtime_v106 import _rational, sha

ROOT=Path(__file__).resolve().parents[3]
ORIGINAL=ROOT/"docs"/"experiments"/"results"/"am1_decision2_first_original"
EXPECTED_TASK_SHA="ad32fd947e4c63fc1b67f849254bb16bd62fad6067bd719d5ad3da6c1f11e99f"
EXPECTED_VIEW_SHA="c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0"

def _math_value_mentioned(raw: str, exact: str)->bool:
    """Candidate token mention only, NO final extraction; may be incidental."""
    correct=Fraction(exact)
    numerator=str(correct.numerator)
    denominator=str(correct.denominator)
    if correct.denominator == 1:
        return bool(re.search(r"(?<![0-9])"+re.escape(numerator)+r"(?![0-9])",raw))
    pair=(r"(?<![0-9])"+re.escape(numerator)+r"\s*/\s*"+
          re.escape(denominator)+r"(?![0-9])")
    latex=r"\\(?:d?frac)\s*\{\s*"+re.escape(numerator)+r"\s*\}\s*\{\s*"+re.escape(denominator)+r"\s*\}"
    return bool(re.search(pair+"|"+latex,raw))

def diagnose():
    tasks=multiplier_tasks()
    if sha(tasks)!=EXPECTED_TASK_SHA or sha([model_view(x) for x,_ in tasks])!=EXPECTED_VIEW_SHA:
        raise ValueError("ORIGINAL_PROBLEM_DRIFT")
    if TASK_SHA256!=EXPECTED_TASK_SHA or MODEL_VIEW_SHA256!=EXPECTED_VIEW_SHA:
        raise ValueError("MANIFEST_IDENTITY_DRIFT")
    report=json.loads((ORIGINAL/"report.json").read_text())
    if report["observations"]!=36 or report["decision_2"]["verdict"]!="FAIL":
        raise ValueError("ORIGINAL_DECISION_2_DRIFT")
    by_id={t["id"]:(t,private) for t,private in tasks}
    pairs=set()
    observations=[]
    output_calls=0
    action_rejections=0
    math_thought_mention={"DIRECT":0,"TOOL":0,"NEUMANN":0}
    math_mention_records=0
    for i in range(36):
        source=ORIGINAL/f"query_{i:02d}.json"
        if not source.is_file():raise ValueError("MISSING_FROZEN_RECEIPT")
        q=json.loads(source.read_text())
        identifier,arm=q["task_id"],q["arm"]
        if identifier not in by_id or arm not in math_thought_mention:
            raise ValueError("UNKNOWN_RECEIPT")
        if (identifier,arm) in pairs:raise ValueError("DUPLICATE_RECEIPT")
        pairs.add((identifier,arm))
        if q["accepted"] is not False or q["tool_calls"] != 0:
            raise ValueError("ORIGINAL_OUTCOME_DRIFT")
        calls=[e["receipt"] for e in q["events"] if e["kind"]=="model_result"]
        rejected=[e for e in q["events"] if e["kind"]=="action_rejected"]
        if len(calls)!=2 or len(rejected)!=2:
            raise ValueError("EVENT_TRACE_DRIFT")
        rawtexts=[]
        for receipt in calls:
            raw=receipt["raw"]
            if (receipt["output_tokens"]!=256 or
                not raw.startswith("<|channel>thought") or
                "<|channel>final" in raw or
                "<channel|>final" in raw):
                raise ValueError("CONTROL_TRACE_DRIFT")
            rawtexts.append(raw)
        output_calls+=len(calls);action_rejections+=len(rejected)
        mention=None
        if identifier.startswith("am_math_"):
            task,private=by_id[identifier]
            exact=_rational(task["public"]["expression"],task["public"]["bindings"])
            if Fraction(exact)!=Fraction(private["exact"]):
                raise ValueError("INDEPENDENT_MATH_GOLD_DRIFT")
            mention=any(_math_value_mentioned(text,exact) for text in rawtexts)
            math_thought_mention[arm]+=int(mention)
            math_mention_records+=int(mention)
        observations.append({"task":identifier,"arm":arm,
                             "actual_original_accepted":False,
                             "first_and_retry_thought_only":True,
                             "math_correct_fraction_text_present":mention})
    if len(pairs)!=36 or len({k for k,v in pairs})!=12:
        raise ValueError("TASK_OR_ARM_COVERAGE")
    if output_calls!=72 or action_rejections!=72:
        raise ValueError("INCOMPLETE_TRACE")
    return {"status":"ROOT_CAUSE_DIAGNOSTIC_NOT_ARCHITECTURE_PASS",
            "original_status":"FAIL_UNMODIFIED",
            "original_receipts":36,"actual_model_calls":output_calls,
            "thought_only_calls":output_calls,
            "json_action_rejections":action_rejections,
            "actual_tool_calls":0,"original_accepted":0,
            "math_records":12,
            "math_correct_fraction_text_mentioned":math_mention_records,
            "math_mentioned_by_original_arm":math_thought_mention,
            "new_model_calls":0,"new_training":0,
            "retroactive_task_passes_authorized":0,
            "next":"NEW_OPENED_MATCHED_EVALUATION_ONLY_WHEN_CLASSICAL_GAP_EXISTS",
            "global_q1_q7_closed":[],
            "math_diagnostic_per_task":observations}

if __name__=="__main__":
    print(json.dumps(diagnose(),ensure_ascii=False,indent=2,sort_keys=True))
