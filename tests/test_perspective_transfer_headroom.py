import numpy as np
import opt_einsum as oe
import pytest
from experiments.perspective_transfer_headroom import changed_problem
from neumann1.public_path_reuse import propose
from neumann1.native_perspective_catalog import topology_key


def prior():
    p = {"equation": "ab,bc,cd->ad", "shapes": [[2, 3], [3, 2], [2, 3]]}
    return [{"public": p, "path": [[0, 1], [0, 1]], "source": {"sha256": "fixture"}, "oracle_used": False, "learned": False}]


def test_splice_keeps_ranks_but_changes_public_connectivity():
    p = {"equation": "ab,bc,cd,de->ae", "shapes": [[3, 3]] * 4}
    q, lineage = changed_problem(p, "SPLICE", 77)
    assert topology_key(q) != topology_key(p)
    assert [len(s) for s in q["shapes"]] == [len(s) for s in p["shapes"]]
    assert q["equation"].split("->")[1] == "ae"
    assert lineage["original_semantics_changed_for_splice"]


def test_public_prior_allowed_across_changed_goal_and_connectivity():
    p = {"equation": "ab,cd,db->ac", "shapes": [[2, 3], [4, 5], [5, 3]]}
    r = propose(p, prior(), "BEST_MODEL", max_work=1000000, max_elements=1000000)
    assert r["status"] == "CERTIFIED_PUBLIC_PRIOR"
    rng = np.random.default_rng(17)
    arrays = [rng.integers(-2, 3, s) for s in p["shapes"]]
    actual = oe.contract(p["equation"], *arrays, optimize=[tuple(s) for s in r["path"]])
    assert np.array_equal(actual, arrays[0] @ arrays[2].T @ arrays[1].T)


def test_oracle_prior_and_excessive_model_cost_rejected():
    records = prior()
    p = records[0]["public"]
    assert propose(p, records, "FIRST", max_work=1, max_elements=1)["status"] == "NO_ELIGIBLE_PUBLIC_PRIOR"
    records[0]["oracle_used"] = True
    with pytest.raises(ValueError, match="Native"):
        propose(p, records, "BEST_MODEL", max_work=1000000, max_elements=1000000)


def test_rebound_preserves_key_without_claiming_new_topology():
    p = prior()[0]["public"]
    q, lineage = changed_problem(p, "REBOUND", 99)
    assert topology_key(q) == topology_key(p)
    assert not lineage["original_semantics_changed_for_splice"]
