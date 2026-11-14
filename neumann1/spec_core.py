"""NEUMANN 1 specification-space core (S).  Development status; nothing here is evidence.

The SECOND evaluation showed that macro compression of solved programs does not add capability: a macro only
re-weights the same generate-and-test search.  This module changes WHAT is searched.

State representation
  * a task is a specification (a vector of required values), not a point in program space;
  * specifications are transformed backwards by INVERSE OPERATORS into smaller specifications (sub-goals);
  * a list-to-list task is re-represented as a traversal whose per-step state is the observable MAXIMAL state
    (element, index, remaining count, reversed input prefix, input suffix, whole input); an integer sequence
    as a self-referential object whose state is its own history.  Every component is read from the examples,
    so the step operator is searched under PER-STEP supervision.  The solved body names the components it
    needs: the minimal sufficient state is an output, not an input.

Operation generation
  * inverse operators are not written by hand: `derive_inverses` poses the inversion of every first-order
    primitive as a self-generated task and solves it with the system's own search;
  * step operators (index-aware maps, positional filters, recurrences) are synthesised per task; they are not
    sub-trees of earlier programs.

Nothing is learned from task data across tasks: no memory, no macro library.  The forward enumerator, the
substrate and the candidate order are those of `invention_core` (unchanged file).  Budgets are CPU seconds.
"""
from __future__ import annotations
import json, pathlib, random, time
from neumann1 import invention_core as ic

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
INVERSES = "docs/experiments/results/spec_core_inverses.json"
Z_TYPES = (T_I, T_I, T_I, T_L, T_L, T_L)        # e, j, r, reversed prefix, suffix, whole
SUB_CAP = 40                                     # per-step examples given to a step search
SUB_SHARE = 0.4                                  # share of the CPU cap spent on traversal sub-tasks first


class Done(Exception):
    def __init__(self, sol, via):
        self.sol, self.via = sol, via


# ---------------------------------------------------------------- search
class GSearch(ic.Search):
    """The frozen forward enumerator plus: a CPU deadline, a table of goal vectors matched by hash against
    every kept top-level value, and backward goals for integer targets."""

    def __init__(self, lib, in_types, out_type, examples, deadline, consts=(), inv=None, accept=None,
                 max_cands=10 ** 12):
        super().__init__(lib, ic.uniform_costs(), in_types, out_type, examples, max_cands, consts=consts)
        self.deadline = deadline
        self.goals = {}
        self.inv = inv
        self.accept = accept
        self.by, self.nback = {}, 0
        self.types = (out_type,)
        self.goals[(out_type, self.target)] = self._root
        if inv is not None and out_type == T_L:
            self._chain()

    def _root(self, e):
        raise Done(("ast", e.ast()), "search")

    def _cand(self, ctx, p, kids, out):
        if not (self.n & 255) and time.process_time() > self.deadline:
            raise ic.Budget()
        ic.Search._cand(self, ctx, p, kids, out)

    def _keep(self, ctx, out, e, t):
        seen = ctx.seen[t]
        v = e.vec
        if v in seen:
            return
        seen.add(v)
        out.append(e)
        if ctx is not self.top:
            return
        if self.accept is not None:
            if t == self.out_type and self.accept(v):
                raise Done(("ast", e.ast()), "search")
            return
        h = self.goals.get((t, v))
        if h is not None:
            h(e)
        if t == T_I and self.out_type == T_I and self.inv is not None:
            self.by[v] = e
            if self.nback < 300:
                self.nback += 1
                self._backward(e)

    # -- structural decomposition of a list target with the derived inverse of cons
    def _chain(self):
        cons = self.inv.get("cons")
        if not cons or "alone" not in cons:
            return
        qh = ic.compile_ast(ic._tup(cons["alone"][0]), 1, self.lib)
        qt = ic.compile_ast(ic._tup(cons["alone"][1]), 1, self.lib)
        f = self.lib["cons"].f
        heads, tails, g = [], [], self.target
        while len(heads) < 16:
            try:
                h = tuple(qh((y,)) for y in g)
                t = tuple(qt((y,)) for y in g)
            except ic.Fail:
                break
            if any(f(a, b) != y for a, b, y in zip(h, t, g)):
                break
            heads.append(h)
            tails.append(t)
            g = t
        hs, ts = [None] * len(heads), [None] * len(tails)
        self.types = (T_L, T_I)

        def check():
            for k in range(len(heads)):
                if hs[k] is None:
                    return
                if ts[k] is not None:
                    ast = ts[k]
                    for j in range(k, -1, -1):
                        ast = ("cons", hs[j], ast)
                    raise Done(("ast", ast), "chain")

        def on(slots, ks):
            def h(e):
                ast = e.ast()
                for k in ks:
                    if slots[k] is None:
                        slots[k] = ast
                check()
            return h
        same = {}
        for k, h in enumerate(heads):
            if len(set(h)) == 1:
                hs[k] = ("k", h[0])                   # a constant read from the data
            else:
                same.setdefault(h, []).append(k)      # equal head vectors share one goal
        for h, ks in same.items():
            self.goals[(T_I, h)] = on(hs, ks)
        for k, t in enumerate(tails):
            self.goals[(T_L, t)] = on(ts, [k])

    # -- one backward step for an integer target: target = op(known, ?) with a derived inverse
    def _backward(self, e):
        g, v = self.target, e.vec
        if None in v:
            return
        for name, k, q in self.inv["_given_I"]:
            f = self.lib[name].f
            try:
                w = tuple(q((c, a)) for c, a in zip(g, v))
            except ic.Fail:
                continue
            if any((f(a, b) if k == 1 else f(b, a)) != c for a, b, c in zip(v, w, g)):
                continue
            ea = e.ast()

            def h(e2, name=name, k=k, ea=ea):
                raise Done(("ast", (name, ea, e2.ast()) if k == 1 else (name, e2.ast(), ea)), "inverse")
            if w in self.by:
                h(self.by[w])
            self.goals.setdefault((T_I, w), h)

    def run(self):
        self.levels = []                 # candidates evaluated when each cost level was completed
        try:
            for c in range(1, self.max_level + 1):
                for t in self.types:
                    self._pool(self.top, t, c)
                self.levels.append(self.n)
        except Done as d:
            return d.sol, d.via
        except ic.Budget:
            return None, None
        return None, None


