from __future__ import annotations

import json

from neumann1.anti_shortcut_v042 import E_METHODS, observe_peeling_method
from neumann1.anti_shortcut_v042_dataset import v042_contract_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    scorer = fit_frozen_v033_scorer()
    output = {}
    for arm, example in v042_contract_examples():
        output[arm] = {}
        for method in E_METHODS:
            row = observe_peeling_method(example, method, frozen_scorer=scorer)
            output[arm][method] = {
                "verified": row.verified,
                "unsafe": row.unsafe_accepted_reductions,
                "solver_savings_recovery": row.solver_savings_recovery,
                "elimination_recovery": row.elimination_recovery,
            }
    return {
        "smoke_only": True,
        "arms": output,
        "keep_smoke_contract": all(
            row["verified"] and row["unsafe"] == 0
            for arm in output.values() for row in arm.values()
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
