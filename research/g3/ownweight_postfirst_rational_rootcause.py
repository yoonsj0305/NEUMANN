"""Post-FIRST exact rational margin diagnosis, no new training or benchmarks.

For FINAL stage, x=(1,0,0,1,1,N/12). Thus each class score is
an affine function A+B*N with EXACT rational coefficients determined by
the immutable 10-decimal stored own weights. A negative winner-vs-rival
slope certifies a finite failure for all sufficiently large N.

Not a new FIRST generalization experiment, and not an original task solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

FROZEN_SHA="982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc"
TARGET_FINAL=(3,2,0,0)


def f(value):
    if not isinstance(value,(float,int)):
        raise ValueError("NON_NUMERIC_STUDENT_WEIGHT")
    return Fraction(str(value))


def affine_final(head,token):
    return (
      f(head[0][token])+f(head[3][token])+f(head[4][token]),
      f(head[5][token])/12
    )


def exact_at(a,b,n):
    return a+b*n


def certificate(checkpoint:Path):
    raw=checkpoint.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FROZEN_SHA:
        raise ValueError("ACTUAL_FIRST_STUDENT_CHECKPOINT_CHANGED")
    data=json.loads(raw)
    if data.get("original_external_test_sources_opened")!=0 or len(data["student_weight"])!=4:
        raise ValueError("INVALID_FROZEN_STUDENT_OR_TRAIN_ACCESS")
    records=[]
    for h,(head,target) in enumerate(zip(data["student_weight"],TARGET_FINAL)):
        if len(head)!=6 or any(len(row)!=4 for row in head):
            raise ValueError("FOURHEAD_CATEGORICAL_CHECKPOINT_REQUIRED")
        A,B=affine_final(head,target)
        for rival in range(4):
            if rival==target:
                continue
            C,D=affine_final(head,rival)
            a,b=A-C,B-D
            if b<0:
                # Rival eventually strictly dominates target, regardless of
                # library, future benchmark or numerical threshold tuning.
                n=max(2, int(a/(-b))+1)
                # Exact rational verification (the crossover may be negative).
                if not exact_at(a,b,n)<0:
                    raise ValueError("NOT_EXACT_CROSSOVER")
                if n>2 and exact_at(a,b,n-1)<0:
                    raise ValueError("NOT_MINIMAL_CROSSOVER")
                records.append({"head":h,"correct_token":target,"rival":rival,
                                "intercept_num":str(a.numerator),
                                "intercept_den":str(a.denominator),
                                "slope_num":str(b.numerator),"slope_den":str(b.denominator),
                                "first_strict_loss_from_this_rival_n":n,
                                "permanent_rival_dominance_for_all_integer_n_ge":n,
                                "proof":"exact rational affine difference decreases strictly with N"})
    if not records:
        raise ValueError("NO_NEGATIVE_SLOPE_CANNOT_EXPLAIN_UNBOUNDED_FAILURE")
    earliest=min(records,key=lambda r:r["first_strict_loss_from_this_rival_n"])
    if earliest["first_strict_loss_from_this_rival_n"]!=40:
        raise ValueError("FIRST_DIAGNOSED_CROSSOVER_NOT_FROZEN_N40_OBSERVATION")
    return {
      "schema":"neumann.g3.ownweight-frozen-final-stage-rational-margin-postfirst.v1",
      "actual_frozen_student_checkpoint_SHA256":FROZEN_SHA,
      "classification_head_count":4,
      "feature_semantics":"FINAL x=(1,0,0,1,1,n/12)",
      "unbounded_count_feature_is_semantically_necessary_for_final_role":False,
      "first_strict_wrong_final_stage_N_from_negative_slope":40,
      "arithmetic":"EXACT_RATIONAL_FROM_STORED_TEN_DECIMAL_WEIGHTS",
      "permanent_wrong_final_stage_for_all_integer_N_ge":40,
      "first_original_failed_symbolic_evaluation_run":42200289388,
      "original_retrained":False,"new_task_sources_opened":0,
      "remedy_semantic":"delete nuisance N/12 or constrain it; HUMAN intervention, not autonomous operator invention",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
      "earliest_counterexample_certificate":earliest,
      "all_negative_slope_competitors":records
    }


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--checkpoint",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    p=a.parse_args()
    result=certificate(p.checkpoint)
    p.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items()
       if k!="all_negative_slope_competitors"},indent=2,sort_keys=True))
