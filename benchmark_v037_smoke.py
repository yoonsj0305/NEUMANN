from __future__ import annotations

import json

from neumann1.residual_predictor import (
    evaluate_policy,
    evaluate_teacher,
    fit_residual_models,
)
from neumann1.residual_predictor_dataset import (
    V037_TRAIN_EXAMPLES_PER_CELL,
    v037_train_examples,
    v037_validation_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run():
    frozen = fit_frozen_v033_scorer()
    models = fit_residual_models(
        v037_train_examples()[::V037_TRAIN_EXAMPLES_PER_CELL],
        frozen_scorer=frozen,
    )
    examples = v037_validation_examples()[:2]
    teacher = evaluate_teacher(
        examples,
        frozen_scorer=frozen,
    )
    ridge = evaluate_policy(
        examples,
        "ridge",
        frozen_scorer=frozen,
        models=models,
    )
    return {
        "experiment": "v0.0.37 smoke",
        "teacher_verified": all(
            row.final_verified
            for row in teacher
        ),
        "ridge_verified": all(
            row.final_verified
            for row in ridge
        ),
        "ridge_nonpositive_accepted": sum(
            row.nonpositive_accepted_count
            for row in ridge
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
