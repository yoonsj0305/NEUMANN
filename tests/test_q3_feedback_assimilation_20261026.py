import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"research"/"q3"/"discovery_policy"))
from feedback_refinement import refine

def test_factual_external_useragent_type_disagreement_resolved_without_claiming_proof():
    h=[
      {"source_predictions":["6.4.9","6.5.0"],"feedback_prediction":"2.9.7","future_predictions":["6.6.2","8.1.7"]},
      {"source_predictions":["6.4.9","6.5.0"],"feedback_prediction":"YNSD","future_predictions":["MF-W878","FZ467"]}
    ]
    x=refine(h,["6.4.9","6.5.0"],{"output":"2.9.7"})
    assert x["status"]=="SOURCE_AND_FEEDBACK_CONSENSUS_ONLY"
    assert x["removed"]==1 and x["prediction"]==["6.6.2","8.1.7"]
    assert not x["candidate_correctness_proven"] and not x["authorized"]

def test_seven_wrong_date_consensus_hypotheses_fail_closed_after_feedback():
    h=[{"source_predictions":["Nov 2041","Nov 2023"],
        "feedback_prediction":"Nov 1974",
        "future_predictions":["Nov 2018","Nov 2007"]} for _ in range(7)]
    x=refine(h,["Nov 2041","Nov 2023"],{"output":"Dec 1974"})
    assert x["status"]=="HOLD_NO_HYPOTHESIS" and x["removed"]==7
    assert x["prediction"] is None

def test_oracle_absent_and_future_hypothesis_disagreement_hold():
    h=[{"source_predictions":["a"],"feedback_prediction":"b","future_predictions":[x]} for x in ("x","y")]
    assert refine(h,["a"],None)["status"]=="HOLD_NO_AUTHENTICATED_FEEDBACK"
    assert refine(h,["a"],{"output":"b"})["status"]=="HOLD_AMBIGUITY"

def test_invalid_predictions_never_authorized():
    assert refine([{"source_predictions":[],"feedback_prediction":"x","future_predictions":[]}],["x"],{"output":"x"})["status"]=="HOLD_INVALID_INPUT"
