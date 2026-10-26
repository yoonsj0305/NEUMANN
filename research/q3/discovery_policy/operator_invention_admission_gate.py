"""Research admission gate. FIRST prediction outcomes must be sealed before scoring.
This is NOT a model, deployment authorization, or global-Q proof.
"""
def evaluate_gate(strong, proposed, gold, *, model_weights_updated=False,
                  new_primitive_semantics_generated=False, total_cost_comparable=False):
    assert set(strong)==set(proposed)==set(gold)
    added=[]; regressions=[]; wrong=[]; classic_exact=novel_exact=0
    for key,truth in gold.items():
        c=strong[key] is not None and strong[key]==truth
        n=proposed[key] is not None and proposed[key]==truth
        classic_exact+=c; novel_exact+=n
        if n and not c:added.append(key)
        if c and not n:regressions.append(key)
        if proposed[key] is not None and not n:wrong.append(key)
    if wrong or regressions:status="REJECT_REGRESSION_OR_WRONG"
    elif not added:status="REJECT_NO_EXTERNAL_INCREMENT"
    elif not model_weights_updated or not new_primitive_semantics_generated:
        status="CLASSICAL_OR_FIXED_LANGUAGE_GAIN_NOT_LEARNED_INVENTION"
    elif not total_cost_comparable:status="HOLD_COST_GATE"
    else:status="CANDIDATE_FOR_FURTHER_INDEPENDENT_REPLICATION"
    return dict(status=status,classical_exact=classic_exact,novel_exact=novel_exact,
                added=added,regressions=regressions,wrong=wrong,
                proven_learned_semantic_invention=False, global_Q1_Q7="OPEN")
