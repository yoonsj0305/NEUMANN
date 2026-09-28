from __future__ import annotations

import json

from neumann1.compression_utility import (
    calibrate_utility_threshold,
    observe_dynamic_greedy_utility,
    observe_static_isolated_utility,
    observe_utility_calibrated_method,
)
from neumann1.compression_utility_dataset import (
    v035_calibration_examples,
    v035_final_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.learned_compression_dataset import (
    learned_scale_grid,
)


def _one_per_cell(examples):
    output = []
    for k, n in learned_scale_grid():
        output.append(
            next(
                example
                for example in examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            )
        )
    return tuple(output)


def run():
    calibration = _one_per_cell(
        v035_calibration_examples()
    )
    final = _one_per_cell(
        v035_final_examples()
    )
    frozen = fit_frozen_v033_scorer()

    calibrations = {
        method: calibrate_utility_threshold(
            calibration,
            method,
            frozen_scorer=frozen,
        )
        for method in (
            "learned_mlp",
            "target_leaf",
            "markowitz",
        )
    }

    calibrated_verified = {}
    for method, calibration_result in calibrations.items():
        rows = [
            observe_utility_calibrated_method(
                example,
                calibration_result,
                frozen_scorer=frozen,
            )
            for example in final
        ]
        calibrated_verified[method] = all(
            row.final_verified
            and row.unsafe_accepted_reductions == 0
            for row in rows
        )

    static = [
        observe_static_isolated_utility(example)
        for example in final
    ]
    dynamic = [
        observe_dynamic_greedy_utility(example)
        for example in final
    ]

    keep = (
        all(calibrated_verified.values())
        and all(row.final_verified for row in static)
        and all(row.final_verified for row in dynamic)
        and all(
            row.positive_marginal_gain_sum
            == row.solver_savings
            for row in dynamic
        )
    )

    return {
        "experiment": "v0.0.35 contract smoke",
        "smoke_only": True,
        "examples": len(final),
        "calibrated_verified": calibrated_verified,
        "static_verified": all(
            row.final_verified
            for row in static
        ),
        "dynamic_verified": all(
            row.final_verified
            for row in dynamic
        ),
        "dynamic_gain_telescopes": all(
            row.positive_marginal_gain_sum
            == row.solver_savings
            for row in dynamic
        ),
        "keep_smoke_contract": keep,
        "boundary": (
            "This is a bounded CI regression smoke. "
            "It does not reproduce or replace the frozen "
            "256-example v0.0.35 full result."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
