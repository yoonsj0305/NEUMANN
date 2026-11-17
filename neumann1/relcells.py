"""Stage A of the first-principles redefinition: relational factorisation over observed cells.

One procedure for every type signature.  An answer is a sequence of cells (a scalar answer of a sequence task
is the cell n of the answer's own sequence).  Each answer cell is related to an OBSERVED cell:
  sources    every list argument; the answer's own earlier cells (self)
  relations  copy:   y_t = src[idx(c)]
             linked: y_t = op(src[idx(c)], v(c)) for every binary op whose inverse the system derived itself
                     (`spec_core_inverses.json`); the residual is computed through that derived inverse and
                     matched by hash against every value the enumerator produces
             value:  y_t = v(c)
idx, v, the case split and the length function are searched over generic coordinates under per-cell
supervision; the result must reproduce every TRAIN example.  Among covers, pieces and predicates are tried in
the enumerator's cost order (the cheapest consistent description first), not by coverage.  No operation is written for a problem.
`self_src=False, linked=False` is the iteration-4 construction (ablation).
"""
from __future__ import annotations
import time
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc, cells as c4

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
MAX_GOALS = 4000
MAX_VALUES = 40000
INIT = 2                         # initial conditions of a sequence: its first cells are data


def is_seq(task):
    if tuple(task["in_types"]) != (T_I,) or task["out_type"] != T_I or len(task["train"]) < 8:
        return False
    ns = [i[0] for i, _ in task["train"]]
    return all(b - a == 1 for a, b in zip(ns, ns[1:]))


# ---------------------------------------------------------------- coordinates
def coords_types(task, self_src):
    if is_seq(task):
        return (T_I, T_I, T_I, T_I, T_L)                     # t, n, y[t-1], y[t-2], reversed history
    base = c4.out_coords(tuple(task["in_types"]))
    return base + ((T_I, T_I) if self_src else ())


def cell(task, inputs, t, m, prefix, self_src):
    p1 = prefix[t - 1] if t >= 1 else -1
    p2 = prefix[t - 2] if t >= 2 else -1
    if is_seq(task):
        return (t, inputs, p1, p2, tuple(prefix[:t][::-1]))
    base = c4.out_cell(inputs, tuple(task["in_types"]), t, m)
    return base + ((p1, p2) if self_src else ())


def sources(task, inputs, prefix, t, self_src):
    out = {}
    if not is_seq(task):
        for a, ty in enumerate(task["in_types"]):
            if ty == T_L:
                out[a] = inputs[a]
    if self_src:
        out["self"] = tuple(prefix[:t])
    return out


# ------------------------------------------------------------------ execution
def _ev(ast, lib, c):
    try:
        return ic.run_program(ast, lib, c)
    except RecursionError:
        return None


def _leaf(node, lib, src, c):
    kind = node[0]
    if kind == "value":
        v = _ev(node[1], lib, c)
        return None if isinstance(v, bool) else v
    s = src.get(node[1])
    j = _ev(node[2], lib, c)
    if s is None or j is None or isinstance(j, bool) or not 0 <= j < len(s):
        return None
    if kind == "copy":
        return s[j]
    w = _ev(node[4], lib, c)
    if w is None or isinstance(w, bool):
        return None
    f = lib[node[3][0]].f
    return f(s[j], w) if node[3][1] == 1 else f(w, s[j])


def _tree(node, lib, src, c):
    if node[0] == "case":
        p = _ev(node[1], lib, c)
        if p is None:
            return None
        return _tree(node[2] if p else node[3], lib, src, c)
    return _leaf(node, lib, src, c)


def run(sol, lib, inputs, task):
    _, m_ast, tree, self_src, init = sol
    if is_seq(task):
        n0 = task["train"][0][0][0]
        hist = [o for _, o in task["train"]]
        t_want = inputs[0] - n0
        if t_want < 0:
            return None
        if t_want < len(hist):
            return hist[t_want]
        if t_want > 4 * len(hist):
            return None
        while len(hist) <= t_want:
            t = len(hist)
            v = _tree(tree, lib, sources(task, None, hist, t, self_src), cell(task, n0 + t, t, None, hist, self_src))
            if v is None:
                return None
            hist.append(v)
        return hist[t_want]
    m = _ev(m_ast, lib, c4.len_cell(inputs, tuple(task["in_types"])))
    if m is None or isinstance(m, bool) or not 0 <= m <= ic.LEN_CAP:
        return None
    out = []
    for t in range(m):
        v = _tree(tree, lib, sources(task, inputs, out, t, self_src), cell(task, inputs, t, m, out, self_src))
        if v is None:
            return None
        out.append(v)
    return tuple(out)


def show(sol):
    def node(n):
        if n[0] == "case":
            return "(%s ? %s : %s)" % (ic.show(n[1]), node(n[2]), node(n[3]))
        if n[0] == "value":
            return "value %s" % ic.show(n[1])
        if n[0] == "copy":
            return "copy %s[%s]" % (n[1], ic.show(n[2]))
        return "%s(%s %s[%s], %s)" % ("linked", n[3][0], n[1], ic.show(n[2]), ic.show(n[4])) if n[3][1] == 1 else \
            "%s(%s %s, %s[%s])" % ("linked", n[3][0], ic.show(n[4]), n[1], ic.show(n[2]))
    return "<relcells m=%s | %s>" % (ic.show(sol[1]) if sol[1] is not None else "-", node(sol[2]))


