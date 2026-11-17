"""Stage A: one relational procedure for lists and sequences; self sources and linked relations are switches."""
import random, sys, time
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, relcells as rc, discovery_core as dc

INV = sc.load_inverses()
LIB = ic.base_library()
RNG = random.Random(3)
XS = [tuple(RNG.randint(0, 9) for _ in range(RNG.randint(4, 8))) for _ in range(16)]


def _lt(f):
    ex = [((x,), f(x)) for x in XS]
    return {"id": "l", "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def _seq(f):
    ex = [((n,), f(n)) for n in range(20)]
    return {"id": "s", "in_types": ["I"], "out_type": "I", "train": ex[:14], "test": ex[14:]}


def _ok(t, **kw):
    sol = rc.solve(t, time.process_time() + 6, INV, LIB, **kw)
    return sol is not None and all(rc.run(sol, LIB, i, t) == o for i, o in t["test"])


def test_self_relation_reaches_divide_and_conquer_recurrences():
    t = _seq(lambda n: bin(n).count("1"))
    assert _ok(t) and not _ok(t, self_src=False, linked=False)
    assert not sc.solve(t, 6, "S", INV)["solved"]


def test_linked_and_self_relations_on_lists():
    for f in (lambda x: tuple(v + 1 for v in x[::-1]), lambda x: tuple(sum(x[:i + 1]) for i in range(len(x)))):
        t = _lt(f)
        assert _ok(t) and not _ok(t, self_src=False, linked=False)


def test_same_code_path_and_switch_in_the_pipeline():
    t = _seq(lambda n: bin(n).count("1"))
    on = dc.solve(t, 6, dc.Policy(), INV, cells="rel")
    off = dc.solve(t, 6, dc.Policy(), INV, cells="rel0")
    assert on["solved"] and "self" in on["via"] and not off["solved"]
