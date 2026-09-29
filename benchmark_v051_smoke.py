from neumann1.pace_order_v051 import greedy_order, order_cost, parse_pace_graph, reference_cost


if __name__ == "__main__":
    graph = parse_pace_graph("1 2\n2 3\n3 4\n4 1\n")
    order = greedy_order(graph, "min_fill")
    assert order_cost(graph, order) == reference_cost(graph, order)
    print("PACE order contract smoke PASS")
