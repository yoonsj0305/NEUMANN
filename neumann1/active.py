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
    lib = _lib()

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
            sol, lib = r["sol"], _lib()
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
def _lib():
    from neumann1 import opgen
    return ic.library_from_spec(opgen.seed_spec())


def _inits(s_type, x0):
    """Initial-state candidates: identity elements of the state's type, or the first element as the state.
    Generic by type; the fold verification on every initial example decides among them."""
    if s_type == T_I:
        return [0, 1, ("unit",)]
    if s_type == T_L:
        return [(), ("unit",)]
    return [False, True]


def fold(kind, g, s0, x, s_type):
    xs = list(x) if kind == "prefix" else list(x)[::-1]
    if isinstance(s0, tuple) and s0 == ("unit",):
        if not xs:
            return None
        s = xs[0] if s_type == T_I else (xs[0],)
        xs = xs[1:]
    else:
        s = s0
    for e in xs:
        s = g((s, e)) if kind == "prefix" else g((e, s))
        if s is None:
            return None
    return s


def consistent(trans):
    seen = {}
    for k, v in trans:
        if k in seen and seen[k] != v:
            return False
        seen[k] = v
    return True


def synth_step(kind, trans, s_type, deadline, checks, prior=None):
    """Step functions consistent with the observed transitions, enumerated in cost order; the first whose fold
    reproduces every check (initial examples and queried states) from some typed initial state is returned.
    For list states the cell construction (`latent`, R2) is tried first: it reaches insertion-like steps."""
    if len(trans) < 2:
        return None
    lib = _lib()
    in_types = (s_type, T_I) if kind == "prefix" else (T_I, s_type)
    target = tuple(v for _, v in trans)
    inputs = [k for k, _ in trans]

    def verify(g):
        for z in _inits(s_type, None):
            if all(fold(kind, g, z, x[0], s_type) == y for x, y in checks):
                return z
        return None

    def as_g(ast):
        fn = ic.compile_ast(ic._tup(ast), 2, lib)

        def g(args):
            try:
                v = fn(tuple(args))
            except (ic.Fail, RecursionError, TypeError):
                return None
            return v if _type(v) == s_type else None
        return g
    if s_type == T_L:
        t = {"id": "step", "in_types": list(in_types), "out_type": T_L,
             "train": [(k, v) for k, v in trans], "test": []}
        end = time.process_time() + 0.5 * max(0.0, deadline - time.process_time())
        sol = lt.solve(t, end, _inv(), lt.Cfg(subst=True, latent=True))
        if sol is not None:
            def g(args, sol=sol, t=t):
                return _safe(lambda: lt.run(sol, lt.library(lt.Cfg(subst=True)), tuple(args), t)) \
                    if sol[0] in ("lat", "residual", "transport", "keep") else None
            z = verify(g)
            if z is not None:
                return g, lt.show(sol), z, None
    found = []
    k = len(target)
    # probe pairs refine observational equivalence: with only the observed transitions as inputs, a rejected
    # candidate would hide every other program with the same values there (including the right one)
    states = list(dict.fromkeys(v for _, v in trans))
    elems = list(dict.fromkeys(e for (a, b) in inputs for e in ((b,) if kind == "prefix" else (a,))))
    for x, _ in checks[:4]:
        elems += [e for e in x[0] if e not in elems]
    probes = []
    for st in states[:6]:
        for el in elems[:6]:
            pr = (st, el) if kind == "prefix" else (el, st)
            if pr not in inputs and pr not in probes:
                probes.append(pr)
    inputs = inputs + probes[:30]

    def offer(e, t):
        if e.vec[:k] == target:
            g = as_g(e.ast())
            z = verify(g)
            if z is not None:
                found.append((g, ic.show(e.ast()), z, e.ast()))
                raise sc.Done(None, None)
    srch = dc.FSearch(lib, in_types, inputs, deadline, (), ic.uniform_costs(), (s_type,), offer)
    if prior:
        srch.cost = ic._as_cost(prior)
    srch.run()
    return found[0] if found else None


