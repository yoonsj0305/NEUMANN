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


def _inits(s_type):
    """Typed identity-like initial values; used only for components whose empty-input value is undefined."""
    return {T_I: [0, 1], T_L: [()], T_B: [False, True]}[s_type]


def consistent(trans):
    seen = {}
    for k, v in trans:
        if k in seen and seen[k] != v:
            return False
        seen[k] = v
    return True


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


MIN_SUPPORT = 2   # every branch of a case tree must explain at least this many observed transitions


def covers(pieces, preds, full, deadline, per_split=2):
    """Case trees over the cells, cheapest first: one piece; pred ? A : B; pred1 ? A : (pred2 ? B : C).
    Predicates are distinct cell partitions (at most 2^cells), so all of them are examined.  A branch that
    explains a single transition is a memorised exception, not a step (FRESH dev: every wrongly adopted
    machine special-cased one observed value, e.g. e == 8), so each branch needs MIN_SUPPORT transitions."""
    sup = lambda m: bin(m).count("1") >= MIN_SUPPORT
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
        if not (sup(pm & full) and sup(~pm & full)):
            continue
        for A in cover_of(pm & full, per_split):
            for B in cover_of(~pm & full, per_split):
                yield ("case", pa, A, B)
    firsts = [(pm, pa, cover_of(pm & full, per_split)) for pm, pa in preds]
    firsts = [f for f in firsts if f[2] and sup(f[0] & full)]
    for pm, pa, As in firsts:
        R = ~pm & full
        for qm, qa in preds:
            if time.process_time() > deadline:
                return
            t_, f_ = qm & R, ~qm & R
            if not (sup(t_) and sup(f_)):
                continue
            Bs = cover_of(t_, per_split)
            if not Bs:
                continue
            Cs = cover_of(f_, per_split)
            for A in As:
                for B in Bs:
                    for C in Cs:
                        yield ("case", pa, A, ("case", qa, B, C))


def synth_cover(in_types, out_type, rows, deadline, check=None, alts=None):
    """Per-transition factorisation of a step: every transition is a cell; pieces are cheap programs that are
    right on some cells, predicates split the cells (the cover principle of `cells`, iteration 4).  Every
    case tree in cost order becomes an ordinary program (nested ifI) and must pass check()."""
    if out_type not in (T_I, T_B):
        return None, None
    lib = _lib()
    target = [o for _, o in rows]
    inputs = [i for i, _ in rows]
    full = (1 << len(rows)) - 1
    pieces, preds, seen = [], [], set()

    def offer(e, t):
        v = e.vec
        if t == T_B:
            mk = sum(1 << j for j, b in enumerate(v) if b)
            if 0 < mk < full and ("p", mk) not in seen:
                seen.add(("p", mk)); preds.append((mk, e.ast()))
        if t == out_type:
            mk = sum(1 << j for j, b in enumerate(v) if b == target[j])
            if mk and ("v", mk) not in seen:
                seen.add(("v", mk)); pieces.append((mk, e.ast()))
    for c in (range(10) if out_type == T_I else (False, True)):
        offer(type("K", (), {"vec": (c,) * len(rows), "ast": lambda self, c=c: ("k", c)})(), out_type)
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
            fn = ic.compile_ast(ast, len(in_types), lib) if out_type == T_I else _case_fn(node, len(in_types), lib)

            def g(args, fn=fn):
                try:
                    v = fn(tuple(args))
                except (ic.Fail, RecursionError, TypeError):
                    return None
                return v if _type(v) == out_type else None
            if check is None or check(g):
                if alts is not None:          # other case trees equally consistent with every observed transition
                    alts.extend(_alt_covers(covers(pieces, preds, full, deadline), repr(ast), out_type,
                                            len(in_types), lib, to_ast))
                return g, ast
        if time.process_time() > deadline:
            break
    return None, None


def _alt_covers(gen, first, out_type, n, lib, to_ast, k=3):
    out, seen = [], {first}
    for node in gen:
        ast = to_ast(node)
        if repr(ast) in seen:
            continue
        seen.add(repr(ast))
        fn = ic.compile_ast(ast, n, lib) if out_type == T_I else _case_fn(node, n, lib)

        def g(args, fn=fn):
            try:
                v = fn(tuple(args))
            except (ic.Fail, RecursionError, TypeError):
                return None
            return v if _type(v) == out_type else None
        out.append(g)
        if len(out) >= k:
            break
    return out


class Exhausted(Exception):
    pass


def _case_fn(node, n, lib):
    """A case tree (pred ? A : B, nested) as a function of the argument tuple (boolean steps have no if-node)."""
    if node[0] == "case":
        p, a, b = (_case_fn(x, n, lib) for x in node[1:])
        return lambda args: a(args) if p(args) else b(args)
    if node[0] == "k":
        return lambda args, c=node[1]: c
    return ic.compile_ast(ic._tup(node), n, lib)


def show_ast(a):
    if isinstance(a, tuple) and a and a[0] in ("ifI", "case") and len(a) == 4:
        return "(if %s %s %s)" % tuple(show_ast(x) for x in a[1:])
    if isinstance(a, tuple) and a and a[0] == "k":
        return repr(a[1])
    try:
        return ic.show(a)
    except Exception:
        return repr(a)


# ------------------------------------------------- invented state: accumulators over the input itself
_ACC = {}


def accumulators():
    """Candidate latent state variables that cost no query: folds h' = G(h, e) over the input, with G every
    small program of the generic substrate (integer and list valued), in cost order, distinct by behaviour.
    Nothing task-specific: the same list for every task."""
    if "all" in _ACC:
        return _ACC["all"]
    lib = _lib()
    out = []
    for in_t, out_t, probes, lim in (
            ((T_I, T_I), T_I, [(h, e) for h in (-3, -1, 0, 1, 2, 5, 7) for e in (-3, -1, 0, 1, 2, 5, 7)], 700),
            ((T_L, T_I), T_L, [(tuple(l), e) for l in ([], [1], [2, 1], [3, 3, 0], [5, -1]) for e in (0, 1, 3, -1)], 120)):
        got = []

        def offer(e, t, got=got, lim=lim):
            got.append(e.ast())
            if len(got) >= lim:
                raise sc.Done(None, None)
        srch = dc.FSearch(lib, in_t, probes, time.process_time() + 2.0, (), ic.uniform_costs(), (out_t,), offer)
        try:
            srch.run()
        except sc.Done:
            pass
        for ast in got:
            fn = ic.compile_ast(ic._tup(ast), 2, lib)
            vec = []
            for pr in probes:
                try:
                    vec.append(fn(pr))
                except Exception:
                    vec.append(None)
            if all(v == pr[0] for v, pr in zip(vec, probes)) or len(set(map(repr, vec))) < 2:
                continue                      # h never changes, or ignores everything
            if not _evolves(fn, out_t):
                continue                      # h settles on a constant after one step: no state
            out.append({"t": out_t, "ast": ast, "fn": fn, "show": show_ast(ast), "size": len(show_ast(ast))})
    out += _conditional_accumulators(lib, {repr(a["ast"]) for a in out})
    _ACC["all"] = out
    return out


_RB = {}


def readout_basis(arity, out_t, n=80):
    """The first small programs of the substrate over `arity` integer variables (cost order, distinct by
    behaviour): the cheap readouts R(h1[, h2]) checked exactly before any synthesis."""
    key = (arity, out_t)
    if key in _RB:
        return _RB[key]
    lib = _lib()
    vals_ = (-3, -1, 0, 1, 2, 5, 7)
    probes = [tuple(v) for v in __import__("itertools").product(vals_, repeat=arity)]
    got = []

    def offer(e, t):
        got.append(e.ast())
        if len(got) >= n:
            raise sc.Done(None, None)
    srch = dc.FSearch(lib, (T_I,) * arity, probes, time.process_time() + 1.0, (), ic.uniform_costs(), (out_t,), offer)
    try:
        srch.run()
    except sc.Done:
        pass
    out = []
    for ast in got:
        fn = ic.compile_ast(ic._tup(ast), arity, lib)
        out.append((ast, fn))
    _RB[key] = out
    return out


