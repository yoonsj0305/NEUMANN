from neumann1 import Problem, CostLedger, IRKind
from neumann1.matching_ir import (
    ControlledMatchingStructureFormer,
    MatchingSemanticVerifier,
    edge_metrics,
)


def compile_text(text):
    return ControlledMatchingStructureFormer().form(Problem(text), CostLedger())


def test_all_nonempty_statements_must_parse():
    rep = compile_text("S1 can use A or C; this statement is unsupported; S2 can use B or C")
    assert rep.kind == IRKind.UNKNOWN
    assert "unparsed nonempty statement" in rep.rationale


def test_conflicting_duplicate_left_fails_closed():
    rep = compile_text("S1 can use A or C; S1 can use B or C; S2 can use B or D")
    assert rep.kind == IRKind.UNKNOWN
    assert "conflicting repeated statement" in rep.rationale


def test_identical_duplicate_is_allowed_but_recorded():
    rep = compile_text("S1 can use A or C; S1 can use C or A; S2 can use B or D")
    assert rep.kind == IRKind.BIPARTITE_MATCHING
    assert rep.payload["edges"]["S1"] == ["A", "C"]
    assert rep.payload["diagnostics"]["duplicate_lefts"] == ["S1"]


def test_negation_and_capacity_fail_closed():
    assert compile_text("S1 can use A except A; S2 can use B or C").kind == IRKind.UNKNOWN
    assert compile_text("S1 can use A or C; S2 can use B with capacity 2").kind == IRKind.UNKNOWN


def test_edge_metrics_detect_drop_and_extra():
    m = edge_metrics(
        {"S1":["A","C"], "S2":["B","C"]},
        {"S1":["A"], "S2":["B","C","D"]},
    )
    assert m.true_positive == 3
    assert m.false_positive == 1
    assert m.false_negative == 1
    assert round(m.precision, 3) == 0.75
    assert round(m.recall, 3) == 0.75


def test_semantic_verifier_reports_precision_recall_on_mismatch():
    p = Problem(
        "S1 can use A or C; S2 can use B or C",
        {"matching_semantic_contract":{"expected_edges":{"S1":["A","C"],"S2":["B","C"]}}},
    )
    rep = compile_text(p.raw_text)
    rep.payload["edges"]["S1"] = ["A"]
    vr = MatchingSemanticVerifier().verify_representation(p, rep, CostLedger())
    assert not vr.ok
    assert "precision=" in vr.reason and "recall=" in vr.reason
