"""Fail-closed evidence boundary for program-consensus and active-label policies.

Observed equality of a small set of program predictions is not a sound
certificate of total version-space uniqueness, even if all programs fit source.
Never infer NEUMANN ownweight learning from classical disagreement policies.
"""
from collections.abc import Sequence

def bounded_portfolio_probe(predictions: Sequence[str | None], required_arms: int = 3) -> dict:
    if not isinstance(required_arms,int) or required_arms<2:
        raise ValueError("minimum two distinct executable candidates")
    good=[x for x in predictions if isinstance(x,str) and x]
    if len(predictions)!=required_arms or len(good)!=required_arms:
        return {
            "source_decision":"REQUEST_ONE_DUE_TO_MISSING_EVIDENCE",
            "completeness":"UNVERIFIED",
            "semantic_uniqueness_certificate":False,
            "may_promote_global_Q":False,
        }
    if len(set(good))>1:
        return {
            "source_decision":"REQUEST_ONE_DUE_TO_OBSERVED_DISAGREEMENT",
            "completeness":"BOUNDED_PORTFOLIO_ONLY",
            "semantic_uniqueness_certificate":False,
            "may_promote_global_Q":False,
        }
    return {
        "source_decision":"MAY_SKIP_IF_LABEL_COST_JUSTIFIES_RISK",
        "completeness":"BOUNDED_PORTFOLIO_UNANIMITY_NOT_VERSION_SPACE_CERTIFIED",
        "semantic_uniqueness_certificate":False,
        "may_promote_global_Q":False,
    }

def active_policy_admission(*,active_exact:int,strong_exact:int,
                            active_cpu:float,strong_cpu:float,
                            active_labels:int,strong_labels:int) -> dict:
    if any(type(x) is not int or x<0 for x in
           (active_exact,strong_exact,active_labels,strong_labels)):
        return {"status":"HOLD_INVALID_METRICS","admit_neural":False}
    if any(not isinstance(x,(float,int)) or x<0 for x in (active_cpu,strong_cpu)):
        return {"status":"HOLD_INVALID_METRICS","admit_neural":False}
    if active_exact<strong_exact and active_cpu>strong_cpu:
        status="ACCURACY_AND_SOLVER_CPU_INFERIOR_LABEL_COST_TRADEOFF_UNKNOWN"
    elif active_exact>=strong_exact and active_cpu<=strong_cpu and active_labels<=strong_labels:
        status="SCOPED_BENCHMARK_ADVANTAGE_NEEDS_COMPLETE_COST_AND_NEW_AUTHOR_TRANSFER"
    else:
        status="TRADEOFF_INDETERMINATE_NEEDS_VALUE_AND_FULL_COST"
    return {"status":status,
            "admit_neural":False,
            "global_neumann_questions":"OPEN",
            "label_dollar_cost_measured":False}
