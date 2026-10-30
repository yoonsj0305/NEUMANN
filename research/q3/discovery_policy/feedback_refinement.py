"""Fail-closed pure feedback assimilation for previously independently evaluated hypotheses.

Only source outputs + one authenticated oracle feedback are allowed. Future inputs
may be used to compare proposals, but future answer labels NEVER enter this call.
This engine does not execute arbitrary untrusted code or prove a unique true rule.
"""

def refine(hypotheses, observed_source, observed_feedback):
    if not isinstance(hypotheses, list) or not isinstance(observed_source, (list, tuple)) or not observed_source:
        return {"status": "HOLD_INVALID_INPUT", "authorized": False}
    if observed_feedback is None or not isinstance(observed_feedback, dict) or "output" not in observed_feedback:
        return {"status": "HOLD_NO_AUTHENTICATED_FEEDBACK", "authorized": False}
    source_valid = []
    for h in hypotheses:
        if not isinstance(h,dict) or not {"source_predictions","feedback_prediction","future_predictions"} <= h.keys():
            return {"status":"HOLD_INVALID_INPUT","authorized":False}
        if len(h["source_predictions"])!=len(observed_source):
            return {"status":"HOLD_INVALID_INPUT","authorized":False}
        if all(pred==actual for pred,actual in zip(h["source_predictions"],observed_source)):
            source_valid.append(h)
    survivors=[h for h in source_valid if h["feedback_prediction"]==observed_feedback["output"]]
    unique=[]
    for h in survivors:
        prediction=h["future_predictions"]
        if not any(prediction==p for p in unique):
            unique.append(prediction)
    state=("HOLD_NO_HYPOTHESIS" if not survivors else
           "HOLD_AMBIGUITY" if len(unique)>1 else
           "SOURCE_AND_FEEDBACK_CONSENSUS_ONLY")
    return {
        "status":state,
        "authorized":False,
        "candidate_correctness_proven":False,
        "count_before":len(source_valid),
        "count_after":len(survivors),
        "removed":len(source_valid)-len(survivors),
        "prediction":unique[0] if len(unique)==1 else None,
        "global_questions_closed":[]
    }
