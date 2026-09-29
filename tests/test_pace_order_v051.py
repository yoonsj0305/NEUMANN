import pytest

from neumann1.pace_order_v051 import (
    bounded_proposals, greedy_order, order_cost, parse_pace_graph, reference_cost,
)


def test_parser_and_independent_counter():
    graph = parse_pace_graph("# path plus cycle\n2 4\n4 6\n6 2\n6 9\n")
    assert len(graph) == 4
    for order in (greedy_order(graph, "min_degree"),
                  greedy_order(graph, "min_fill"), *bounded_proposals(graph, "smoke")):
        assert order_cost(graph, order) == reference_cost(graph, order)


def test_reproducible_and_fallback_baseline():
    graph = parse_pace_graph("1 2\n2 3\n3 4\n4 1\n2 5\n5 6\n6 4\n")
    proposals = bounded_proposals(graph, "fixed")
    assert proposals == bounded_proposals(graph, "fixed")
    baseline = min(order_cost(graph, greedy_order(graph, rule)).arithmetic_ops
                   for rule in ("min_degree", "min_fill"))
    assert min([baseline] + [order_cost(graph, order).arithmetic_ops
                             for order in proposals]) <= baseline


@pytest.mark.parametrize("bad", ["", "1 1", "1 2\n2 1", "1 2 3", "-1 1"])
def test_bad_graph_rejected(bad):
    with pytest.raises(ValueError):
        parse_pace_graph(bad)


def test_zero_based_pace_vertex_is_valid():
    assert len(parse_pace_graph("0 2\n2 5\n")) == 3
