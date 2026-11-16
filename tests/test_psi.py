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
    assert 0.0 < ac.PSI_CPU_FRAC <= 1.0 and ac.PSI_SYNTH_SHARE <= 1.0


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


# ---------------------------------------------------------------- section 40: structural state identification
from neumann1 import stateid as SI, latent as LT


def test_psi40_is_opt_in():
    assert ac.PSI40 is False and ac.PSI40_ABLATE is False and LT.LENGTH_FLOOR == 0.0


def _parity_of_big(u):
    """hidden state: parity of the number of elements >= 10 (the answer keeps x only in state 0 after reading it)"""
    s, out = 0, []
    for x in u:
        s ^= x >= 10
        if s == 0:
            out.append(x)
    return tuple(out)


def test_residual_signatures_separate_hidden_states_across_different_answers():
    prefixes = [(), (3,), (12,), (3, 12), (12, 12), (12, 5)]
    fut = {u: {(w,): _parity_of_big(u + (w,)) for w in (4, 11)} for u in prefixes}
    seps, groups, info = SI.residual_signatures(prefixes, _parity_of_big, lambda u: fut[u])
    hidden = {u: sum(x >= 10 for x in u) % 2 for u in prefixes}
    assert seps and all(hidden[u] != hidden[v] for u, v in seps)
    assert all(hidden[u] == hidden[v] for u, v in groups)
    assert info["history_dependent_suffixes"] >= 1


def test_constructed_automaton_generalises_beyond_the_observed_elements():
    prefixes = [(), (3,), (12,), (3, 12), (12, 12), (12, 5), (5, 3), (12, 3, 12)]
    seps = [(u, v) for i, u in enumerate(prefixes) for v in prefixes[i + 1:]
            if sum(x >= 10 for x in u) % 2 != sum(x >= 10 for x in v) % 2]

    def enum(alphabet, deadline, limit):
        return [(("lt", ("k", 9), ("v", 0)), lambda e: 9 < e, 3, "(lt 9 $0)"),
                (("eq", ("v", 0), ("k", 3)), lambda e: e == 3, 3, "(eq $0 3)")]
    guards = SI.guard_partitions([3, 5, 12], enum, time.process_time() + 2)
    reps, info = SI.construct_automata(seps, prefixes, lambda u: u, guards, time.process_time() + 5)
    assert info["k"] == 2 and reps
    top = [r for r in reps if r["guard"] == "(lt 9 $0)"][0]
    run = lambda u: [top["fn"]((h, x)) for h in [0] for x in []] or _fold(lambda h, x: top["fn"]((h, x)), 0)(u)
    for u in [(15, 1, 16, 0), (10,), (2, 4, 6)]:        # elements never observed
        assert run(u) == sum(x >= 10 for x in u) % 2


def test_dfa_search_reports_unrepresentable_constraints():
    words = {(): (), (0,): (0,), (0, 0): (0, 0), (0, 0, 0): (0, 0, 0)}
    seps = [((), (0,)), ((0,), (0, 0)), ((), (0, 0)), ((0, 0, 0), ()), ((0, 0, 0), (0,)), ((0, 0, 0), (0, 0))]
    assert SI.dfa_search(words, seps, 3)[0] is None
    assert SI.dfa_search(words, seps, 4)[0] is not None


def test_rank_prefers_the_value_an_update_can_use_within_one_partition_class():
    prefixes = [(), (0,), (0, 0)]
    reps = [{"values": {(): 1, (0,): 2, (0, 0): 4}, "size": 4, "show": "double"},
            {"values": {(): 0, (0,): 1, (0, 0): 2}, "size": 4, "show": "len"}]
    ranked, _ = SI.rank(reps, [((), (0,))], [], prefixes)
    assert ranked[0]["show"] == "len"


# ---------------------------------------------------------------- section 41: evidence-driven structural invention
def test_psi41_is_opt_in():
    assert ac.PSI41 is False


def test_version_space_keeps_the_larger_structure_until_evidence_removes_it():
    """count of 'big' elements mod 3: with only 0-hit / 1-hit evidence a 2-state table fits; the 3-state table stays a
    competing hypothesis, and the separation of 1 hit from 2 hits (observed later) leaves only 3-state structures"""
    seq = lambda u: u
    g = {"ast": ("lt", ("k", 9), ("v", 0)), "fn": lambda e: int(e > 9), "size": 3, "show": "(lt 9 $0)"}
    pre = [(), (12,), (3,), (12, 3)]
    seps = [((), (12,))]
    hyps, info = SI.version_space(seps, [], pre, [(12, 12), (12, 12, 12)], seq, [g], time.process_time() + 5)
    assert info["kmin"] == 2 and any(h["k"] == 3 for h in hyps) and any(h["k"] == 2 for h in hyps)
    seps2 = seps + [((12,), (12, 12)), ((), (12, 12))]
    left = [h for h in hyps if SI.consistent(h, seps2, [])]
    assert left and all(h["k"] == 3 for h in left)


def test_unobserved_cells_stay_unknown():
    g = {"ast": ("lt", ("k", 9), ("v", 0)), "fn": lambda e: int(e > 9), "size": 3, "show": "(lt 9 $0)"}
    a = SI.make_partial_automaton(2, g, {(0, 0): 0, (0, 1): 1})
    assert a["fn"]((0, 12)) == 1 and a["fn"]((1, 12)) is None and (1, 1) in a["unseen"]


def test_dfa_enumerate_respects_merges():
    words = {(): (), (1,): (1,), (1, 1): (1, 1)}
    tabs, _ = SI.dfa_enumerate(words, [((), (1,))], [((), (1, 1))], 2)
    assert tabs and all(t[(1, 1)] == 0 for t in tabs)


# ---------------------------------------------------------------- section 43: joint latent invention (needs z3)
def test_psi43_is_opt_in():
    assert ac.PSI43 is False and ac.PSI43_ABLATE is False


def test_joint_encoding_smoke_identity_transducer():
    """encoding check only (size 0): emitting each element is found and generalises; harder machines are a CPU
    question recorded in section 43, not a unit test"""
    import pytest
    from neumann1 import joint as J
    if J.z3 is None:
        pytest.skip("z3 not installed (optional dependency)")
    steps = [(x[:i], x[i], (x[i],)) for x in [(3, 1, 4), (1, 5, 9, 2), (6, 5, 3)] for i in range(len(x))]
    sol, info = J.synthesise_steps_by_size(steps, time.process_time() + 60, max_ops=1, size_timeout=30)
    assert sol is not None
    assert J.run_solution(sol, (9, 0, 7, 7)) == (9, 0, 7, 7)


def _diff_trace(x):
    h, out = 0, []
    for v in x:
        h2 = v - h
        out.append((v, h, h2))
        h = h2
    return out
