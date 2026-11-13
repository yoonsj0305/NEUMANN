"""Representation formation from observation (Stage A follow-up; development, SOURCE only).

Question: can the system decide which relations and intermediate representations a new problem needs, and
learn from verified experience how to look for them?  Four configurations of ONE procedure:

  R0  Stage A: fixed relations (copy, linked through derived inverses, value) over fixed cell coordinates
  R1  + a typed relational substrate: cell SETS become coordinates (each input list's prefix up to the cell,
        the answer's own prefix) and `len`, the aggregate the system derived as the inverse of `range`.
        Conditional selection, aggregation and order relations over cell sets are now EXPRESSIBLE as
        coordinate programs (len (filter p S), folds over S, ...), but nothing constructs them: blind search.
  R2  + formation of intermediate representations from observation and counterexample, by two generic rules:
        * residual latent: an observed relation that explains the answer only up to a residual (answer cell
          = op(observed cell, w) through a derived inverse) creates a NEW specification, the residual w, which
          is solved recursively by the same procedure.  A residual is formed only if it is simpler than what
          it replaces (fewer distinct values or smaller magnitude): a minimal-description choice.
        * transport latent: an observed correspondence between answer cells and input cells is read in the
          other direction: every input cell gets its observed destination as a new supervised target
          (iteration 4 read only the source of each answer cell).
  R3  + learning from verified SOURCE experience of other tasks: the generative order of coordinate programs
        and the order of latent kinds are fitted on the representations R2 verified on OTHER folds.

No relation type, aggregate or operation is written for a problem.  Hidden tests never reach construction.
"""
from __future__ import annotations
import time
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc, cells as c4, relcells as rc
from neumann1 import opgen

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
INIT = rc.INIT
MAX_GOALS, MAX_VALUES = 4000, 40000
MAX_RESIDUALS = 8


class Cfg:
    def __init__(self, subst=False, latent=False, prior=None, order=("residual", "transport")):
        self.subst, self.latent, self.prior, self.order = subst, latent, prior or {}, tuple(order)

    def cost(self, ctx):
        c = ic.uniform_costs()
        if ctx in self.prior:
            c = ic._as_cost(self.prior[ctx])
        return c


def library(cfg):
    return ic.library_from_spec(opgen.seed_spec()) if cfg.subst else ic.base_library()


# ---------------------------------------------------------------- coordinates
def _lists(task):
    return [a for a, t in enumerate(task["in_types"]) if t == T_L]


def coords_types(task, cfg):
    base = rc.coords_types(task, True)
    if cfg.subst and not rc.is_seq(task):
        base = base + (T_L,) * (len(_lists(task)) + 1)
    return base


def cell(task, inputs, t, m, prefix, cfg):
    base = rc.cell(task, inputs, t, m, prefix, True)
    if cfg.subst and not rc.is_seq(task):
        base = base + tuple(tuple(inputs[a][:t + 1][::-1]) for a in _lists(task)) + (tuple(prefix[:t][::-1]),)
    return base


def in_types_cell(task, a):
    ints = [b for b, t in enumerate(task["in_types"]) if t == T_I]
    return (T_I, T_I, T_I, T_L, T_L, T_L) + (T_I,) * len(ints)


def in_cell(task, inputs, a, j):
    x = inputs[a]
    ints = [b for b, t in enumerate(task["in_types"]) if t == T_I]
    return (x[j], j, len(x) - 1 - j, tuple(x[:j][::-1]), tuple(x[j + 1:]), tuple(x)) + tuple(inputs[b] for b in ints)


# ------------------------------------------------------------------ execution
def _seq_hist(task):
    return [o for _, o in task["train"]], task["train"][0][0][0]


def run(sol, lib, inputs, task):
    kind = sol[0]
    if kind == "keep":
        x, out = inputs[sol[1]], []
        for j in range(len(x)):
            p = rc._ev(sol[2], lib, in_cell(task, inputs, sol[1], j))
            if p is None:
                return None
            if p:
                out.append(x[j])
        return tuple(out)
    if kind == "transport":
        _, a, dest = sol[:3]
        x = inputs[a]
        out = [None] * len(x)
        for j in range(len(x)):
            d = rc._ev(dest, lib, in_cell(task, inputs, a, j))
            if d is None or isinstance(d, bool) or not 0 <= d < len(x) or out[d] is not None:
                return None
            out[d] = x[j]
        return tuple(out)
    if kind == "residual":
        return _run_residual(sol, lib, inputs, task)
    _, m_ast, tree, cfg_subst = sol[0], sol[1], sol[2], sol[3]
    cfg = Cfg(subst=cfg_subst)
    if rc.is_seq(task):
        hist, n0 = _seq_hist(task)
        tw = inputs[0] - n0
        if tw < 0 or tw > 4 * len(hist):
            return None
        while len(hist) <= tw:
            t = len(hist)
            v = rc._tree(tree, lib, rc.sources(task, None, hist, t, True), cell(task, n0 + t, t, None, hist, cfg))
            if v is None:
                return None
            hist.append(v)
        return hist[tw]
    m = rc._ev(m_ast, lib, c4.len_cell(inputs, tuple(task["in_types"])))
    if m is None or isinstance(m, bool) or not 0 <= m <= ic.LEN_CAP:
        return None
    out = []
    for t in range(m):
        v = rc._tree(tree, lib, rc.sources(task, inputs, out, t, True), cell(task, inputs, t, m, out, cfg))
        if v is None:
            return None
        out.append(v)
    return tuple(out)


