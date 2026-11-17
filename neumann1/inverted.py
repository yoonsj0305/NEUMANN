"""Inverted inventions (development; nothing here is evidence).

SECOND showed that an invented operation used FORWARD, as one more primitive of generate-and-test, adds nothing.
THIRD showed that an operation used BACKWARD, through its inverse, removes most of the search.
This module joins the two: every operation the system invented from experience is tested, on self-generated
data, for recoverability of each argument from the result; a recoverable argument turns the invention into a
decomposition operator on goals.  Goals are decomposed recursively (derived inverse of cons, inverses of
inventions), and every sub-goal is matched by hash against the forward bank as it grows.

Nothing names a problem family.  The inventions themselves come from experience (a `spec` learned on SOURCE);
with `ops={}` the same search runs with primitive inverses only: that is the causal control for the inventions.
"""
from __future__ import annotations
import random, time
from neumann1 import invention_core as ic, spec_core as sc

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L


def sublists(c):
    return {c[i:j] for i in range(len(c) + 1) for j in range(i, len(c) + 1)}


def universe(t, c, others):
    """Candidate values of an unknown argument, read off the result and the known arguments."""
    if t == T_L:
        return sublists(c) if isinstance(c, tuple) else set()
    vals = set(range(-2, 13))
    for v in (c,) + tuple(others):
        if isinstance(v, tuple):
            vals.update(v)
            vals.add(len(v))
        elif not isinstance(v, bool):
            vals.add(v)
    return vals


def _apply(vf, k, u, a):
    try:
        return vf((u, a) if k == 0 else (a, u))
    except ic.Fail:
        return None


def derive_op_inverses(spec, seed=0, samples=300):
    """{name: [k, ...]}: binary first-order inventions and the argument positions that are recoverable from
    (result, other argument) by search over the universe, on self-generated samples.  No task data."""
    lib = ic.library_from_spec(spec)
    out = {}
    for name, ret, params, _ in spec:
        p = lib[name]
        if not p.first_order() or p.arity != 2 or ret == T_B:
            continue
        vf = p.value_fn()
        for k in (0, 1):
            rng = random.Random("%d:%s:%d" % (seed, name, k))
            tot = ok = 0
            for _ in range(samples):
                args = [sc._sample(t, rng) for t, _ in p.params]
                try:
                    c = vf(tuple(args))
                except ic.Fail:
                    continue
                tot += 1
                sols = [u for u in universe(p.params[k][0], c, [args[1 - k]]) if _apply(vf, k, u, args[1 - k]) == c]
                ok += sols == [args[k]]
            if tot >= 50 and ok >= 0.7 * tot:
                out.setdefault(name, []).append(k)
    return out


