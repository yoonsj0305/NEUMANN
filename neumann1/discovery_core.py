"""NEUMANN 1 discovery core (development).  Nothing here is evidence for any gate.

Purpose (owner's directive of 2026-11-12): make the DISCOVERY POLICY the learned object.  The THIRD
specification-space core stays as an execution/verification mechanism; its fixed schedule is not counted as
learned invention.

Typed, family-agnostic interface
  observation    a task = typed examples; a per-point specification derived from it (`spec_core.subtasks`)
  hypothesis     (kind, strategy, scope): how the specification is re-represented
                   kind      direct | zmap | zfilter | rec      (alignment relation read from the examples)
                   strategy  body     the step operator over the full observable state
                             feature  a LATENT state variable = a function of a strict subset of the state
                                      (scope), combined with the rest by one shallow readout
  method         an executable program (substrate AST, or kind + step-operator AST) with typed inputs/outputs;
                 it fails (None) outside its domain
  verification   the method reproduces every TRAIN example; a mismatch is a counterexample
  counterexample a point the hypothesis gets wrong; it joins the sample and the search resumes
  policy update  `fit(experience)`: which hypotheses verified, and what verified methods look like

The base proposer (this file, `solve`) generates and tests hypotheses.  The POLICY decides how the CPU cap is
divided among hypotheses and in which order each generator proposes programs.  An untrained policy is uniform
on both.  Nothing in the proposer or the policy names a problem family: contexts are keyed by types and by the
alignment relation only.
"""
from __future__ import annotations
import time
from neumann1 import invention_core as ic, spec_core as sc

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
SUB_SHARE = 0.4           # as in spec_core: share of the cap for per-point hypotheses, before the direct search


class Refuted(Exception):
    """A candidate passed the sample and failed elsewhere: its counterexamples."""

    def __init__(self, bad):
        self.bad = bad


class Policy:
    """Everything the discovery policy knows.  Policy() is the untrained policy."""

    def __init__(self, costs=None, weights=None, memory=None):
        self.costs = costs or {}          # context -> {symbol: bits}; absent = uniform order
        self.weights = weights or {}      # hypothesis -> expected usefulness; absent = 1 (uniform)
        self.memory = memory or []        # verified methods of earlier tasks: (kind, ast, in_types, out_type)
        self.default = 0.5 if self.weights else 1.0     # a hypothesis the policy has no experience with

    def cost(self, *ctx):
        for k in (ctx, ctx[:1]):
            if k in self.costs:
                return ic._as_cost(self.costs[k])
        return ic.uniform_costs()

    def weight(self, hyp):
        return self.weights.get(hyp, self.default)


def scopes(in_types):
    """Strict subsets of the state on which a latent feature may depend: every single component, and the first
    integer component paired with every list component.  Types and positions only."""
    L = [i for i, t in enumerate(in_types) if t == T_L]
    I = [i for i, t in enumerate(in_types) if t == T_I]
    out = [(i,) for i in range(len(in_types)) if in_types[i] in (T_I, T_L)]
    if I and len(in_types) > 2:
        out += [(I[0], l) for l in L]
    return [s for s in out if len(s) < len(in_types)]


def _remap(ast, scope, n_full):
    h = ast[0]
    if h == "v":
        return ("v", scope[ast[1]]) if ast[1] < len(scope) else ("v", ast[1] - len(scope) + n_full)
    if h == "k":
        return ast
    return (h,) + tuple(_remap(c, scope, n_full) for c in ast[1:])


class FSearch(sc.GSearch):
    """Enumerates functions of a state subset; every kept total value is offered to the readout."""

    def __init__(self, lib, in_types, inputs, deadline, consts, cost, types, offer):
        super().__init__(lib, in_types, T_I, [(i, 0) for i in inputs], deadline, consts=consts)
        self.cost, self.types, self.offer, self.goals = cost, types, offer, {}

    def _keep(self, ctx, out, e, t):
        seen = ctx.seen[t]
        v = e.vec
        if v in seen:
            return
        seen.add(v)
        out.append(e)
        if ctx is self.top and e.hv and t in self.types and None not in v:
            self.offer(e, t)


def feature_search(lib, inv, st, pts, scope, end, consts, cost):
    """Latent feature of `scope` + one shallow readout.  Returns (body AST over the full state, feature AST
    over the scope, candidates) or (None, None, candidates).  Readouts are generated from the library by type,
    not listed by hand: integer goals through the DERIVED inverses, boolean goals through every binary integer
    predicate.  `pts` screens candidates; a candidate that passes is confirmed on EVERY point of the
    specification.  If it fails there, the failing points are counterexamples: they join the sample and the
    enumeration restarts, because the sample could not tell the candidate from the programs behind it."""
    pts, total = list(pts), 0
    while True:
        try:
            body, feat, k = _feature_round(lib, inv, st, pts, scope, end, consts, cost)
            return body, feat, total + k
        except Refuted as r:
            total += r.k
            fresh = [p for p in r.bad if p not in pts]
            if not fresh or time.process_time() > end:
                return None, None, total
            pts += fresh[:8]


