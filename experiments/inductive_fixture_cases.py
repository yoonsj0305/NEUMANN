"""Opened hand-authored F engineering fixtures, never independent benchmarks."""
from neumann1.inductive_symbolic_baseline import from_expressions
from neumann1.inductive_perspective import HORIZON, projections


def coordinate_fixture(power=2, *, goal="position"):
    import sympy as sp
    parameters, state = ["a", "b", "c", "k"], ["x", "y", "t"]
    a, b, c, k, x, y, t = sp.symbols("a b c k x y t")
    n = sp.Symbol(HORIZON)
    z0, z1 = sp.symbols("__z0 __z1")
    increment = sp.expand((x + k) ** power - x ** power)
    original_goal = y if goal == "position" else y - x ** power
    problem = {"semantics": "exact_integer_recurrence", "parameters": parameters, "state": state,
               "initial": projections(parameters, ["a", "b", "c"]),
               "transition": from_expressions(parameters + state, [x + k, y + increment, 3 * t + 1]),
               "goal": from_expressions(parameters + state, [original_goal])}
    if goal == "position":
        proposal = {"encoding": from_expressions(parameters + state, [x, y - x ** power]),
                    "initial": from_expressions(parameters, [a, b - a ** power]),
                    "transition": from_expressions(parameters + ["__z0", "__z1"], [z0 + k, z1]),
                    "closed_form": from_expressions(parameters + [HORIZON], [a + k * n, b - a ** power]),
                    "decode": from_expressions(parameters + ["__z0", "__z1"], [z0 ** power + z1])}
    else:
        proposal = {"encoding": from_expressions(parameters + state, [y - x ** power]),
                    "initial": from_expressions(parameters, [b - a ** power]),
                    "transition": projections(parameters + ["__z0"], ["__z0"]),
                    "closed_form": from_expressions(parameters + [HORIZON], [b - a ** power]),
                    "decode": projections(parameters + ["__z0"], ["__z0"])}
    return problem, proposal


def exponential_goal_fixture():
    import sympy as sp
    problem, _ = coordinate_fixture()
    problem["goal"] = from_expressions(problem["parameters"] + problem["state"], [sp.Symbol("t")])
    return problem
