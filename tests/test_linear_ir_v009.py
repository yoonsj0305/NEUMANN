from neumann1 import (
    Problem, CostLedger, IRKind, NeumannEngine,
    LinearSystemSolver, BipartiteMatchingSolver, DeterministicVerifier,
)
from neumann1.linear_ir import ControlledLinearSystemStructureFormer, LinearSemanticVerifier
from neumann1.matching_ir import ControlledMatchingStructureFormer
from neumann1.composite import CompositeStructureFormer


def test_linear_compiler_generates_complete_solver_ready_ir():
    p = Problem(
        "Solve: x + y = 5; x - y = 1",
        {"linear_semantic_contract": {
            "variables": ["x", "y"],
            "A": [[1, 1], [1, -1]],
            "b": [5, 1],
        }},
    )
    former = ControlledLinearSystemStructureFormer()
    rep = former.form(p, CostLedger())
    assert rep.kind == IRKind.LINEAR_SYSTEM
    assert rep.payload["variables"] == ["x", "y"]
    assert rep.payload["A"] == [[1.0, 1.0], [1.0, -1.0]]
    assert rep.payload["b"] == [5.0, 1.0]
    assert LinearSemanticVerifier().verify_representation(p, rep, CostLedger()).ok


def test_linear_compiler_handles_coefficients_and_constants():
    rep = ControlledLinearSystemStructureFormer().form(
        Problem("2*x + 3*y = 13; 5*x - y = 7"),
        CostLedger(),
    )
    assert rep.kind == IRKind.LINEAR_SYSTEM
    assert rep.payload["A"] == [[2.0, 3.0], [5.0, -1.0]]
    assert rep.payload["b"] == [13.0, 7.0]


def test_nonlinear_and_inequality_fail_closed():
    former = ControlledLinearSystemStructureFormer()
    assert former.form(Problem("x*x + y = 3; x - y = 1"), CostLedger()).kind == IRKind.UNKNOWN
    assert former.form(Problem("x + y <= 5; x - y = 1"), CostLedger()).kind == IRKind.UNKNOWN


def test_composite_routes_matching_and_linear_to_different_solvers():
    composite = CompositeStructureFormer([
        ControlledMatchingStructureFormer(),
        ControlledLinearSystemStructureFormer(),
    ])
    engine = NeumannEngine(
        composite,
        [BipartiteMatchingSolver(), LinearSystemSolver()],
        DeterministicVerifier(),
    )

    matching = engine.solve(Problem("S1 can use A or C; S2 can use B or C"))
    assert matching.representation.kind == IRKind.BIPARTITE_MATCHING
    assert matching.solver_name == "augmenting_path_matching"
    assert matching.verified

    linear = engine.solve(Problem("Solve: x + y = 5; x - y = 1"))
    assert linear.representation.kind == IRKind.LINEAR_SYSTEM
    assert linear.solver_name == "gaussian_elimination"
    assert linear.verified
    assert abs(linear.answer["x"] - 3.0) < 1e-9
    assert abs(linear.answer["y"] - 2.0) < 1e-9


def test_composite_unknown_fails_closed():
    composite = CompositeStructureFormer([
        ControlledMatchingStructureFormer(),
        ControlledLinearSystemStructureFormer(),
    ])
    rep = composite.form(Problem("Find a minimum spanning tree."), CostLedger())
    assert rep.kind == IRKind.UNKNOWN
