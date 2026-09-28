from __future__ import annotations

import json

from neumann1.block_discovery import (
    DISCOVERY_METHODS,
    aggregate_discovery_method,
    deterministic_discovery_decision,
    observe_discovery_method,
    select_best_deterministic,
)
from neumann1.block_discovery_dataset import (
    V040_FINAL_EXAMPLES_PER_CELL,
    prior_v040_signatures,
    v040_final_examples,
)
from neumann1.mixed_coupled import (
    FROZEN_FIRST_STAGE_THRESHOLD,
    FROZEN_RESIDUAL_METHOD,
    FROZEN_RESIDUAL_THRESHOLD,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)
from neumann1.structural_compression import (
    scale_grid,
)


def run() -> dict[str, object]:
    examples = v040_final_examples()
    frozen = fit_frozen_v033_scorer()

    signatures = {
        example.signature
        for example in examples
    }
    disjoint = signatures.isdisjoint(
        prior_v040_signatures()
    )

    method_rows = {}
    method_aggregates = {}

    for method in DISCOVERY_METHODS:
        rows = tuple(
            observe_discovery_method(
                example,
                method,
                frozen_scorer=frozen,
            )
            for example in examples
        )
        method_rows[method] = rows
        method_aggregates[method] = (
            aggregate_discovery_method(
                rows
            )
        )

    (
        best_method,
        best_aggregate,
    ) = select_best_deterministic(
        method_aggregates
    )
    decision = (
        deterministic_discovery_decision(
            best_aggregate
        )
    )

    final_cells_complete = all(
        len(
            [
                example
                for example in examples
                if (
                    example.core_dimension,
                    example.apparent_dimension,
                )
                == (k, n)
            ]
        )
        == V040_FINAL_EXAMPLES_PER_CELL
        for k, n in scale_grid()
    )

    all_safe = all(
        aggregate[
            "verified_retention"
        ]
        == 1.0
        and aggregate[
            "unsafe_accepted_reduction_count"
        ]
        == 0
        for aggregate
        in method_aggregates.values()
    )

    controls_unchanged = all(
        row.total_eliminated_variables
        == 0
        and row.retained_dimension
        == row.apparent_dimension
        for rows in method_rows.values()
        for row in rows
        if row.oracle_elimination_count
        == 0
    )

    thresholds_frozen = (
        FROZEN_FIRST_STAGE_THRESHOLD
        == 0.10
        and FROZEN_RESIDUAL_METHOD
        == "markowitz"
        and FROZEN_RESIDUAL_THRESHOLD
        == 0.05
    )

    keep = (
        disjoint
        and final_cells_complete
        and all_safe
        and controls_unchanged
        and thresholds_frozen
    )

    return {
        "experiment": (
            "v0.0.40 Coupled-Block "
            "Discovery / Routing Gauntlet"
        ),
        "data_contract": {
            "final_examples": len(
                examples
            ),
            "final_examples_per_cell": (
                V040_FINAL_EXAMPLES_PER_CELL
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in scale_grid()
            ],
            "fresh_signature_disjointness": (
                disjoint
            ),
        },
        "frozen_contract": {
            "legacy_local_pipeline": (
                "target_leaf @ 0.10 -> "
                "Markowitz @ 0.05"
            ),
            "learned_models_trained": 0,
            "generator_identity_available_to_deployable_methods": False,
        },
        "final_methods": (
            method_aggregates
        ),
        "primary_final": {
            "best_deterministic_method": (
                best_method
            ),
            "solver_savings_recovery": (
                best_aggregate[
                    "mean_solver_savings_recovery"
                ]
            ),
            "elimination_recovery": (
                best_aggregate[
                    "mean_elimination_recovery"
                ]
            ),
            "block_precision": (
                best_aggregate[
                    "block_precision"
                ]
            ),
            "block_recall": (
                best_aggregate[
                    "block_recall"
                ]
            ),
            "block_f1": (
                best_aggregate[
                    "block_f1"
                ]
            ),
            "verified_retention": (
                best_aggregate[
                    "verified_retention"
                ]
            ),
            "unsafe_accepted_reduction_count": (
                best_aggregate[
                    "unsafe_accepted_reduction_count"
                ]
            ),
            "decision": (
                decision[
                    "decision"
                ]
            ),
            "gates": {
                key: value
                for key, value
                in decision.items()
                if key.startswith(
                    "gate_"
                )
            },
        },
        "routing_diagnostic": {
            "D1_mean_coupled_target_consumed_locally": (
                method_aggregates[
                    "D1_local_first_exact_overlap"
                ][
                    "mean_coupled_target_consumed_locally"
                ]
            ),
            "D2_mean_coupled_target_consumed_locally": (
                method_aggregates[
                    "D2_incidence_exact_overlap"
                ][
                    "mean_coupled_target_consumed_locally"
                ]
            ),
            "D2_easy_leaf_routing_precision": (
                method_aggregates[
                    "D2_incidence_exact_overlap"
                ][
                    "easy_leaf_routing_precision"
                ]
            ),
            "D2_easy_leaf_routing_recall": (
                method_aggregates[
                    "D2_incidence_exact_overlap"
                ][
                    "easy_leaf_routing_recall"
                ]
            ),
        },
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "all_methods_verified_and_safe": (
                all_safe
            ),
            "controls_unchanged": (
                controls_unchanged
            ),
            "legacy_thresholds_frozen": (
                thresholds_frozen
            ),
        },
        "keep_v040_contract": keep,
        "boundary": (
            "v0.0.40 tests deterministic routing and block "
            "discovery on the frozen mixed 2x2 family. "
            "It trains no learned block scorer and makes no "
            "domain-general discovery claim."
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
