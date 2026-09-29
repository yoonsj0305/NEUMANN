from __future__ import annotations

import json

from neumann1.sparse_order_v050 import greedy_order, optimal_symbolic_order, solve_in_order
from neumann1.sparse_order_v050_dataset import contract_examples


if __name__ == "__main__":
    for item in contract_examples():
        order, cost, _ = optimal_symbolic_order(item.graph)
        best = min(solve_in_order(item.matrix, item.rhs, greedy_order(item.graph, rule=rule)).arithmetic_ops
                   for rule in ("min_degree", "min_fill"))
        result = solve_in_order(item.matrix, item.rhs, order)
        assert result.answer == item.truth and result.arithmetic_ops == cost <= best
    print(json.dumps({"smoke_only": True, "exact": True}))
