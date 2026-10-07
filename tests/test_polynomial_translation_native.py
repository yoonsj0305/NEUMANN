import copy

import pytest

from experiments.inductive_cost_cases import make_case
from neumann1.inductive_perspective import check_perspective, compile_acceleration, original_execution, projections
from neumann1.polynomial_translation_native import propose


@pytest.mark.parametrize("degree,shear", [(2,-2),(2,3),(4,-2),(4,3),(6,-2),(6,3)])
def test_native_recovers_public_coordinates_and_matches_given_ceiling(degree, shear):
    problem, supplied, requests, expected, _ = make_case(degree, shear, 81200+degree+shear)
    native = propose(problem)
    assert check_perspective(problem, native)["accepted"]
    assert check_perspective(problem, supplied)["accepted"]
    actual = compile_acceleration(problem, native)
    for request, answer in zip(requests, expected):
        assert list(actual.run(request["parameters"], request["steps"])) == answer
    assert actual.run((2, 1, 3, -2), 7) == original_execution(problem, (2, 1, 3, -2), 7)


def test_changed_condition_and_changed_goal_do_not_get_silent_authority():
    problem, _, _, _, _ = make_case(4, 3, 81207)
    changed = copy.deepcopy(problem)
    p = changed["transition"]
    # Drift not represented by the primitive polynomial.
    p["nodes"] += [["const", 1], ["add", p["outputs"][1], len(p["nodes"])]]
    p["outputs"][1] = len(p["nodes"])-1
    try:
        proposal = propose(changed)
    except ValueError:
        pass
    else:
        assert not check_perspective(changed, proposal)["accepted"]
    changed = copy.deepcopy(problem)
    changed["goal"] = projections(changed["parameters"]+changed["state"], ["w"])
    assert not check_perspective(changed, propose(changed))["accepted"]
