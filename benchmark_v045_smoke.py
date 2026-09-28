from __future__ import annotations

import json

from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.schur_cost_v045 import execute_v045
from neumann1.schur_cost_v045_dataset import v045_contract_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    high, alt = v045_contract_examples()
    scorer = fit_frozen_v033_scorer()
    oracle = materialize_mixed_reference(high.example)
    h = execute_v045(high.example, frozen_scorer=scorer)
    a = execute_v045(alt.example, frozen_scorer=scorer)
    return {"smoke_only": True,
            "high_degree": {"verified": h.verified, "mode": h.mode,
                            "oracle_dimension": oracle.retained_system.dimension if oracle else None,
                            "dimension": h.retained_dimension},
            "alternatives": {"verified": a.verified, "mode": a.mode,
                             "dimension": a.retained_dimension},
            "keep_smoke_contract": bool(oracle and h.verified and a.verified
                                        and h.retained_dimension == oracle.retained_system.dimension
                                        and a.retained_dimension == alt.example.apparent_dimension-2)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
