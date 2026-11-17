"""Failure-derived operation generation: an operation is proposed from gaps, synthesised over pieces only,
identified by its behaviour on self-generated arguments, kept only with support from two tasks, and used."""
import random, sys
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, opgen, discovery_core as dc

INV = sc.load_inverses()
RNG = random.Random(5)
LISTS = [tuple(RNG.randint(0, 9) for _ in range(n)) for n in (5, 7, 6, 8, 5, 7, 6, 8, 7, 5, 6, 8, 7, 6, 5, 8)]


def _task(f, tid):
    ex = [((x,), f(x)) for x in LISTS]
    return {"id": tid, "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def test_signature_identifies_an_operation_and_rejects_trivial_definitions():
    lib = ic.library_from_spec(opgen.seed_spec())
    app = ("foldrL", ("cons", ("v", 2), ("v", 3)), ("v", 1), ("v", 0))
    a = opgen.canonical(app, ("L", "L"), lib)
    b = opgen.canonical(opgen._swap(app), ("L", "L"), lib)
    assert a is not None and a[0] == b[0]                                   # argument order does not matter
    assert opgen.canonical(("tail", ("v", 0)), ("L",), lib) is None         # a single primitive is not new
    assert opgen.canonical(("cons", ("k", 3), ("cons", ("k", 1), ("nil",))), ("L",), lib) is None   # no argument
    assert opgen.existing_signatures(lib)[a[0]] == "old_f7"                 # same behaviour as the old append
    one = opgen.canonical(("cons", ("head", ("v", 1)), ("tail", ("v", 1))), ("I", "L"), lib)
    assert one is None or one[2] == ("L",)                                  # the unused argument is dropped


def test_operations_come_from_gaps_need_two_tasks_and_are_then_used():
    tasks = [_task(lambda x: x + (7, 3, 8, 4, 3), "a"), _task(lambda x: x[::-1] + x[1:], "b"),
             _task(lambda x: tuple(sorted(x)), "c")]
    rows = []
    for t in tasks:
        ops, meta = opgen.gaps(t, INV, 6)
        assert not meta["solved"] and meta["specs"] > 0
        rows.append(dict(meta, id=t["id"], ops=ops))
    spec, table, rec = opgen.select(rows)
    assert [o["support"] for o in table] == [2] and table[0]["recoverable_arguments"] == [0, 1]
    assert opgen.select(rows, exclude={"a"})[1] == []                       # one task is not enough
    new = _task(lambda x: (11, 21) + x + (7, 89), "new")
    c = dc.solve(new, 6, dc.Policy(), INV, spec=spec, ops=rec)
    cn = dc.solve(new, 6, dc.Policy(), INV, spec=opgen.seed_spec(), ops={})
    assert c["solved"] and c["ops_used"] == ["g0"] and "g0" not in c["program"] and not cn["solved"]
