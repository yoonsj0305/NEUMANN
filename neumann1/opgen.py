"""Failure-derived operation generation (development, SOURCE only; nothing here is evidence).

For a task the existing system fails on, the system itself
  1. proposes the FUNCTION AND TYPE of an operation it lacks: a gap specification
        (available pieces) -> (an open goal),
     where the pieces are the cheapest forward values of the context (or what is left of a list goal after an
     embedded piece is removed) and the goal is the task's target, an unsolved sub-goal of the goal graph, or
     the per-point target of a traversal sub-specification;
  2. synthesises an executable definition over the pieces alone (the task input is not visible, so the
     definition is a function of its arguments);
  3. checks the definition on self-generated arguments: defined often enough, not constant, not a projection,
     and records its behaviour there (the signature that identifies the operation across tasks);
  4. tests on self-generated data which arguments are recoverable from the result (`inverted`): a recoverable
     argument makes the operation a decomposition operator;
  5. keeps an operation only if gaps of at least two DIFFERENT tasks produced it (`select`).
No operation is written by hand and nothing names a problem family.  Vocabulary: the substrate plus `len`,
which the system derived earlier as the inverse of `range`.
"""
from __future__ import annotations
import hashlib, json, pathlib, random, time
from neumann1 import invention_core as ic, spec_core as sc, inverted as iv, discovery_core as dc

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
N_L, N_I = 6, 8                 # pieces per type
SPEC_S = 0.25                   # CPU seconds per gap specification
MAX_SPECS = 12                  # per goal
TESTS = 24                      # self-generated arguments per operation
MIN_SUPPORT = 2
MAX_OPS = 8


def seed_spec():
    raw = json.loads(pathlib.Path(sc.INVERSES).read_text())["inverses"]
    return [("len", T_I, [(T_L, [])], ic._to_body(ic._tup(raw["range"]["alone"]["0"]), 1))]


def _vars(ast, n, acc):
    if ast[0] == "v":
        if ast[1] < n:
            acc.add(ast[1])
    elif ast[0] != "k":
        for c in ast[1:]:
            _vars(c, n, acc)
    return acc


def _swap(ast):
    if ast[0] == "v":
        return ("v", 1 - ast[1]) if ast[1] < 2 else ast
    if ast[0] == "k":
        return ast
    return (ast[0],) + tuple(_swap(c) for c in ast[1:])


def _drop_unused(ast, keep):
    """Re-index a two-argument definition that uses only argument `keep` as a one-argument definition."""
    if ast[0] == "v":
        return ("v", 0) if ast[1] == keep else ("v", ast[1] - 1) if ast[1] >= 2 else ast
    if ast[0] == "k":
        return ast
    return (ast[0],) + tuple(_drop_unused(c, keep) for c in ast[1:])


def signature(ast, arg_types, lib):
    """Behaviour on self-generated arguments (fixed per type signature), or None if the definition is trivial."""
    rng = random.Random("opgen:" + "".join(arg_types))
    tests = [tuple(sc._sample(t, rng) for t in arg_types) for _ in range(TESTS)]
    out = tuple(ic.run_program(ast, lib, a) for a in tests)
    defined = [o for o in out if o is not None]
    if len(defined) < TESTS // 2 or len(set(defined)) < 2:
        return None
    for k in range(len(arg_types)):
        if all(o is None or o == a[k] for o, a in zip(out, tests)):
            return None
    return out


def canonical(ast, arg_types, lib):
    """(key, ast, arg_types) with a canonical argument order, or None.  Unused arguments are dropped."""
    used = sorted(_vars(ast, len(arg_types), set()))
    if not used or ic.size(ast) < 4:
        return None
    if len(arg_types) == 2 and len(used) == 1:
        ast, arg_types = _drop_unused(ast, used[0]), (arg_types[used[0]],)
    cands = [(ast, tuple(arg_types))]
    if len(arg_types) == 2:
        cands.append((_swap(ast), tuple(arg_types[::-1])))
    best = None
    for a, ts in cands:
        sig = signature(a, ts, lib)
        if sig is None:
            return None
        key = (ts, repr(sig))
        if best is None or key < best[0]:
            best = (key, a, ts)
    return best


