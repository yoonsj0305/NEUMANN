from __future__ import annotations

import json

from neumann1.adversarial_v044 import exact_schur_witness
from neumann1.adversarial_v044_dataset import v044_contract_examples
from neumann1.indexed_peeling_v043 import execute_peeling
from neumann1.mixed_coupled import materialize_mixed_reference
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


def run() -> dict[str, object]:
    high, alternatives = v044_contract_examples()
    scorer = fit_frozen_v033_scorer()
    result_h = execute_peeling(high.example, frozen_scorer=scorer, indexed=True)
    oracle = materialize_mixed_reference(high.example)
    result_a = execute_peeling(alternatives.example, frozen_scorer=scorer, indexed=True)
    witnesses = [exact_schur_witness(alternatives.example.full_system,
                                     alternatives.witness.row_pair, pair)
                 for pair in alternatives.witness.target_pairs]
    keep = bool(oracle and oracle.verified and result_h.verified and
                result_h.retained_dimension > oracle.retained_system.dimension and
                result_a.verified and result_a.block_keys == () and
                all(w and w.verified for w in witnesses))
    return {"smoke_only": True, "high_retained_dimension": result_h.retained_dimension,
            "alternative_witnesses_verified": sum(bool(w and w.verified) for w in witnesses),
            "keep_smoke_contract": keep}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
