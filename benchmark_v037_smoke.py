from __future__ import annotations

import json

from neumann1.residual_learning import (
    fit_residual_models,
    inspect_residual_model,
    observe_deterministic_residual_policy,
    observe_learned_residual_policy,
)
from neumann1.residual_learning_dataset import (
    v037_final_examples,
    v037_train_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()

    models, training_rows = fit_residual_models(
        v037_train_examples()[:2],
        frozen_scorer=frozen,
    )
    mlp = models["tiny_mlp"]
    footprint = inspect_residual_model(mlp)

    examples = v037_final_examples()[:2]
    learned = tuple(
        observe_learned_residual_policy(
            example,
            mlp,
            0.10,
            frozen_scorer=frozen,
        )
        for example in examples
    )
    deterministic = tuple(
        observe_deterministic_residual_policy(
            example,
            "markowitz",
            0.05,
            frozen_scorer=frozen,
        )
        for example in examples
    )

    learned_safe = all(
        row.final_verified
        and row.unsafe_accepted_reductions == 0
        for row in learned
    )
    deterministic_safe = all(
        row.final_verified
        and row.unsafe_accepted_reductions == 0
        for row in deterministic
    )

    keep = (
        bool(training_rows)
        and footprint.input_feature_dimension == 22
        and footprint.hidden_units == 8
        and footprint.fitted_weight_bias_scalars == 193
        and learned_safe
        and deterministic_safe
    )

    return {
        "experiment": "v0.0.37 bounded regression smoke",
        "examples": len(examples),
        "training_rows": len(training_rows),
        "tiny_mlp_footprint": {
            "feature_dimension": (
                footprint.input_feature_dimension
            ),
            "hidden_units": footprint.hidden_units,
            "fitted_weight_bias_scalars": (
                footprint.fitted_weight_bias_scalars
            ),
        },
        "frozen_learned_threshold": 0.10,
        "frozen_deterministic_method": "markowitz",
        "frozen_deterministic_threshold": 0.05,
        "learned_verified": learned_safe,
        "deterministic_verified": deterministic_safe,
        "keep_smoke_contract": keep,
        "smoke_only": True,
        "boundary": (
            "This bounded smoke does not reproduce or replace "
            "the frozen 192-example v0.0.37 full result."
        ),
    }


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2,
            sort_keys=True,
        )
    )