# ------------------------------------------------------ operation generation
def _sample(t, rng):
    if t == T_I:
        return rng.randint(-2, 12)
    if t == T_B:
        return rng.random() < 0.5
    return tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 5)))


def _perturb(v, rng):
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + rng.choice([d for d in range(-12, 13) if d])
    r = rng.random()
    if r < 0.3 and v:
        return (v[0] + 1,) + v[1:]
    if r < 0.6 and v:
        return v[:1] + tuple(rng.randint(0, 9) for _ in range(rng.randint(0, 4)))
    if r < 0.8:
        return v + (rng.randint(0, 9),)
    return v[1:] if v else (rng.randint(0, 9),)


def derive_inverses(seed=0, budget=60000, log=None):
    """For every first-order primitive f and argument position k, pose `recover argument k` as a task on
    self-generated data and solve it with the system's own enumerator.

      alone: argument k from the output only;   given: argument k from the output and the other argument.

    Kept only if (1) f is injective in k on perturbation tests, (2) the search finds a program q with
    f(.., q, ..) == output wherever q is defined, (3) q is never wrong on fresh samples.  No task data."""
    lib = ic.base_library()
    out = {}
    for name in sorted(lib):
        p = lib[name]
        if p.kind != "fo" or p.arity not in (1, 2):
            continue
        for k in range(p.arity):
            rng = random.Random("%d:%s:%d" % (seed, name, k))
            pts, coll, tries = [], 0, 0
            while len(pts) < 220 and tries < 5000:
                tries += 1
                args = [_sample(t, rng) for t, _ in p.params]
                c = p.f(*args)
                if c is None:
                    continue
                hit = False
                for _ in range(20):
                    alt = list(args)
                    alt[k] = _perturb(args[k], rng)
                    if alt[k] != args[k] and p.f(*alt) == c:
                        hit = True
                        break
                coll += hit
                pts.append((args, c, hit))
            if len(pts) < 220 or coll > 0.3 * len(pts):
                continue
            clean = [(a, c) for a, c, hit in pts if not hit]
            train, fresh = clean[:12], clean[12:]
            for mode in (("alone", "given") if p.arity == 2 else ("alone",)):
                def view(a, c):
                    return (c,) if mode == "alone" else (c, a[1 - k])
                in_types = (p.ret,) if mode == "alone" else (p.ret, p.params[1 - k][0])

                def ok(vec, pts_):
                    bad = 0
                    for v, pt in zip(vec, pts_):
                        if v is None:
                            bad += 1
                        elif _reapply(p, k, pt, v) != pt[1]:
                            return False
                    return bad <= 2
                q, tr = None, list(train)
                for _ in range(4):                       # counterexample-guided: failures join the sample
                    s = GSearch(lib, in_types, p.params[k][0], [(view(a, c), a[k]) for a, c in tr],
                                time.process_time() + 3600, accept=lambda vec, tr=tr: ok(vec, tr),
                                max_cands=budget)
                    sol, _ = s.run()
                    if sol is None:
                        break
                    vec = tuple(ic.run_program(sol[1], lib, view(a, c)) for a, c in fresh)
                    wrong = [pt for v, pt in zip(vec, fresh) if v is not None and _reapply(p, k, pt, v) != pt[1]]
                    if not wrong and sum(v is None for v in vec) <= 0.2 * len(vec):
                        q = sol[1]
                        break
                    tr += (wrong or [pt for v, pt in zip(vec, fresh) if v is None])[:4]
                if q is None:
                    continue
                out.setdefault(name, {}).setdefault(mode, {})[str(k)] = q
                if log:
                    log("%s arg%d %s: %s  (candidates %d)" % (name, k, mode, ic.show(q), s.n))
    return out


