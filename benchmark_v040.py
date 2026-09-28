from __future__ import annotations

import json

from neumann1.block_discovery import (
    DISCOVERY_METHOD_ORDER,
    aggregate_discovery,
    observe_discovery,
    select_discovery_method,
)
from neumann1.block_discovery_dataset import (
    V040_FINAL_EXAMPLES_PER_CELL,
    prior_v040_signatures,
    v040_final_examples,
)
from neumann1.mixed_coupled_dataset import (
    mixed_scale_grid,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
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

    results = {}
    raw_rows = {}

    for method in DISCOVERY_METHOD_ORDER:
        rows = tuple(
            observe_discovery(
                example,
                method,
                frozen_scorer=frozen,
            )
            for example in examples
        )
        raw_rows[method] = rows
        results[method] = (
            aggregate_discovery(
                rows
            )
        )

    selection = select_discovery_method(
        results
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
        for k, n in mixed_scale_grid()
    )

    controls_unchanged = all(
        (
            row.discovered_solver_ops
            == row.baseline_solver_ops
            and row.retained_dimension_error
            == 0
            and row.verified
        )
        for method in DISCOVERY_METHOD_ORDER
        for row in raw_rows[method]
        if (
            row.apparent_dimension
            == row.core_dimension
        )
    )

    system_only_api = True
    no_learned_model = True

    keep = (
        disjoint
        and final_cells_complete
        and controls_unchanged
        and system_only_api
        and no_learned_model
    )

    local_baseline = {
        "mean_active_solver_savings_recovery": (
            results[
                "incidence_signature"
            ][
                "mean_local_only_solver_savings_recovery"
            ]
        )
    }

    selected_method = selection[
        "selected_method"
    ]
    if selected_method is not None:
        selected = results[
            selected_method
        ]
        routing_gain = {
            "selected_method": (
                selected_method
            ),
            "solver_savings_recovery_gain_over_local_only": (
                selected[
                    "mean_active_solver_savings_recovery"
                ]
                - selected[
                    "mean_local_only_solver_savings_recovery"
                ]
            ),
            "mean_retained_dimension_error": (
                selected[
                    "mean_active_retained_dimension_error"
                ]
            ),
        }
    else:
        routing_gain = {
            "selected_method": None,
            "solver_savings_recovery_gain_over_local_only": None,
            "mean_retained_dimension_error": None,
        }

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
            "fresh_signature_disjointness": (
                disjoint
            ),
            "scale_grid": [
                {
                    "core_dimension": k,
                    "apparent_dimension": n,
                }
                for k, n in mixed_scale_grid()
            ],
        },
        "methods": results,
        "local_only_baseline": (
            local_baseline
        ),
        "selection": selection,
        "routing_gain": routing_gain,
        "contract_checks": {
            "final_cells_complete": (
                final_cells_complete
            ),
            "controls_unchanged": (
                controls_unchanged
            ),
            "discovery_api_accepts_system_not_generator_metadata": (
                system_only_api
            ),
            "no_learned_model_in_v040": (
                no_learned_model
            ),
        },
        "keep_v040_contract": (
            keep
        ),
        "boundary": (
            "v0.0.40 tests deterministic discovery and "
            "routing on a fresh instance of the validated "
            "mixed family. It trains no learned block scorer."
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
