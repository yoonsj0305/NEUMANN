from __future__ import annotations

import json

from neumann1.anti_shortcut_dataset import v041_contract_examples
from neumann1.block_discovery import DISCOVERY_METHODS, observe_discovery_method
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    frozen = fit_frozen_v033_scorer()
    arms = {}
    for arm, example in v041_contract_examples():
        oracle = materialize_mixed_reference(example)
        observations = [observe_discovery_method(
            example, method, frozen_scorer=frozen,
        ) for method in DISCOVERY_METHODS]
        arms[arm] = {
            "oracle_verified": oracle is not None and oracle.verified,
            "all_methods_verified": all(row.final_verified for row in observations),
            "unsafe_accepted_reductions": sum(
                row.unsafe_accepted_reductions for row in observations),
        }
    return {
        "arms": arms,
        "keep_smoke_contract": all(
            item["oracle_verified"] and item["all_methods_verified"]
            and item["unsafe_accepted_reductions"] == 0
            for item in arms.values()
        ),
        "smoke_only": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
