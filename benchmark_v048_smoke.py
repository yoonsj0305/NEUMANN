from __future__ import annotations

import json

from neumann1.cost_gate_v048 import run_static_gate
from neumann1.cost_gate_v048_dataset import contract_examples
from neumann1.stopping_gauntlet import fit_frozen_v033_scorer


if __name__ == "__main__":
    scorer = fit_frozen_v033_scorer()
    result = [run_static_gate(item.example, frozen_scorer=scorer)
              for item in contract_examples()]
    assert all(item.verified and not item.fallback for item in result)
    assert [item.route for item in result] == ["F3", "F1", "F1"]
    print(json.dumps({"smoke_only": True, "routes": [item.route for item in result],
                      "verified": True}))