def _reapply(p, k, pt, v):
    b = list(pt[0])
    b[k] = v
    return p.f(*b)


def load_inverses(path=INVERSES):
    """Compiled form of the derived table: {'cons': {'alone': (q_head, q_tail)}, '_given_I': [(op, k, fn)]}."""
    raw = json.loads(pathlib.Path(path).read_text())["inverses"]
    lib = ic.base_library()
    inv = {"_given_I": []}
    for name, modes in raw.items():
        p = lib[name]
        al = modes.get("alone", {})
        if p.arity == 2 and len(al) == 2:
            inv[name] = {"alone": (al["0"], al["1"])}
        if p.ret == T_I and p.arity == 2 and all(t == T_I for t, _ in p.params):
            for k, q in sorted(modes.get("given", {}).items()):
                inv["_given_I"].append((name, int(k), ic.compile_ast(ic._tup(q), 2, lib)))
    return inv


# ------------------------------------------------------------ traversal state
def zstate(x, j):
    return (x[j], j, len(x) - 1 - j, x[:j][::-1], x[j + 1:], x)


def _embed(x, y, left=True):
    """Keep-labels of x that spell y (leftmost or rightmost embedding), or None."""
    keep = [False] * len(x)
    if left:
        i = 0
        for j, v in enumerate(x):
            if i < len(y) and v == y[i]:
                keep[j] = True
                i += 1
        return keep if i == len(y) else None
    i = len(y) - 1
    for j in range(len(x) - 1, -1, -1):
        if i >= 0 and x[j] == y[i]:
            keep[j] = True
            i -= 1
    return keep if i < 0 else None


def _pick(points, cap=SUB_CAP):
    """Deterministic subset: both edges of every example first, moving inwards, round-robin over examples."""
    if len(points) <= cap:
        return list(points)
    by = {}
    for pt in points:
        by.setdefault(pt[0], []).append(pt)
    ranks = {i: sorted(v, key=lambda pt: (min(pt[1] - v[0][1], v[-1][1] - pt[1]), pt[1])) for i, v in by.items()}
    order, depth = [], 0
    while len(order) < cap:
        added = False
        for i in sorted(ranks):
            if depth < len(ranks[i]) and len(order) < cap:
                order.append(ranks[i][depth])
                added = True
        if not added:
            break
        depth += 1
    return order


def subtasks(task):
    """Re-representations of a task whose state is fully observable in the examples."""
    train, out = task["train"], []
    ins, ot = tuple(task["in_types"]), task["out_type"]
    if ins == (T_L,) and ot == T_L:
        xs, ys = [i[0] for i, _ in train], [o for _, o in train]
        if all(len(x) == len(y) for x, y in zip(xs, ys)) and any(xs):
            pts = [(i, j, zstate(x, j), y[j]) for i, (x, y) in enumerate(zip(xs, ys)) for j in range(len(x))]
            out.append({"kind": "zmap", "in_types": Z_TYPES, "out_type": T_I, "points": pts})
        elif all(len(y) <= len(x) for x, y in zip(xs, ys)):
            seen = []
            for left in (True, False):
                ks = [_embed(x, y, left) for x, y in zip(xs, ys)]
                if any(k is None for k in ks) or ks in seen:
                    continue
                seen.append(ks)
                pts = [(i, j, zstate(x, j), ks[i][j]) for i, x in enumerate(xs) for j in range(len(x))]
                out.append({"kind": "zfilter", "in_types": Z_TYPES, "out_type": T_B, "points": pts})
    elif ins == (T_I,) and ot == T_I and len(train) >= 8:
        ns, ys = [i[0] for i, _ in train], [o for _, o in train]
        if all(b - a == 1 for a, b in zip(ns, ns[1:])):
            pts = [(0, j, (ns[j], tuple(ys[:j][::-1])), ys[j]) for j in range(3, len(ys))]
            out.append({"kind": "rec", "in_types": (T_I, T_L), "out_type": T_I, "points": pts})
    return out


