"""Active structural discovery (development; SOURCE only).  Nothing here names a problem family.

An agent gets an initial observation (input-output examples) and an environment it may query a few times.
It never sees the hidden program, internal states or test inputs.

Arms (same initial observation, same query budget, same CPU cap):
  A   passive: the strongest passive core (`discovery_core.solve` with the latent configuration R2)
  B   A + random queries (the agent's own generic input sampler), answers used as extra examples
  C   A + uncertainty-driven queries: a committee of passive hypotheses; query the generic or edited inputs on
      which the committee disagrees most; answers used as extra examples.  No state formation.
  Dq  the queries of D, answers used as extra examples, solved passively (D without state formation)
  D   C's fallback + STATE FORMATION BY INTERVENTION: two generic structural hypotheses about a hidden state,
        prefix   the answer on x is a state built left to right:  s_{i+1} = g(s_i, x_i)
        suffix   built right to left:                             s_i = g(x_i, s_{i+1})
      The hidden states are not given.  The agent makes them observable by querying the answer on prefixes /
      suffixes of an observed input (interventions on the input), refutes a hypothesis when two equal
      (state, element) pairs lead to different states, synthesises the step g under per-transition
      supervision, verifies the fold on every initial example, and uses later queries as counterexamples.
  E   D + a discovery policy learned on other tasks: which hypothesis to test first and how to split the
      queries, and the generative order of step programs.
"""
from __future__ import annotations
import random, time
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc, latent as lt

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
INV = None


def _inv():
    global INV
    if INV is None:
        INV = sc.load_inverses()
        dc.LATENT_CFG.setdefault("R2", lt.Cfg(subst=True, latent=True))
    return INV


def _type(v):
    return T_B if isinstance(v, bool) else T_I if isinstance(v, int) else T_L


def task_of(examples):
    out_t = _type(examples[0][1])
    return {"id": "t", "in_types": [T_L], "out_type": out_t, "train": list(examples), "test": []}


def passive(examples, cap, cost=None):
    """Returns (predict, row) from the passive core; predict(inputs) -> output or None."""
    t = task_of(examples)
    pol = dc.Policy()
    r = dc.solve(t, cap, pol, _inv(), cells="R2")
    sol = r.get("sol")
    if sol is None:
        return None, r
    lib = ic.base_library()

    def predict(inp):
        try:
            return dc._run(sol, lib, inp, t["train"], t["in_types"], t)
        except Exception:
            return None
    return predict, r


# ------------------------------------------------------------------ queries
def generic_input(rng):
    return tuple(rng.randrange(0, 17) for _ in range(rng.randrange(0, 10)))


def edits(x, rng):
    """Generic edits of an observed input (no task knowledge)."""
    out = []
    x = list(x)
    if x:
        i = rng.randrange(len(x))
        y = list(x); y[i] = rng.randrange(0, 17); out.append(y)
        out.append(x[:i] + x[i + 1:])
        out.append(x[:i] + [x[i]] + x[i:])
        out.append(x[::-1])
        out.append(sorted(x))
    out.append(x + [rng.randrange(0, 17)])
    return [tuple(v) for v in out]


def ask(env, x, obs):
    y = env.query(x)
    if y is not None:
        obs.append(((tuple(x),), y))
    return y


def random_queries(env, rng, budget):
    obs = []
    for _ in range(budget):
        ask(env, generic_input(rng), obs)
    return obs


