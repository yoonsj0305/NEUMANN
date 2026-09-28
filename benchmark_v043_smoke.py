from __future__ import annotations

import json

from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.indexed_peeling_v043_dataset import v043_contract_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    scorer = fit_frozen_v033_scorer()
    arms = {}
    for arm, example in v043_contract_examples():
        old = execute_peeling(example, frozen_scorer=scorer, indexed=False)
        new = execute_peeling(example, frozen_scorer=scorer, indexed=True)
        arms[arm] = {
            "verified": new.verified,
            "equal_keys_answer_dimension_ops": (
                old.local_keys == new.local_keys and old.block_keys == new.block_keys
                and old.answer == new.answer
                and old.retained_dimension == new.retained_dimension
                and old.solver_ops == new.solver_ops
            ),
            "old_pairs": old.row_pair_examinations,
            "indexed_pairs": new.row_pair_examinations,
        }
    return {
        "smoke_only": True, "arms": arms,
        "keep_smoke_contract": all(row["verified"] and row["equal_keys_answer_dimension_ops"]
                                   for row in arms.values()),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