def _apply(lib, op, a, w):
    f = lib[op[0]].f
    return f(a, w) if op[1] == 1 else f(w, a)


def _run_residual(sol, lib, inputs, task):
    _, key, idx, op, sub, subtask, m_ast, cfg_subst = sol
    cfg = Cfg(subst=cfg_subst)
    if rc.is_seq(task):
        hist, n0 = _seq_hist(task)
        tw = inputs[0] - n0
        if tw < 0 or tw > 4 * len(hist):
            return None
        while len(hist) <= tw:
            t = len(hist)
            j = rc._ev(idx, lib, cell(task, n0 + t, t, None, hist, cfg))
            w = run(sub, lib, (n0 + t,), subtask)
            if j is None or isinstance(j, bool) or not 0 <= j < t or w is None:
                return None
            v = _apply(lib, op, hist[j], w)
            if v is None:
                return None
            hist.append(v)
        return hist[tw]
    w = run(sub, lib, inputs, subtask)
    m = rc._ev(m_ast, lib, c4.len_cell(inputs, tuple(task["in_types"])))
    if w is None or m is None or isinstance(m, bool) or len(w) != m:
        return None
    out = []
    for t in range(m):
        src = rc.sources(task, inputs, out, t, True).get(key, ())
        j = rc._ev(idx, lib, cell(task, inputs, t, m, out, cfg))
        if j is None or isinstance(j, bool) or not 0 <= j < len(src):
            return None
        v = _apply(lib, op, src[j], w[t])
        if v is None:
            return None
        out.append(v)
    return tuple(out)


def show(sol):
    if sol[0] == "transport":
        return "<transport arg%d dest=%s>" % (sol[1], ic.show(sol[2]))
    if sol[0] == "keep":
        return "<transport arg%d present=%s>" % (sol[1], ic.show(sol[2]))
    if sol[0] == "residual":
        return "<residual %s(%s[%s], w) | w = %s>" % (sol[3][0], sol[1], ic.show(sol[2]), show(sol[4]))
    return rc.show(("relcells", sol[1], sol[2]))


def kinds(sol):
    if sol[0] in ("transport", "keep"):
        return ["transport"]
    if sol[0] == "residual":
        return ["residual"] + kinds(sol[4])
    return ["cells"]


def programs(sol, task):
    """(context, coordinate program, coordinate types) of every searched function in a representation."""
    out = []
    if sol[0] in ("transport", "keep"):
        return [("transport", sol[2], in_types_cell(task, sol[1]))]
    if sol[0] == "residual":
        ctx = "seq" if rc.is_seq(task) else "list"
        return [(ctx, sol[2], coords_types(task, Cfg(subst=sol[7])))] + programs(sol[4], sol[5])
    ctx = "seq" if rc.is_seq(task) else "list"
    ts = coords_types(task, Cfg(subst=sol[3]))

    def walk(n):
        if n[0] == "case":
            out.append((ctx, n[1], ts))
            walk(n[2])
            walk(n[3])
        elif n[0] == "value":
            if n[1][0] != "k":
                out.append((ctx, n[1], ts))
        elif n[0] == "copy":
            out.append((ctx, n[2], ts))
        else:
            out.append((ctx, n[2], ts))
            if n[4][0] != "k":
                out.append((ctx, n[4], ts))
    walk(sol[2])
    return out


# --------------------------------------------------------------- construction
def _size(node):
    if node[0] == "case":
        return 1 + ic.size(node[1]) + _size(node[2]) + _size(node[3])
    if node[0] == "value":
        return 1 + ic.size(node[1])
    if node[0] == "copy":
        return 1 + ic.size(node[2])
    return 1 + ic.size(node[2]) + ic.size(node[4])


def _simpler(w, y):
    dw, dy = len(set(w)), len(set(y))
    mw, my = max(abs(v) for v in w), max(abs(v) for v in y)
    return dw < dy or (dw == dy and mw < my)


