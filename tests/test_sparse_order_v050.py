import pytest

from neumann1.sparse_order_v050 import (
    graph_from_matrix, greedy_order, optimal_symbolic_order, solve_in_order,
)
from neumann1.sparse_order_v050_dataset import contract_examples


@pytest.mark.parametrize("item", contract_examples())
def test_exact_ordering_contract(item):
    optimal, lower_cost, states = optimal_symbolic_order(item.graph)
    assert states > 0
    for rule in ("min_degree", "min_fill"):
        greedy = greedy_order(item.graph, rule=rule)
        result = solve_in_order(item.matrix, item.rhs, greedy)
        assert result.answer == item.truth
        assert result.arithmetic_ops >= lower_cost
    reference = solve_in_order(item.matrix, item.rhs, optimal)
    assert reference.answer == item.truth
    assert reference.arithmetic_ops == lower_cost
    assert graph_from_matrix(item.matrix) == item.graph


def test_bad_inputs_fail_closed():
    item = contract_examples()[0]
    with pytest.raises(ValueError):
        greedy_order(item.graph, rule="unknown")
    with pytest.raises(ValueError):
        solve_in_order(item.matrix, item.rhs, tuple(range(11)))
    with pytest.raises(ValueError):
        graph_from_matrix(((1, 2), (3, 4)))
