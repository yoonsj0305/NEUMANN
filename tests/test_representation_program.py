import itertools

import pytest

from neumann1.representation_program import (Builder, ProgramError, compile_program,
    polynomial_forms, sympy_transform, validate, verify_original)


def examples():
    b = Builder(["x", "y", "z"])
    x, y, z = [b.input(n) for n in b.inputs]
    original = b.finish([b.add(b.mul(x, y), b.mul(x, z))])
    c = Builder(b.inputs)
    x, y, z = [c.input(n) for n in c.inputs]
    factored = c.finish([c.mul(x, c.add(y, z))])
    return original, factored


def test_universal_identity_and_compiled_exact_execution():
    original, factored = examples()
    assert verify_original(original, factored)["accepted"]
    rows = list(itertools.product([-7, 0, 13, 10**40], repeat=3))
    expected = [(x * y + x * z,) for x, y, z in rows]
    direct, reduced = compile_program(original), compile_program(factored)
    assert direct.run(rows) == reduced.run(rows) == expected
    assert direct.mul_calls == 2 and reduced.mul_calls == 1


def test_nearby_goal_rejects_wrong_analogy_even_if_some_inputs_match():
    original, factored = examples()
    changed = {**original, "nodes": original["nodes"] + [["const", 1], ["add", original["outputs"][0], len(original["nodes"]) ]],
               "outputs": [len(original["nodes"]) + 1]}
    assert not verify_original(changed, factored)["accepted"]
    assert not verify_original({**original, "inputs": ["z", "y", "x"]}, factored)["accepted"]


def test_original_output_order_and_unused_work_are_preserved():
    b = Builder(["x", "y"])
    x, y = b.input("x"), b.input("y")
    dead = b.mul(x, y)
    for _ in range(10):
        dead = b.mul(dead, dead)
    source = b.finish([x, y])
    assert len(polynomial_forms(source)) == 2
    compiled = compile_program(source)
    assert compiled.add_calls == compiled.mul_calls == 0
    assert compiled.run([(3, 8)]) == [(3, 8)]
    assert not verify_original(source, {**source, "outputs": [y, x]})["accepted"]


@pytest.mark.parametrize("method", ["CSE", "FACTOR_CSE", "FACTOR_TERMS_CSE", "HORNER_CSE"])
def test_mature_cas_preserves_full_function_and_multiple_outputs(method):
    original, _ = examples()
    original = {**original, "outputs": original["outputs"] * 2}
    candidate = sympy_transform(original, method)
    assert verify_original(original, candidate)["accepted"]
    assert compile_program(candidate).run([(5, -3, 12)]) == [(45, 45)]


def test_exact_integer_domain_and_public_schema_fail_closed():
    original, _ = examples()
    with pytest.raises(ProgramError, match="schema"):
        validate({**original, "oracle": "hidden"})
    with pytest.raises(ProgramError, match="semantics"):
        validate({**original, "semantics": "float64"})
    with pytest.raises(ProgramError, match="reference"):
        validate({**original, "nodes": [["add", 1, 1]]})
    with pytest.raises(ProgramError):
        validate({**original, "nodes": [["const", True]], "outputs": [0]})
    with pytest.raises(ProgramError, match="tuple"):
        compile_program(original).run([(1, 2, 0.5)])


def test_cas_generated_symbols_cannot_capture_public_names():
    b = Builder(["_generated0", "x"])
    x, y = b.input("_generated0"), b.input("x")
    term = b.add(x, y)
    original = b.finish([b.mul(term, term), b.add(term, x)])
    candidate = sympy_transform(original, "FACTOR_CSE")
    assert verify_original(original, candidate)["accepted"]
    assert compile_program(candidate).run([(2, 5)]) == [(49, 9)]
