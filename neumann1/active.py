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


OUTPUT_STATE_QUERIES = 4   # at most this many queries for the output-as-state hypotheses


def form_state(env, examples, budget, deadline, order=("prefix", "suffix"), split=None, prior=None, rng=None):
    """Returns (predict or None, observations, record)."""
    rng = rng or random.Random(0)
    obs, rec = [], {"hypotheses": {}, "queries": 0, "validation": []}
    limit = min(env.budget - RESERVE, env.used + OUTPUT_STATE_QUERIES)
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
                    stop = env.used + RESERVE
                    while p is not None and env.used < min(env.budget, stop):
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


# --------------------------------------- latent state from distinguishing experiments (Myhill-Nerode)
def experiments(examples):
    """Generic single-cell continuations w to distinguish prefixes (type- and range-based, no task knowledge):
    a value above every value seen, a value below every value seen, and the first element again."""
    vals = [v for (x,), _ in examples for v in x] or [0]
    return [("above", lambda u: (max(vals) + 1,)), ("below", lambda u: (min(min(vals) - 1, 0),)),
            ("repeat-first", lambda u: (u[0],) if u else None)]


def synth_multi(in_types, out_type, rows, deadline, check=None, prior=None):
    """Enumerate f over in_types matching rows [(inputs, output)], refine equivalence with probe inputs, accept
    the first candidate for which check(fn) holds (None = accept)."""
    lib = _lib()
    target = tuple(o for _, o in rows)
    inputs = [i for i, _ in rows]
    k = len(target)
    pool = [list(dict.fromkeys(i[j] for i in inputs)) for j in range(len(in_types))]
    probes = []
    import itertools
    for combo in itertools.product(*[p[:4] for p in pool]):
        if combo not in inputs and combo not in probes:
            probes.append(combo)
        if len(probes) >= 30:
            break
    found = []

    def offer(e, t):
        if e.vec[:k] == target:
            fn = ic.compile_ast(ic._tup(e.ast()), len(in_types), lib)

            def g(args, fn=fn):
                try:
                    v = fn(tuple(args))
                except (ic.Fail, RecursionError, TypeError):
                    return None
                return v if _type(v) == out_type else None
            if check is None or check(g):
                found.append((g, e.ast()))
                raise sc.Done(None, None)
    srch = dc.FSearch(lib, tuple(in_types), inputs + probes, deadline, (), ic.uniform_costs(), (out_type,), offer)
    if prior:
        srch.cost = ic._as_cost(prior)
    srch.run()
    return found[0] if found else (None, None)


def covers(pieces, preds, full, deadline, per_split=2):
    """Case trees over the cells, cheapest first: one piece; pred ? A : B; pred1 ? A : (pred2 ? B : C).
    Predicates are distinct cell partitions (at most 2^cells), so all of them are examined."""
    def cover_of(R, k):
        out = []
        for m, a in pieces:
            if not R & ~m:
                out.append(a)
                if len(out) >= k:
                    break
        return out
    for m, a in pieces:
        if m == full:
            yield a
    for pm, pa in preds:
        if time.process_time() > deadline:
            return
        for A in cover_of(pm & full, per_split):
            for B in cover_of(~pm & full, per_split):
                yield ("case", pa, A, B)
    firsts = [(pm, pa, cover_of(pm & full, per_split)) for pm, pa in preds]
    firsts = [f for f in firsts if f[2]]
    for pm, pa, As in firsts:
        R = ~pm & full
        for qm, qa in preds:
            if time.process_time() > deadline:
                return
            t_, f_ = qm & R, ~qm & R
            if not t_ or not f_:
                continue
            Bs = cover_of(t_, per_split)
            if not Bs:
                continue
            Cs = cover_of(f_, per_split)
            for A in As:
                for B in Bs:
                    for C in Cs:
                        yield ("case", pa, A, ("case", qa, B, C))