def construct(task, lib, consts, deadline, inv, cfg, depth=0):
    t0 = time.process_time()
    span = deadline - t0
    seq = rc.is_seq(task)
    train = task["train"]
    if seq:
        m_ast = None
        ys, n0 = _seq_hist(task)
        examples = [(n0, ys)]
    else:
        m_ast = c4._length(lib, task, consts, t0 + 0.12 * span)
        if m_ast is None:                  # the answer's length is not a function of the input lengths:
            if cfg.latent and depth == 0:  # no cell-by-cell construction; the input-side reading may still apply
                return _transport(task, lib, consts, deadline, cfg)
            return None
        examples = list(train)
    pts, ys_, srcs, where = [], [], [], []
    for e, (inputs, y) in enumerate(examples):
        for t in range(INIT if seq else 0, len(y)):
            pts.append(cell(task, (inputs + t) if seq else inputs, t, len(y), y, cfg))
            ys_.append(y[t])
            srcs.append(rc.sources(task, inputs, y, t, True))
            where.append((e, t))
    if len(pts) < 2:
        return None
    keys = sorted({k for s in srcs for k in s}, key=str)
    prov = [{k: {i for i, v in enumerate(s.get(k, ())) if v == y} for k in keys} for s, y in zip(srcs, ys_)]
    full = (1 << len(pts)) - 1
    pieces, seen, preds, pseen, values, goals, order = [], set(), [], set(), {}, {}, []
    ops = list((inv or {}).get("_given_I", []))

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
        if vec in goals:
            for k, idx_ast, op in goals[vec]:
                raise sc.Done(("found", ("linked", k, idx_ast, op, ast)), None)
        if len(values) < MAX_VALUES:
            values.setdefault(vec, ast)
        for k in keys:
            known = []
            for j, s in zip(vec, srcs):
                src = s.get(k, ())
                if isinstance(j, bool) or not 0 <= j < len(src):
                    break
                known.append(src[j])
            if len(known) != len(vec):
                continue
            for name, kk, q in ops:
                f = lib[name].f
                try:
                    w = tuple(q((y, a)) for y, a in zip(ys_, known))
                except ic.Fail:
                    continue
                if any((f(a, b) if kk == 1 else f(b, a)) != y for a, b, y in zip(known, w, ys_)):
                    continue
                if w in values:
                    raise sc.Done(("found", ("linked", k, ast, (name, kk), values[w])), None)
                if len(goals) < MAX_GOALS and w not in goals:
                    goals[w] = [(k, ast, (name, kk))]
                    order.append(w)

    def wrap(node):
        """Minimal description: a representation longer than the cells it explains is not accepted."""
        return ("lat", m_ast, node, cfg.subst) if node is not None and _size(node) <= len(pts) else None
    lat = cfg.latent and depth == 0
    bank_end = t0 + (0.45 if lat else 0.75) * span
    try:
        for c in sorted(set(range(10)) | set(consts)):
            take((c,) * len(pts), ("k", c), T_I)
    except sc.Done as d:
        return wrap(d.sol[1])
    got = None
    s = dc.FSearch(lib, coords_types(task, cfg), pts, bank_end, consts, cfg.cost("seq" if seq else "list"), (T_I, T_B),
                   lambda e, t: take(e.vec, e.ast(), t))
    for lvl in range(1, s.max_level + 1):
        try:
            for t in s.types:
                s._pool(s.top, t, lvl)
        except sc.Done as d:
            if wrap(d.sol[1]) is not None:
                return wrap(d.sol[1])
            break                              # complete but longer than the data: go on to formation
        except ic.Budget:
            break
        if lvl >= 3:
            node = c4._cover(pieces, preds, full, min(deadline, time.process_time() + 0.08 * span))
            if wrap(node) is not None:
                return wrap(node)
    node = c4._cover(pieces, preds, full, min(deadline, time.process_time() + 0.05 * span))
    if wrap(node) is not None or not lat:
        return wrap(node)
    # ---- formation of intermediate representations (R2): in the learned or default order of latent kinds
    for kind in cfg.order:
        if time.process_time() > deadline:
            break
        if kind == "transport" and not seq:
            got = _transport(task, lib, consts, min(deadline, time.process_time() + 0.25 * (deadline - time.process_time())), cfg)
            if got is not None:
                return got
        if kind == "residual":
            got = _residual(task, lib, consts, deadline, inv, cfg, order, goals, where, examples, seq, m_ast, ys_)
            if got is not None:
                return got
    return None


