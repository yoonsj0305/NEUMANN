"""Original semantics, false analogy and independent execution backend checks."""
import pytest

from experiments.representation_headroom import execute_batch, make_case, reference_answers
from experiments.representation_headroom_replay import interpret_original
from neumann1.representation_program import Builder, compile_program, sympy_transform, verify_original


@pytest.mark.parametrize("motif", ["FACTORED", "PATCHED", "CANCELLED"])
def test_unscored_fixture_preserves_original_with_every_public_cas(motif):
    fixture = make_case({"seed": 99, "degree": 2, "motif": motif},
                        {"input_variables": 3, "rows_per_query": 2, "actual_reuse_queries": 2})
    original = fixture["original"]
    rows = [(0, 0, 0), (-3, 5, 9), (10**40, -10**35, 7)]
    reference = reference_answers(original, rows)
    for candidate in [fixture["supplied"]] + [sympy_transform(original, m) for m in
                     ["CSE", "FACTOR_CSE", "FACTOR_TERMS_CSE", "HORNER_CSE"]]:
        assert verify_original(original, candidate)["accepted"]
        compiled = compile_program(candidate)
        assert execute_batch(compiled, rows, "PYTHON_SCALAR") == reference
        assert execute_batch(compiled, rows, "NUMPY_OBJECT") == reference


def test_near_analogy_requires_the_extra_constraint():
    registration = {"input_variables": 3, "rows_per_query": 1, "actual_reuse_queries": 1}
    plain = make_case({"seed": 123, "degree": 2, "motif": "FACTORED"}, registration)
    patched = make_case({"seed": 123, "degree": 2, "motif": "PATCHED"}, registration)
    assert not verify_original(patched["original"], plain["supplied"])["accepted"]
    assert verify_original(patched["original"], patched["supplied"])["accepted"]
    assert set(patched["original"]) == {"semantics", "inputs", "nodes", "outputs"}


def test_vector_backend_preserves_constant_and_ordered_multiple_outputs():
    builder = Builder(["x"])
    x, one = builder.input("x"), builder.const(1)
    program = builder.finish([one, builder.mul(x, x), x])
    rows = [(10**90,), (-2,), (0,)]
    expected = [(1, row[0]**2, row[0]) for row in rows]
    assert execute_batch(compile_program(program), rows, "NUMPY_OBJECT") == expected
    assert interpret_original(program, rows) == expected


def test_cas_does_not_evaluate_dead_exponential_subexpression():
    builder = Builder(["x"])
    x = builder.input("x")
    dead = builder.add(x, builder.const(1))
    for _ in range(24):
        dead = builder.mul(dead, dead)
    original = builder.finish([x])
    candidate = sympy_transform(original, "FACTOR_CSE")
    assert verify_original(original, candidate)["accepted"]
    assert execute_batch(compile_program(candidate), [(10**40,)], "NUMPY_OBJECT") == [(10**40,)]
