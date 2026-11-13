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


class Exhausted(Exception):
    pass


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


def grammar(vals, kinds=None):
    """Generic continuation grammar (a starting point only): values above / below every value seen, once or
    twice.  `kinds` (learned on other tasks) reorders it; nothing task-specific is added."""
    hi, lo = max(vals) + 1, min(min(vals) - 1, 0)
    g = {"above": (hi,), "below": (lo,), "above2": (hi, hi), "below2": (lo, lo)}
    order = [k for k in (kinds or []) if k in g] + [k for k in ("above", "below", "above2", "below2") if k not in (kinds or [])]
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
                 prior_structure=None):
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
    obs, rec = [], {"direction": direction, "components": [], "events": []}
    s_type = _type(examples[0][1])
    if s_type == T_B:
        s_type = T_B
    vals = sorted({v for (x,), _ in examples for v in x}) or list(range(10))
    memo = {tuple(x): y for (x,), y in examples}

    def F(u):
        u = tuple(u)
        if u in memo:
            return memo[u]
        if env.used >= qlimit:
            raise Exhausted
        y = ask(env, u, obs)
        memo[u] = y
        return y

    def cont(u, w):
        return tuple(u) + tuple(w) if direction == "prefix" else tuple(w) + tuple(u)

    def step_input(u, e):
        return tuple(u) + (e,) if direction == "prefix" else (e,) + tuple(u)

    W = [()]

    def S(u):
        return tuple(F(cont(u, w)) for w in W)
    lo, hi = min(vals), max(vals)
    pool = list(range(lo, hi + 1))
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

    def transitions():
        """Observed transitions.  With a virtual value set, transitions into and out of partly undefined states
        are kept with the undefined components replaced by that value (no query)."""
        out = []
        for u, e in points():
            v = step_input(u, e)
            a, b = vs(S(u), u), vs(S(v), v)
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
        """Add one continuation whose values are not a function of the current state (new information), or one
        that makes the state defined where the answer is undefined.  Checked on a few observed prefixes only."""
        allp = list(dict.fromkeys(u for u, e in points()))
        # most diagnostic first: prefixes where the current state is (partly) undefined, then the shortest
        pref = sorted(allp, key=lambda u: (None not in tuple(memo.get(cont(u, w0)) for w0 in W), len(u)))[:8]
        cands = [(k, tuple(w)) for k, w in grammar(vals, prior_ws) if tuple(w) not in W and tuple(w) not in tried_grammar]
        # screening (early accept, no extra cost: the screened prefixes are a subset of the full check's): two
        # prefixes where the state is undefined, or two prefixes the state merges -- a difference there is decisive
        st = {u: S(u) for u in pref}
        und = [u for u in pref if None in st[u] and u][:2]
        groups = {}
        for u in pref:
            if None not in st[u]:
                groups.setdefault(st[u], []).append(u)
        mrg = next((g[:2] for g in groups.values() if len(g) > 1), [])
        for kind, w in cands:
            for pair in (und, mrg):
                if len(pair) == 2:
                    v1, v2 = F(cont(pair[0], w)), F(cont(pair[1], w))
                    if v1 is not None and v2 is not None and v1 != v2:
                        tried_grammar.add(w)
                        if add_component(w, why + "; informative continuation (screen)"):
                            rec["components"][-1]["kind"] = kind
                            return True
        for kind, w in cands:
            if w in tried_grammar:
                continue
            tried_grammar.add(w)
            feat, merged, undefined_vals = {}, False, set()
            for u in pref:
                a = S(u)
                v = F(cont(u, w))
                if None in a:
                    if v is not None:
                        undefined_vals.add(repr(v))      # what it says where the state says nothing
                    continue
                if a in feat and feat[a] != v:
                    merged = True                       # not a function of the state: new information
                feat[a] = v
            # informative = distinguishes states the representation merges, or varies where the state is undefined
            informative = merged or len(undefined_vals) > 1
            if informative and add_component(w, why + "; informative continuation"):
                rec["components"][-1]["kind"] = kind
                return True
        rec["events"].append("no informative continuation")
        return False
    def attempt(trans, share):
        """Update per component from the observed transitions, then the best initial state.  No query.
        Returns (updates, asts, z, failing examples), or (None, asts found so far, None, None)."""
        in_t = tuple([s_type] * len(W)) + (T_I,)
        rows = [[(a + (e,), b[j]) for (a, e), b, _ in trans] for j in range(len(W))]
        upd, asts = [], []
        for j in range(len(W)):
            end = min(deadline, time.process_time() + share * max(0.0, deadline - time.process_time()))
            g, ast = (None, None)
            if s_type == T_L:                 # list-valued components: the cell construction (R2) first
                g, ast = synth_cells(in_t, rows[j], end)
            if g is None:
                g, ast = synth_multi(in_t, s_type, rows[j], end)
            if g is None and s_type == T_I:
                g, ast = synth_cover(in_t, s_type, rows[j], min(deadline, time.process_time() + 0.6))
            if g is None:
                return None, asts, None, None
            upd.append(g)
            asts.append(ast)
        best = None
        for z in init_candidates():
            fails = [x for (x,), y in examples if (lambda r: r is None or r[0] != y)(fold(upd, z, tuple(x)))]
            if best is None or len(fails) < len(best[1]):
                best = (z, fails)
        return upd, asts, best[0], best[1]
    try:
        for rnd in range(25):
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
                if not represent(trans, "update not found"):
                    break
                continue
            rec["events"].append("round %d: m=%d, examples failing %d" % (rnd, len(W), len(fails)))
            if not fails:
                rec["update"] = [a[1] if isinstance(a, tuple) and a and a[0] == "cells" else ic.show(a) for a in asts]
                rec["virtual_value"] = virt["value"]
                rec["init"] = repr(z)
                rec["formed"] = True

                def predict(inp, upd=list(upd), z=z):
                    r = fold(upd, z, tuple(inp[0]))
                    return None if r is None else r[0]
                return predict, obs, rec
            # 3. counterexample: binary search for the first step leaving the true states, add that point
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
                t = vs(S(prefixes[mid]), prefixes[mid])
                if t is None or ps == t:
                    lo_ = mid
                else:
                    hi_ = mid
            added = False
            for i in list(range(max(1, lo_), len(seq) + 1)) + list(range(1, max(1, lo_))):
                u, e = prefixes[i - 1], seq[i - 1]
                if (u, e) in extra:
                    continue
                a, b = vs(S(u), u), vs(S(prefixes[i]), prefixes[i])
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
                if not represent(trans, "counterexample hidden in undefined prefixes"):
                    break
    except Exhausted:
        rec["events"].append("query limit")
    return None, obs, rec


# -------------------------------------------------------------------- arms
CHALLENGE = 3     # fresh inputs a formed machine must predict before it may replace the passive solution
DISCRIMINATE = 2  # queries kept to decide between an accepted machine and the passive solution where they differ


def challenge(env, machine, examples, obs, rng, k=CHALLENGE):
    """Independent challenge on fresh inputs the machine was not built from.  Returns True / False / None
    (None: no query left, the machine is NOT accepted)."""
    seen = {e[0][0] for e in list(examples) + obs}
    results = []
    tries = 0
    while len(results) < k and env.used < env.budget and tries < 50:
        tries += 1
        x = generic_input(rng)
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
        for direction in (directions or ("prefix", "suffix")):
            if time.process_time() > c0 + 0.6 * cap or env.used >= qlimit:
                break
            m, mobs, mrec = form_machine(env, ex + obs, c0 + 0.6 * cap, qlimit, direction, rng,
                                         pol["continuation_kinds"] if pol else None, None,
                                         (pol or {}).get("structures", {}).get(direction))
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
                    x = next((x for x in (generic_input(rng) for _ in range(200))
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
