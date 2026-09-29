from __future__ import annotations

import json
from statistics import mean, median
from time import perf_counter_ns

from neumann1.sparse_order_v050 import greedy_order, optimal_symbolic_order, solve_in_order
from neumann1.sparse_order_v050_dataset import final_examples
from neumann1.structural_compression import ExactLinearSystem, solve_exact_gauss_jordan


def _measure(call):
    start = perf_counter_ns()
    result = call()
    return result, (perf_counter_ns() - start) / 1_000_000


def run() -> dict[str, object]:
    items = final_examples()
    signatures = {(item.matrix, item.rhs) for item in items}
    graphs = {item.graph for item in items}
    fresh = len(items) == len(signatures) == len(graphs) == 48
    cells = {degree: [] for degree in (3, 4)}
    for item in items:
        natural = tuple(range(12))
        mindegree, degree_search_ms = _measure(lambda: greedy_order(item.graph, rule="min_degree"))
        minfill, fill_search_ms = _measure(lambda: greedy_order(item.graph, rule="min_fill"))
        (optimal, symbolic_cost, states), teacher_search_ms = _measure(
            lambda: optimal_symbolic_order(item.graph))
        outputs = {}
        solve_times = {}
        for name, order in (("natural", natural), ("min_degree", mindegree),
                            ("min_fill", minfill), ("teacher", optimal)):
            outputs[name], solve_times[name] = _measure(
                lambda order=order: solve_in_order(item.matrix, item.rhs, order))
        system = ExactLinearSystem(tuple(f"v{i}" for i in range(12)),
                                   item.matrix, item.rhs, item.truth)
        baseline, _ = solve_exact_gauss_jordan(system)
        verified = all(result.answer == item.truth
                       and all(result.answer[i] == baseline[f"v{i}"] for i in range(12))
                       for result in outputs.values())
        best_greedy = min(outputs["min_degree"].arithmetic_ops,
                          outputs["min_fill"].arithmetic_ops)
        headroom = (best_greedy - symbolic_cost) / best_greedy
        contract = (verified and outputs["teacher"].arithmetic_ops == symbolic_cost
                    and headroom >= 0 and states > 0)
        cells[item.degree].append({
            "contract": contract, "headroom": headroom,
            "natural_ops": outputs["natural"].arithmetic_ops,
            "degree_ops": outputs["min_degree"].arithmetic_ops,
            "fill_ops": outputs["min_fill"].arithmetic_ops,
            "teacher_ops": symbolic_cost,
            "natural_fill": outputs["natural"].fill_edges,
            "teacher_fill": outputs["teacher"].fill_edges,
            "teacher_states": states, "teacher_search_ms": teacher_search_ms,
            "degree_search_ms": degree_search_ms, "fill_search_ms": fill_search_ms,
            "teacher_solve_ms": solve_times["teacher"],
        })
    valid = fresh and all(len(cells[degree]) == 24 and
                          all(row["contract"] for row in cells[degree]) for degree in cells)
    qualifying = {degree: sum(row["headroom"] >= 0.10 for row in rows)
                  for degree, rows in cells.items()}
    decision = ("INVALID_FAMILY" if not valid else
                "ORDERING_HEADROOM_VISIBLE" if sum(qualifying.values()) >= 8
                and all(count >= 2 for count in qualifying.values()) else
                "SPARSE_ORDER_SATURATED")
    return {"version": "0.0.50", "count": len(items), "fresh": fresh,
            "verified_contract": valid, "decision": decision,
            "qualifying_10pct": {str(k): v for k, v in qualifying.items()},
            "arms": {str(degree): {
                "count": len(rows), "verified": all(row["contract"] for row in rows),
                "mean_headroom": mean(row["headroom"] for row in rows),
                "median_headroom": median(row["headroom"] for row in rows),
                "max_headroom": max(row["headroom"] for row in rows),
                "mean_natural_ops": mean(row["natural_ops"] for row in rows),
                "mean_min_degree_ops": mean(row["degree_ops"] for row in rows),
                "mean_min_fill_ops": mean(row["fill_ops"] for row in rows),
                "mean_teacher_ops": mean(row["teacher_ops"] for row in rows),
                "median_teacher_states": median(row["teacher_states"] for row in rows),
                "median_teacher_search_ms": median(row["teacher_search_ms"] for row in rows),
                "median_teacher_solve_ms": median(row["teacher_solve_ms"] for row in rows),
            } for degree, rows in cells.items()},
            "boundary": "Synthetic SPD graph Laplacians, scalar arithmetic proxy; no learned model or total-compute advantage."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