def _feature_round(lib, inv, st, pts, scope, end, consts, cost):
    types = st["in_types"]
    n = len(types)
    g = tuple(p[3] for p in pts)
    col = lambda i: tuple(p[2][i] for p in pts)
    knowns = [(("v", i), col(i)) for i, t in enumerate(types) if t == T_I]
    knowns += [(("k", c), (c,) * len(pts)) for c in sorted(set(range(3)) | set(consts))]
    for p in lib.values():                       # unary integer observations of a list component, e.g. head
        if p.kind == "fo" and p.arity == 1 and p.ret == T_I:
            for i, t in enumerate(types):
                if t == p.params[0][0]:
                    vec = p.vf(col(i))
                    if None not in vec:
                        knowns.append(((p.name, ("v", i)), vec))
    out_t = st["out_type"]
    if out_t == T_I:
        table = {g: None}
        for name, k, q in inv["_given_I"]:
            f = lib[name].f
            for ast, v in knowns:
                try:
                    w = tuple(q((c, a)) for c, a in zip(g, v))
                except ic.Fail:
                    continue
                if all((f(a, b) if k == 1 else f(b, a)) == c for a, b, c in zip(v, w, g)):
                    table.setdefault(w, (name, k, ast))
        ftypes = (T_I,)
    else:
        ng = tuple(not b for b in g)
        preds = [p for p in lib.values() if p.kind == "fo" and p.ret == T_B and p.arity == 2
                 and all(t == T_I for t, _ in p.params)]
        ftypes = (T_B, T_I)          # a boolean feature needs no readout: it comes first at each level

    def confirm(body, e):
        fn = ic.compile_ast(body, n, lib)
        bad = []
        for p in st["points"]:
            try:
                ok = fn(p[2]) == p[3]
            except ic.Fail:
                ok = False
            if not ok:
                bad.append(p)
        if bad:
            raise Refuted(bad)
        raise sc.Done(("ast", body), e.ast())

    def offer(e, t):
        v = e.vec
        if out_t == T_I:
            if v in table:
                r = table[v]
                f = _remap(e.ast(), scope, n)
                confirm(f if r is None else ((r[0], r[2], f) if r[1] == 1 else (r[0], f, r[2])), e)
            return
        if t == T_B:
            if v == g or v == ng:
                f = _remap(e.ast(), scope, n)
                confirm(f if v == g else ("not", f), e)
            return
        for p in preds:
            pf = p.f
            for ast, kv in knowns:
                for a, b, swap in ((v, kv, False), (kv, v, True)):
                    r = tuple([pf(x, y) for x, y in zip(a, b)])
                    if r == g or r == ng:
                        f = _remap(e.ast(), scope, n)
                        body = (p.name, ast, f) if swap else (p.name, f, ast)
                        confirm(body if r == g else ("not", body), e)
    s = FSearch(lib, tuple(types[i] for i in scope), [tuple(p[2][i] for i in scope) for p in pts], end, consts,
                cost, ftypes, offer)
    try:
        sol, feat = s.run()
    except Refuted as r:
        r.k = s.n
        raise
    return (sol[1], feat, s.n) if sol is not None else (None, None, s.n)