def relations_used(sol):
    out = []

    def walk(n):
        if n[0] == "case":
            walk(n[2])
            walk(n[3])
        else:
            out.append((n[0], "self" if len(n) > 1 and n[1] == "self" else ("list" if n[0] != "value" else "-"),
                        n[3][0] if n[0] == "linked" else None))
    walk(sol[2])
    return out


# --------------------------------------------------------------- construction
def construct(task, lib, consts, deadline, inv, self_src=True, linked=True):
    t0 = time.process_time()
    span = deadline - t0
    seq = is_seq(task)
    train = task["train"]
    if seq:
        m_ast = None
        ys = [o for _, o in train]
        n0 = train[0][0][0]
        examples = [(n0, ys)]
    else:
        m_ast = c4._length(lib, task, consts, t0 + 0.15 * span)
        if m_ast is None:
            return None
        examples = [(i, o) for i, o in train]
    pts, ys_, srcs = [], [], []
    for inputs, y in examples:
        for t in range(INIT if seq else 0, len(y)):
            pts.append(cell(task, (inputs + t) if seq else inputs, t, len(y), y, self_src))
            ys_.append(y[t])
            srcs.append(sources(task, inputs, y, t, self_src))
    if len(pts) < 2:
        return None
    keys = sorted({k for s in srcs for k in s}, key=str)
    prov = [{k: {i for i, v in enumerate(s.get(k, ())) if v == y} for k in keys} for s, y in zip(srcs, ys_)]
    full = (1 << len(pts)) - 1
    pieces, seen, preds, pseen = [], set(), [], set()
    values, goals = {}, {}
    ops = [(n_, k, q) for n_, k, q in (inv or {}).get("_given_I", [])] if linked else []

    def add_piece(mk, node, key):
        if mk and (key, mk) not in seen and len(pieces) < c4.MAX_PIECES:
            seen.add((key, mk))
            pieces.append((mk, node))
            if mk == full:
                raise sc.Done(("found", node), None)

    def take(vec, ast, t):
        if t == T_B:
            mk = sum(1 << k for k, b in enumerate(vec) if b)
            if 0 < mk < full and mk not in pseen and len(preds) < c4.MAX_PREDS:
                pseen.add(mk)
                preds.append((mk, ast))
            return
        add_piece(sum(1 << k for k, (a, b) in enumerate(zip(vec, ys_)) if a == b), ("value", ast), ("value",))
        for k in keys:
            add_piece(sum(1 << j for j, (a, p) in enumerate(zip(vec, prov)) if a in p[k]), ("copy", k, ast), ("copy", k))
        if not ops:
            return
        if vec in goals:                                     # a value that completes a registered linked relation
            for k, idx_ast, op in goals[vec]:
                raise sc.Done(("found", ("linked", k, idx_ast, op[:2], ast)), None)
        if len(values) < MAX_VALUES:
            values.setdefault(vec, ast)
        for k in keys:                                       # this vector as an index into source k
            known = []
            for j, s in zip(vec, srcs):
                src = s.get(k, ())
                if isinstance(j, bool) or not 0 <= j < len(src):
                    break
                known.append(src[j])
            if len(known) != len(vec):
                continue
            for op in ops:
                name, kk, q = op
                f = lib[name].f
                try:
                    w = tuple(q((y, a)) for y, a in zip(ys_, known))
                except ic.Fail:
                    continue
                if any((f(a, b) if kk == 1 else f(b, a)) != y for a, b, y in zip(known, w, ys_)):
                    continue
                if w in values:
                    raise sc.Done(("found", ("linked", k, ast, (name, kk), values[w])), None)
                if len(goals) < MAX_GOALS:
                    goals.setdefault(w, []).append((k, ast, (name, kk)))
    try:
        for c in sorted(set(range(10)) | set(consts)):
            take((c,) * len(pts), ("k", c), T_I)
    except sc.Done as d:
        return ("relcells", m_ast, d.sol[1], self_src, INIT)
    s = dc.FSearch(lib, coords_types(task, self_src), pts, t0 + 0.75 * span, consts, ic.uniform_costs(), (T_I, T_B),
                   lambda e, t: take(e.vec, e.ast(), t))
    for lvl in range(1, s.max_level + 1):
        try:
            for t in s.types:
                s._pool(s.top, t, lvl)
        except sc.Done as d:
            return ("relcells", m_ast, d.sol[1], self_src, INIT)
        except ic.Budget:
            break
        if lvl >= 3:
            node = c4._cover(pieces, preds, full,
                             min(deadline, time.process_time() + 0.1 * span))
            if node is not None:
                return ("relcells", m_ast, node, self_src, INIT)
    node = c4._cover(pieces, preds, full, deadline)
    return ("relcells", m_ast, node, self_src, INIT) if node is not None else None


def solve(task, deadline, inv, lib=None, self_src=True, linked=True):
    lib = lib or ic.base_library()
    if not (is_seq(task) or (task["out_type"] == T_L and T_L in task["in_types"])):
        return c4.solve(task, deadline, lib)                 # scalar selection: unchanged
    consts = ic.data_constants(task["train"])
    sol = construct(task, lib, consts, deadline, inv, self_src, linked)
    if sol is None:
        return None
    if is_seq(task):                    # every non-initial TRAIN term from its true predecessors
        ys = [o for _, o in task["train"]]
        n0 = task["train"][0][0][0]
        ok = all(_tree(sol[2], lib, sources(task, n0, ys, t, self_src), cell(task, n0 + t, t, None, ys, self_src))
                 == ys[t] for t in range(INIT, len(ys)))
    else:
        ok = all(run(sol, lib, i, task) == o for i, o in task["train"])
    return sol if ok else None