def run_solution(sol, lib, inputs, train):
    """Executes a solution on one input.  None = failure."""
    kind = sol[0]
    if kind == "ast":
        return ic.run_program(sol[1], lib, inputs)
    body = sol[1]
    if kind == "rec":
        ns, ys = [i[0] for i, _ in train], [o for _, o in train]
        n = inputs[0]
        if n < ns[0] or n - ns[0] > 4 * len(ns):
            return None
        hist = list(ys)
        while len(hist) <= n - ns[0]:
            v = ic.run_program(body, lib, (ns[0] + len(hist), tuple(hist[::-1])))
            if v is None:
                return None
            hist.append(v)
        return hist[n - ns[0]]
    x, res = inputs[0], []
    for j in range(len(x)):
        v = ic.run_program(body, lib, zstate(x, j))
        if v is None:
            return None
        if kind == "zmap":
            res.append(v)
        elif v:
            res.append(x[j])
    return tuple(res)


def show(sol):
    if sol is None:
        return None
    return ic.show(sol[1]) if sol[0] == "ast" else "<%s e=$0 j=$1 r=$2 pre=$3 suf=$4 x=$5 | %s>" % (
        sol[0], ic.show(sol[1])) if sol[0] != "rec" else "<rec n=$0 hist=$1 | %s>" % ic.show(sol[1])


# -------------------------------------------------------------------- solve
ARMS = {            # (traversal state, derived inverse operators)
    "A": (False, False),                    # the frozen forward enumerator under the same CPU cap
    "S": (True, True),
    "S_no_state": (False, True),
    "S_no_inverse": (True, False),
}


def solve(task, cap_s, arm="S", inv=None):
    """One task, one arm, one CPU cap (seconds of process CPU, everything included)."""
    c0, w0 = time.process_time(), ic.WORK[0]
    deadline = c0 + cap_s
    use_state, use_inv = ARMS[arm]
    lib = ic.base_library()
    train = task["train"]
    consts = ic.data_constants(train)
    sol, via, cands, levels = None, None, 0, None
    if use_state:
        subs = subtasks(task)
        for st in subs:
            pts = _pick(st["points"])
            end = min(deadline, time.process_time() + SUB_SHARE * cap_s / len(subs))
            for _ in range(4):                 # counterexample-guided: steps the body gets wrong join the sample
                s = GSearch(lib, st["in_types"], st["out_type"], [(p[2], p[3]) for p in pts], end, consts=consts)
                got, _ = s.run()
                cands += s.n
                if got is None:
                    break
                cand = (st["kind"], got[1])
                if all(run_solution(cand, lib, i, train) == o for i, o in train):
                    sol, via = cand, st["kind"]
                    break
                bad = [p for p in st["points"] if p not in pts and ic.run_program(got[1], lib, p[2]) != p[3]]
                if not bad or time.process_time() > end:
                    break
                pts = pts + bad[:8]
            if sol is not None:
                break
    if sol is None:
        s = GSearch(lib, task["in_types"], task["out_type"], train, deadline, consts=consts,
                    inv=inv if use_inv else None)
        sol, via = s.run()
        cands += s.n
        levels = s.levels
    ok = sol is not None and all(run_solution(sol, lib, i, train) == o for i, o in task["test"])
    return {"fit": sol is not None, "solved": bool(ok), "via": via, "candidates": cands,
            "sol": sol, "program": show(sol), "size": ic.size(sol[1]) + (sol[0] != "ast") if sol else None,
            "levels": levels, "cpu_seconds": round(time.process_time() - c0, 4), "work": ic.WORK[0] - w0}