def solve(task, cap_s, policy, inv, features=True, replay=True, log=None):
    """One task under one policy and one CPU cap.  `features=False, policy=Policy()` is the THIRD core."""
    c0, w0 = time.process_time(), ic.WORK[0]
    deadline = c0 + cap_s
    lib = ic.base_library()
    train = task["train"]
    consts = ic.data_constants(train)
    sig = ic.sig_key(task)
    sol, via, cands, tried = None, None, 0, []
    subs = sc.subtasks(task)

    def check(cand):
        return all(sc.run_solution(cand, lib, i, train) == o for i, o in train)
    if replay:                                  # verified methods of earlier tasks, re-verified on this one
        for kind, ast, in_types, out_type in policy.memory:
            if kind == "ast":
                ok = (tuple(in_types) == tuple(task["in_types"]) and out_type == task["out_type"]
                      and check((kind, ast)))
            else:                               # a step operator must reproduce every supervised point
                ok = any(st["kind"] == kind and all(ic.run_program(ast, lib, p[2]) == p[3] for p in st["points"])
                         for st in subs)
            if ok:
                sol, via = (kind, ast), "memory"
                break
    if sol is None:
        hyps = []
        for st in subs:
            hyps.append((st, "body", ()))
            if features:
                hyps += [(st, "feature", sc_) for sc_ in scopes(st["in_types"])]
        key = lambda h: (h[0]["kind"], h[1], h[2])
        order = sorted(range(len(hyps)), key=lambda i: (-policy.weight(key(hyps[i])), i))
        sub_end = c0 + SUB_SHARE * cap_s
        for n, i in enumerate(order):
            st, strat, scope = hyps[i]
            now = time.process_time()
            if now >= sub_end:
                break
            rest = sum(policy.weight(key(hyps[j])) for j in order[n:])
            end = min(sub_end, now + (sub_end - now) * policy.weight(key(hyps[i])) / rest)
            pts = sc._pick(st["points"])
            got, feat = None, None
            for _ in range(4):                  # counterexample-guided: wrong points join the sample
                if strat == "body":
                    s = sc.GSearch(lib, st["in_types"], st["out_type"], [(p[2], p[3]) for p in pts], end, consts=consts)
                    s.cost = policy.cost("body", st["kind"])
                    r, _ = s.run()
                    cands += s.n
                    body, feat = (r[1] if r is not None else None), None
                else:
                    body, feat, k = feature_search(lib, inv, st, pts, scope, end, consts,
                                                   policy.cost("feature", st["kind"]))
                    cands += k
                if body is None:
                    break
                if check((st["kind"], body)):
                    got = body
                    break
                bad = [p for p in st["points"] if p not in pts and ic.run_program(body, lib, p[2]) != p[3]]
                if not bad or time.process_time() > end:
                    break
                pts = pts + bad[:8]
            tried.append({"hyp": [st["kind"], strat, list(scope)], "ok": got is not None,
                          "cpu": round(time.process_time() - now, 4)})
            if got is not None:
                sol, via = (st["kind"], got), st["kind"] + ("+feature" if strat == "feature" else "")
                tried[-1].update(body=got, feature=feat, scope_types=[st["in_types"][j] for j in scope],
                                 in_types=list(st["in_types"]))
                break
    levels = None
    if sol is None:
        s = sc.GSearch(lib, task["in_types"], task["out_type"], train, deadline, consts=consts, inv=inv)
        s.cost = policy.cost("direct", sig)
        sol, via = s.run()
        cands += s.n
        levels = s.levels
        tried.append({"hyp": ["direct", "body", []], "ok": sol is not None})
    ok = sol is not None and all(sc.run_solution(sol, lib, i, train) == o for i, o in task["test"])
    return {"fit": sol is not None, "solved": bool(ok), "via": via, "candidates": cands, "sol": sol,
            "program": sc.show(sol), "size": ic.size(sol[1]) + (sol[0] != "ast") if sol else None,
            "tried": tried, "levels": levels,
            "cpu_seconds": round(time.process_time() - c0, 4), "work": ic.WORK[0] - w0}


def fit(experience, lib=None):
    """Policy update from verified experience.  experience: rows of `solve` (with `sol`, `tried`, task types).
    Only what the system verified itself on TRAIN examples is used; hidden tests never reach the policy.
      weights  smoothed success rate of each hypothesis (kind, strategy, scope) over the tasks where it ran
      costs    description lengths of the symbols of verified methods, per context:
                 ("body", kind)      step operators of that alignment kind
                 ("feature", kind)   latent features of that kind, pooled with all verified step operators
                 ("direct", sig)     direct programs of that type signature
      memory   the verified methods themselves (used only by arms that have memory)."""
    lib = lib or ic.base_library()
    att, suc, bodies, feats, direct, memory = {}, {}, {}, {}, {}, []
    for r in experience:
        for t in r["tried"]:
            k = (t["hyp"][0], t["hyp"][1], tuple(t["hyp"][2]))
            att[k] = att.get(k, 0) + 1
            if t["ok"]:
                suc[k] = suc.get(k, 0) + 1
                if "body" in t:
                    bodies.setdefault(k[0], []).append((ic._tup(t["body"]), tuple(t["in_types"])))
                    if t.get("feature") is not None:
                        feats.setdefault(k[0], []).append((ic._tup(t["feature"]), tuple(t["scope_types"])))
        if r["sol"] is not None:
            kind, ast = r["sol"][0], ic._tup(r["sol"][1])
            memory.append((kind, ast, tuple(r["in_types"]), r["out_type"]))
            if kind == "ast":
                direct.setdefault(r["sig"], []).append((ast, tuple(r["in_types"])))
    weights = {k: (suc.get(k, 0) + 0.5) / (n + 1.0) for k, n in att.items()}
    costs = {}
    pooled = [b for bs in bodies.values() for b in bs]
    for kind, bs in bodies.items():
        costs[("body", kind)] = ic.learn_costs(bs, lib)
    for kind in set(bodies) | set(feats):
        costs[("feature", kind)] = ic.learn_costs(feats.get(kind, []) + pooled, lib)
    for sig, ds in direct.items():
        costs[("direct", sig)] = ic.learn_costs(ds, lib)
    return Policy(costs, weights, memory)
