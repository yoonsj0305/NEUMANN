import pytest

from neumann1.collision_boundary_v047 import analyze, exact_rank, matrix_for


@pytest.mark.parametrize("arm,expected", [
    ("overlap", (3, ((0, 1), (1, 2)), True)),
    ("repair", (4, ((0, 1),), False)),
    ("disjoint", (4, ((0, 1), (2, 3)), False)),
])
def test_contract(arm, expected):
    result = analyze(matrix_for(arm, 3_400_123))
    assert (result.rank, result.pairs, result.overlapping_pairs) == expected


def test_exact_rank_rejects_nonsquare_and_counts_zero():
    with pytest.raises(ValueError):
        exact_rank(((1, 2),))
    assert exact_rank(((0, 0), (0, 0))) == 0


def test_unknown_arm():
    with pytest.raises(ValueError):
        matrix_for("unknown", 3_400_123)