def synth_cover(in_types, out_type, rows, deadline, check=None):
    """Per-transition factorisation of a step: every transition is a cell; pieces are cheap programs that are
    right on some cells, predicates split the cells (the cover principle of `cells`, iteration 4).  Every
    case tree in cost order becomes an ordinary program (nested ifI) and must pass check()."""
    if out_type != T_I:
        return None, None
    lib = _lib()
    target = [o for _, o in rows]
    inputs = [i for i, _ in rows]
    full = (1 << len(rows)) - 1
    pieces, preds, seen = [], [], set()

    def offer(e, t):
        v = e.vec
        mk = sum(1 << j for j, b in enumerate(v) if (b if t == T_B else b == target[j]))
        if t == T_B:
            if 0 < mk < full and ("p", mk) not in seen:
                seen.add(("p", mk)); preds.append((mk, e.ast()))
        elif mk and ("v", mk) not in seen:
            seen.add(("v", mk)); pieces.append((mk, e.ast()))
    for c in range(10):
        offer(type("K", (), {"vec": (c,) * len(rows), "ast": lambda self, c=c: ("k", c)})(), T_I)
    srch = dc.FSearch(lib, tuple(in_types), inputs, deadline, (), ic.uniform_costs(), (T_I, T_B), offer)
    tried = set()

    def to_ast(n):
        return ("ifI", n[1], to_ast(n[2]), to_ast(n[3])) if n[0] == "case" else n
    for lvl in range(1, srch.max_level + 1):
        try:
            for t in srch.types:
                srch._pool(srch.top, t, lvl)
        except ic.Budget:
            break
        if lvl < 2:
            continue
        for node in covers(pieces, preds, full, deadline):
            ast = to_ast(node)
            if repr(ast) in tried:
                continue
            tried.add(repr(ast))
            fn = ic.compile_ast(ast, len(in_types), lib)

            def g(args, fn=fn):
                try:
                    v = fn(tuple(args))
                except (ic.Fail, RecursionError, TypeError):
                    return None
                return v if _type(v) == out_type else None
            if check is None or check(g):
                return g, ast
        if time.process_time() > deadline:
            break
    return None, None


