"""Discovery core: the untrained proposer, latent features, the policy update and the memory switch."""
import random, sys
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc

INV = sc.load_inverses()
RNG = random.Random(11)
LISTS = [tuple(RNG.randint(0, 9) for _ in range(n)) for n in (7, 9, 8, 10, 7, 9, 8, 10, 9, 7, 8, 10, 9, 8, 7, 10)]


def _task(f, xs=LISTS, tid="t"):
    ex = [((x,), f(x)) for x in xs]
    return {"id": tid, "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def _row(t, r):
    return dict(r, id=t["id"], in_types=list(t["in_types"]), out_type=t["out_type"], sig=ic.sig_key(t))


def _running_max(x):
    out, m = [], -1
    for v in x:
        if v > m:
            out.append(v)
            m = v
    return tuple(out)


def test_scopes_and_remap_are_type_driven():
    assert dc.scopes(sc.Z_TYPES) == [(0,), (1,), (2,), (3,), (4,), (5,), (0, 3), (0, 4), (0, 5)]
    assert dc.scopes(("I", "L")) == [(0,), (1,)]
    f = ("foldrI", ("add", ("v", 1), ("v", 2)), ("k", 0), ("v", 0))           # sum of the scope variable
    g = dc._remap(f, (3,), 6)
    assert g == ("foldrI", ("add", ("v", 6), ("v", 7)), ("k", 0), ("v", 3))
    assert ic.run_program(g, ic.base_library(), sc.zstate((4, 5, 6, 7), 2)) == 9


def test_latent_feature_solves_what_the_full_state_search_does_not():
    t = _task(_running_max)
    lib = ic.base_library()
    st = sc.subtasks(t)[0]
    import time
    body, feat, n = dc.feature_search(lib, INV, st, sc._pick(st["points"]), (0, 3), time.process_time() + 20, (),
                                      ic.uniform_costs())
    assert body is not None and feat is not None                       # "nothing earlier is >= this element"
    assert all(sc.run_solution(("zfilter", body), lib, i, t["train"]) == o for i, o in t["test"])
    assert not sc.solve(t, 6, "S", INV)["solved"]                          # the THIRD core at the test cap
    focused = dc.Policy(weights={("zfilter", "feature", (0, 3)): 1.0})
    focused.default = 0.01
    r = dc.solve(t, 30, focused, INV)                                      # a policy that knows where to look
    assert r["solved"] and r["via"] == "zfilter+feature", r["via"]
    assert not dc.solve(t, 12, dc.Policy(), INV)["solved"]                 # the untrained policy spreads too thin


def test_without_features_and_policy_the_proposer_is_the_third_core():
    for f in (lambda x: x[:-2], lambda x: tuple(v + j for j, v in enumerate(x)), lambda x: (9,) + x[1:]):
        t = _task(f)
        a = dc.solve(t, 4, dc.Policy(), INV, features=False, replay=False)
        b = sc.solve(t, 4, "S", INV)
        assert a["solved"] and b["solved"] and a["sol"] == b["sol"]


def test_policy_is_updated_by_verified_experience_only():
    tasks = [_task(lambda x: x[:-2], tid="a"), _task(lambda x: tuple(v for j, v in enumerate(x) if j % 2 == 0), tid="b"),
             _task(_running_max, tid="c"), _task(lambda x: tuple(sorted(x)), tid="unsolved")]
    exp = [_row(t, dc.solve(t, 8, dc.Policy(), INV)) for t in tasks]
    pol = dc.fit(exp)
    assert len(pol.memory) == sum(r["fit"] for r in exp) >= 2
    assert pol.weights[("zfilter", "body", ())] > 2 * pol.weights[("zfilter", "feature", (4,))] and pol.default == 0.5
    untrained = dc.Policy()
    assert untrained.cost("body", "zfilter")["foldrL"] == 1 and untrained.weight(("zfilter", "body", ())) == 1.0
    c = pol.cost("body", "zfilter")
    assert min(c["lt"], c["eq"]) < c["isnil"] and c != dict(untrained.cost("body", "zfilter"))   # order changed
    assert all(not r["solved"] or r["fit"] for r in exp)


def test_memory_is_reverified_and_is_a_separate_switch():
    t1, t2 = _task(lambda x: x[:-2], tid="a"), _task(lambda x: x[:-2], xs=LISTS[::-1], tid="b")
    pol = dc.fit([_row(t1, dc.solve(t1, 4, dc.Policy(), INV))])
    assert dc.solve(t2, 4, dc.Policy(memory=pol.memory), INV)["via"] == "memory"
    assert dc.solve(t2, 4, dc.Policy(memory=pol.memory), INV, replay=False)["via"] != "memory"
    fib = [1, 1]
    while len(fib) < 20:
        fib.append(fib[-1] + fib[-2])
    seq = {"id": "s", "in_types": ["I"], "out_type": "I", "train": [((n,), v) for n, v in enumerate(fib[:14])],
           "test": [((n,), v) for n, v in enumerate(fib)][14:]}
    wrong = dc.Policy(memory=[("rec", ("mul", ("k", 2), ("head", ("v", 1))), ("I", "L"), "I")])
    r = dc.solve(seq, 4, wrong, INV)
    assert r["via"] != "memory" and r["solved"]                              # a stored wrong recurrence is rejected
