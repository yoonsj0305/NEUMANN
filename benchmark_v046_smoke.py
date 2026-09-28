from __future__ import annotations

import json

from neumann1.cached_cost_v046 import execute_v046
from neumann1.cached_cost_v046_dataset import v046_contract_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.schur_cost_v045 import execute_v045
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    high, dense = v046_contract_examples()
    scorer = fit_frozen_v033_scorer()
    f2 = execute_v045(high.example, frozen_scorer=scorer)
    f3 = execute_v046(high.example, frozen_scorer=scorer)
    f1_dense = execute_peeling(dense.example, frozen_scorer=scorer, indexed=True)
    f3_dense = execute_v046(dense.example, frozen_scorer=scorer)
    return {
        "smoke_only": True,
        "high_exact_match": f2.verified and f3.verified and f2.block_keys == f3.block_keys
                            and f2.answer == f3.answer and f2.solver_ops == f3.solver_ops,
        "high_f2_checkers": f2.checkers,
        "high_f3_checkers": f3.checkers,
        "dense_abstention_match": f1_dense.verified and f3_dense.verified
                                  and f1_dense.answer == f3_dense.answer
                                  and f1_dense.block_keys == f3_dense.block_keys,
        "keep_smoke_contract": (f2.verified and f3.verified
                                and f2.block_keys == f3.block_keys
                                and f3.checkers < f2.checkers
                                and f1_dense.answer == f3_dense.answer),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