def _conditional_accumulators(lib, have):
    """The case-split class h' = if P(h, e) then A else B, composed from the same substrate: P every small
    predicate of (h, e) in cost order, A / B the elementary terms (keep h, take e, add, count, multiply,
    subtract, reset to 0 / 1; for lists: keep, collect e, restart from e).  Running maxima / minima,
    conditional sums and counts, first-of-a-kind and filtered collections are all in this class; nothing
    task-specific is named."""
    out, seen = [], set(have)
    v0, v1 = ("v", 0), ("v", 1)
    for in_t, terms, iff, probes, npred in (
            ((T_I, T_I), [v0, v1, ("add", v0, v1), ("add", v0, ("k", 1)), ("mul", v0, v1), ("sub", v0, v1),
                          ("k", 0), ("k", 1)], "ifI",
             [(h, e) for h in (-3, -1, 0, 1, 2, 5, 7) for e in (-3, -1, 0, 1, 2, 5, 7)], 60),
            ((T_L, T_I), [v0, ("cons", v1, v0), ("cons", v1, ("nil",))], "ifL",
             [(tuple(l), e) for l in ([], [1], [2, 1], [3, 3, 0], [5, -1]) for e in (0, 1, 3, -1)], 40)):
        preds = []

        def offer(e, t, preds=preds, npred=npred):
            if len(set(e.vec)) > 1:
                preds.append(e.ast())
            if len(preds) >= npred:
                raise sc.Done(None, None)
        srch = dc.FSearch(lib, in_t, probes, time.process_time() + 2.0, (), ic.uniform_costs(), (T_B,), offer)
        try:
            srch.run()
        except sc.Done:
            pass
        for pr in preds:
            for ta in terms:
                for tb in terms:
                    if ta == tb:
                        continue
                    ast = (iff, pr, ta, tb)
                    try:
                        fn = ic.compile_ast(ic._tup(ast), 2, lib)
                    except Exception:
                        continue
                    vec = []
                    for q in probes:
                        try:
                            v = fn(q)
                            vec.append(tuple(v) if isinstance(v, list) else v)
                        except Exception:
                            vec.append(None)
                    key = repr(vec)
                    if key in seen or None in vec or not _evolves(fn, in_t[0]):
                        continue
                    seen.add(key)
                    out.append({"t": in_t[0], "ast": ast, "fn": fn, "show": show_ast(ast), "size": len(show_ast(ast))})
    return out


def _apply_knowledge(knowledge, items, singles, partials, conf, fullm, rec, route):
    """Structural knowledge (SKUs from OTHER tasks' verified machines) as hypotheses about the CURRENT task.

    mode "relevant" (arm E): an SKU's relation -- its variable set -- is rebuilt from the current candidates (same
      definition, values recomputed on THIS task's observations) and proposed only if it explains the current
      contradictions (state route: covers every observed contradiction; readout route: separates every pair of
      points with different answers).  Transition / readout are re-synthesised on the current data, never copied.
      Proposed sets go first; D's own order follows unchanged.
    mode "norelevance": the same SKU sets first, whether or not they explain anything here.
    mode "shuffled": random variable sets of the same sizes (the link between knowledge and task broken).
    Each application is logged with its outcome (cost of trying it included in the CPU accounting)."""
    mode, units = knowledge.get("mode"), knowledge.get("units", [])
    pool = {}
    mk = "mask" if route == "state" else "rmask"
    for it in list(singles) + list(partials):
        if len(it["vars"]) == 1:
            c, z = it["vars"][0]
            pool.setdefault((c["show"], _zk_of(it, c, z)), it)
    out, log = [], rec.setdefault("knowledge", [])
    rng = __import__("random").Random(len(items))
    for u in units:
        if u.get("route") != route:
            continue
        if mode == "shuffled":
            keys = rng.sample(sorted(pool), k=min(len(pool), len(u["vars"])))
        else:
            keys = [tuple(v) for v in u["vars"]]
        parts = [pool.get(k) for k in keys]
        if None in parts:
            log.append({"sku": u["id"], "route": route, "applied": False, "reason": "relation not formable here"})
            continue
        mask = 0
        for p_ in parts:
            mask |= p_.get(mk, 0)
        explains = (not conf) or mask == fullm
        if mode == "relevant" and not explains:
            log.append({"sku": u["id"], "route": route, "applied": False, "reason": "does not explain the current contradictions"})
            continue
        it = {"vars": [v for p_ in parts for v in p_["vars"]], "size": sum(p_["size"] for p_ in parts),
              "ns": max(p_.get("ns", p_.get("nd", 0)) for p_ in parts), "nd": max(p_.get("nd", p_.get("ns", 0)) for p_ in parts),
              "mask": mask, mk: mask, "sku": u["id"],
              "feat": parts[0].get("feat", {})}
        if route == "state":
            it["hv"] = [h for p_ in parts for h in p_.get("hv", [])]
        else:
            it["rv"] = [r for p_ in parts for r in p_.get("rv", [])]
        out.append(it)
        log.append({"sku": u["id"], "route": route, "applied": True, "explains": explains})
    return out + [it for it in items if all(it is not o for o in out)]


def _zk_of(it, c, z):
    return (it.get("zkinds") or ["nil" if z == () else repr(z)])[0]


def _inv_features(it, n_prefixes, n_conf, why, s_type, zkind):
    """Evidence of the CURRENT task about one candidate set of invented variables (no identity of a variable,
    nothing remembered from other tasks): how many contradictions were observed and why invention was called,
    how finely the set splits the observed prefixes, its description length, and the structural class of each
    variable (reads the element, keeps memory, case split, list valued, kind of start)."""
    vs_ = it["vars"]
    f = {"bias": 1.0, "n_vars2": float(len(vs_) >= 2), "size": it["size"] / 40.0,
         "granularity": it["ns"] / max(1, n_prefixes), "conflicts": min(n_conf, 20) / 20.0,
         "why_conflict": float(why.startswith("inconsistent")), "why_noupdate": float(why.startswith("update")),
         "ans_bool": float(s_type == T_B), "ans_list": float(s_type == T_L)}
    for c, z in vs_:
        sh = c["show"]
        for k, v in (("reads_e", "$1" in sh), ("keeps_h", "$0" in sh), ("case", sh.startswith("(if")),
                     ("list", c["t"] == T_L), ("start_" + zkind(z) if zkind(z) in ("below", "above", "nil") else
                                               "start_const", True)):
            f[k] = f.get(k, 0.0) + float(v) / len(vs_)
    return {k: round(v, 4) for k, v in f.items()}


class DiscoveryPolicy:
    """Learned discovery policy (V3) with separated credit.  Two logistic models over the current task's evidence
    (`_inv_features`):
      synthesis  P(an Update exists | variables tried)              -- credit to variable selection + synthesis
      repair     P(verified machine | set adopted, failing fraction) -- credit to counterexample repair
    `expected` = synthesis x repair at the typical failing fraction orders the candidate sets; `repairable`
    decides adoption.  Labels come only from independently verified outcomes of OTHER tasks."""

    def __init__(self, w_syn, w_rep, threshold=0.5, adopt=True):
        self.w_syn, self.w_rep, self.threshold, self.adopt = w_syn, w_rep, threshold, adopt

    @staticmethod
    def _p(w, f):
        import math
        z = sum(w.get(k, 0.0) * v for k, v in f.items())
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))

    def expected(self, f):
        return self._p(self.w_syn, f) * self._p(self.w_rep, dict(f, fail_frac=0.0))

    def repairable(self, f, fail_frac):
        return self._p(self.w_rep, dict(f, fail_frac=fail_frac)) >= self.threshold

    def to_json(self):
        return {"w_syn": self.w_syn, "w_rep": self.w_rep, "threshold": self.threshold, "adopt": self.adopt}

    @classmethod
    def from_json(cls, d):
        return None if not d else cls(d["w_syn"], d["w_rep"], d.get("threshold", 0.5), d.get("adopt", True))

    @staticmethod
    def fit_logistic(data, epochs=300, lr=0.1, l2=0.01):
        """data: [(features, label)].  Plain batch gradient descent, L2-regularised."""
        import math
        keys = sorted({k for f, _ in data for k in f})
        w = {k: 0.0 for k in keys}
        n = max(1, len(data))
        pos = sum(y for _, y in data)
        cw = {1: n / (2.0 * max(1, pos)), 0: n / (2.0 * max(1, n - pos))}     # class-balanced
        for _ in range(epochs):
            g = {k: l2 * w[k] for k in keys}
            for f, y in data:
                z = sum(w[k] * v for k, v in f.items())
                p_ = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
                for k, v in f.items():
                    g[k] += cw[y] * (p_ - y) * v / n
            for k in keys:
                w[k] -= lr * g[k]
        return {k: round(v, 5) for k, v in w.items()}


def _acc_step(fn, h, e):
    try:
        v = fn((h, e))
    except Exception:
        return None
    return tuple(v) if isinstance(v, list) else v


def _evolves(fn, t):
    """Does h keep carrying information along an input (not constant from the second step on)?"""
    seqs = [(3, -1, 4, 1, -5, 9), (2, 7, 1, 8, 2, 8), (0, 0, 5, -2, 5, 3)]
    for z in ((0, 1, -2) if t == T_I else ((),)):
        for q in seqs:
            h, hs = z, []
            try:
                for e in q:
                    h = fn((h, e))
                    h = tuple(h) if isinstance(h, list) else h
                    hs.append(h)
            except Exception:
                continue
            if len(set(map(repr, hs))) > 1:
                return True
    return False