def _residual(task, lib, consts, deadline, inv, cfg, order, goals, where, examples, seq, m_ast, ys_):
    tried = 0
    cands = sorted((w for w in order if _simpler(w, ys_)),          # simplest residual first
                   key=lambda w: (len(set(w)), max(abs(v) for v in w)))
    for w in cands:
        if tried >= MAX_RESIDUALS or time.process_time() > deadline:
            return None
        k, idx_ast, op = goals[w][0]
        if seq:
            n0 = examples[0][0]
            sub = {"id": "residual", "in_types": [T_I], "out_type": T_I,
                   "train": [((n0 + t,), v) for (e, t), v in zip(where, w)]}
            if not rc.is_seq(sub):
                continue
        else:
            lists = [[] for _ in examples]
            for (e, t), v in zip(where, w):
                lists[e].append(v)
            sub = {"id": "residual", "in_types": list(task["in_types"]), "out_type": T_L,
                   "train": [(inputs, tuple(l)) for (inputs, _), l in zip(examples, lists)]}
        tried += 1
        left = deadline - time.process_time()
        got = solve_cfg(sub, time.process_time() + min(left, max(left / 3, 0.2)), inv, lib, cfg, depth=1)
        if got is None:
            continue
        sol = ("residual", k, idx_ast, op, got, sub, m_ast, cfg.subst)
        if all(run(sol, lib, i, task) == o for i, o in task["train"]) or seq:
            return sol
    return None


def _transport(task, lib, consts, deadline, cfg):
    """The observed correspondence read from the input side: every input cell of one list argument gets a
    new supervised target.  Permutation (same multiset): its destination index.  Subsequence (the kept cells,
    in input order, spell the answer): present / absent.  Ambiguity from repeated values is left to the
    acceptance test over the whole vector, not resolved by a fixed embedding."""
    train = task["train"]
    t0 = time.process_time()
    for a in _lists(task):
        perm = all(len(i[a]) == len(o) and sorted(i[a]) == sorted(o) for i, o in train)
        sub = not perm and all(len(o) <= len(i[a]) for i, o in train) and any(len(o) < len(i[a]) for i, o in train)
        if not (perm or sub):
            continue
        pts, groups = [], []
        for inputs, y in train:
            g = []
            for j in range(len(inputs[a])):
                g.append((len(pts), inputs[a][j], {t for t, v in enumerate(y) if v == inputs[a][j]}))
                pts.append(in_cell(task, inputs, a, j))
            groups.append((g, y))
        if perm:
            def accept(vec):
                for g, y in groups:
                    used = set()
                    for k, _, ok in g:
                        d = vec[k]
                        if d is None or isinstance(d, bool) or d not in ok or d in used:
                            return False
                        used.add(d)
                return True
            out_t, kind = T_I, "transport"
        else:
            def accept(vec):
                for g, y in groups:
                    if tuple(v for k, v, _ in g if vec[k]) != y:
                        return False
                return True
            out_t, kind = T_B, "keep"
        s = sc.GSearch(lib, in_types_cell(task, a), out_t, [(p, 0) for p in pts], deadline, consts=consts, accept=accept)
        s.cost = cfg.cost("transport")
        r, _ = s.run()
        if r is not None:
            sol = (kind, a, r[1])
            if all(run(sol, lib, i, task) == o for i, o in train):
                return sol
    return None


def solve_cfg(task, deadline, inv, lib, cfg, depth=0):
    if not (rc.is_seq(task) or (task["out_type"] == T_L and T_L in task["in_types"])):
        return None
    consts = ic.data_constants(task["train"])
    sol = construct(task, lib, consts, deadline, inv, cfg, depth)
    if sol is None:
        return None
    if rc.is_seq(task):
        if sol[0] != "lat":
            return sol                                       # residual: verified by construction on TRAIN terms
        ys, n0 = _seq_hist(task)
        ok = all(rc._tree(sol[2], lib, rc.sources(task, n0, ys, t, True), cell(task, n0 + t, t, None, ys, cfg)) == ys[t]
                 for t in range(INIT, len(ys)))
    else:
        ok = all(run(sol, lib, i, task) == o for i, o in task["train"])
    return sol if ok else None


def solve(task, deadline, inv, cfg):
    lib = library(cfg)
    if not (rc.is_seq(task) or (task["out_type"] == T_L and T_L in task["in_types"])):
        return c4.solve(task, deadline, lib)
    return solve_cfg(task, deadline, inv, lib, cfg)


def fit_prior(experience, lib=None):
    """R3: generative order per context and latent-kind order, from representations verified on other tasks.
    experience: [(kinds, [(ctx, ast, coord types)])]."""
    lib = lib or ic.library_from_spec(opgen.seed_spec())
    by = {}
    count = {"residual": 0, "transport": 0}
    for ks, progs in experience:
        for k in ks:
            if k in count:
                count[k] += 1
        for ctx, ast, ts in progs:
            by.setdefault(ctx, []).append((ic._tup(ast), tuple(ts)))
    prior = {ctx: ic.learn_costs(ps, lib) for ctx, ps in by.items()}
    order = tuple(sorted(count, key=lambda k: -count[k]))
    return Cfg(subst=True, latent=True, prior=prior, order=order)
