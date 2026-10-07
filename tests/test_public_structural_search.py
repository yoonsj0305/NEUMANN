import itertools
import numpy as np
import pytest

from neumann1.contraction_structure import certify_path, is_matrix_chain, public_plan, validate_public
from neumann1.public_rewrite_search import propose
from neumann1.representation_program import Builder, compile_program, verify_original
from neumann1.representation_rewrite_certificate import check_certificate


def test_public_symbolic_composition_has_checkable_trace_without_supplied_answer():
    b = Builder(["x", "y", "z"])
    x, y, z = [b.input(name) for name in b.inputs]
    root = b.add(b.mul(x, y), b.mul(z, x))
    root = b.add(b.mul(root, b.const(1)), b.const(0))
    original = b.finish([root, y])
    result = propose(original)
    assert len(result["certificate"]["steps"]) == 3
    assert check_certificate(original, result["candidate"], result["certificate"])["accepted"]
    assert verify_original(original, result["candidate"])["accepted"]
    rows = list(itertools.product([-7, 0, 10**40], repeat=3))
    assert compile_program(result["candidate"]).run(rows) == [(x * (y + z), y) for x, y, z in rows]


def test_public_symbolic_search_rejects_false_common_factor():
    b = Builder(["x", "y", "z", "w"])
    x, y, z, w = [b.input(name) for name in b.inputs]
    original = b.finish([b.add(b.mul(x, y), b.mul(z, w))])
    result = propose(original)
    assert result["candidate"] == original and result["certificate"]["steps"] == []


@pytest.mark.parametrize("strategy", ["greedy", "auto", "auto-hq", "random-greedy-128", "dynamic-programming"])
def test_hyperedge_is_kept_until_every_dependent_tensor_consumed(strategy):
    public = {"equation": "ab,bc,bd->acd", "shapes": [[2, 3], [3, 2], [3, 2]]}
    result = public_plan(public, strategy)
    a = np.arange(6).reshape(2, 3) - 2
    b = np.arange(6).reshape(3, 2) - 1
    c = np.arange(6).reshape(3, 2)
    expected = np.array([[[sum(int(a[i, k]) * int(b[k, j]) * int(c[k, l]) for k in range(3))
                           for l in range(2)] for j in range(2)] for i in range(2)])
    # Small bounded exact integer fixture: no rounding or overflow.
    import opt_einsum as oe
    actual = oe.contract(public["equation"], a, b, c, optimize=[tuple(s) for s in result["path"]])
    assert np.array_equal(actual, expected)
    assert result["certificate"]["ordered_output"] == "acd"
    assert not result["certificate"]["numerical_dataset_answer_verified"]


def test_chain_recognition_uses_only_original_topology_and_has_strong_native_dp():
    public = {"equation": "bc,cd,ab->ad", "shapes": [[2, 100], [100, 3], [4, 2]]}
    assert is_matrix_chain(public)
    result = public_plan(public, "dynamic-programming")
    assert result["certificate"]["accepted"]
    assert not is_matrix_chain({"equation": "ab,bc,ca->", "shapes": [[2, 2]] * 3})


def test_malformed_or_leaked_structural_state_is_rejected():
    public = {"equation": "ab,bc->ac", "shapes": [[2, 3], [3, 4]]}
    with pytest.raises(ValueError):
        validate_public({**public, "oracle_path": [[0, 1]]})
    with pytest.raises(ValueError):
        validate_public({**public, "shapes": [[2, 3], [2, 4]]})
    for bad in [[[0, 0]], [[True, 1]], [[0, 2]], [[0]], [[0, 1], [0, 1]]]:
        with pytest.raises(ValueError):
            certify_path(public, bad)
    with pytest.raises(ValueError):
        validate_public({**public, "equation": "ab,bc->aa"})


def test_diagonal_repeated_index_matches_original_sum():
    public = {"equation": "aa->", "shapes": [[3, 3]]}
    proof = certify_path(public, [[0]])
    assert proof["witness"][0]["summed"] == ["a"]
    assert proof["dense_arithmetic_work_model"] == 6
