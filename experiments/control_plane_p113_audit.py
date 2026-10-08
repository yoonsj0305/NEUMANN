"""Post-run model-free guard around the immutable P1.13 first evaluator.

The first source overlay is preserved. Malformed numeric receipts can make that
frozen evaluator raise TypeError. This guard maps rejected malformed evidence to
NOT_EVALUATED; it changes no model input, score, budget or retained verdict.
"""
from experiments.control_plane_p113 import evaluate as frozen_evaluate


def evaluate(records, reg, arm_costs):
    try:
        return frozen_evaluate(records,reg,arm_costs)
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        return {"verdict":"NOT_EVALUATED","reason":"MALFORMED_COST_OR_CAPABILITY_RECEIPT",
            "error_type":type(exc).__name__,"development_only":True,
            "p2_admitted":False,"decision3_admitted":False,"global_questions_closed":[],
            "economic_advantage_established":False}
