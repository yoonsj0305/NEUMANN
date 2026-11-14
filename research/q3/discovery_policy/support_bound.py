"""Proof-only eligibility gate for learned rerankers on frozen source receipts.
This cannot establish general solver limitations or any global Q PASS.
"""
import json

def reranker_upper_bound(source_only_receipt):
    rows=source_only_receipt["first"]
    ids=[r["id"] for r in rows]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("missing or duplicate external task IDs")
    valid=[]
    for r in rows:
        if r.get("status") != "HOLD_NO_MODEL_PROPOSAL":
            valid.append(r["id"])
        elif r.get("source_fit") or r.get("first_predictions"):
            valid.append(r["id"])
    return {
        "tasks_checked":len(ids),
        "zero_source_valid_count":len(ids)-len(valid),
        "oracle_reranker_admission_upper_bound":len(valid),
        "interpretation":"only unchanged frozen candidate programs; not general classical or newly generated methods",
        "global_questions_closed":[],
    }

def evaluate_record(path):
    with open(path,encoding="utf-8") as file:
        record=json.load(file)
    result=reranker_upper_bound(record)
    assert result["tasks_checked"]==12
    assert result["oracle_reranker_admission_upper_bound"]==0
    return result

if __name__=="__main__":
    from pathlib import Path
    import sys
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python support_bound.py <frozen-source-first.json> (from RC50 PR #615)")
    print(evaluate_record(sys.argv[1]))
