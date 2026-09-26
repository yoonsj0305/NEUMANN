from neumann1 import (
    Problem, NeumannEngine, ExplicitStructureFormer,
    BipartiteMatchingSolver, ShortestPathSolver, LinearSystemSolver,
    DeterministicVerifier,
)


def engine():
    return NeumannEngine(
        ExplicitStructureFormer(),
        [BipartiteMatchingSolver(), ShortestPathSolver(), LinearSystemSolver()],
        DeterministicVerifier(),
    )


def test_satellite_assignment_routes_to_matching_and_verifies():
    p = Problem(
        raw_text="Assign six satellites to compatible slots.",
        metadata={"candidate_ir": {
            "kind": "bipartite_matching",
            "confidence": 0.99,
            "payload": {
                "left": ["S1","S2","S3","S4","S5","S6"],
                "edges": {
                    "S1":["A","C"], "S2":["B","C"], "S3":["A","D"],
                    "S4":["D","E"], "S5":["C","F"], "S6":["E","F"]
                }
            }
        }}
    )
    r = engine().solve(p)
    assert r.verified
    assert r.answer["perfect"] is True
    assert r.solver_name == "augmenting_path_matching"
    assert r.ledger.total_steps > 0


def test_employee_assignment_same_structure_different_surface():
    p = Problem(
        raw_text="Assign employees to jobs they can perform.",
        metadata={"candidate_ir": {
            "kind": "bipartite_matching",
            "confidence": 0.98,
            "payload": {
                "left": ["P1","P2","P3","P4","P5","P6"],
                "edges": {
                    "P1":["J1","J3"], "P2":["J2","J3"], "P3":["J1","J4"],
                    "P4":["J4","J5"], "P5":["J3","J6"], "P6":["J5","J6"]
                }
            }
        }}
    )
    r = engine().solve(p)
    assert r.verified
    assert r.answer["perfect"] is True


def test_shortest_path_routes_to_dijkstra():
    p = Problem(
        raw_text="Find the cheapest route from A to D.",
        metadata={"candidate_ir": {
            "kind": "shortest_path",
            "confidence": 0.97,
            "payload": {
                "source":"A", "target":"D",
                "graph": {
                    "A":[["B",1.0],["C",5.0]],
                    "B":[["A",1.0],["C",1.0],["D",4.0]],
                    "C":[["A",5.0],["B",1.0],["D",1.0]],
                    "D":[["B",4.0],["C",1.0]],
                }
            }
        }}
    )
    r = engine().solve(p)
    assert r.verified
    assert r.answer["distance"] == 3.0
    assert r.answer["path"] == ["A","B","C","D"]


def test_linear_system_routes_to_gaussian_elimination():
    p = Problem(
        raw_text="Solve x+y=5 and x-y=1.",
        metadata={"candidate_ir": {
            "kind": "linear_system",
            "confidence": 0.99,
            "payload": {"A":[[1,1],[1,-1]], "b":[5,1], "variables":["x","y"]}
        }}
    )
    r = engine().solve(p)
    assert r.verified
    assert abs(r.answer["x"] - 3.0) < 1e-9
    assert abs(r.answer["y"] - 2.0) < 1e-9


def test_unknown_fails_closed():
    p = Problem(raw_text="A vague problem with no IR.")
    r = engine().solve(p)
    assert not r.verified
    assert r.solver_name == "fallback_required"
    assert r.answer is None


def test_low_confidence_fails_closed():
    p = Problem(raw_text="Maybe matching", metadata={"candidate_ir": {
        "kind":"bipartite_matching", "confidence":0.3, "payload":{"left":[],"edges":{}}
    }})
    r = engine().solve(p)
    assert not r.verified
    assert r.solver_name == "fallback_required"


def test_internal_verifier_does_not_prove_raw_problem_semantics():
    p = Problem(
        raw_text="Find the shortest route from A to D.",
        metadata={"candidate_ir": {
            "kind":"bipartite_matching", "confidence":0.99,
            "payload":{"left":["A"],"edges":{"A":["D"]}}
        }}
    )
    r = engine().solve(p)
    assert r.verified is True
    assert r.representation.kind.value == "bipartite_matching"


def test_reference_semantic_contract_blocks_wrong_ir():
    from neumann1 import ReferenceSemanticVerifier
    eng = NeumannEngine(
        ExplicitStructureFormer(),
        [BipartiteMatchingSolver(), ShortestPathSolver(), LinearSystemSolver()],
        ReferenceSemanticVerifier(),
    )
    p = Problem(
        raw_text="Find the shortest route from A to D.",
        metadata={
            "semantic_contract": {
                "expected_kind":"shortest_path",
                "required_payload_keys":["graph","source","target"],
            },
            "candidate_ir": {
                "kind":"bipartite_matching", "confidence":0.99,
                "payload":{"left":["A"],"edges":{"A":["D"]}}
            },
        },
    )
    r = eng.solve(p)
    assert r.verified is False
    assert "semantic kind mismatch" in r.verification_reason