class RSearch(sc.GSearch):
    """Forward enumeration + a recursive goal graph.  `ops` = {invention: recoverable argument positions}."""

    def __init__(self, lib, in_types, out_type, examples, deadline, consts, inv, ops, lib_ops,
                 max_goals=400, max_depth=3):
        super().__init__(lib, in_types, out_type, examples, deadline, consts=consts, inv=None)
        self.inv, self.ops, self.lib_ops = inv, ops, lib_ops
        self.max_goals, self.max_depth = max_goals, max_depth
        self.bank = {T_I: {}, T_L: {}}
        self.cbs, self.solved, self.open = {}, {}, []
        self.direct = False
        if out_type == T_L:
            self.types = (T_L, T_I)
        cons = inv.get("cons") if inv else None
        self.qh = ic.compile_ast(ic._tup(cons["alone"][0]), 1, lib) if cons else None
        self.qt = ic.compile_ast(ic._tup(cons["alone"][1]), 1, lib) if cons else None
        self.goals = {}

        def root(ast):
            names = set()

            def walk(a):
                if a[0] not in ("v", "k"):
                    names.add(a[0])
                    for c in a[1:]:
                        walk(c)
            walk(ast)
            via = "search" if self.direct else "inverted" if names & set(self.ops) else "chain"
            raise sc.Done(("ast", ast), via)
        self.add_goal(out_type, self.target, 0, root)

    # ---- goal graph
    def add_goal(self, t, vec, depth, cb):
        key = (t, vec)
        if key in self.solved:
            cb(self.solved[key])
            return
        if key in self.cbs:
            self.cbs[key].append(cb)
            return
        self.cbs[key] = [cb]
        if t == T_I and len(set(vec)) == 1 and depth > 0:
            self.finish(key, ("k", vec[0]))          # a constant read from the data
            return
        if vec in self.bank.get(t, ()):
            self.finish(key, self.bank[t][vec])
            return
        if t == T_L and len(self.cbs) < self.max_goals:
            self.expand(key, depth)

    def finish(self, key, ast):
        if key in self.solved:
            return
        self.solved[key] = ast
        for cb in self.cbs.pop(key, []):
            cb(ast)

    def expand(self, key, depth):
        g = key[1]
        if self.qh is not None:                      # derived inverse of cons: head goal AND tail goal
            try:
                h = tuple(self.qh((y,)) for y in g)
                t = tuple(self.qt((y,)) for y in g)
            except ic.Fail:
                h = None
            if h is not None:
                part = [None, None]

                def got(i):
                    def cb(ast):
                        part[i] = ast
                        if part[0] is not None and part[1] is not None:
                            self.finish(key, ("cons", part[0], part[1]))
                    return cb
                self.add_goal(T_I, h, max(depth, 1), got(0))
                self.add_goal(T_L, t, max(depth, 1), got(1))
        if self.ops and depth < self.max_depth:
            U = [sublists(y) for y in g]
            self.open.append((key, depth, U))
            for vec, ast in list(self.bank[T_L].items()):
                self.try_ops(key, depth, U, vec, ast)

    def try_ops(self, key, depth, U, kv, kast):
        """The known value must be a sub-value of the goal on every example (hash test); then every recoverable
        argument of every invention is solved for by search over the universe."""
        g = key[1]
        if kv == g or key in self.solved or not all(a in u for a, u in zip(kv, U)):
            return
        for name, ks in self.ops.items():
            p = self.lib_ops[name]
            if p.ret != T_L:
                continue
            vf = p.value_fn()
            for k in ks:
                if p.params[1 - k][0] != T_L or p.params[k][0] != T_L:
                    continue
                w = []
                for gi, ai in zip(g, kv):
                    c = [u for u in U[len(w)] if _apply(vf, k, u, ai) == gi]
                    if len(c) != 1:
                        break
                    w.append(c[0])
                if len(w) != len(g) or tuple(w) == g:
                    continue

                def cb(ast, name=name, k=k):
                    self.finish(key, (name, ast, kast) if k == 0 else (name, kast, ast))
                self.add_goal(T_L, tuple(w), depth + 1, cb)

    def _keep(self, ctx, out, e, t):
        seen = ctx.seen[t]
        v = e.vec
        if v in seen:
            return
        seen.add(v)
        out.append(e)
        if ctx is not self.top or t == T_B or None in v:
            return
        ast = e.ast()
        self.bank[t][v] = ast
        if (t, v) in self.cbs:
            self.direct = v == self.target and t == self.out_type
            self.finish((t, v), ast)
        if t == T_L and self.open:
            for key, depth, U in self.open:
                self.try_ops(key, depth, U, v, ast)


def solve(task, cap_s, inv, spec=(), ops=None, state=True):
    """The THIRD pipeline with the recursive goal graph in the direct phase.  `ops=None`: derive from `spec`;
    `ops={}`: primitive inverses only (control)."""
    c0 = time.process_time()
    deadline = c0 + cap_s
    lib = ic.base_library()
    lib_ops = ic.library_from_spec(spec)
    if ops is None:
        ops = derive_op_inverses(spec)
    train = task["train"]
    consts = ic.data_constants(train)
    sol, via, cands = None, None, 0
    if state:
        subs = sc.subtasks(task)
        for st in subs:
            pts = sc._pick(st["points"])
            end = min(deadline, time.process_time() + sc.SUB_SHARE * cap_s / len(subs))
            for _ in range(4):
                s = sc.GSearch(lib, st["in_types"], st["out_type"], [(p[2], p[3]) for p in pts], end, consts=consts)
                got, _v = s.run()
                cands += s.n
                if got is None:
                    break
                cand = (st["kind"], got[1])
                if all(sc.run_solution(cand, lib, i, train) == o for i, o in train):
                    sol, via = cand, st["kind"]
                    break
                bad = [p for p in st["points"] if p not in pts and ic.run_program(got[1], lib, p[2]) != p[3]]
                if not bad or time.process_time() > end:
                    break
                pts = pts + bad[:8]
            if sol is not None:
                break
    if sol is None:
        if task["out_type"] == T_L:
            s = RSearch(lib, task["in_types"], task["out_type"], train, deadline, consts, inv, ops, lib_ops)
        else:
            s = sc.GSearch(lib, task["in_types"], task["out_type"], train, deadline, consts=consts, inv=inv)
        sol, via = s.run()
        cands += s.n
        if sol is not None:                          # inventions are expanded: the method is a substrate program
            sol = ("ast", ic.inline(sol[1], len(task["in_types"]), lib_ops))
    ok = sol is not None and all(sc.run_solution(sol, lib, i, train) == o for i, o in task["test"])
    fit = sol is not None and all(sc.run_solution(sol, lib, i, train) == o for i, o in train)
    return {"fit": bool(fit), "solved": bool(ok and fit), "via": via, "candidates": cands, "sol": sol,
            "program": sc.show(sol), "size": ic.size(sol[1]) + (sol[0] != "ast") if sol else None,
            "cpu_seconds": round(time.process_time() - c0, 4)}