class Plan:
    """Per hypothesis: per-example trajectories grown from the KNOWN final state inwards, round-robin over the
    initial examples (longest first), so every query adds one transition."""

    def __init__(self, kind, examples):
        self.kind = kind
        self.traj = []
        for (x,), y in sorted(examples, key=lambda e: -len(e[0][0])):
            if len(x) >= 1:
                n = len(x)
                self.traj.append({"x": tuple(x), "states": {n if kind == "prefix" else 0: y}})
        self.rr = 0

    def next_query(self):
        for _ in range(len(self.traj)):
            tr = self.traj[self.rr % len(self.traj)]
            self.rr += 1
            n, st = len(tr["x"]), tr["states"]
            idx = range(n - 1, -1, -1) if self.kind == "prefix" else range(1, n + 1)
            for i in idx:
                if i not in st:
                    return tr, i
        return None

    def part(self, tr, i):
        return tr["x"][:i] if self.kind == "prefix" else tr["x"][i:]

    def transitions(self):
        out = []
        for tr in self.traj:
            x, st = tr["x"], tr["states"]
            for i in range(len(x)):
                a, b = st.get(i), st.get(i + 1)
                if a is None or b is None:
                    continue
                out.append(((a, x[i]), b) if self.kind == "prefix" else ((x[i], b), a))
        return out


RESERVE = 2      # queries kept to test a formed state machine on fresh, non-intervened inputs


def form_state(env, examples, budget, deadline, order=("prefix", "suffix"), split=None, prior=None, rng=None):
    """Returns (predict or None, observations, record)."""
    rng = rng or random.Random(0)
    obs, rec = [], {"hypotheses": {}, "queries": 0, "validation": []}
    limit = env.budget - RESERVE
    s_type = _type(examples[0][1])
    plans = {k: Plan(k, examples) for k in order}
    alive = {k: True for k in order}
    split = dict(split or {k: 2 for k in order})       # phase 1: a few queries per hypothesis
    asked = {k: 0 for k in order}

    def query(k):
        nq = plans[k].next_query()
        if nq is None:
            return False
        tr, i = nq
        y = ask(env, plans[k].part(tr, i), obs)
        rec["queries"] += 1
        asked[k] += 1
        tr["states"][i] = y
        if not consistent(plans[k].transitions()):
            alive[k] = False
            rec["hypotheses"].setdefault(k, {})["refuted_by_intervention"] = True
        return True

    def attempt(k):
        trans = plans[k].transitions()
        checks = list(examples) + [o for o in obs]
        got = synth_step(k, trans, s_type, min(deadline, time.process_time() + 0.35 * max(0.0, deadline - time.process_time())),
                         checks, prior)
        rec["hypotheses"].setdefault(k, {}).update({"transitions": len(trans), "verified": got is not None,
                                                    "program": got[1] if got else None})
        if got is None:
            return None
        g, prog, z, ast = got
        rec["hypotheses"][k]["ast"] = ast
        return lambda inp, g=g, z=z: fold(k, g, z, inp[0], s_type)

    phase = 0
    while time.process_time() < deadline:
        for k in order:
            while alive[k] and asked[k] < split[k] and env.used < limit:
                if not query(k):
                    break
        for k in order:
            if alive[k] and time.process_time() < deadline:
                p = attempt(k)
                if p is not None:
                    # the reserved queries test the formed state machine on fresh inputs it was not built from;
                    # a mismatch is a counterexample: it joins the checks and the step is synthesised again
                    seen = {e[0][0] for e in list(examples) + obs}
                    while p is not None and env.used < env.budget:
                        x = generic_input(rng)
                        while x in seen or len(x) < 2:
                            x = generic_input(rng)
                        y = ask(env, x, obs)
                        if y is None:
                            continue
                        ok = p((x,)) == y
                        rec["validation"].append(ok)
                        if not ok:
                            p = attempt(k)
                    if p is not None and alive[k]:
                        rec["formed"] = k
                        rec["state_type"] = s_type
                        return p, obs, rec
        live = [k for k in order if alive[k]]
        if env.used >= limit or not live or phase > 3:
            break
        phase += 1
        left = limit - env.used
        for j, k in enumerate(live):                      # phase 2: spread what is left over live hypotheses
            split[k] = asked[k] + left // len(live) + (1 if j < left % len(live) else 0)
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
        order, split, prior = ("prefix", "suffix"), None, None
        if arm == "E" and policy:
            order, split, prior = policy["order"], dict(policy["split"]), policy.get("prior")
        p, obs, frec = form_state(env, ex, env.budget, c0 + 0.6 * cap, order, split, prior, rng)
        rec["formation"] = frec
        if arm == "Dq":
            pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
        elif p is not None:
            pred, r = p, {"via": "state:" + frec["formed"], "program": frec["hypotheses"][frec["formed"]]["program"]}
        else:
            rest = env.budget - env.used
            if rest > 0:
                obs += committee_queries(env, ex + obs, rng, rest, time.process_time() + 0.3 * (deadline - time.process_time()))
            pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    rec.update({"via": r.get("via") if r else None, "program": r.get("program") if r else None,
                "fit": pred is not None, "queries": env.used, "cpu_seconds": round(time.process_time() - c0, 4)})
    return pred, rec
