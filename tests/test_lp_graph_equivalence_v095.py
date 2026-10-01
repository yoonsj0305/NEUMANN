import pytest

torch = pytest.importorskip("torch")

from experiments.lp_input_compaction_v094 import propose
from experiments.lp_state_models_v087 import GraphStateModel, PointwiseModel
from neumann1.lp_graph_equivalence_v095 import (
    DECISION,
    authority_boundary,
    permutation_from,
)


@pytest.mark.parametrize("m,n", [(3, 24), (4, 64), (5, 80)])
def test_compact_graph_cannot_change_restricted_support(m, n):
    torch.manual_seed(95000 + m + n)
    A = torch.randn(m, n)
    rows = torch.randn(m, 8)
    cols = torch.randn(n, 8)
    point = PointwiseModel(16).eval()
    full = GraphStateModel(16, False).eval()
    with torch.inference_mode():
        point_only = propose(A, rows, cols, point, None, False)
        compact = propose(A, rows, cols, point, full, True)

    result = authority_boundary(point_only, compact)
    assert result["restricted_support_equivalent"] is True
    assert set(compact["selected"]) == set(point_only["shortlist"])
    assert set(compact["shortlist"]) == set(point_only["shortlist"])
    assert len(compact["shortlist"]) == 2 * m
    assert compact["state_columns"] == 2 * m

    perm = permutation_from(point_only["shortlist"], compact["shortlist"])
    assert sorted(perm) == list(range(2 * m))


def test_boundary_detects_real_support_change_and_duplicate_corruption():
    point = {"basis": [0, 1], "shortlist": [0, 1, 2, 3]}
    same = {"basis": [1, 0], "shortlist": [3, 2, 1, 0]}
    changed = {"basis": [0, 4], "shortlist": [0, 1, 2, 4]}

    assert authority_boundary(point, same) == {
        "restricted_support_equivalent": True,
        "basis_equivalent": True,
        "semantic_delta": "ORDER_ONLY",
    }
    assert authority_boundary(point, changed)["semantic_delta"] == "SUPPORT_CHANGED"
    with pytest.raises(ValueError, match="duplicate"):
        authority_boundary(point, {"basis": [0, 1], "shortlist": [0, 1, 1, 3]})


def test_v095_decision_is_candidate_specific_not_global_q3_q4_closure():
    assert DECISION == "STOP_SAME_SUPPORT_GRAPH_REFINEMENT_NO_NEW_FIT"
