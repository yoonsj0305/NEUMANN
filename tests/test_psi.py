"""Predictive State Invention (neumann1/psi.py): distinctions from the same future, executable latent selection."""
import sys
import time

sys.path.insert(0, ".")
from neumann1 import active as ac, psi as P


def _positions(u):
    return tuple(i for i, x in enumerate(u) if x != 0)


def _fold(g, z):
    def h(u):
        s = z
        for x in u:
            s = g(s, x)
        return s
    return h


def test_psi_is_opt_in():
    assert ac.PSI is False and ac.PSI_ABLATE is False and ac.PSI_POLICY is None


def test_distinctions_come_from_the_same_future_and_select_the_executable_counter():
    """positions(u) merges prefixes that differ only by trailing zeros; the same suffix (5,) answers differently,
    which refutes 'last element' and 'parity of the length' and leaves the length counter."""
    prefixes = [(), (0,), (0, 0, 0), (3,), (3, 0)]
    hyps = {"len": (_fold(lambda h, x: h + 1, 0), 9), "last": (_fold(lambda h, x: x, -1), 2),
            "parity": (_fold(lambda h, x: 1 - h, 0), 8)}
    cands = [{"show": k, "size": sz, "hv": {u: f(u) for u in prefixes}} for k, (f, sz) in hyps.items()]
    pairs = P.merged_pairs(prefixes, _positions)
    assert ((), (0,)) in pairs and ((0,), (0, 0, 0)) in pairs
    asked = []

    def query(x):
        asked.append(x)
        return _positions(x)
    evid, equal, info = P.discover_distinctions(pairs, cands, [(5,)], lambda u, w: tuple(u) + tuple(w), query,
                                                lambda x: False, 10, time.process_time() + 5)
    assert info["queries"] <= 10 and evid
    for u, v, w, yu, yv in evid:
        assert _positions(u) == _positions(v) and yu != yv and yu == _positions(u + w)
    trans = [(_positions(u), x, _positions(u + (x,)), u) for u in prefixes for x in (0, 5)]
    ranked, iinfo = P.invent_state([(u, v) for u, v, _, _, _ in evid], equal, cands, trans)
    assert ranked and ranked[0]["vars"][0]["show"] == "len"
    assert all(it["vars"][0]["show"] != "last" for it in ranked)


def test_policy_learning_prefers_features_of_verified_latents():
    data = [({"bias": 1.0, "keeps_h": 1.0}, 1), ({"bias": 1.0, "keeps_h": 0.0}, 0)] * 5
    w = P.update_discovery_policy(data)
    assert P.score(w, {"bias": 1.0, "keeps_h": 1.0}) > P.score(w, {"bias": 1.0, "keeps_h": 0.0})


def test_psi_cpu_allowance_is_a_fraction_of_the_formation_span():
    assert 0.0 < ac.PSI_CPU_FRAC < 1.0 and ac.PSI_SYNTH_SHARE <= 1.0


def test_fst_family_names_rebuild_the_same_task():
    sys.path.insert(0, "research/q3")
    import psi_fst_family as F
    import random
    for s in F.generate("test-seed", 12):
        t = F.parse(s.name)
        assert t.name == s.name
        rng = random.Random(5)
        for _ in range(20):
            x = s.sample(rng)
            assert t.run(x) == s.run(x)
    s = F.FSTSpec(2, "eq", 3, "count", "state")
    assert s.run((3, 1, 3, 3)) == (1, 1, 0, 1)
