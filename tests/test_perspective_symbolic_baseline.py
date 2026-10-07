import itertools

import pytest

from neumann1.perspective_symbolic_baseline import evaluate_integer, optimize_representation


def test_symbolic_factorization_generates_equivalent_ast_without_oracle():
    ast = ["add", ["mul", ["var", "x"], ["var", "y"]], ["mul", ["var", "x"], ["var", "z"]]]
    result = optimize_representation(ast)
    assert result["extracted_tree_cost"] < result["original_tree_cost"]
    assert not result["learned"] and not result["oracle_used"]
    for x, y, z in itertools.product([-11, 0, 17], repeat=3):
        bindings = dict(x=x, y=y, z=z)
        assert evaluate_integer(ast, bindings) == evaluate_integer(result["representation"], bindings)


def test_composed_integer_rules_preserve_large_values_and_remove_zero():
    ast = ["add", ["mul", ["var", "x"], ["int", 1]], ["mul", ["int", 0], ["var", "y"]]]
    result = optimize_representation(ast)
    assert result["representation"] == ["var", "x"]
    assert evaluate_integer(result["representation"], {"x": 10**80}) == 10**80
    assert not result["global_optimum_proven"]


def test_float_and_unregistered_operator_semantics_are_rejected():
    with pytest.raises(ValueError, match="exact-integer"):
        optimize_representation(["var", "x"], semantics="float64")
    with pytest.raises(ValueError, match="constructor"):
        optimize_representation(["div", ["var", "x"], ["int", 0]])
    with pytest.raises(ValueError, match="constructor"):
        optimize_representation(["int", True])
    with pytest.raises(ValueError, match="bounded"):
        optimize_representation(["var", "x"], iterations=100)