def committee_queries(env, examples, rng, budget, deadline):
    """Uncertainty sampling: candidate inputs on which the passive hypotheses disagree most."""
    members = []
    share = max(0.2, (deadline - time.process_time()) / 3)
    for cfg in ("R2", False, "rel0"):
        t = task_of(examples)
        r = dc.solve(t, share, dc.Policy(), _inv(), cells=cfg)
        if r.get("sol") is not None:
            sol, lib = r["sol"], ic.base_library()
            members.append(lambda inp, sol=sol, t=t: _safe(lambda: dc._run(sol, lib, inp, t["train"], t["in_types"], t)))
    seen = {e[0][0] for e in examples}
    pool = [generic_input(rng) for _ in range(40)]
    for (x,), _ in examples:
        pool += edits(x, rng)
    pool = [p for p in dict.fromkeys(pool) if p not in seen]

    def score(x):
        preds = {repr(m((x,))) for m in members}
        novelty = len(x) not in {len(e[0][0]) for e in examples}
        return (len(preds), novelty, len(set(x)))
    obs = []
    for _ in range(budget):
        if not pool:
            break
        best = max(pool, key=score)
        pool.remove(best)
        ask(env, best, obs)
    return obs


def _safe(f):
    try:
        return f()
    except Exception:
        return None


# ------------------------------------------------------- state formation (D)
def _init_guess(kind, x0, s1_type):
    return x0 if s1_type == T_I else (x0,) if s1_type == T_L else None


class Trajectory:
    """Observed states of one input under one structural hypothesis."""

    def __init__(self, kind, x, final):
        self.kind, self.x, self.states = kind, tuple(x), {}
        n = len(self.x)
        self.states[n if kind == "prefix" else 0] = final

    def next_index(self):
        n = len(self.x)
        order = range(0, n) if self.kind == "prefix" else range(n, 0, -1)
        for i in order:
            if i not in self.states:
                return i
        return None

    def part(self, i):
        return self.x[:i] if self.kind == "prefix" else self.x[i:]

    def transitions(self):
        n, out = len(self.x), []
        for i in range(n):
            if self.kind == "prefix" and i in self.states and i + 1 in self.states \
                    and self.states[i] is not None and self.states[i + 1] is not None:
                out.append(((self.states[i], self.x[i]), self.states[i + 1]))
            if self.kind == "suffix" and i in self.states and i + 1 in self.states \
                    and self.states[i] is not None and self.states[i + 1] is not None:
                out.append(((self.x[i], self.states[i + 1]), self.states[i]))
        return out


def consistent(trans):
    seen = {}
    for k, v in trans:
        if k in seen and seen[k] != v:
            return False
        seen[k] = v
    return True


def fold(kind, g, s0, x, s_type):
    """Run the hypothesised state machine.  s0: state of the empty input, or None (first element as state)."""
    xs = list(x)
    if kind == "prefix":
        if s0 is None:
            if not xs:
                return None
            s = _init_guess(kind, xs[0], s_type)
            xs = xs[1:]
        else:
            s = s0
        for e in xs:
            s = g((s, e))
            if s is None:
                return None
        return s
    if s0 is None:
        if not xs:
            return None
        s = _init_guess(kind, xs[-1], s_type)
        xs = xs[:-1]
    else:
        s = s0
    for e in reversed(xs):
        s = g((e, s))
        if s is None:
            return None
    return s


def synth_step(kind, trans, s_type, cap, cost=None):
    if not trans:
        return None, None
    ex = [((a, b), out) for (a, b), out in trans]
    in_types = [s_type, T_I] if kind == "prefix" else [T_I, s_type]
    t = {"id": "step", "in_types": in_types, "out_type": s_type, "train": ex, "test": []}
    pol = dc.Policy(costs={("direct", ic.sig_key(t)): cost} if cost else None)
    r = dc.solve(t, cap, pol, _inv(), cells="R2")
    sol = r.get("sol")
    if sol is None:
        return None, None
    lib = ic.base_library()

    def g(args):
        return _safe(lambda: dc._run(sol, lib, tuple(args), t["train"], t["in_types"], t))
    return g, r["program"]


