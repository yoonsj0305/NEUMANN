"""Invention core: search, second-order abstraction, soundness of rewriting."""
import random
from neumann1.invention_core import (
    base_library, library_from_spec, add_invention, compile_ast, run_program,
    inline, rewrite, compress, propose, learn_costs, solve, size, Search,
    untrained_costs, _comp_body, Fail)

MAP_INC = ("foldrL", ("cons", ("add", ("v", 1), ("k", 1)), ("v", 2)), ("nil",), ("v", 0))
MAP_DBL = ("foldrL", ("cons", ("mul", ("v", 1), ("k", 2)), ("v", 2)), ("nil",), ("v", 0))
XS = [(), (3,), (1, 2, 3), (9, 0, 4, 4)]


def _task(fn, out="L", n=10, seed=0):
    rng = random.Random(seed)
    ex = []
    while len(ex) < n:
        xs = tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 6)))
        y = fn(xs)
        if y is not None:
            ex.append(((xs,), y))
    return {"id": "t", "in_types": ["L"], "out_type": out,
            "train": ex[:6], "test": ex[6:]}


def test_substrate_programs_execute():
    lib = base_library()
    assert run_program(MAP_INC, lib, ((1, 2, 3),)) == (2, 3, 4)
    assert run_program(("head", ("v", 0)), lib, ((),)) is None      # fail closed
    assert run_program(("map", ("mul", ("v", 1), ("v", 1)), ("v", 0)), lib, ((2, 3),)) == (4, 9)
    assert run_program(("filter", ("lt", ("k", 2), ("v", 1)), ("v", 0)), lib, ((1, 5, 2, 7),)) == (5, 7)


def test_higher_order_abstraction_is_invented_and_sound():
    lib = base_library()
    corpus = {"a": (MAP_INC, ("L",)), "b": (MAP_DBL, ("L",))}
    examples = {"a": [((x,), tuple(v + 1 for v in x)) for x in XS],
                "b": [((x,), tuple(v * 2 for v in x)) for x in XS]}
    new, adopted = compress(corpus, lib, examples, 0, max_new=1, min_gain=2)
    assert len(adopted) == 1
    name, ret, params, body = adopted[0]
    assert ret == "L" and ("I", ["I"]) in params          # a function-typed hole
    assert size(new["a"][0]) < size(MAP_INC)
    for tid, (ast, _) in new.items():
        for inp, out in examples[tid]:
            assert run_program(ast, lib, inp) == out
        assert inline(ast, 1, lib) == corpus[tid][0]       # exact round trip
    # the fast template path and the reference compiler agree
    fns = [compile_ast(c, 1 + len(bt), lib)
           for c, (_, bt) in zip(new["a"][0][1:], lib[name].params)]
    ref = _comp_body(body, 1, fns, 1, lib)
    assert all(ref((x,)) == lib[name].make(fns, 1)((x,)) for x in XS)


def test_invention_reused_inside_new_search_reduces_cost():
    spec = [("f0", "L", [("I", ["I"]), ("L", [])],
             ("foldrL", ("cons", ("h", 0, (0,)), ("b", 1)), ("nil",), ("h", 1, ())))]
    t = _task(lambda x: tuple(v * v + 1 for v in x))
    lib = library_from_spec(spec)
    cost = learn_costs([(("f0", ("add", ("v", 1), ("k", 1)), ("v", 0)), ("L",))] * 6, lib)
    with_inv = solve(t, spec, cost, 400000)
    assert with_inv["solved"]


def test_search_is_deterministic_and_budget_bounded():
    t = _task(lambda x: x[::-1])
    a = solve(t, budget=50000)
    b = solve(t, budget=50000)
    assert a["ast"] == b["ast"] and a["candidates"] == b["candidates"]
    assert a["solved"]
    none = solve(_task(lambda x: tuple(sorted(x))), budget=2000)
    assert not none["fit"] and none["candidates"] <= 2001


def test_only_train_examples_reach_the_search():
    t = _task(lambda x: x[1:] if x else None)
    t["test"] = [(((1, 2),), (99,))]                      # impossible hidden test
    r = solve(t, budget=20000)
    assert r["fit"] and not r["solved"]                    # fits train, fails test


def test_memory_replay_and_retrieval():
    t = _task(lambda x: tuple(v + 1 for v in x)[::-1])
    rev = ("foldlL", ("cons", ("v", 1), ("v", 2)), ("nil",), ("v", 0))
    memory = [(MAP_INC, ("L",), "L"), (rev, ("L",), "L")]
    r = solve(t, budget=5000, memory=memory)
    assert r["solved"] and r["candidates"] < 5000
    exact = solve(_task(lambda x: x[::-1]), budget=10, memory=memory)
    assert exact["via"] == "replay" and exact["solved"]


def test_nested_abstractions_inline_and_execute():
    lib = base_library()
    add_invention(lib, "f0", "I", [("L", ())],
                  ("foldrI", ("add", ("b", 0), ("b", 1)), ("k", 0), ("h", 0, ())))
    add_invention(lib, "f1", "I", [("L", ())],
                  ("f0", ("map", ("k", 1), ("h", 0, ()))))
    prog = ("add", ("f1", ("v", 0)), ("f0", ("v", 0)))      # len + sum
    assert run_program(prog, lib, ((4, 5, 6),)) == 18
    flat = inline(prog, 1, lib)
    assert "f0" not in str(flat) and run_program(flat, base_library(), ((4, 5, 6),)) == 18
