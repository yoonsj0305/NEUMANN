from __future__ import annotations

import json

from neumann1.compression_economics import (
    aggregate_economics_observations,
    audit_checker_economics,
)
from neumann1.stopping_gauntlet import (
    METHODS,
    THRESHOLD_GRID,
    calibrate_threshold,
    fit_frozen_v033_scorer,
)
from neumann1.stopping_gauntlet_dataset import (
    v034_calibration_examples,
    v034_final_examples,
)


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()
    calibration_examples = v034_calibration_examples()
    final_examples = v034_final_examples()

    calibrations = {
        method: calibrate_threshold(
            calibration_examples,
            method,
            frozen_scorer=frozen,
        )
        for method in METHODS
    }

    final: dict[str, dict[str, object]] = {}
    for method in METHODS:
        calibration = calibrations[method]
        observations = tuple(
            audit_checker_economics(
                example,
                method,
                calibration.threshold,
                frozen_scorer=frozen,
            )
            for example in final_examples
        )
        final[method] = aggregate_economics_observations(
            observations
        )

    parity_all = all(
        result["checker_parity_rate"] == 1.0
        for result in final.values()
    )
    verified_all = all(
        result["verified_retention"] == 1.0
        for result in final.values()
    )
    unsafe_zero = all(
        result["unsafe_accepted_reduction_count"] == 0
        for result in final.values()
    )
    thresholds_on_grid = all(
        calibration.threshold in THRESHOLD_GRID
        for calibration in calibrations.values()
    )

    failing_methods = [
        method
        for method in METHODS
        if final[method][
            "mean_successful_path_lb_ratio"
        ]
        >= 1.0
    ]

    keep = (
        parity_all
        and verified_all
        and unsafe_zero
        and thresholds_on_grid
    )

    return {
        "experiment": "v0.0.35 Compression Economics Audit",
        "frozen_inputs": {
            "source_release": "v0.0.34",
            "calibration_examples": len(calibration_examples),
            "final_examples": len(final_examples),
            "learned_checkpoint_sha256": (
                frozen.fitted_state_sha256
            ),
            "methods": list(METHODS),
            "threshold_grid": list(THRESHOLD_GRID),
        },
        "calibrations": {
            method: {
                "threshold": calibration.threshold,
                "micro_precision": (
                    calibration.micro_precision
                ),
                "micro_recall": calibration.micro_recall,
                "micro_f1": calibration.micro_f1,
            }
            for method, calibration in calibrations.items()
        },
        "final": final,
        "economics_gate": {
            "methods_with_mean_successful_path_lb_ratio_ge_1": (
                failing_methods
            ),
            "all_methods_below_1": not failing_methods,
            "interpretation": (
                "A ratio >= 1 is a decisive negative for the "
                "current per-candidate rematerialization path "
                "because the measured quantity omits scorer, "
                "enumeration, rejected hidden work, runtime, "
                "memory, and serialization costs. A ratio < 1 "
                "is only inconclusive, not a positive total-"
                "compute result."
            ),
        },
        "contract_checks": {
            "checker_parity_all": parity_all,
            "verified_retention_all_1": verified_all,
            "unsafe_accepted_reductions_all_0": unsafe_zero,
            "thresholds_on_frozen_grid": thresholds_on_grid,
        },
        "keep_v035_contract": keep,
        "boundary": (
            "Unweighted arithmetic-operation events are an "
            "instrumentation unit, not FLOPs, latency, energy, "
            "or hardware cost. The successful-path measure is "
            "an optimistic lower bound because rejected "
            "materialization work and proposal costs are omitted."
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