def form_state(env, examples, budget, deadline, order=("prefix", "suffix"), split=None, cost=None, log=None):
    """Returns (predict or None, observations, record)."""
    obs, rec = [], {"hypotheses": {}, "queries": 0}
    x_star = max((e[0][0] for e in examples), key=len)
    final = next(y for (x,), y in examples if x == x_star)
    if len(x_star) < 2:
        return None, obs, rec
    s_type = _type(final)
    trajs = {k: Trajectory(k, x_star, final) for k in order}
    alive = {k: True for k in order}
    split = split or {k: budget // len(order) for k in order}
    used = {k: 0 for k in order}
    s0 = {}

    def query(kind):
        tr = trajs[kind]
        i = tr.next_index()
        if i is None:
            return False
        y = ask(env, tr.part(i), obs)
        rec["queries"] += 1
        used[kind] += 1
        tr.states[i] = y
        if len(tr.part(i)) == 0:
            s0[kind] = y
        if not consistent(tr.transitions()):
            alive[kind] = False
        return True

    def attempt(kind):
        tr = trajs[kind]
        trans = tr.transitions()
        if len(trans) < 2 or not alive[kind]:
            return None
        g, prog = synth_step(kind, trans, s_type, max(0.2, min(1.2, deadline - time.process_time())), cost)
        if g is None:
            return None
        z = s0.get(kind)

        def predict(inp, g=g, z=z, kind=kind):
            return fold(kind, g, z, inp[0], s_type)
        ok = all(predict(i) == o for i, o in list(examples) + obs)
        rec["hypotheses"][kind] = {"program": prog, "transitions": len(trans), "verified": ok}
        return predict if ok else None
    # interleave by the split, test after each round, and use left-over queries as counterexamples
    rounds = 0
    while env.used < env.budget and time.process_time() < deadline:
        progressed = False
        for k in order:
            if alive[k] and used[k] < split[k] and env.used < env.budget:
                progressed |= query(k)
        rounds += 1
        for k in order:
            if alive[k] and time.process_time() < deadline:
                p = attempt(k)
                if p is not None:
                    while env.used < env.budget and trajs[k].next_index() is not None:
                        before = list(obs)
                        query(k)
                        if obs != before and p(obs[-1][0]) != obs[-1][1]:
                            p = attempt(k)               # counterexample: re-synthesise
                            if p is None:
                                break
                    if p is not None:
                        rec["formed"] = k
                        return p, obs, rec
        if not progressed:
            if all(used[k] >= split[k] for k in order):
                for k in order:
                    split[k] = budget
            else:
                break
    return None, obs, rec


# -------------------------------------------------------------------- arms
def run_arm(arm, env, cap, seed=0, policy=None):
    """Returns a row: predict + cost record."""
    rng = random.Random(seed)
    c0 = time.process_time()
    deadline = c0 + cap
    ex = env.initial()
    rec = {"arm": arm}
    if arm == "A":
        pred, r = passive(ex, cap)
    elif arm == "B":
        obs = random_queries(env, rng, env.budget)
        pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    elif arm == "C":
        obs = committee_queries(env, ex, rng, env.budget, c0 + 0.4 * cap)
        pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    else:
        order, split, cost = ("prefix", "suffix"), None, None
        if arm == "E" and policy:
            order, split, cost = policy["order"], dict(policy["split"]), policy.get("cost")
        p, obs, frec = form_state(env, ex, env.budget, c0 + 0.6 * cap, order, split, cost)
        rec["formation"] = frec
        if arm == "Dq":
            pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
        elif p is not None:
            pred, r = p, {"via": "state:" + frec.get("formed", "?"), "program": frec["hypotheses"][frec["formed"]]["program"]}
        else:
            rest = env.budget - env.used
            if rest > 0:
                obs += committee_queries(env, ex + obs, rng, rest, time.process_time() + 0.3 * (deadline - time.process_time()))
            pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    rec.update({"via": r.get("via") if r else None, "program": r.get("program") if r else None,
                "fit": pred is not None, "queries": env.used, "cpu_seconds": round(time.process_time() - c0, 4)})
    return pred, rec