def _pieces(lib, in_types, inputs, consts, deadline):
    """Cheapest total forward values of a context, by type: [(program, vector)]."""
    got = {T_L: [], T_I: []}
    n = len(inputs)
    for l, t in enumerate(in_types):
        if t in got:
            got[t].append((("v", l), tuple(i[l] for i in inputs)))
    for c in sorted(set(range(4)) | set(consts)):
        got[T_I].append((("k", c), (c,) * n))
    seen = {T_L: {v for _, v in got[T_L]}, T_I: {v for _, v in got[T_I]}}
    cap = {T_L: N_L, T_I: N_I + len(got[T_I])}

    def offer(e, t):
        if e.vec not in seen[t] and len(got[t]) < cap[t]:
            seen[t].add(e.vec)
            got[t].append((e.ast(), e.vec))
        if all(len(got[k]) >= cap[k] for k in got):
            raise sc.Done(None, None)
    dc.FSearch(lib, tuple(in_types), inputs, deadline, consts, ic.uniform_costs(), (T_L, T_I), offer).run()
    return got


def _score(p, g):
    """How much of the goal's material a piece carries (shared elements), per example."""
    s = 0
    for a, b in zip(p, g):
        ea = set(a) if isinstance(a, tuple) else {a}
        eb = set(b) if isinstance(b, tuple) else {b}
        s += bool(ea & eb)
    return s


def _specs(pieces, g, gt):
    """Gap specifications for one goal: [(piece programs, argument types, argument vectors)]."""
    out = []
    if gt == T_L:                           # what is left of the goal after an embedded piece is removed
        for past, pv in pieces[T_L]:
            for front in (True, False):
                rem = []
                for a, y in zip(pv, g):
                    if len(a) == 0 or len(a) >= len(y) or (y[:len(a)] if front else y[len(y) - len(a):]) != a:
                        break
                    rem.append(y[len(a):] if front else y[:len(y) - len(a)])
                if len(rem) == len(g):
                    out.append(((past, None), (T_L, T_L), (pv, tuple(rem))))
    ranked = sorted(((-_score(v, g), i, t, a, v) for t in (T_L, T_I) for i, (a, v) in enumerate(pieces[t])))
    top = ranked[:7]
    for x in range(len(top)):
        for y in range(len(top)):
            if x != y:
                _, _, tp, ap, vp = top[x]
                _, _, tq, aq, vq = top[y]
                out.append(((ap, aq), (tp, tq), (vp, vq)))
    return out[:MAX_SPECS]


def gaps(task, inv, cap_s, lib=None):
    """Operations synthesised from the gaps of one failed task: [{key, ast, arg_types, ret, where, ...}]."""
    c0 = time.process_time()
    end = c0 + cap_s
    lib = lib or ic.library_from_spec(seed_spec())
    train = task["train"]
    consts = ic.data_constants(train)
    contexts = []
    s = iv.RSearch(lib, task["in_types"], task["out_type"], train, c0 + 0.08 * cap_s, consts, inv, {}, lib)
    if s.run()[0] is not None:
        return [], {"specs": 0, "cpu_seconds": round(time.process_time() - c0, 3), "solved": True}
    open_goals = [k for k in s.cbs if k[0] in (T_L, T_I)]
    root = (task["out_type"], s.target)
    chosen = [root] + [k for k in open_goals if k != root and k[0] == T_L][:1] + \
             [k for k in open_goals if k != root and k[0] == T_I][:1]
    pieces = _pieces(lib, task["in_types"], [i for i, _ in train], consts, time.process_time() + 0.04 * cap_s)
    for t, g in chosen:
        if t in (T_L, T_I, T_B):
            contexts.append(("direct" if (t, g) == root else "subgoal", pieces, g, t))
    for st in sc.subtasks(task):
        pts = sc._pick(st["points"])
        pp = _pieces(lib, st["in_types"], [p[2] for p in pts], consts, time.process_time() + 0.04 * cap_s)
        contexts.append((st["kind"], pp, tuple(p[3] for p in pts), st["out_type"]))
    ops, posed = {}, 0
    for where, pcs, g, gt in contexts:
        for progs, ats, vecs in _specs(pcs, g, gt):
            if time.process_time() > end:
                break
            posed += 1
            ex = [(tuple(v[i] for v in vecs), g[i]) for i in range(len(g))]
            r, _ = sc.GSearch(lib, ats, gt, ex, min(end, time.process_time() + SPEC_S), consts=consts).run()
            if r is None:
                continue
            c = canonical(ic._tup(r[1]), ats, lib)
            if c is None:
                continue
            key = hashlib.sha1(repr(c[0]).encode()).hexdigest()[:16]
            ops.setdefault(key, {"key": key, "ast": c[1], "arg_types": list(c[2]), "ret": gt, "where": where,
                                 "residual": progs[1] is None, "program": ic.show(c[1])})
    return list(ops.values()), {"specs": posed, "cpu_seconds": round(time.process_time() - c0, 3), "solved": False}


