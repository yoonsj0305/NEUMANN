from neumann1 import (
    Problem, NeumannEngine, BipartiteMatchingSolver, DeterministicVerifier,
    CostLedger, IRKind,
)
from neumann1.matching_ir import ControlledMatchingStructureFormer, MatchingSemanticVerifier


def test_controlled_matching_compiles_complete_ir_and_solves():
    problem = Problem(
        raw_text="S1 can use A or C; S2 can use B or C; S3 can use A or D",
        metadata={"matching_semantic_contract": {"expected_edges": {
            "S1": ["A", "C"], "S2": ["B", "C"], "S3": ["A", "D"]
        }}},
    )
    former = ControlledMatchingStructureFormer()
    ledger = CostLedger()
    rep = former.form(problem, ledger)
    assert rep.kind == IRKind.BIPARTITE_MATCHING
    assert rep.payload["edges"]["S2"] == ["B", "C"]
    sem = MatchingSemanticVerifier().verify_representation(problem, rep, ledger)
    assert sem.ok

    engine = NeumannEngine(former, [BipartiteMatchingSolver()], DeterministicVerifier(), min_confidence=0.8)
    result = engine.solve(problem)
    assert result.verified
    assert result.answer["perfect"] is True


def test_surface_variants_compile_same_ir():
    p1 = Problem("P1 may be assigned to J1, J3; P2 may be assigned to J2 or J3")
    p2 = Problem("Allowed for P1: J1, J3; Allowed for P2: J2 and J3")
    former = ControlledMatchingStructureFormer()
    r1 = former.form(p1, CostLedger())
    r2 = former.form(p2, CostLedger())
    assert r1.payload["edges"] == r2.payload["edges"]


def test_unrecognized_text_fails_closed():
    p = Problem("Find the minimum spanning tree of this network.")
    rep = ControlledMatchingStructureFormer().form(p, CostLedger())
    assert rep.kind == IRKind.UNKNOWN


def test_semantic_contract_catches_dropped_edge():
    problem = Problem(
        "S1 can use A or C; S2 can use B or C",
        metadata={"matching_semantic_contract": {"expected_edges": {
            "S1": ["A", "C"], "S2": ["B", "C"]
        }}},
    )
    former = ControlledMatchingStructureFormer()
    rep = former.form(problem, CostLedger())
    rep.payload["edges"]["S1"] = ["A"]
    vr = MatchingSemanticVerifier().verify_representation(problem, rep, CostLedger())
    assert not vr.ok