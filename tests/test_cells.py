"""Iteration 4: cell representations are constructed per task from observed relations, verified on TRAIN,
and removed cleanly by the switch."""
import random, sys, time
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc, cells

INV = sc.load_inverses()
RNG = random.Random(9)
XS = [tuple(RNG.randint(0, 9) for _ in range(RNG.randint(4, 8))) for _ in range(16)]


def _task(f, ins=None):
    ins = ins or [(x,) for x in XS]
    ex = [(i, f(*i)) for i in ins]
    return {"id": "t", "in_types": ["L"] * len(ins[0]), "out_type": "I" if isinstance(ex[0][1], int) else "L",
            "train": ex[:8], "test": ex[8:]}


def test_constructs_index_value_case_and_length_functions():
    lib = ic.base_library()
    for f in (lambda x: x[2:] + x[:2], lambda x: x[:-2] + (4,) + x[-2:], lambda x: tuple(v for e in x for v in (e, e))):
        t = _task(f)
        sol = cells.solve(t, time.process_time() + 10, lib)
        assert sol is not None and sol[0] == "cells"
        assert all(cells.run(sol, lib, i, t["in_types"]) == o for i, o in t["test"])
    t = _task(lambda x, y: tuple(v for p in zip(x, y) for v in p), [(x, x[::-1]) for x in XS])
    sol = cells.solve(t, time.process_time() + 10, lib)
    assert sol is not None and "copy arg1" in cells.show(sol)                    # two list arguments


def test_selection_for_scalar_output_and_no_construction_without_lists():
    lib = ic.base_library()
    t = _task(lambda x: max(x))
    sol = cells.solve(t, time.process_time() + 10, lib)
    assert sol[0] == "select" and all(cells.run(sol, lib, i, ["L"]) == o for i, o in t["test"])
    seq = {"in_types": ["I"], "out_type": "I", "train": [((n,), n * n) for n in range(14)]}
    assert cells.solve(seq, time.process_time() + 2, lib) is None


def test_switch_removes_exactly_the_construction():
    t = _task(lambda x: x[:-2] + (4,) + x[-2:])
    on = dc.solve(t, 6, dc.Policy(), INV, cells=True)
    off = dc.solve(t, 6, dc.Policy(), INV)
    assert on["solved"] and on["via"].startswith("cells:") and not off["solved"]
    assert all(h["hyp"][0] != "cells" for h in off["tried"])
