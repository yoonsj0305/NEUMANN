from __future__ import annotations

import json

from neumann1.block_discovery import (
    observe_discovery_method,
)
from neumann1.block_discovery_dataset import (
    v040_contract_examples,
)
from neumann1.stopping_gauntlet import (
    fit_frozen_v033_scorer,
)


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()
    examples = v040_contract_examples()

    methods = (
        "D2_incidence_exact_overlap",
        "D4_incidence_component_graph",
    )

    results = {}
    all_safe = True
    all_exact = True

    for method in methods:
        rows = tuple(
            observe_discovery_method(
                example,
                method,
                frozen_scorer=frozen,
            )
            for example in examples
        )

        safe = all(
            row.final_verified
            and row.unsafe_accepted_reductions == 0
            for row in rows
        )
        exact = all(
            row.elimination_recovery == 1.0
            and row.solver_savings_recovery == 1.0
            for row in rows
        )

        results[method] = {
            "count": len(rows),
            "verified_and_safe": safe,
            "exact_recovery_on_contract_fixtures": (
                exact
            ),
        }

        all_safe = (
            all_safe
            and safe
        )
        all_exact = (
            all_exact
            and exact
        )

    return {
        "experiment": (
            "v0.0.40 bounded block-discovery "
            "regression smoke"
        ),
        "methods": results,
        "all_methods_verified_and_safe": (
            all_safe
        ),
        "contract_fixtures_exact": (
            all_exact
        ),
        "keep_smoke_contract": (
            all_safe
            and all_exact
        ),
        "smoke_only": True,
        "boundary": (
            "This bounded smoke does not reproduce or replace "
            "the frozen 256-system v0.0.40 full result."
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
