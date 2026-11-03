"""Check pair-free provenance and geometric invariants."""
import numpy as np
from experiments.prh_pairfree_geometry_p01 import match_pair_free, fingerprints, CONTRACT
from experiments.prh_good_views_p0 import orthogonal


def test_pairfree_recovers_permutation_under_exact_rotation():
    rng = np.random.default_rng(7)
    x = rng.standard_normal((32, 6))
    perm = rng.permutation(32)
    y = (x @ orthogonal(9, 6))[perm]
    out = match_pair_free(x, y)
    assert all(perm[j] == i for i, j in enumerate(out["mapping"]))
    assert out["relative_pairwise_distance_error"] < 1e-10


def test_pairfree_rejects_mismatched_scene_sizes():
    x = np.eye(4)
    try:
        match_pair_free(x, x[:3])
    except ValueError:
        pass
    else:
        raise AssertionError("mismatched scenes allowed")


def test_no_global_claim_from_local_gate():
    assert CONTRACT["global_questions_closed"] == []
    assert CONTRACT["gold_pair_ids_as_input"] is False
    assert CONTRACT["new_training"] is False
