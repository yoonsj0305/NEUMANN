import numpy as np
import pytest
from neumann1.native_perspective_catalog import NativePerspectiveCatalog, topology_key


def public(shapes=None):
    return {"equation": "ab,bc,cd->ad", "shapes": shapes or [[2, 100], [100, 2], [2, 100]]}


def catalog():
    return NativePerspectiveCatalog([{"public": public(), "path": path, "source": {"sha256": "fixture_public_native"},
                                      "oracle_used": False, "learned": False} for path in [[[0, 1], [0, 1]], [[1, 2], [0, 1]]]])


def test_dimensions_rebound_select_different_program():
    cache = catalog()
    a = cache.propose(public(), max_work=10**12, max_intermediate_elements=10**9)
    b = cache.propose(public([[100, 2], [2, 100], [100, 2]]), max_work=10**12, max_intermediate_elements=10**9)
    assert a["path"][0] == [0, 1] and b["path"][0] == [1, 2]
    assert not b["learned"] and not b["novel_representation_generated"]


def test_relabelled_original_goal_with_new_numeric_inputs():
    import opt_einsum as oe
    query = {"equation": "xy,yz,zw->wx", "shapes": [[3, 2], [2, 4], [4, 5]]}
    result = catalog().propose(query, max_work=10**12, max_intermediate_elements=10**9)
    assert result["status"] == "CERTIFIED_NATIVE_PRIOR"
    rng = np.random.default_rng(12)
    arrays = [rng.integers(-3, 4, s, dtype=np.int64) for s in query["shapes"]]
    actual = oe.contract(query["equation"], *arrays, optimize=[tuple(s) for s in result["path"]])
    assert np.array_equal(actual, (arrays[0] @ arrays[1] @ arrays[2]).T)


def test_changed_constraints_and_budget_abstain():
    cache = catalog()
    other = {"equation": "ab,bc,cd->abc", "shapes": public()["shapes"]}
    assert cache.propose(other, max_work=10**12, max_intermediate_elements=10**9)["status"] == "CACHE_MISS"
    assert cache.propose(public(), max_work=1, max_intermediate_elements=1)["status"] == "RESOURCE_MODEL_REJECTED"


def test_supervision_must_not_enter_native_catalog():
    row = {"public": public(), "path": [[0, 1], [0, 1]], "source": {"sha256": "fixture"}, "oracle_used": True, "learned": False}
    with pytest.raises(ValueError, match="Oracle"):
        NativePerspectiveCatalog([row])
    with pytest.raises(ValueError):
        topology_key({**public(), "gold_path": []})


def test_diagonal_multiplicity_not_erased():
    a = {"equation": "ii,i->", "shapes": [[2, 2], [2]]}
    b = {"equation": "i,i->", "shapes": [[2], [2]]}
    assert topology_key(a) != topology_key(b)


def test_source_mutation_cannot_change_catalog():
    records = [{"public": public(), "path": [[0, 1], [0, 1]], "source": {"sha256": "fixture"}, "oracle_used": False, "learned": False}]
    cache = NativePerspectiveCatalog(records)
    records[0]["path"][0] = [99]
    result = cache.propose(public(), max_work=10**12, max_intermediate_elements=10**9)
    assert result["status"] == "CERTIFIED_NATIVE_PRIOR"
    result["path"][0] = [99]
    assert cache.propose(public(), max_work=10**12, max_intermediate_elements=10**9)["status"] == "CERTIFIED_NATIVE_PRIOR"
