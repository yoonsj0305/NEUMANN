"""Post-FIRST analytic root-cause of frozen G3 role-policy extrapolation.

No source fetch, no model retraining, no learner import, no replay of 8382
previously evaluated points. Uses the immutable first negative receipt and
original trained weights to algebraically identify the scale feature
responsible for the earliest wrong final-stage interval choice.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path


WEIGHT_SHA="982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc"
EXPECTED_FIRST_RUN=42200289388


def audit(checkpoint:Path,first:Path)->dict:
    raw=checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=WEIGHT_SHA:
        raise ValueError("NOT_THE_ORIGINAL_BEFORE_EXTERNAL_FIRST_STUDENT")
    weights=json.loads(raw)["student_weight"]
    recorded=json.loads(first.read_bytes())
    if (recorded.get("schema")!="neumann.g3.ownweight-frozen-2-128-sourcefree-extrapolation-first.v1"
       or recorded.get("scientific_status")!="FAIL_FROZEN_OUT_OF_DISTRIBUTION_SYMBOLIC_N"
       or recorded.get("total_role_prediction_points")!=8382
       or recorded.get("trained_role_predictions_exact")!=8257
       or recorded.get("fully_exact_stage_counts")!=38
       or recorded.get("original_frozen_weights_SHA256")!=WEIGHT_SHA):
        raise ValueError("DO_NOT_REWRITE_ORIGINAL_NEGATIVE_RESULT")
    first_bad=recorded.get("first_out_of_distribution_counterexample",{})
    if (first_bad.get("n")!=40 or first_bad.get("stage")!=40
       or first_bad.get("expected")!=[3,2,0,0]
       or first_bad.get("actual_frozen_own_weight")!=[1,2,0,0]):
        raise ValueError("NOT_THE_ORIGINAL_FIRST_COUNTEREXAMPLE")
    # Final stage role metadata has features (1,0,0,1,1,n/12).
    # Compare head 0 token WHOLE(3) against PREFIX(1) exactly.
    head=weights[0]
    diff=lambda feature: head[feature][3]-head[feature][1]
    intercept=diff(0)+diff(3)+diff(4)
    per_stage_count_slope=diff(5)/12.0
    score_difference=lambda n: intercept+per_stage_count_slope*n
    at_39=score_difference(39)
    at_40=score_difference(40)
    if not(at_39>0 and at_40<0 and per_stage_count_slope<0):
        raise ValueError("SIZE_FEATURE_NOT_CAUSAL_CROSSING_AT_ORIGINAL_FIRST")
    critical=-intercept/per_stage_count_slope
    if not 39.0<critical<40.0:
        raise ValueError("NOT_THE_FROZEN_SCORE_CROSSING")
    return {
      "schema":"neumann.g3.ownweight-first-failure-analytic-parameter-root-cause.v1",
      "science_status":"POSTFIRST_CAUSAL_LOGIT_DIAGNOSTIC_PASS_NO_ORIGINAL_RERUN",
      "original_negative_first_run":EXPECTED_FIRST_RUN,
      "first_original_score_sha256":hashlib.sha256(first.read_bytes()).hexdigest(),
      "exact_original_frozen_weights_sha256":WEIGHT_SHA,
      "first_actual_failure":{"n":40,"stage":40,
          "wrong_student_interval":"PREFIX","required_interval":"WHOLE"},
      "analytical_head0_logit_difference":"WHOLE_minus_PREFIX_at_final_stage",
      "intercept_at_symbolic_n0":intercept,
      "n_stage_count_coefficient":per_stage_count_slope,
      "zero_crossing_n":critical,
      "difference_at_n39":at_39,"difference_at_n40":at_40,
      "root_cause":"MODEL_LEARNED_A_SIZE_DEPENDENT_LOGIT_WHEN_G3_INVARIANT_ROLE_SHOULD_BE_N_INVARIANT",
      "postfirst_tuning_performed":False,
      "new_original_task_bodies_opened":0,"new_original_solver_runs":0,
      "new_model_gradient_updates":0,
      "original_sourcefree_8382_predictions_preserved":True,
      "safe_operational_action":"NEVER_TRUST_UNVERIFIED_NEURAL_INTERVAL; use independent original Horn proof and proven human classical fallback, otherwise UNKNOWN",
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN"
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--original-first",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    out=audit(args.checkpoint,args.original_first)
    args.report.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
