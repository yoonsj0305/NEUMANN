"""Finite semantic/interface regressions; no fixture is capability evidence."""
from collections import Counter
import importlib.util
import pathlib
import time

import pytest

from neumann1.q6.joint_transport import (Expression, _products, joint_transport,
                                         relational_bindings, typed_bindings)
from neumann1.q6.transport import Kernel, LIB, substitute
from neumann1 import invention_core as ic

SPEC = importlib.util.spec_from_file_location(
    "q6_joint_reference", pathlib.Path(__file__).resolve().parents[2] / "research/q6/reference.py")
REF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REF)


def expression(ast, states):
    return Expression(ast, tuple(REF.execute(("ast", ast), s) for s in states))


def test_joint_relation_finds_two_compound_roles_and_one_role_ablation_cannot():
    states = [(-3, 2), (3, -4), (-2, -3), (1, -2), (-5, -1), (4, 2)]
    pts = [(j, 0, s, s[0] ** 2 < s[1] ** 2) for j, s in enumerate(states)]
    asts = [("v", 0), ("v", 1), ("mul", ("v", 0), ("v", 0)),
            ("mul", ("v", 1), ("v", 1))]
    pools = {"I": [expression(a, states) for a in asts], "B": [], "L": []}
    k = Kernel("synthetic-only", (), ("lt", ("v", 0), ("v", 1)), ("I", "I"), "B")
    matches = [b for b in relational_bindings(k, pools, pts, time.process_time() + 2, Counter()) if b]
    assert matches and all(sum(a[0] not in ("v", "k") for a in b.values()) == 2 for b in matches)
    limited = [b for b in relational_bindings(k, pools, pts, time.process_time() + 2,
                                            Counter(), max_compound=1) if b]
    assert not limited
    for bindings in matches:
        body = substitute(k.ast, 2, 2, bindings)
        assert all(REF.execute(("ast", body), s) == g for _, _, s, g in pts)


def test_relational_join_covers_same_finite_assignments_as_full_typed_composition():
    states = [(-3, 2), (3, -4), (-2, -3), (1, -2)]
    pts = [(j, 0, s, s[0] ** 2 + s[1] ** 2) for j, s in enumerate(states)]
    asts = [("v", 0), ("v", 1), ("mul", ("v", 0), ("v", 0)),
            ("mul", ("v", 1), ("v", 1))]
    pools = {"I": [expression(a, states) for a in asts], "B": [], "L": []}
    k = Kernel("synthetic-only", (), ("add", ("v", 0), ("v", 1)), ("I", "I"), "I")
    key = lambda b: tuple(sorted(b.items()))
    joint = {key(b) for b in relational_bindings(k, pools, pts, time.process_time() + 2, Counter()) if b}
    typed = set()
    for b in typed_bindings(k, pools, pts, time.process_time() + 2, Counter()):
        if b:
            body = substitute(k.ast, 2, 2, b)
            if all(REF.execute(("ast", body), s) == g for _, _, s, g in pts):
                typed.add(key(b))
    assert joint == typed and joint


def test_joint_domain_has_no_small_integer_window_and_preserves_repeated_role():
    states = [(10 ** 10,), (10 ** 10 + 3,)]
    ast = ("add", ("v", 0), ("k", 100))
    pools = {"I": [expression(ast, states)], "B": [], "L": []}
    k = Kernel("synthetic-only", (), ("add", ("v", 0), ("v", 0)), ("I",), "I")
    pts = [(j, 0, s, 2 * (s[0] + 100)) for j, s in enumerate(states)]
    matches = [b for b in relational_bindings(k, pools, pts, time.process_time() + 2, Counter()) if b]
    assert matches == [{0: ast}]


def test_undefined_source_preimage_is_not_a_match():
    states = [(0,), (1,)]
    pool = {"I": [], "B": [], "L": [Expression(("nil",), ((), ()))]}
    k = Kernel("synthetic-only", (), ("head", ("v", 0)), ("L",), "I")
    pts = [(j, 0, s, 0) for j, s in enumerate(states)]
    assert not any(relational_bindings(k, pool, pts, time.process_time() + 2, Counter()))


def test_product_order_and_empty_domain():
    a = Expression(("v", 0), (1,))
    b = Expression(("add", ("v", 0), ("k", 1)), (2,))
    rows = list(_products([[a, b], [a, b]]))
    assert len(rows) == 4
    assert [sum(ic.size(e.ast) for e in r) for r in rows] == [2, 4, 4, 6]
    assert list(_products([[]])) == []


def test_joint_inference_refuses_hidden_receiver_test():
    with pytest.raises(ValueError, match="hidden TEST"):
        joint_transport({"test": ["secret"]}, {}, cap_s=0)


def test_joint_zero_budget_is_unknown_with_explicit_cost():
    task = {"in_types": ["I"], "out_type": "I", "train": [((1,), 2)], "test": ()}
    r = joint_transport(task, {"kernels": [], "methods": []}, cap_s=0)
    assert r["verification_status"] == "UNKNOWN"
    c = r["measured_cost"]
    assert sum(c["phase_cpu_seconds"].values()) == pytest.approx(c["total_cpu_seconds"])
    assert c["energy_joules"] is None