def task_input(rng, vals, lens):
    """An input from the task's own value and length distribution: observed values, their neighbours,
    duplicates, shorter and longer lists; one input in five also carries one boundary element (beyond the
    observed range, or a sign change) -- F10.  Nothing task-specific: only what was observed."""
    lo, hi = min(vals), max(vals)
    span = max(1, hi - lo)
    n = rng.randint(max(0, min(lens) - 1), max(lens) + 2)
    x = []
    for _ in range(n):
        r = rng.random()
        if x and r < 0.2:
            v = rng.choice(x)                                   # duplicate
        elif r < 0.75:
            v = rng.choice(vals)
        else:
            v = rng.choice(vals) + rng.choice((-1, 1))
        x.append(v)
    if x and rng.random() < 0.2:
        # boundary element inside the domain the observations show: beyond the observed range, but never a
        # sign the task was not observed with (references are often undefined there)
        opts = [hi + rng.randint(1, span)] if hi >= 0 or lo < 0 else []
        opts += [lo - rng.randint(1, span)] if lo < 0 else [max(0, lo - rng.randint(1, span))]
        if lo < 0 < hi:
            opts.append(-rng.choice(vals))
        x[rng.randrange(len(x))] = rng.choice(opts)
    return tuple(x)


def synth_cells(in_types, rows, deadline):
    """A list-valued Update by the representation-construction core (`latent`, R2), under per-transition
    supervision; returns (g, description)."""
    t = {"id": "update", "in_types": list(in_types), "out_type": T_L, "train": [(k, v) for k, v in rows], "test": []}
    sol = lt.solve(t, deadline, _inv(), lt.Cfg(subst=True, latent=True))
    if sol is None or sol[0] not in ("lat", "residual", "transport", "keep"):
        return None, None
    lib = lt.library(lt.Cfg(subst=True))

    def g(args, sol=sol, t=t):
        return _safe(lambda: lt.run(sol, lib, tuple(args), t))
    return g, ("cells", lt.show(sol))


def grammar(vals, kinds=None, restrict=False):
    """Generic continuation grammar (a starting point only): values above / below every value seen, once or
    twice.  `kinds` (learned on other tasks) reorders it; with `restrict` (learned: the other kinds never
    became a component of an accepted machine on this kind of task) only those kinds are tried."""
    hi, lo = max(vals) + 1, min(min(vals) - 1, 0)
    g = {"above": (hi,), "below": (lo,), "above2": (hi, hi), "below2": (lo, lo)}
    order = [k for k in (kinds or []) if k in g] + ([] if restrict else
                                                    [k for k in ("above", "below", "above2", "below2") if k not in (kinds or [])])
    return [(k, g[k]) for k in order]


def features(examples):
    """Observable task features for the discovery policy (initial examples only)."""
    out_t = _type(examples[0][1])
    ins = [x for (x,), _ in examples]
    outs = [y for _, y in examples]
    if out_t == T_L:
        rel = "same" if all(len(a) == len(b) for a, b in zip(ins, outs)) else \
            "shorter" if all(len(b) <= len(a) for a, b in zip(ins, outs)) else \
            "longer" if all(len(b) >= len(a) for a, b in zip(ins, outs)) else "mixed"
        contained = all(set(b) <= set(a) for a, b in zip(ins, outs))
    else:
        rel = "scalar"
        contained = out_t == T_I and all(b in a for a, b in zip(ins, outs) if a)
    return "%s|%s|%s" % (out_t, rel, "contained" if contained else "computed")


