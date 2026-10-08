import copy
import itertools

import pytest
import sympy as sp

from experiments.inductive_fixture_cases import coordinate_fixture, exponential_goal_fixture
from neumann1.inductive_perspective import (HORIZON, check_perspective, compile_acceleration,
                                          original_execution, projections)
from neumann1.inductive_symbolic_baseline import (discover_polynomial_invariants,
    from_expressions, propose_polynomial_acceleration, state_closure)
from neumann1.representation_program import ProgramError, polynomial_forms


@pytest.mark.parametrize("power,goal", list(itertools.product([2, 3], ["position", "invariant"])))
def test_generated_coordinates_are_universally_certified_and_replay_original(power, goal):
    problem, proposal = coordinate_fixture(power, goal=goal)
    proof = check_perspective(problem, proposal)
    assert proof["accepted"] and len(proof["obligations"]) == 5
    accelerated = compile_acceleration(problem, proposal)
    for parameters in [(2, 7, 3, 1), (-4, 11, -2, -3), (10**40, -10**60, 9, 0)]:
        for steps in [0, 1, 7, 31]:
            assert accelerated.run(parameters, steps) == original_execution(problem, parameters, steps)
    assert accelerated.run((2, 7, 3, 1), 10**30) == ((2 + 10**30) ** power + 7 - 2 ** power if goal == "position" else 7 - 2 ** power,)


def test_false_analogy_after_transition_constraint_change_is_rejected():
    problem, proposal = coordinate_fixture()
    changed = copy.deepcopy(problem)
    program = changed["transition"]
    program["nodes"] += [["const", 1], ["add", program["outputs"][1], len(program["nodes"])]]
    program["outputs"][1] = len(program["nodes"]) - 1
    proof = check_perspective(changed, proposal)
    assert proof["status"] == "REJECTED" and proof["failed_obligation"] == "TRANSITION_COMMUTES"


def test_goal_sufficiency_prevents_dropping_relevant_information():
    problem, proposal = coordinate_fixture()
    problem["goal"] = projections(problem["parameters"] + problem["state"], ["t"])
    proof = check_perspective(problem, proposal)
    assert not proof["accepted"] and proof["failed_obligation"] == "ORIGINAL_GOAL_SUFFICIENT"


def test_irrelevant_transition_can_change_without_invalidating_original_goal():
    problem, proposal = coordinate_fixture()
    state_inputs = problem["parameters"] + problem["state"]
    x, y, t, k = sp.symbols("x y t k")
    problem["transition"] = from_expressions(state_inputs, [x + k, y + 2 * k * x + k*k, t*t + 1])
    assert check_perspective(problem, proposal)["accepted"]


def test_four_matching_unrolled_samples_do_not_authorize_a_false_closed_form():
    problem, proposal = coordinate_fixture()
    a, b, k = sp.symbols("a b k")
    n = sp.Symbol(HORIZON)
    bad = n * (n-1) * (n-2) * (n-3)
    proposal["closed_form"] = from_expressions(problem["parameters"] + [HORIZON], [a + k*n + sp.expand(bad), b-a*a])
    proof = check_perspective(problem, proposal)
    assert not proof["accepted"] and proof["failed_obligation"] == "CLOSED_STEP"
    with pytest.raises(ProgramError, match="Uncertified"):
        compile_acceleration(problem, proposal)


def test_stale_certificate_is_not_an_execution_authority():
    problem, proposal = coordinate_fixture()
    assert check_perspective(problem, proposal)["accepted"]
    program = proposal["initial"]
    program["nodes"] += [["const", 1], ["add", program["outputs"][0], len(program["nodes"])]]
    program["outputs"][0] = len(program["nodes"]) - 1
    assert check_perspective(problem, proposal)["failed_obligation"] == "ENCODE_INITIAL"
    with pytest.raises(ProgramError):
        compile_acceleration(problem, proposal)


def test_verification_budget_exhaustion_is_not_acceptance():
    problem, proposal = coordinate_fixture()
    proof = check_perspective(problem, proposal, max_terms=1)
    assert not proof["accepted"] and proof["status"] == "NOT_VERIFIED"


@pytest.mark.parametrize("mutation", ["oracle", "float", "reserved", "overlapping", "output_order"])
def test_semantics_and_ordered_public_interfaces_fail_closed(mutation):
    problem, proposal = coordinate_fixture()
    if mutation == "oracle":
        problem["oracle"] = "supplied answer"
    elif mutation == "float":
        problem["semantics"] = "float64"
    elif mutation == "reserved":
        problem["parameters"][0] = "__steps"
    elif mutation == "overlapping":
        problem["state"][0] = "a"
    else:
        proposal["closed_form"]["outputs"].reverse()
    assert not check_perspective(problem, proposal)["accepted"]


def test_runtime_exact_integer_nonnegative_domain():
    problem, proposal = coordinate_fixture()
    engine = compile_acceleration(problem, proposal)
    for parameters, steps in [((2, 7, 3, 1), -1), ((2, 7, 3, 1), True), ((2.0, 7, 3, 1), 1), ((2, 7), 1)]:
        with pytest.raises(ProgramError):
            engine.run(parameters, steps)


@pytest.mark.parametrize("power", [2, 3])
def test_native_generates_closed_programs_from_public_spec_and_certifies_them(power):
    problem, _ = coordinate_fixture(power)
    result = propose_polynomial_acceleration(problem)
    assert result["status"] == "CERTIFIED_NATIVE_PROPOSAL" and result["certificate"]["accepted"]
    assert result["retained_state"] == state_closure(problem) == ["x", "y"]
    assert result["learned"] is False and result["oracle_used"] is False
    engine = compile_acceleration(problem, result["proposal"])
    assert engine.run((-4, 11, -2, -3), 17) == original_execution(problem, (-4, 11, -2, -3), 17)


def test_native_rejects_polynomial_interpolation_for_exponential_goal():
    result = propose_polynomial_acceleration(exponential_goal_fixture())
    assert result["status"].startswith("ABSTAINED")
    assert not result.get("certificate", {}).get("accepted", False)


def test_native_synthesizes_nontrivial_invariant_coefficients_without_oracle():
    problem, _ = coordinate_fixture()
    result = discover_polynomial_invariants(problem)
    x, y = sp.symbols("x y")
    desired = polynomial_forms(from_expressions(problem["parameters"] + problem["state"], [y-x*x]))
    opposite = polynomial_forms(from_expressions(problem["parameters"] + problem["state"], [x*x-y]))
    assert any(polynomial_forms(i["program"]) in [desired, opposite] for i in result["invariants"])
    assert all(i["universally_checked"] for i in result["invariants"])
    assert result["learned"] is False and result["goal_sufficiency_established"] is False


def test_invariant_feature_budget_and_synthesis_degree_are_enforced():
    problem, _ = coordinate_fixture()
    with pytest.raises(ProgramError, match="budget"):
        discover_polynomial_invariants(problem, max_features=1)
    assert propose_polynomial_acceleration(problem, degree=4)["status"].startswith("ABSTAINED")
