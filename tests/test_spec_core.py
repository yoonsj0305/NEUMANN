"""Specification-space core: derived inverses are reproducible; each decomposition solves what it should;
the baseline arm is the frozen enumerator; no decomposition is used when its switch is off."""
import json, pathlib, random, sys
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc

INV = sc.load_inverses()
RNG = random.Random(7)
LISTS = [tuple(RNG.randint(0, 9) for _ in range(n)) for n in (7, 9, 8, 10, 7, 9, 8, 10, 9, 7, 8, 10, 9, 8, 7, 10)]


def _task(f, xs=LISTS):
    ex = [((x,), f(x)) for x in xs]
    return {"id": "t", "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def test_derived_inverse_table_is_reproducible_and_self_generated():
    stored = json.loads(pathlib.Path(sc.INVERSES).read_text())
    assert json.loads(json.dumps(sc.derive_inverses(stored["seed"], stored["budget"]))) == stored["inverses"]
    inv = stored["inverses"]
    assert ic.show(ic._tup(inv["cons"]["alone"]["0"])) == "(head $0)"
    assert ic.show(ic._tup(inv["add"]["given"]["1"])) == "(sub $0 $1)"
    assert "mod" not in inv and "head" not in inv and "tail" not in inv       # not injective: rejected
    q = ic._tup(inv["range"]["alone"]["0"])                                   # length, invented as range^-1
    assert all(ic.run_program(q, ic.base_library(), (tuple(range(n)),)) == n for n in range(12))


def test_chain_decomposition_solves_a_positional_edit_far_beyond_forward_search():
    t = _task(lambda x: (x[2], x[1], x[0], 4) + x[4:])
    r = sc.solve(t, 4, "S", INV)
    assert r["solved"] and r["via"] in ("chain", "zmap", "zmap+split")
    assert not sc.solve(t, 4, "A", INV)["fit"]
    assert sc.solve(t, 4, "S_no_state", INV)["via"] == "chain"
    c = _task(lambda x: (18, 42, 77, 20, 36))
    assert sc.solve(c, 2, "S_no_state", INV)["solved"] and not sc.solve(c, 2, "S_no_inverse", INV)["solved"]


def test_traversal_state_gives_index_aware_step_operators():
    r = sc.solve(_task(lambda x: tuple(v * (j + 1) for j, v in enumerate(x))), 4, "S", INV)
    assert r["solved"] and r["via"] == "zmap"
    r = sc.solve(_task(lambda x: x[:-2]), 4, "S", INV)
    assert r["solved"] and r["via"] == "zfilter" and "$2" in r["program"]        # needs the remaining count
    assert not sc.solve(_task(lambda x: tuple(v * (j + 1) for j, v in enumerate(x))), 4, "S_no_state", INV)["solved"]


def test_sequence_as_self_referential_object():
    fib = [1, 1]
    while len(fib) < 20:
        fib.append(fib[-1] + fib[-2])
    fact = [1]
    for n in range(1, 20):
        fact.append(fact[-1] * n)
    for seq in (fib, fact):
        ex = [((n,), v) for n, v in enumerate(seq)]
        t = {"id": "s", "in_types": ["I"], "out_type": "I", "train": ex[:14], "test": ex[14:]}
        r = sc.solve(t, 4, "S", INV)
        assert r["solved"] and r["via"] == "rec", r
        assert not sc.solve(t, 4, "S_no_state", INV)["solved"]


def test_backward_step_with_a_derived_inverse_and_case_analysis():
    ex = [((n,), n * n * n + 3 * n + 7) for n in range(20)]
    t = {"id": "p", "in_types": ["I"], "out_type": "I", "train": ex[:14], "test": ex[14:]}
    r = sc.solve(t, 4, "S_no_state", INV)
    assert r["solved"] and r["via"] in ("inverse", "search")
    t = _task(lambda x: x[1:] if x[0] > 4 else (9,) + x)
    r = sc.solve(t, 4, "S", INV)
    assert r["fit"] and r["via"] == "split"
    assert not sc.solve(t, 4, "S_no_split", INV)["fit"]


def test_baseline_arm_is_the_frozen_enumerator():
    t = _task(lambda x: x[1:])
    a = sc.solve(t, 4, "A", INV)
    b = ic.solve(t, budget=10 ** 6)
    assert a["sol"][1] == b["ast"] and a["candidates"] == b["candidates"] and a["via"] == "search"