def form_machine(env, examples, deadline, qlimit, direction="prefix", rng=None, prior_ws=None, log=None,
                 prior_structure=None, restrict_kinds=False, acc_prior=None, policy_model=None, knowledge=None,
                 action_policy=None):
    """Learn S(u) = (f(u.w) for w in W), Update and Readout = component 0, with W grown only when needed.

      * W starts with the empty continuation: the answer itself as the state (the output-state machine).
      * Transitions are observed on order-covering trajectories (ascending, descending, random distinct values);
        every component value is a query f(u.w) the agent designs.
      * Insufficient state, detected as two equal (state, element) pairs with different successors, yields the
        distinguishing continuation e.w_j directly (Rivest-Schapire / L*); otherwise, when no Update fits or a
        counterexample cannot be repaired, a grammar continuation is added only if its values on the observed
        prefixes are NOT a function of the current state (it carries new information).
      * Each component's Update is synthesised under per-transition supervision (enumeration with refined
        equivalence, then a per-transition case cover); the machine must reproduce every initial example;
        a failing example is localised by binary search and adds the transition that refutes the machine.
    Returns (predict or None, observations, record)."""
    rng = rng or random.Random(0)
    examples = list(examples)                 # discriminating observations join the verification set
    obs, rec = [], {"direction": direction, "components": [], "events": []}
    s_type = _type(examples[0][1])
    if s_type == T_B:
        s_type = T_B
    vals = sorted({v for (x,), _ in examples for v in x}) or list(range(10))
    memo = {tuple(x): y for (x,), y in examples}
    tag, qp = ["states"], {}
    rec["query_purpose"] = qp

    def F(u):
        u = tuple(u)
        if u in memo:
            return memo[u]
        if env.used >= qlimit:
            raise Exhausted
        y = ask(env, u, obs)
        memo[u] = y
        qp[tag[0]] = qp.get(tag[0], 0) + 1          # what the query was for (instrumentation only)
        return y

    def cont(u, w):
        return tuple(u) + tuple(w) if direction == "prefix" else tuple(w) + tuple(u)

    def step_input(u, e):
        return tuple(u) + (e,) if direction == "prefix" else (e,) + tuple(u)

    W = [()]

    def S(u):
        return tuple(F(cont(u, w)) for w in W)

    # invented state variables computed from the input itself (no query): folds h' = G(h, e) from z
    acc = []
    lens = [len(x) for (x,), _ in examples]

    def hseq(u):
        return tuple(u) if direction == "prefix" else tuple(u)[::-1]

    def hval(fn, z, u, cache):
        """h(u) by the fold, prefix-closed cache (trajectories and counterexample points share prefixes)."""
        u = tuple(u)
        if u in cache:
            return cache[u]
        if not u:
            h = z
        else:
            parent, e = (u[:-1], u[-1]) if direction == "prefix" else (u[1:], u[0])
            hp = hval(fn, z, parent, cache)
            try:
                h = None if hp is None else fn((hp, e))
            except Exception:
                h = None
            if isinstance(h, list):
                h = tuple(h)
        cache[u] = h
        return h

    def H(u):
        out = []
        for a in acc:
            h = hval(a["fn"], a["z"], u, a["cache"])
            if h is None:
                return None
            out.append(h)
        return tuple(out)
    lo, hi = min(vals), max(vals)
    # order-covering trajectory values: the observed range, or (a large range, F9 in the FRESH record) the
    # observed values and their neighbours
    pool = list(range(lo, hi + 1)) if hi - lo <= 256 else sorted({v + d for v in vals for d in (-1, 0, 1)})
    rng.shuffle(pool)
    asc = tuple(sorted(pool[:4]))
    trajs = [asc, asc[::-1], tuple(pool[4:8])]
    extra = []                        # (u, e) points added by counterexamples

    def points():
        pts = []
        for x in trajs:
            seq = x if direction == "prefix" else x[::-1]
            u = ()
            for e in seq:
                pts.append((u, e))
                u = step_input(u, e)
        return pts + extra

    virt = {"value": None, "tried": []}

    def vs(t, u):
        """A state with its undefined components replaced by the virtual value (None: unusable).  A state that is
        entirely undefined below the root carries no information and is never virtualised."""
        if None not in t:
            return t
        if virt["value"] is None or (all(v is None for v in t) and u):
            return None
        return tuple(virt["value"] if v is None else v for v in t)

    def full(u):
        """Observed components (virtualised where undefined) followed by the invented accumulators."""
        t = vs(S(u), u)
        if t is None:
            return None
        hh = H(u)
        return None if hh is None else t + hh

    def transitions():
        """Observed transitions.  With a virtual value set, transitions into and out of partly undefined states
        are kept with the undefined components replaced by that value (no query)."""
        out = []
        tag[0] = "states"
        for u, e in points():
            v = step_input(u, e)
            a, b = full(u), full(v)
            if a is None or b is None:
                continue
            out.append(((a, e), b, u))
        return out

    def partly_undefined():
        """Is there an observed state with some components defined and some not (the only case a virtual value
        can change anything beyond the initial state, which init_candidates already covers)?"""
        return any(None in t and any(c is not None for c in t)
                   for t in (tuple(memo.get(cont(u, w)) if cont(u, w) in memo else 0 for w in W)
                             for u in dict.fromkeys(u for u, e in points())))

    def fold(upd, z, x):
        st = z
        seq = x if direction == "prefix" else x[::-1]
        for e in seq:
            st = tuple(g(st + (e,)) for g in upd)
            if None in st:
                return None
        return st

    sentinels = {T_I: [0, 1, min(vals) - 1, max(vals) + 1], T_L: [()], T_B: [False, True]}[s_type]

    def init_candidates():
        """The observed empty-input state where it is defined; where it is not (the answer is undefined on short
        inputs), virtual initial values: identities and sentinels below / above every value seen.  No query."""
        z = S(())
        options = [[v] if v is not None else ([virt["value"]] if virt["value"] is not None else sentinels) for v in z]
        options += [[a["z"]] for a in acc]
        import itertools
        return [tuple(c) for c in itertools.product(*options)]

    def add_component(w, why):
        if w in W or len(W) >= 4:
            return False
        W.append(w)
        rec["components"].append({"w": list(w), "why": why, "kind": "derived:e+w"})
        virt["value"], virt["tried"] = None, []          # the structure changed: boundary repairs are retried
        return True
    tried_grammar = set()
    if prior_structure:                       # a learned hypothesis about the state structure, tested like any other
        g = dict(grammar(vals))
        for kind in prior_structure:
            if kind in g and add_component(g[kind], "learned structure prior"):
                rec["components"][-1]["kind"] = kind
                tried_grammar.add(g[kind])

    def represent(trans, why):
        """Add one continuation that carries information the current state does not: its values differ on two
        observed prefixes the state merges, or on two prefixes where the state is undefined.  Two queries per
        candidate (the dev experience: an 8-prefix check never produced a component of an accepted machine,
        and its queries were what pushed formations over the limit)."""
        tag[0] = "candidate"
        allp = sorted(dict.fromkeys(u for u, e in points()), key=len)
        cands = [(k, tuple(w)) for k, w in grammar(vals, prior_ws, restrict_kinds)
                 if tuple(w) not in W and tuple(w) not in tried_grammar]
        st = {u: S(u) for u in allp}                    # all observed already (transitions() ran this round)
        # undefined prefixes nearest the definedness boundary first (a short continuation can define them)
        und = sorted((u for u in allp if None in st[u] and u), key=len, reverse=True)[:4]
        groups = {}
        for u in allp:
            if None not in st[u]:
                groups.setdefault(st[u], []).append(u)
        mrg = next((g[:4] for g in groups.values() if len(g) > 1), [])
        for kind, w in cands:
            for pool in (und, mrg):
                got = []                                 # two defined answers (a blocked / invalid one is skipped)
                for u in pool:
                    if len(got) == 2:
                        break
                    v = F(cont(u, w))
                    if v is not None:
                        got.append(v)
                if len(got) == 2:
                    v1, v2 = got
                    if v1 != v2:
                        tried_grammar.add(w)
                        if add_component(w, why + "; informative continuation (screen)"):
                            rec["components"][-1]["kind"] = kind
                            return True
        rec["events"].append("no informative continuation")
        return False
    def attempt(trans, share, cover=0.6):
        """Update per component from the observed transitions, then the best initial state.  No query.
        Returns (updates, asts, z, failing examples), or (None, asts found so far, None, None)."""
        in_t = tuple([s_type] * len(W)) + tuple(a["t"] for a in acc) + (T_I,)
        upd_alts[:] = []
        rows = [[(a + (e,), b[j]) for (a, e), b, _ in trans] for j in range(len(W))]
        upd, asts = [], []
        for j in range(len(W)):
            end = min(deadline, time.process_time() + share * max(0.0, deadline - time.process_time()))
            g, ast = (None, None)
            if s_type == T_L:                 # list-valued components: the cell construction (R2) first
                g, ast = synth_cells(in_t, rows[j], end)
            if g is None:
                g, ast = synth_multi(in_t, s_type, rows[j], end)
            if g is None and s_type in (T_I, T_B):
                alts = [] if j == 0 else None
                g, ast = synth_cover(in_t, s_type, rows[j], min(deadline, time.process_time() + cover), alts=alts)
                if j == 0:
                    upd_alts[:] = alts or []
            if g is None:
                return None, asts, None, None
            upd.append(g)
            asts.append(ast)
        for k, a in enumerate(acc):                  # the invented variables carry their own (known) update
            upd.append(lambda args, fn=a["fn"], i=len(W) + k: _acc_step(fn, args[i], args[-1]))
        best = None
        for z in init_candidates():
            fails = [x for (x,), y in examples if (lambda r: r is None or r[0] != y)(fold(upd, z, tuple(x)))]
            if best is None or len(fails) < len(best[1]):
                best = (z, fails)
        return upd, asts, best[0], best[1]
    invent_tried, rejected, rivals, upd_alts = set(), set(), [], []
    fail_hist = []                           # failing examples per round (stagnation triggers invention)
    t_start, q_start = time.process_time(), env.used

    def choose(why, trans, n_fail):
        """A discovery decision: invent new state now, or keep repairing the current representation (localise,
        continuation, virtual values).  D: invent first (ACTION_MODE); a learned action policy decides from the
        CURRENT evidence only.  Every decision is logged with its evidence for counterfactual learning."""
        groups = {}
        for (a, e), b, u in trans:
            groups.setdefault((a, e), set()).add(b)
        f = {"bias": 1.0, "why_" + why.split()[0]: 1.0,
             "contradictions": min(sum(len(v) > 1 for v in groups.values()), 10) / 10.0,
             "components": (len(W) - 1) / 3.0, "invented": len(acc) / 3.0,
             "ans_bool": float(s_type == T_B), "ans_list": float(s_type == T_L),
             "fail_frac": n_fail / max(1, len(examples)),
             "cpu_left": max(0.0, deadline - time.process_time()) / max(1e-6, deadline - t_start),
             "q_left": max(0, qlimit - env.used) / max(1, qlimit - q_start),
             "rounds": min(len(fail_hist), 10) / 10.0, "undefined": float(virt["value"] is not None)}
        a = ACTION_MODE
        if action_policy is not None:
            a = action_policy(f) or a
        rec.setdefault("decisions", []).append({"why": why, "action": a, "feat": {k: round(v, 3) for k, v in f.items()}})
        return a
    hcache = {}                              # (candidate, start) -> {prefix: value}, shared by every invention call
    selftest = {"left": SELFTEST * 3}
    inv_budget = {"left": INVENT_SHARE * max(0.0, deadline - time.process_time())}

    def sufficiency_probe(state_of):
        """Is the machine's state sufficient?  Two inputs that end in the SAME state must have the same answer
        (Myhill-Nerode on the final state).  A pair is searched among task-distribution inputs and their generic
        edits (no query); the unknown answers are asked (at most two queries).  Different answers refute the
        state representation itself -- not an Update or a start."""
        base_ = [task_input(rng, vals, lens) for _ in range(80)]
        cand = list(dict.fromkeys(base_ + [y for x in base_[:40] for y in edits(x, rng)]))
        by = {}
        for x in cand:
            st_ = _safe(lambda: state_of(x))
            if st_ is None:
                continue
            k_ = repr(st_)
            if k_ in by and by[k_] != x and (x not in memo or by[k_] not in memo):
                pair = (by[k_], x)
                break
            by.setdefault(k_, x)
        else:
            return None
        if selftest["left"] < 2:
            return None
        ys = []
        for x in pair:
            if x not in memo:
                selftest["left"] -= 1
            ys.append(F(x))
        if None in ys or ys[0] == ys[1]:
            return None
        return [(pair[0], ys[0]), (pair[1], ys[1])]

    def revise(reason):
        """A wrong structural hypothesis: the invented variable could not be repaired -> rejected, and the next
        admissible one is invented (3.2E: state / transition / init / domain errors are handled elsewhere)."""
        if not acc:
            return False
        k = max(i for i, c in enumerate(rec["components"]) if c.get("kind") == "accumulator")
        n = rec["components"][k].get("set_size", 1)
        for _ in range(n):                   # the whole adopted set: it was one structural hypothesis
            a = acc.pop()
            rejected.add((a["show"], zkind(a["z"])))
            k = max(i for i, c in enumerate(rec["components"]) if c.get("kind") == "accumulator")
            rec["components"].pop(k)
            rec["events"].append("rejected invented variable %s (%s)" % (a["show"], reason))
        return invent(transitions(), reason)

    def ident_start(c, z):
        """z is an identity start for G when G(z, e) = e for every observed value (0 for sums, the sentinel below
        every value for maxima, ...): the variable then does not depend on an arbitrary start."""
        return c["t"] == T_I and all(_acc_step(c["fn"], z, e) == e for e in vals)

    def zkind(z):
        return "nil" if z == () else "below" if z == min(vals) - 1 else "above" if z == max(vals) + 1 else repr(z)

    ro = {}

    def readout(rdata, rconf, rfull, rcands, why, log_, exact_only=False):
        """Moore readout from invented state: the answer as a function R of invented variables only, each
        updated by its own fold.  Admissible sets make the answer a function of them on every observed prefix
        and example (they cover every pair of data points with different answers); one variable, else pairs
        (set cover).  Coarsest first (a minimal sufficient statistic), then description length.  R is
        synthesised from all those points; the self-test then probes where the next admissible readout
        disagrees, and a counterexample joins the data (the next set is tried)."""
        if not rdata or time.process_time() > deadline:
            return False
        cl = sorted(rcands.values(), key=lambda it: (it["nd"], it["size"]))
        sets = [it for it in cl if it["rmask"] == rfull][:40]
        # set-cover partners: the variables that explain the most answer differences, smallest first
        # pairs by meet-in-the-middle: for a readout op(h1, h2) of the substrate's invertible binary operations,
        # the values h2 must take are determined by h1 and the answers; the candidates are indexed by their value
        # vectors, so every (h1, op) costs one lookup instead of a scan over all partners
        if MULTI and s_type == T_I and len(rdata) >= 3:
            ys = [y for _, y in rdata]
            index = {}
            for it in cl:
                if it["vars"][0][0]["t"] == T_I:
                    index.setdefault(tuple(it["rv"][0]), it)
            inv = (("sub", lambda a, y: a - y, ("sub", ("v", 0), ("v", 1))),     # h1 - h2 = y
                   ("rsub", lambda a, y: a + y, ("sub", ("v", 1), ("v", 0))),    # h2 - h1 = y
                   ("add", lambda a, y: y - a, ("add", ("v", 0), ("v", 1))),     # h1 + h2 = y
                   ("mul", lambda a, y: y // a if a and y % a == 0 else None, ("mul", ("v", 0), ("v", 1))))
            joined = []
            for it in cl:
                if it["vars"][0][0]["t"] != T_I:
                    continue
                h1 = it["rv"][0]
                for name, f_, ast_r in inv:
                    try:
                        need = tuple(f_(a, y) for a, y in zip(h1, ys))
                    except Exception:
                        continue
                    if None in need or need not in index:
                        continue
                    other = index[need]
                    if other["vars"][0][0]["show"] == it["vars"][0][0]["show"]:
                        continue
                    joined.append({"vars": it["vars"] + other["vars"], "rv": it["rv"] + other["rv"],
                                   "nd": len(set(zip(h1, need))), "size": it["size"] + other["size"] + PAIR_COST,
                                   "join": ast_r})
            joined.sort(key=lambda it: it["size"])
            sets += joined[:200]
        for it in sets:
            it["ns"] = it["nd"]
            it["feat"] = _inv_features(it, len(rdata), len(rconf), "readout:" + why, s_type, zkind)
            it["feat"]["readout"] = 1.0
        sets.sort(key=lambda it: (it["nd"], it["size"]))
        if knowledge:
            sets = _apply_knowledge(knowledge, sets, sets, cl, rconf, rfull, rec, "readout")
        if policy_model is not None:
            learned = sorted(sets, key=lambda it: -policy_model.expected(it["feat"]))
            mixed, seen_ = [], set()
            for a_, b_ in zip(learned, sets):
                for it in (a_, b_):
                    if id(it) not in seen_:
                        seen_.add(id(it)); mixed.append(it)
            sets = mixed
        log_["readout_sets"] = len(sets)
        found = []
        # exact check against the cheap readout basis (early exit on the first point that disagrees)
        if s_type in (T_I, T_B):
            exact = []
            # a boolean answer carries one bit per point: the hypotheses searched are bounded (first 50 sets,
            # 30 readouts) so that a chance fit stays unlikely (dev: a hash-like variable with a threshold fitted)
            nset, nbas = (50, 30) if s_type == T_B else (1200, 80)
            for it in sets[:nset]:
                if any(c["t"] != T_I for c, _ in it["vars"]):
                    continue
                pts = [(tuple(r[k] for r in it["rv"]), y) for k, (_, y) in enumerate(rdata)]
                basis = readout_basis(len(it["vars"]), s_type)[:nbas]
                if it.get("join"):
                    basis = [(it["join"], ic.compile_ast(ic._tup(it["join"]), 2, _lib()))] + basis
                for ast, fn in basis:
                    try:
                        if all(fn(xx) == y for xx, y in pts):
                            exact.append((it["size"] + len(show_ast(ast)), it, ast, fn))
                            break
                    except Exception:
                        continue
            exact.sort(key=lambda r: r[0])
            for _, it, ast, fn in exact[:2]:
                g = lambda args, fn=fn: _safe(lambda: fn(tuple(args)))
                log_["tried"].append({"vars": [[c["show"], zkind(z)] for c, z in it["vars"]], "feat": it["feat"],
                                      "update_found": True, "fail_frac": 0.0})
                it["g"] = g

                def pred(x, g=g, vs=it["vars"]):
                    hs = []
                    for c, z in vs:
                        h = z
                        for e in (tuple(x) if direction == "prefix" else tuple(x)[::-1]):
                            h = _acc_step(c["fn"], h, e)
                            if h is None:
                                return None
                        hs.append(h)
                    return g(tuple(hs))
                found.append((it, pred, ast))
        # staged: a cheap readout attempt for many sets (small programs appear within milliseconds), then the
        # longer synthesis for the first ones that had none
        staged = [] if found or exact_only else [(it, 0.03, 0.0) for it in sets[:30]] + [(it, 0.15, 0.15) for it in sets[:6]]
        done_ = set()
        ro_end = time.process_time() + min(0.3 * max(0.0, deadline - time.process_time()), inv_budget["left"])
        for it, t_m, t_c in staged:
            if time.process_time() > ro_end or len(found) >= 2:
                break
            if id(it) in done_:
                continue
            in_t = tuple(c["t"] for c, _ in it["vars"])
            rows = [(tuple(r[k] for r in it["rv"]), y) for k, (_, y) in enumerate(rdata)]
            g, ast = synth_multi(in_t, s_type, rows, min(deadline, time.process_time() + t_m))
            if g is None and t_c and s_type in (T_I, T_B):
                g, ast = synth_cover(in_t, s_type, rows, min(deadline, time.process_time() + t_c))
            if g is not None:
                done_.add(id(it))
            log_["tried"].append({"vars": [[c["show"], zkind(z)] for c, z in it["vars"]], "feat": it["feat"],
                                  "update_found": g is not None, "fail_frac": 0.0 if g is not None else None})
            if g is None:
                continue

            def pred(x, g=g, vs=it["vars"]):
                hs = []
                for c, z in vs:
                    h = z
                    for e in (tuple(x) if direction == "prefix" else tuple(x)[::-1]):
                        h = _acc_step(c["fn"], h, e)
                        if h is None:
                            return None
                    hs.append(h)
                return g(tuple(hs))
            found.append((it, pred, ast))
        if not found:
            return False
        it, pred, ast = found[0]
        rivs = [found[1][1]] if len(found) > 1 else []
        if it.get("g"):                      # the same readout from other starts (initial-state hypotheses)
            for k_, (c_, z_) in enumerate(it["vars"]):
                for z_alt in ([0, 1, min(vals) - 1, max(vals) + 1] if c_["t"] == T_I else []):
                    if z_alt == z_:
                        continue
                    vs2 = list(it["vars"])
                    vs2[k_] = (c_, z_alt)

                    def p2(x, g=it["g"], vs=vs2):
                        hs = []
                        for c, z in vs:
                            h = z
                            for e in (tuple(x) if direction == "prefix" else tuple(x)[::-1]):
                                h = _acc_step(c["fn"], h, e)
                                if h is None:
                                    return None
                            hs.append(h)
                        return g(tuple(hs))
                    p2.vs = vs2
                    rivs.insert(0, p2)
        tag[0] = "selftest"
        used_r = set()

        def hstate(x, vs=it["vars"]):
            hs = []
            for c, z in vs:
                h = z
                for e in (tuple(x) if direction == "prefix" else tuple(x)[::-1]):
                    h = _acc_step(c["fn"], h, e)
                hs.append(h)
            return tuple(hs)
        pr_ = sufficiency_probe(hstate)
        if pr_:
            examples.extend(((x_,), y_) for x_, y_ in pr_)
            rec["events"].append("readout state insufficient: equal invented states, different answers")
            rec["state_refutations"] = rec.get("state_refutations", 0) + 1
            rejected.update((c["show"], zkind(z)) for c, z in it["vars"])
            return False
        for _ in range(SELFTEST):
            if selftest["left"] <= 0:
                break
            base_ = [task_input(rng, vals, lens) for _ in range(120)]
            pool_ = [x for x in dict.fromkeys(base_ + [y for x in base_[:60] for y in edits(x, rng)]) if x not in memo]
            x = None
            for ri, r_ in enumerate(rivs):                    # one experiment per rival, closest first
                if ri in used_r:
                    continue
                used_r.add(ri)
                x = next((x for x in pool_ if _safe(lambda: pred(x)) != _safe(lambda r_=r_: r_(x))), None)
                if x is not None:
                    break
            if x is None:
                x = pool_[0] if pool_ else None
            if x is None:
                break
            y = F(x)
            selftest["left"] -= 1
            if y is not None and _safe(lambda: pred(x)) != y:
                examples.append(((x,), y))
                # classify: if another START of the same variables explains this and every earlier point, it was an
                # initial-state error -- switch the start, keep the variables
                pts_all = [(xx, yy) for xx, yy in rdata] + [(tuple(xx), yy) for (xx,), yy in examples]
                fix = next((r_ for r_ in rivs if getattr(r_, "vs", None)
                            and all(_safe(lambda r_=r_, xx=xx: r_(xx)) == yy for xx, yy in pts_all)), None)
                if fix is not None:
                    it, pred = dict(it, vars=fix.vs), fix
                    rec["events"].append("readout self-test counterexample: initial-state error, start switched")
                    continue
                rec["events"].append("readout self-test counterexample")
                rejected.update((c["show"], zkind(z)) for c, z in it["vars"])
                return False
        if len(it["vars"]) == 2 and s_type in (T_I, T_B):
            mini = rec.setdefault("minimality", [])
            pts_all = [(x, y) for x, y in rdata] + [(tuple(x), y) for (x,), y in examples]
            for k_ in range(2):
                c_, z_ = it["vars"][1 - k_]
                vals_ = [hstate(x, [(c_, z_)])[0] for x, _ in pts_all]
                one = next(((ast1, fn1) for ast1, fn1 in readout_basis(1, s_type)
                            if all(_safe(lambda: fn1((v_,))) == y for v_, (_, y) in zip(vals_, pts_all))), None)
                gone = it["vars"][k_][0]["show"]
                if one:
                    mini.append({"var": gone, "removable": True})
                    ast, fn1 = one
                    it = dict(it, vars=[(c_, z_)])
                    pred = (lambda x, fn1=fn1, c_=c_, z_=z_: _safe(lambda: fn1((hstate(x, [(c_, z_)])[0],))))
                    break
                mini.append({"var": gone, "removable": False, "without_it": "no readout of the other variable alone"})
        ro["predict"] = pred
        log_["adopted"] = [[c["show"], zkind(z)] for c, z in it["vars"]]
        rec["readout"] = show_ast(ast)
        rec["accumulators"] = log_["adopted"]
        for c, z in it["vars"]:
            rec["components"].append({"w": None, "why": why + "; invented variable (readout)", "kind": "accumulator",
                                      "update": c["show"], "init": zkind(z), "set_size": len(it["vars"])})
        rec["events"].append("readout %s of %s" % (show_ast(ast), " + ".join(c["show"] for c, _ in it["vars"])))
        return True

    def invent(trans, why):
        """Budgeted wrapper: all invention calls of one machine share INVENT_SHARE of its CPU, so invention never
        starves repair and the continuation route (dev: four list-routines regressions)."""
        if inv_budget["left"] <= 0:
            return False
        t_ = time.process_time()
        try:
            return _invent(trans, why)
        finally:
            inv_budget["left"] -= time.process_time() - t_

    def _invent(trans, why):
        """Counterexample-driven state invention (no query to form a hypothesis).

        The observed contradictions are the pairs of transitions with equal (state, element) and different
        successors.  Every candidate variable h' = G(h, e) (from `accumulators()`, the same list for every task)
        is computed on every observed prefix; it *explains* a contradiction when it separates its two prefixes.
        A set of variables is admissible when together they explain every contradiction, i.e. with them the
        observed transitions become a function of (state, element): one variable when one suffices, otherwise
        pairs whose explained sets cover all contradictions (a set cover over the contradictions; a single
        variable never needs to explain everything).  Sets inducing the same partition of the observed prefixes
        cannot be told apart by anything observed and are collapsed.  Order: description length (sizes, plus
        PAIR_COST per extra variable), then coarseness -- or, for arm E, the learned discovery policy, which
        scores the CURRENT task's evidence (see `DiscoveryPolicy`).  Each tried set: Update synthesis on the
        extended state, then the fold on every initial example; the first whose Update exists and leaves at
        most a quarter of the examples failing is adopted (the repair loop owns the rest)."""
        key = (len(W), len(acc), virt["value"], why, len(rejected))
        if key in invent_tried or len(acc) >= (MAX_ACC if MULTI else 1) or time.process_time() > deadline:
            return False
        invent_tried.add(key)
        us = list(dict.fromkeys([u for _, _, u in trans] + [step_input(u, e) for (a, e), b, u in trans]))
        groups = {}
        for (a, e), b, u in trans:
            groups.setdefault((a, e), []).append((b, u))
        conf = []
        for g in groups.values():
            for x in range(len(g)):
                for y in range(x + 1, len(g)):
                    if g[x][0] != g[y][0]:
                        conf.append((g[x][1], g[y][1]))
        conf = conf[:60]
        fullm = (1 << len(conf)) - 1
        base = {u: (full(u) or ()) for u in us}

        def signature(hvs):
            lab = {}
            return tuple(lab.setdefault(base[u] + tuple(h[u] for h in hvs), len(lab)) for u in us), len(lab)
        singles, partial = {}, {}
        # Moore readout data: the answer at every observed prefix where it is defined and at every example
        rdata = [(u, memo[cont(u, W[0])]) for u in us if memo.get(cont(u, W[0])) is not None]
        rdata += [(tuple(x), y) for (x,), y in examples if all(tuple(x) != u for u, _ in rdata)]
        rconf = [(i, j) for i in range(len(rdata)) for j in range(i + 1, len(rdata)) if rdata[i][1] != rdata[j][1]][:400]
        rfull = (1 << len(rconf)) - 1
        rcands = {}
        for c in accumulators():
            for z in ([0, 1, min(vals) - 1, max(vals) + 1] if c["t"] == T_I else [()]):
                if (c["show"], zkind(z)) in rejected:
                    continue
                cache = hcache.setdefault((id(c), z), {})   # values persist across invention calls (no recompute)
                hv = {u: hval(c["fn"], z, u, cache) for u in us}
                if None in hv.values() or len(set(hv.values())) < 2:
                    continue
                if rdata:
                    rv = [hval(c["fn"], z, u, cache) for u, _ in rdata]
                    if None not in rv:
                        rmask = sum(1 << k for k, (i_, j_) in enumerate(rconf) if rv[i_] != rv[j_])
                        if rmask:
                            nd = len(set(rv))
                            k2 = tuple(rv)        # values, not the partition: a readout needs the values
                            sz = c["size"] + (0 if ident_start(c, z) else 3)
                            if k2 not in rcands or (sz, nd) < (rcands[k2]["size"], rcands[k2]["nd"]):
                                rcands[k2] = {"vars": [(c, z)], "rv": [rv], "rmask": rmask, "size": sz, "nd": nd,
                                              "zkinds": [zkind(z)]}
                mask = sum(1 << k for k, (p_, q_) in enumerate(conf) if hv[p_] != hv[q_])
                if not mask and conf:
                    continue
                sig, ns = signature([hv])
                it = {"vars": [(c, z)], "size": c["size"] + (0 if ident_start(c, z) else 3), "mask": mask, "ns": ns,
                      "hv": [hv], "zkinds": [zkind(z)]}
                bucket = singles if mask == fullm else partial
                k_ = (sig, c["show"]) if bucket is singles else sig
                if k_ not in bucket or (it["size"], ns) < (bucket[k_]["size"], bucket[k_]["ns"]):
                    bucket[k_] = it
        # the same variable from another start stays (an initial-state hypothesis); other equal partitions collapse
        sl, seen_sig = [], {}
        for (sig, show), it in sorted(singles.items(), key=lambda kv: (kv[1]["size"], kv[1]["ns"])):
            if sig in seen_sig and seen_sig[sig] != show:
                continue
            seen_sig.setdefault(sig, show)
            sl.append(it)
        combos = []
        pl = [] if not MULTI else sorted(partial.values(), key=lambda it: (-bin(it["mask"]).count("1"), it["size"]))[:120] if conf else sl[:12]
        for x in range(len(pl)):
            for y in range(x + 1, len(pl)):
                if conf and pl[x]["mask"] | pl[y]["mask"] != fullm:
                    continue
                if pl[x]["vars"][0][0]["show"] == pl[y]["vars"][0][0]["show"]:
                    continue
                combos.append({"vars": pl[x]["vars"] + pl[y]["vars"], "hv": pl[x]["hv"] + pl[y]["hv"],
                               "size": pl[x]["size"] + pl[y]["size"] + PAIR_COST, "mask": fullm})
        csig = {}
        for it in combos:
            sig, ns = signature(it["hv"])
            it["ns"] = ns
            if sig not in csig or (it["size"], ns) < (csig[sig]["size"], csig[sig]["ns"]):
                csig[sig] = it
        items = sl + list(csig.values())
        for it in items:                     # the evidence the discovery policy sees (current task only)
            it["feat"] = _inv_features(it, len(us), len(conf), why, s_type, zkind)
        items.sort(key=lambda it: (it["size"], it["ns"]))
        if knowledge:
            items = _apply_knowledge(knowledge, items, sl, list(partial.values()), conf, fullm, rec, "state")
        if policy_model is not None:
            # learned order, interleaved with the description-length order: the policy can bring a set forward
            # on the current task's evidence, it can never drop D's own first choices
            learned = sorted(items, key=lambda it: -policy_model.expected(it["feat"]))
            mixed, seen_ = [], set()
            for a_, b_ in zip(learned, items):
                for it in (a_, b_):
                    if id(it) not in seen_:
                        seen_.add(id(it))
                        mixed.append(it)
            items = mixed
        log_ = {"why": why, "admissible": len(sl), "combinations": len(csig), "conflicts": len(conf),
                "tried": [], "adopted": None, "cpu_left": round(deadline - time.process_time(), 2)}
        rec.setdefault("inventions", []).append(log_)
        if not conf and readout(rdata, rconf, rfull, rcands, why, log_, exact_only=True):
            return True                      # no contradiction observed: an exact readout is the stronger evidence
        tol = max(1, len(examples) // 4)
        chosen, rival = None, None
        inv_end = time.process_time() + min(0.3 * max(0.0, deadline - time.process_time()), inv_budget["left"])
        for it in items[:INVENT_K]:
            if time.process_time() > inv_end:           # invention may not starve the other routes
                break
            for c, z in it["vars"]:
                acc.append({"t": c["t"], "fn": c["fn"], "z": z, "cache": {}, "show": c["show"]})
            try:
                upd, asts, z0, fails = attempt(transitions(), 0.03, 0.3)
            finally:
                del acc[len(acc) - len(it["vars"]):]
            nf = None if upd is None else len(fails)
            log_["tried"].append({"vars": [[c["show"], zkind(z)] for c, z in it["vars"]], "feat": it["feat"],
                                  "update_found": upd is not None,
                                  "fail_frac": None if nf is None else round(nf / max(1, len(examples)), 3)})
            ok_ = upd is not None and nf <= tol
            if upd is not None and policy_model is not None and policy_model.adopt:
                # learned adoption: will the repair loop turn this set into a verified machine?
                ok_ = policy_model.repairable(it["feat"], nf / max(1, len(examples)))
            if ok_:
                if chosen is None:
                    chosen = it
                    continue
                rival = lambda x, upd=upd, z0=z0: (lambda r: None if r is None else r[0])(fold(upd, z0, x))
                break
        if chosen is None:
            return readout(rdata, rconf, rfull, rcands, why, log_)
        rivals[:] = [rival] if rival else []
        for c, z in chosen["vars"]:
            acc.append({"t": c["t"], "fn": c["fn"], "z": z, "cache": {}, "show": c["show"]})
            rec["components"].append({"w": None, "why": why + "; invented accumulator", "kind": "accumulator",
                                      "update": c["show"], "init": zkind(z), "set_size": len(chosen["vars"])})
        log_["adopted"] = [[c["show"], zkind(z)] for c, z in chosen["vars"]]
        rec["events"].append("invented %s (%s)" % (" + ".join("h' = %s from %s" % (c["show"], zkind(z))
                                                              for c, z in chosen["vars"]), why))
        return True
    try:
        for rnd in range(25):
            if ro:
                rec["formed"] = True
                rec["update"] = ["readout " + rec["readout"]]
                return (lambda inp, p_=ro["predict"]: p_(inp[0])), obs, rec
            if time.process_time() > deadline:
                rec["events"].append("deadline")
                break
            trans = transitions()
            if len(trans) < 3:
                rec["events"].append("too few defined transitions")
                break
            # 1. insufficient state: equal (state, element), different successors -> distinguishing continuation
            seen, conflict = {}, None
            for (a, e), b, u in trans:
                if (a, e) in seen and seen[(a, e)][0] != b:
                    conflict = (seen[(a, e)], (b, u), e)
                    break
                seen.setdefault((a, e), (b, u))
            if conflict and choose("inconsistent transitions", trans, 0) == "invent" and invent(trans, "inconsistent transitions"):
                continue
            if conflict:
                (b1, _), (b2, _), e = conflict
                j = next(i for i in range(len(W)) if b1[i] != b2[i])
                w = ((e,) + W[j]) if direction == "prefix" else (W[j] + (e,))
                if not add_component(w, "inconsistent transitions"):
                    rec["events"].append("state insufficient, component limit")
                    break
                continue
            # 2. Update per component, then joint verification on every initial example
            upd, asts, z, fails = attempt(trans, 0.25)
            if upd is None:
                rec["events"].append("no update for component %d" % len(asts))
                act_ = choose("update not found", trans, len(examples))
                if act_ == "invent" and (invent(trans, "update not found") or revise("update not found")):
                    continue
                if represent(trans, "update not found"):
                    continue
                if act_ != "invent" and (invent(trans, "update not found") or revise("update not found")):
                    continue
                break
            rec["events"].append("round %d: m=%d, examples failing %d" % (rnd, len(W), len(fails)))
            if not fails and selftest["left"] > 0:
                # verification-driven repair: inputs from the task's own distribution and boundaries where the
                # machine is most exposed (duplicates, extremes, other lengths); a wrong prediction is a
                # counterexample that joins the verification set and is localised next round (a transition
                # error), never a reason to accept.  The independent challenge after formation is separate.
                tag[0] = "selftest"
                m_ = lambda x, upd=list(upd), z=z: (lambda r: None if r is None else r[0])(fold(upd, z, x))
                # rival hypotheses: other answer Updates equally consistent with every observed transition, and
                # the runner-up invented variable; the experiment is an input where they predict differently
                riv = [lambda x, u2=[g0] + list(upd[1:]), z=z: (lambda r: None if r is None else r[0])(fold(u2, z, x))
                       for g0 in upd_alts]
                # the same machine from another start of an invented variable (an initial-state hypothesis)
                for k_, a_ in enumerate(acc):
                    for z_alt in ([0, 1, min(vals) - 1, max(vals) + 1] if a_["t"] == T_I else []):
                        if z_alt != a_["z"]:
                            zz = tuple(z[:len(W) + k_]) + (z_alt,) + tuple(z[len(W) + k_ + 1:])
                            riv.insert(0, lambda x, upd=list(upd), zz=zz: (lambda r: None if r is None else r[0])(fold(upd, zz, x)))
                # closest rivals first (another start, another equally consistent Update): random tests miss the
                # small regions where they differ; a distant rival is refuted by any test, so it comes last
                riv += rivals
                used_r = set()
                bad = None
                if acc:
                    pr_ = sufficiency_probe(lambda x, upd=list(upd), z=z: fold(upd, z, x))
                    if pr_:
                        examples.extend(((x_,), y_) for x_, y_ in pr_)
                        rec["events"].append("state insufficient: equal final states, different answers")
                        rec["state_refutations"] = rec.get("state_refutations", 0) + 1
                        if revise("state insufficient"):
                            continue
                        break
                for _ in range(SELFTEST):
                    base_ = [task_input(rng, vals, lens) for _ in range(120)]
                    # the experiment is searched, not sampled: task-distribution inputs and their generic edits
                    # (sorted, reversed, an element replaced / deleted / duplicated), where the hypotheses split
                    pool_ = [x for x in dict.fromkeys(base_ + [y for x in base_[:60] for y in edits(x, rng)])
                             if x not in memo]
                    # an experiment from the hypotheses: where the rival invented variable predicts otherwise
                    x = None
                    for ri, r in enumerate(riv):          # one experiment per rival, closest first
                        if ri in used_r:
                            continue
                        x = next((x for x in pool_ if _safe(lambda: m_(x)) != _safe(lambda r=r: r(x))), None)
                        used_r.add(ri)
                        if x is not None:
                            break
                    if x is None:
                        x = pool_[0] if pool_ else None
                    if x is None:
                        break
                    y = F(x)
                    selftest["left"] -= 1
                    if y is not None and _safe(lambda: m_(x)) != y:
                        bad = (x, y)
                        break
                if bad:
                    examples.append(((bad[0],), bad[1]))
                    rec["events"].append("self-test counterexample (transition error)")
                    rec["selftest_counterexamples"] = rec.get("selftest_counterexamples", 0) + 1
                    continue
            if not fails and len(acc) >= 2:
                # actual minimality (within this substrate): drop each invented variable in turn; it stays only if
                # the machine without it cannot be re-synthesised to reproduce every observation
                mini = rec.setdefault("minimality", [])
                for k_ in reversed(range(len(acc))):
                    a_ = acc.pop(k_)
                    u2, as2, z2, f2 = attempt(transitions(), 0.05, 0.3)
                    if u2 is not None and not f2:
                        upd, asts, z = u2, as2, z2
                        ci = [i for i, c in enumerate(rec["components"]) if c.get("kind") == "accumulator"][k_]
                        rec["components"].pop(ci)
                        mini.append({"var": a_["show"], "removable": True})
                    else:
                        acc.insert(k_, a_)
                        mini.append({"var": a_["show"], "removable": False,
                                     "counterexample": None if f2 is None else [list(f2[0])] if f2 else None,
                                     "without_it": "no Update" if u2 is None else "%d examples fail" % len(f2)})
            if not fails:
                rec["update"] = [show_ast(a) if not (isinstance(a, tuple) and a and a[0] == "cells") else a[1] for a in asts]
                rec["virtual_value"] = virt["value"]
                rec["accumulators"] = [[a["show"], zkind(a["z"])] for a in acc]
                rec["init"] = repr(z)
                rec["formed"] = True

                def predict(inp, upd=list(upd), z=z):
                    r = fold(upd, z, tuple(inp[0]))
                    return None if r is None else r[0]
                return predict, obs, rec
            # representation change before more repair: the fold fails on at least half the examples and has not
            # improved over two rounds -> the state, not a transition, is the likely error (invention is query-free)
            fail_hist.append(len(fails))
            if len(fail_hist) >= 3 and fail_hist[-1] >= fail_hist[-3] and len(fails) * 2 >= len(examples) \
                    and choose("no progress", trans, len(fails)) == "invent" and invent(trans, "no progress"):
                continue
            # 3. counterexample: binary search for the first step leaving the true states, add that point
            tag[0] = "localise"
            x = tuple(fails[0])
            seq = x if direction == "prefix" else x[::-1]
            prefixes = [()]
            for e in seq:
                prefixes.append(step_input(prefixes[-1], e))
            pred_states = [z]
            for e in seq:
                st = pred_states[-1]
                pred_states.append(None if st is None or None in st else tuple(g(st + (e,)) for g in upd))
            lo_, hi_ = 0, len(seq)
            while hi_ - lo_ > 1:
                mid = (lo_ + hi_) // 2
                ps = pred_states[mid]
                a0 = F(cont(prefixes[mid], W[0]))       # the answer component first (one query)
                if a0 is not None and ps is not None and None not in ps and ps[0] != a0:
                    hi_ = mid
                    continue
                t = full(prefixes[mid])
                if t is None or ps == t:
                    lo_ = mid
                else:
                    hi_ = mid
            added = False
            for i in list(range(max(1, lo_), len(seq) + 1)) + list(range(1, max(1, lo_))):
                u, e = prefixes[i - 1], seq[i - 1]
                if (u, e) in extra:
                    continue
                a, b = full(u), full(prefixes[i])
                if a is None or b is None:
                    continue
                if tuple(g(a + (e,)) for g in upd) != b:
                    extra.append((u, e))
                    added = True
                    break
            rec.setdefault("counterexamples", 0)
            rec["counterexamples"] += added
            if not added:
                rec["events"].append("counterexample not localisable")
                rec.setdefault("unlocalised", []).append(list(x))
                if s_type == T_I and partly_undefined() and not virt["tried"]:
                    # first: a virtual value for the undefined components -- every candidate is compared on the
                    # observations already made (no query); the one leaving the fewest failing examples is kept
                    scored = []
                    for v in (min(vals) - 1, max(vals) + 1):
                        virt["value"] = v
                        u_, _, _, f_ = attempt(transitions(), 0.1)
                        scored.append((len(examples) + 1 if u_ is None else len(f_), v))
                    virt["tried"] = [v for _, v in scored]
                    rec["events"].append("virtual values compared: %s" % scored)
                    nf, v = min(scored)
                    if nf <= len(fails):         # a tie still moves the failure where it can be localised
                        virt["value"] = v
                        rec["events"].append("virtual value %d for undefined components (%d failing)" % (v, nf))
                        continue
                virt["value"] = None
                act_ = choose("not localisable", trans, len(fails))
                if act_ == "invent" and (invent(trans, "counterexample not localisable") or revise("counterexample not localisable")):
                    continue
                if represent(trans, "counterexample hidden in undefined prefixes"):
                    continue
                if act_ != "invent" and (invent(trans, "counterexample not localisable") or revise("counterexample not localisable")):
                    continue
                break
    except Exhausted:
        rec["events"].append("query limit")
    return None, obs, rec


# -------------------------------------------------------------------- arms
SELFTEST = 3      # self-test queries per formed machine (at most 3 repairs) before it is returned
MAX_ACC = 3       # invented variables per machine
ACTION_MODE = "invent"   # D's fixed decision at a discovery branch point ("repair": the counterfactual arm)
MULTI = True      # ablation switch: False = one invented variable at a time, no sets, no joined readouts
PAIR_COST = 6     # description-length charge for each additional invented variable
INVENT_SHARE = 0.4  # share of a machine's formation CPU that all its invention calls may use together
INVENT_K = 10     # admissible invented variables tried per invention (cost order, or learned order for E)
CHALLENGE = 3     # fresh inputs a formed machine must predict before it may replace the passive solution
DISCRIMINATE = 2  # queries kept to decide between an accepted machine and the passive solution where they differ


def _action_policy(d):
    """Learned discovery-action policy (V3): P(inventing now beats repairing the current representation | the
    decision's evidence), learned from counterfactual pairs on other tasks.  Decides only when confident
    (|p - 0.5| > margin); otherwise None, and D's own decision stands."""
    if not d:
        return None
    w, m = d["w"], d.get("margin", 0.15)

    def pol(f):
        p = DiscoveryPolicy._p(w, f)
        return "invent" if p > 0.5 + m else "repair" if p < 0.5 - m else None
    return pol


def challenge(env, machine, examples, obs, rng, k=CHALLENGE):
    """Independent challenge on fresh inputs the machine was not built from.  Returns True / False / None
    (None: no query left, the machine is NOT accepted)."""
    seen = {e[0][0] for e in list(examples) + obs}
    vals = sorted({v for (x,), _ in examples for v in x}) or list(range(10))
    lens = [len(x) for (x,), _ in examples]
    results = []
    tries = 0
    while len(results) < k and env.used < env.budget and tries < 200:
        tries += 1
        x = task_input(rng, vals, lens)          # F10: the task's own value distribution and its boundaries
        if x in seen or len(x) < 2:
            continue
        seen.add(x)
        y = ask(env, x, obs)
        if y is None:
            continue
        results.append(machine((x,)) == y)
    if len(results) < k:
        return None
    return all(results)


def run_arm(arm, env, cap, seed=0, policy=None, replay=None):
    """One arm on one task.  `replay`: for Dq, the exact list of query inputs D made (answers come from the
    environment again, so the information is identical)."""
    rng = random.Random(seed)
    c0 = time.process_time()
    deadline = c0 + cap
    ex = env.initial()
    rec = {"arm": arm}
    obs = []
    if arm == "A":
        pred, r = passive(ex, cap)
    elif arm == "B":
        obs = random_queries(env, rng, env.budget)
        pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    elif arm == "C":
        obs = committee_queries(env, ex, rng, env.budget, c0 + 0.4 * cap)
        pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    elif arm == "Dq":
        for x in replay or []:
            ask(env, tuple(x), obs)
        pred, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
    else:
        frec = {"machines": []}
        p = None
        qlimit = env.budget - CHALLENGE - DISCRIMINATE
        pol = None
        if arm == "E" and policy:
            pol = policy["by_feature"].get(features(ex), policy["global"])
        directions = pol["directions"] if pol else None
        lim = (pol or {}).get("formation") or {}
        if lim.get("skip"):                  # learned: formation never succeeded on this kind of task
            directions = ()
            frec["skipped_by_policy"] = True
        for direction in (("prefix", "suffix") if directions is None else directions):
            if time.process_time() > c0 + 0.6 * cap or env.used >= qlimit:
                break
            q0, t0 = env.used, time.process_time()
            # learned allotment per machine: what every accepted machine on this kind of task needed (+ margin)
            f_q = min(qlimit, q0 + lim["max_queries"]) if lim.get("max_queries") else qlimit
            f_end = min(c0 + 0.6 * cap, t0 + lim["max_cpu"]) if lim.get("max_cpu") else c0 + 0.6 * cap
            m, mobs, mrec = form_machine(env, ex + obs, f_end, f_q, direction, rng,
                                         pol["continuation_kinds"] if pol else None, None,
                                         (pol or {}).get("structures", {}).get(direction),
                                         bool((pol or {}).get("restrict_kinds")), None,
                                         DiscoveryPolicy.from_json((policy or {}).get("discovery")),
                                         (policy or {}).get("knowledge"), _action_policy((policy or {}).get("action")))
            mrec["queries_used"], mrec["cpu"] = env.used - q0, round(time.process_time() - t0, 3)
            obs += mobs
            frec["machines"].append(mrec)
            if m is not None:
                verdict = challenge(env, m, ex, obs, rng)
                mrec["challenge"] = verdict
                if verdict:
                    p = m
                    frec["formed"] = direction
                    break
        rest = env.budget - env.used - (DISCRIMINATE if p is not None else 0)
        if rest > 0:
            obs += committee_queries(env, ex + obs, rng, rest, time.process_time() + 0.3 * max(0.0, deadline - time.process_time()))
        rec["formation"] = frec
        pp, r = passive(ex + obs, max(0.2, deadline - time.process_time()))
        pred = pp
        if p is not None:
            mr = frec["machines"][-1]
            rm = {"via": "state:%s:m=%d" % (frec["formed"], len(mr["components"]) + 1),
                  "program": "W=%s update=%s" % ([[]] + [c["w"] for c in mr["components"]], mr.get("update"))}
            choice = "machine"
            if pp is not None:
                # two hypotheses fit everything observed: query where they disagree, keep the one that is right
                seen = {e[0][0] for e in ex + obs}
                for _ in range(DISCRIMINATE):
                    vals_ = sorted({v for (x,), _ in ex for v in x}) or list(range(10))
                    x = next((x for x in (task_input(rng, vals_, [len(x) for (x,), _ in ex]) for _ in range(300))
                              if x not in seen and len(x) >= 2 and _safe(lambda: p((x,))) != _safe(lambda: pp((x,)))), None)
                    if x is None or env.used >= env.budget:
                        break
                    seen.add(x)
                    y = ask(env, x, obs)
                    if y is None:
                        continue
                    choice = "machine" if p((x,)) == y else "passive" if pp((x,)) == y else "neither"
                    break
            frec["adoption"] = choice
            if choice == "machine" or pp is None:
                pred, r = p, rm
    rec.update({"via": r.get("via") if r else None, "program": r.get("program") if r else None,
                "fit": pred is not None, "queries": env.used, "cpu_seconds": round(time.process_time() - c0, 4),
                "query_inputs": [list(x) for x, _ in env.log]})
    return pred, rec
