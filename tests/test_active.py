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