def existing_signatures(lib):
    """Behaviour of everything the system already had: primitives, the eight old inventions, `len`."""
    out = {}
    old = json.loads(pathlib.Path("docs/experiments/results/invention_core_frozen.json").read_text())["spec"]
    full = ic.library_from_spec(seed_spec() + [(("old_" + n), r, p, _rename(b)) for n, r, p, b in old])
    for name, p in full.items():
        if p.kind not in ("fo", "inv") or not p.first_order() or p.arity not in (1, 2):
            continue
        ats = tuple(t for t, _ in p.params)
        ast = (name,) + tuple(("v", i) for i in range(p.arity))
        for a, ts in ((ast, ats),) + (((_swap(ast), ats[::-1]),) if p.arity == 2 else ()):
            sig = signature(a, ts, full)
            if sig is not None:
                out[(ts, repr(sig))] = name
    return out


def _rename(body):
    """Bodies of the old inventions refer to each other as f0..f7; give them the old_ prefix."""
    if isinstance(body, (list, tuple)):
        if body and isinstance(body[0], str) and body[0][:1] == "f" and body[0][1:].isdigit():
            return ("old_" + body[0],) + tuple(_rename(b) for b in body[1:])
        return tuple(_rename(b) for b in body)
    return body


def select(rows, exclude=()):
    """Operations produced by the gaps of at least MIN_SUPPORT different tasks (tasks in `exclude` do not
    count).  Returns (spec for `library_from_spec`, table of the kept operations)."""
    lib = ic.library_from_spec(seed_spec())
    seen = existing_signatures(lib)
    sup = {}
    for r in rows:
        if r["id"] in exclude:
            continue
        for o in r["ops"]:
            d = sup.setdefault(o["key"], {"op": o, "tasks": set()})
            d["tasks"].add(r["id"])
            if ic.size(ic._tup(o["ast"])) < ic.size(ic._tup(d["op"]["ast"])):
                d["op"] = o
    kept = sorted((d for d in sup.values() if len(d["tasks"]) >= MIN_SUPPORT),
                  key=lambda d: (-len(d["tasks"]), ic.size(ic._tup(d["op"]["ast"])), d["op"]["key"]))[:MAX_OPS]
    spec, table = seed_spec(), []
    for n, d in enumerate(kept):
        o = d["op"]
        ast, ats = ic._tup(o["ast"]), tuple(o["arg_types"])
        c = canonical(ast, ats, lib)
        name = "g%d" % n
        spec.append((name, o["ret"], [(t, []) for t in ats], ic._to_body(ast, len(ats))))
        table.append({"name": name, "key": o["key"], "program": ic.show(ast), "arg_types": list(ats), "ret": o["ret"],
                      "support": len(d["tasks"]), "tasks": sorted(d["tasks"]),
                      "same_as_existing": seen.get(c[0]) if c else None})
    rec = iv.derive_op_inverses(spec)
    for row in table:
        row["recoverable_arguments"] = rec.get(row["name"], [])
    return spec, table, {k: v for k, v in rec.items() if k != "len"}
