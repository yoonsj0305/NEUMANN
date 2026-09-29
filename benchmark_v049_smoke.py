from __future__ import annotations

import json

from neumann1.cost_gate_v048 import prechoice_features, run_static_gate
from neumann1.matched_topology_v049_dataset import contract_pair
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


if __name__ == "__main__":
    pair = contract_pair()
    scorer = fit_frozen_v033_scorer()
    assert prechoice_features(pair.recoverable) == prechoice_features(pair.retained_support)
    paths = [run_static_gate(example, frozen_scorer=scorer)
             for example in (pair.recoverable, pair.retained_support)]
    assert all(item.verified and item.route == "F3" for item in paths)
    print(json.dumps({"smoke_only": True, "matched": True, "verified": True}))
