"""Active structural discovery: the environment exposes nothing but answers, queries are charged, Dq replays
D's queries exactly, an unchallenged machine is not adopted, and a hidden-state task is solved by formation."""
import sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
from neumann1 import active as ac

TS = {t.name: t for t in E.tasks()}


def test_environment_charges_queries_and_blocks_hidden_test_inputs():
    env = E.Env(TS["max"], 0, budget=3)
    assert len(env.initial()) == 8 and not hasattr(env, "spec")
    assert env.query(env._test[0]) is None and env.used == 1            # a hidden test input is blocked, charged
    assert env.query((1, 5, 2)) == 5 and env.query(()) is None          # invalid input charged
    assert env.query((3,)) is None and env.used == 3                    # budget exhausted


def test_dq_replays_exactly_the_queries_of_d():
    env_d = E.Env(TS["count-k(k=2)"], 0, budget=60)
    _, rd = ac.run_arm("D", env_d, 20.0)
    env_q = E.Env(TS["count-k(k=2)"], 0, budget=60)
    _, rq = ac.run_arm("Dq", env_q, 20.0, replay=rd["query_inputs"])
    assert env_d.log == env_q.log and rd["queries"] == rq["queries"]


def test_state_machine_is_formed_challenged_and_solves_a_hidden_state_task():
    env = E.Env(TS["count-k(k=2)"], 0, budget=60)
    pred, rec = ac.run_arm("D", env, 20.0)
    f = rec["formation"]
    assert f.get("formed") and f["machines"][-1]["challenge"] is True and env._score(pred)


def test_no_queries_left_means_no_adoption():
    env = E.Env(TS["count-k(k=2)"], 0, budget=60)
    env.used = env.budget
    assert ac.challenge(env, lambda x: 0, env.initial(), [], __import__("random").Random(0)) is None


def test_learned_policy_gate_and_allotment_are_obeyed():
    pol = {"directions": ("prefix", "suffix"), "continuation_kinds": [], "structures": {},
           "formation": {"skip": True, "max_queries": None, "max_cpu": None}}
    env = E.Env(TS["count-k(k=2)"], 0, budget=60)
    _, rec = ac.run_arm("E", env, 20.0, policy={"global": pol, "by_feature": {}})
    assert rec["formation"].get("skipped_by_policy") and rec["formation"]["machines"] == []
    pol["formation"] = {"skip": False, "max_queries": 5, "max_cpu": None}
    env = E.Env(TS["count-k(k=2)"], 0, budget=60)
    _, rec = ac.run_arm("E", env, 20.0, policy={"global": pol, "by_feature": {}})
    assert all(m["queries_used"] <= 5 for m in rec["formation"]["machines"])


def test_formation_handles_a_huge_value_range():
    class Env:                                   # F9: values near -1e16 once exhausted memory
        budget, used, log = 60, 0, []

        def query(self, x):
            self.used += 1
            y = min(x) if x else None
            self.log.append((tuple(x), y))
            return y
    ex = [((x,), min(x)) for x in [(2, -9999999999999999, 4), (1000000, 3), (5, 7, 1), (9, 9)]]
    pred, _, rec = ac.form_machine(Env(), ex, __import__("time").process_time() + 10, 40)
    assert pred is not None and pred(((4, -10 ** 17, 8),)) == -10 ** 17


def test_goal_directed_update_synthesizes_an_unseen_residual_relation():
    """A held-out state/element pair must satisfy an invented Update, not a lookup table."""
    import time
    from neumann1 import invention_core as ic
    pairs = [(0, 0), (0, 1), (2, 0), (2, 2), (3, -1), (3, 2), (7, 1), (7, -1)]
    rows = [((s, e), s + 2 * e) for s, e in pairs]
    g, ast = ac.synth_goal_update(
        (ic.T_I, ic.T_I), ic.T_I, rows, time.process_time() + 8)
    assert g is not None and ast is not None
    assert all(g(inputs) == expected for inputs, expected in rows)
    assert g((12, -3)) == 6
    assert g((-4, 5)) == 6


def test_list_update_delta_synthesizes_append_and_prepend():
    """One-element structural deltas become executable list Update programs."""
    import time
    from neumann1 import invention_core as ic

    cases = [((), 2), ((3,), 1), ((3, 2), -1), ((), -3),
             ((2, 4, 6), 5), ((0, 0), 0), ((9, 8), 7)]
    for mode in ("append", "prepend"):
        rows = []
        for old, e in cases:
            goal = old + (2 * e,) if mode == "append" else (2 * e,) + old
            rows.append(((old, e), goal))
        g, ast = ac.synth_list_delta_update(
            (ic.T_L, ic.T_I), rows, time.process_time() + 8)
        assert g is not None and ast is not None
        assert all(g(inp) == goal for inp, goal in rows)
        if mode == "append":
            assert g(((7, 9), 4)) == (7, 9, 8)
        else:
            assert g(((7, 9), 4)) == (8, 7, 9)


def test_opt_in_first_update_snapshot_matches_observed_transition_hash():
    """A main-loop Update snapshot is replayable and contains SOURCE-only rows."""
    import hashlib
    import json
    old = ac.CAPTURE_UPDATE_TRANSITIONS
    ac.CAPTURE_UPDATE_TRANSITIONS = True
    try:
        env = E.Env(TS["count-k(k=2)"], 0, budget=60)
        _, rec = ac.run_arm("D", env, 10.0, seed=0)
    finally:
        ac.CAPTURE_UPDATE_TRANSITIONS = old
    machines = (rec.get("formation") or {}).get("machines", [])
    snapshots = [m["first_update_input"] for m in machines if "first_update_input" in m]
    assert snapshots
    snap = snapshots[0]
    expected = hashlib.sha256(json.dumps(
        {k: v for k, v in snap.items() if k != "sha256"},
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert snap["sha256"] == expected
    assert snap["transitions"]
    assert all(len(r["state"]) + 1 == len(snap["in_types"]) for r in snap["transitions"])
