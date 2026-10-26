"""RC43 strict pre-admission: a single limited classical portfolio failure
is NEVER enough to authorize neural model evaluation or global Q3 closure.
"""
import json
from pathlib import Path

RECORD=Path(__file__).with_name("frozen_gap_report.json")

def audit():
    p=json.loads(RECORD.read_text(encoding="utf-8"))
    r=p["records"]
    assert len(r)==24 and len({x["id"] for x in r})==24
    assert sum(x["correct"] for x in r[:12])==p["opened_expanded"]==8
    assert sum(x["correct"] for x in r[12:])==p["heldout_training_expanded"]==2
    assert p["zero_neural_calls"] is True
    assert p["classical_exhaustion_proven"] is False
    assert p["neural_admitted"] is False
    assert all(q=="OPEN" for q in p["global_gates"].values())
    return {"status":"RECORDED_AUDIT_NOT_PYTHON_FULL_REPLAY",
            "source_tasks":24,"opened":8,"heldout_training":2,
            "neural_calls":0,"admission":"NOT_ADMITTED",
            "next":"FULL_CORPUS_PYTHON_PARITY_THEN_STRONG_CLASSICAL_BASELINE"}
