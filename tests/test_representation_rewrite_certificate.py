from itertools import product
import pytest

from neumann1.representation_program import Builder, compile_program, verify_original
from neumann1.representation_rewrite_certificate import check_certificate, rewrite_step


def test_composed_certificate_preserves_goal_and_rejects_forged_final_answer():
    b = Builder(["x", "y", "z"])
    x, y, z = [b.input(n) for n in b.inputs]
    inner = b.add(b.mul(x, y), b.mul(x, z))
    original = b.finish([b.add(inner, b.const(0)), y])
    first = rewrite_step(original, "FACTOR_COMMON", inner)
    final = rewrite_step(first, "ADD_ZERO", first["outputs"][0])
    certificate = {"semantics": "exact_integer", "steps": [
        {"rule": "FACTOR_COMMON", "node": inner},
        {"rule": "ADD_ZERO", "node": first["outputs"][0]}]}
    assert check_certificate(original, final, certificate)["accepted"]
    assert verify_original(original, final)["accepted"]
    rows = list(product([-4, 0, 7, 10**60], repeat=3))
    assert compile_program(final).run(rows) == [(x * (y + z), y) for x, y, z in rows]
    forged = {**final, "outputs": list(reversed(final["outputs"]))}
    assert not check_certificate(original, forged, certificate)["accepted"]
    assert not check_certificate(original, final, {**certificate, "semantics": "float64"})["accepted"]


@pytest.mark.parametrize("left_swap,right_swap", list(product([False, True], repeat=2)))
def test_all_common_factor_positions_are_universally_valid(left_swap, right_swap):
    b = Builder(["x", "y", "z"])
    x, y, z = [b.input(n) for n in b.inputs]
    left = b.mul(y, x) if left_swap else b.mul(x, y)
    right = b.mul(z, x) if right_swap else b.mul(x, z)
    original = b.finish([b.add(left, right)])
    candidate = rewrite_step(original, "FACTOR_COMMON", original["outputs"][0])
    assert verify_original(original, candidate)["accepted"]


@pytest.mark.parametrize("rule,kind", [("SWAP_ADD", "add"), ("SWAP_MUL", "mul"),
                                      ("ASSOC_ADD", "add"), ("ASSOC_MUL", "mul")])
def test_structural_ring_laws_preserve_multiple_outputs(rule, kind):
    b = Builder(["x", "y", "z"])
    x, y, z = [b.input(n) for n in b.inputs]
    goal = b.node(kind, b.node(kind, x, y), z)
    original = b.finish([goal, x])
    candidate = rewrite_step(original, rule, goal)
    assert check_certificate(original, candidate, {"semantics": "exact_integer", "steps": [{"rule": rule, "node": goal}]})["accepted"]
    assert verify_original(original, candidate)["accepted"]


def test_distribution_and_identities_preserve_unbounded_integer_semantics():
    for rule, constructor in [("DISTRIBUTE_LEFT", lambda b, x, y: b.mul(x, b.add(x, y))),
                              ("MUL_ZERO", lambda b, x, y: b.mul(x, b.const(0))),
                              ("MUL_ONE", lambda b, x, y: b.mul(b.const(1), x)),
                              ("ADD_ZERO", lambda b, x, y: b.add(b.const(0), x))]:
        b = Builder(["x", "y"])
        x, y = [b.input(n) for n in b.inputs]
        goal = constructor(b, x, y)
        original = b.finish([goal])
        candidate = rewrite_step(original, rule, goal)
        assert verify_original(original, candidate)["accepted"]


def test_incorrect_analogy_and_unregistered_executable_payload_fail_closed():
    b = Builder(["x", "y"])
    x, y = [b.input(n) for n in b.inputs]
    original = b.finish([b.add(x, y)])
    certificate = {"semantics": "exact_integer", "steps": [{"rule": "FACTOR_COMMON", "node": original["outputs"][0]}]}
    assert not check_certificate(original, original, certificate)["accepted"]
    assert not check_certificate(original, original, {**certificate, "oracle": original})["accepted"]
    assert not check_certificate(original, original, {**certificate, "steps": [{"rule": "EXEC", "node": 0}]})["accepted"]
    assert not check_certificate(original, original, {**certificate, "steps": certificate["steps"] * 33})["accepted"]
