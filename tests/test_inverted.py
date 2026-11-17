"""Inverted inventions: recoverability is decided by self-play; an invention becomes a decomposition operator;
removing the inventions removes exactly that capability; the result is a substrate program."""
import json, random, sys
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, inverted as iv

INV = sc.load_inverses()
APPEND = ("f7", "L", [["L", []], ["L", []]], ("foldrL", ("cons", ("b", 0), ("b", 1)), ("h", 0, ()), ("h", 1, ())))
DROP = ("f1", "L", [["L", []], ["L", []]], ("foldrL", ("tail", ("b", 1)), ("h", 0, ()), ("h", 1, ())))
RNG = random.Random(5)
LISTS = [tuple(RNG.randint(0, 9) for _ in range(n)) for n in (5, 7, 6, 8, 5, 7, 6, 8, 7, 5, 6, 8, 7, 6, 5, 8)]


def _task(f):
    ex = [((x,), f(x)) for x in LISTS]
    return {"id": "t", "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def test_recoverability_is_decided_on_self_generated_data():
    ops = iv.derive_op_inverses([APPEND, DROP])
    assert ops == {"f7": [0, 1]}                         # append: both arguments; drop-n: neither
    core = json.load(open("docs/experiments/results/invention_core_frozen.json"))
    spec = [tuple(x) for x in core["spec"]]              # the operations the old core invented on SOURCE
    assert iv.derive_op_inverses(spec)["f7"] == [0, 1] and "f1" not in iv.derive_op_inverses(spec)


def test_an_inverted_invention_decomposes_goals_and_its_removal_removes_the_capability():
    ops = iv.derive_op_inverses([APPEND])
    for f in (lambda x: x + (7, 3, 8, 4, 3), lambda x: (11, 21) + x + (7, 89), lambda x: x + (len(x),)):
        t = _task(f)
        a = iv.solve(t, 4, INV, [APPEND], ops)
        assert a["solved"] and a["via"] == "inverted", (a["via"], a["program"])
        assert "f7" not in a["program"]                  # expanded to substrate primitives
        assert all(ic.run_program(a["sol"][1], ic.base_library(), i) == o for i, o in t["test"])
        assert not iv.solve(t, 4, INV, [APPEND], {})["solved"]          # same search, inventions removed
        assert not sc.solve(t, 4, "S", INV)["solved"]                   # THIRD core


def test_without_inventions_the_goal_graph_is_the_chain_of_the_third_core():
    for f in (lambda x: (x[2], x[1], x[0], 4) + x[4:], lambda x: (18, 42, 77), lambda x: x[1:]):
        t = _task(f)
        a, b = iv.solve(t, 4, INV, [], {}), sc.solve(t, 4, "S", INV)
        assert a["solved"] and b["solved"] and a["via"] in ("chain", "search", "zmap", "zfilter")