def form_latent(env, examples, deadline, order=None, rng=None, log=None):
    """Prefix-state hypothesis with the state AUGMENTED by the answer under a distinguishing continuation w:
    state(u) = (f(u), f(u.w)).  The extra component is a hidden intermediate the data never shows; the agent
    makes it observable by its own experiment, then synthesises both component steps under per-transition
    supervision and verifies the fold on every initial example."""
    rng = rng or random.Random(0)
    rec = {"tried": []}
    obs = []
    s_type = _type(examples[0][1])
    memo = {tuple(x): y for (x,), y in examples}

    def F(u):
        u = tuple(u)
        if u in memo:
            return memo[u]
        if env.used >= env.budget - RESERVE:
            raise StopIteration
        y = ask(env, u, obs)
        memo[u] = y
        return y
    TRAJ_Q = 12                                     # queries for trajectories; the rest go to counterexamples
    exps = experiments(examples)
    if order:
        exps = sorted(exps, key=lambda e: order.index(e[0]) if e[0] in order else 99)
    # informative trajectories: fresh inputs with distinct values walked from the start, so the hidden state
    # changes often (a long observed input walked from its end mostly repeats one state)
    vals = sorted({v for (x,), _ in examples for v in x}) or list(range(10))
    lo, hi = min(vals), max(vals)
    # order-covering designs: ascending, descending and random distinct values, so that any hidden state
    # defined by order relations among the elements changes along at least one trajectory
    pool = list(range(lo, hi + 1))
    rng.shuffle(pool)
    asc = tuple(sorted(pool[:5]))
    trajs = [asc, asc[::-1], tuple(pool[5:9])]
    for name, wf in exps:
        if time.process_time() > deadline or env.used >= env.budget - RESERVE:
            break
        trans_s, trans_p, consistent_ = [], [], True
        start = env.used
        try:
            for x in trajs:
                for i in range(1, len(x)):             # from the start outwards
                    u, ue = x[:i], x[:i + 1]
                    w, we = wf(u), wf(ue)
                    if w is None or we is None:
                        continue
                    su, sue = F(u), F(ue)
                    pu, pue = F(u + w), F(ue + we)
                    if None in (su, sue, pu, pue):
                        continue
                    if env.used - start >= TRAJ_Q:
                        raise StopIteration
                    trans_s.append(((su, pu, x[i]), sue))
                    trans_p.append(((su, pu, x[i]), pue))
                    if time.process_time() > deadline:
                        break
        except StopIteration:
            pass
        info = {"experiment": name, "transitions": len(trans_s)}
        rec["tried"].append(info)
        if len(trans_s) < 3 or not consistent(trans_s) or not consistent(trans_p):
            info["consistent"] = False
            continue
        info["consistent"] = True
        x0s = [(tuple(x), y) for (x,), y in examples]
        in_t = (s_type, s_type, T_I)

        def F_w(u):
            w = wf(tuple(u))
            return F(tuple(u) + w) if w is not None else None

        def run_trace(gs, gp, z, x):
            """States of the candidate machine along x (None where undefined)."""
            s_, p_ = z
            out = []
            for e in x:
                s_, p_ = (gs((s_, p_, e)), gp((s_, p_, e))) if s_ is not None and p_ is not None else (None, None)
                out.append((s_, p_))
            return out
        def init_candidates():
            """Identity elements of the state type (both components); the fold on the examples decides."""
            base = [z for z in _inits(s_type, None) if not (isinstance(z, tuple) and z == ("unit",))]
            return [(z, zp) for z in base for zp in base]
        holder, rounds = {}, 0
        while time.process_time() < deadline and rounds < 15:
            rounds += 1
            end = min(deadline, time.process_time() + 0.3 * max(0.0, deadline - time.process_time()))
            gp, ast_p = synth_multi(in_t, s_type, trans_p, end)
            if gp is None:
                break
            gs, ast_s = synth_multi(in_t, s_type, trans_s, min(deadline, time.process_time() + 0.2))
            if gs is None:
                gs, ast_s = synth_cover(in_t, s_type, trans_s, min(deadline, time.process_time() + 0.6))
            if gs is None:
                break
            best = None
            for z in init_candidates():
                fails = [x for x, y in x0s if run_trace(gs, gp, z, x)[-1:] != [] and run_trace(gs, gp, z, x)[-1][0] != y]
                if best is None or len(fails) < len(best[1]):
                    best = (z, fails)
            z, fails = best
            info.setdefault("rounds", []).append({"answer": ic.show(ast_s), "latent": ic.show(ast_p),
                                                  "fails": len(fails), "init": repr(z), "queries": env.used})
            if not fails:
                holder.update(gs=gs, gp=gp, ast_s=ast_s, ast_p=ast_p, z=z)
                break
            # counterexample: localise, by binary search over prefix lengths, the first step where the machine
            # leaves the observed states of x; the true states on both sides of it give one new transition
            x = fails[0]
            trace = run_trace(gs, gp, z, x)
            added = False
            try:
                lo_, hi_ = 0, len(x)                      # trace agrees at lo_ (0 = initial state), differs at hi_
                while hi_ - lo_ > 1:
                    mid = (lo_ + hi_) // 2
                    true = (F(x[:mid]), F_w(x[:mid]))
                    if None in true or trace[mid - 1] == true:
                        lo_ = mid
                    else:
                        hi_ = mid
                # from just before the localised point, find the first step whose prediction from the TRUE
                # previous state is wrong (prefixes where the answer is undefined are skipped)
                for i in list(range(max(1, lo_), len(x) + 1)) + list(range(1, max(1, lo_))):
                    prev = (F(x[:i - 1]), F_w(x[:i - 1]))
                    if None in prev:
                        continue
                    true = (F(x[:i]), F_w(x[:i]))
                    if None in true:
                        continue
                    step = (gs((prev[0], prev[1], x[i - 1])), gp((prev[0], prev[1], x[i - 1])))
                    if step != true:
                        trans_s.append(((prev[0], prev[1], x[i - 1]), true[0]))
                        trans_p.append(((prev[0], prev[1], x[i - 1]), true[1]))
                        added = True
                        break
            except StopIteration:
                pass
            info.setdefault("counterexamples", 0)
            info["counterexamples"] += added
            if not added or not consistent(trans_s) or not consistent(trans_p):
                break
        info.update(step_latent=ic.show(holder["ast_p"]) if holder else None,
                    step_answer=ic.show(holder["ast_s"]) if holder else None)
        if not holder:
            continue
        gs, gp, ast_s, ast_p = holder["gs"], holder["gp"], holder["ast_s"], holder["ast_p"]
        z = holder["z"]
        rec["formed"] = name
        rec["latent"] = {"experiment": name, "step_answer": ast_s, "step_latent": ast_p, "init": list(z) if not isinstance(z[0], tuple) else None}
        def predict(inp, gs=gs, gp=gp, z=z):
            tr = run_trace(gs, gp, z, tuple(inp[0]))
            return tr[-1][0] if tr else z[0]
        return predict, obs, rec
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
        p, obs, frec = form_state(env, ex, env.budget, c0 + 0.35 * cap, order, split, prior, rng)
        if p is None and time.process_time() < c0 + 0.7 * cap:
            lp, lobs, lrec = form_latent(env, ex + obs, c0 + 0.7 * cap, (policy or {}).get("experiments") if arm == "E" else None, rng)
            obs += lobs
            frec["latent"] = lrec
            if lp is not None:
                seen = {e[0][0] for e in ex + obs}
                ok_all = True
                while env.used < env.budget:            # validation on fresh inputs, as for the output state
                    x = generic_input(rng)
                    if x in seen or len(x) < 2:
                        continue
                    y = ask(env, x, obs)
                    if y is not None:
                        ok = lp((x,)) == y
                        frec["validation"].append(ok)
                        ok_all &= ok
                if ok_all:
                    p = lp
                    frec["formed"] = "latent:" + lrec["formed"]
                    frec["hypotheses"]["latent:" + lrec["formed"]] = {"program": "answer=%s ; latent=%s" % (
                        ic.show(lrec["latent"]["step_answer"]), ic.show(lrec["latent"]["step_latent"]))}
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
