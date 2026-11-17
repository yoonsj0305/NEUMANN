"""Iteration 4: representations constructed from observed cell relations (development; nothing here is evidence).

Diagnosis that motivates it (iteration 4, steps 1-2): every constructor iteration 3 could not define IS
expressible in the definition language, but as a whole program it sits at cost level 9-33, i.e. 1e7-1e26
candidates; and the THIRD solver, which avoids that cost by per-position supervision, re-represents only tasks
with one list input and a fixed alignment (equal length or subsequence).

Mechanism.  One type-generic procedure; no operation, traversal or alignment is written for a problem.
  cells       every list in the problem is a sequence of cells; a scalar is one cell
  coordinates of an output cell t of an output of length m: t, m-1-t, m, the length of every list argument,
              every integer argument, the element of every list argument at t (-1 outside), every list argument
              coordinates of an input cell i of list argument a: its element, i, n-1-i, every integer argument,
              every list argument
  relation    observed, not specified: for every output cell, the set of input cells holding an equal value
              (its provenance), per list argument
The system then constructs the representation of the task from these observations:
  * list output: a length function of the input lengths and integer arguments; a set of PIECES, each either
    "copy from list argument a at index idx(c)" (idx must land in the observed provenance) or "value v(c)";
    and a case split by predicates over the coordinates, when one piece does not cover every cell;
  * integer output: a SELECTION over the input cells of one list argument (the first cell whose predicate holds
    must carry the output value).
idx, v, the predicates and the length function are searched over the coordinates with the frozen forward
enumerator under per-cell supervision.  The representation is accepted only if it reproduces every TRAIN
example; hidden tests never reach it.

Claim scope, stated in advance: the developer supplies the cell coordinates and the equality relation; the
system constructs, per task, which relation is used, the index / value / length functions and the case split.
"""
from __future__ import annotations
import time
from neumann1 import invention_core as ic, spec_core as sc, discovery_core as dc

T_I, T_B, T_L = ic.T_I, ic.T_B, ic.T_L
MAX_PIECES = 1500
MAX_PREDS = 1500


def _args(in_types):
    return [i for i, t in enumerate(in_types) if t == T_L], [i for i, t in enumerate(in_types) if t == T_I]


def out_coords(in_types):
    L, I = _args(in_types)
    return (T_I,) * (3 + len(L) + len(I) + len(L)) + (T_L,) * len(L)


def out_cell(inputs, in_types, t, m):
    L, I = _args(in_types)
    return ((t, m - 1 - t, m) + tuple(len(inputs[a]) for a in L) + tuple(inputs[a] for a in I)
            + tuple(inputs[a][t] if t < len(inputs[a]) else -1 for a in L) + tuple(inputs[a] for a in L))


def len_coords(in_types):
    L, I = _args(in_types)
    return (T_I,) * (len(L) + len(I))


def len_cell(inputs, in_types):
    L, I = _args(in_types)
    return tuple(len(inputs[a]) for a in L) + tuple(inputs[a] for a in I)


def in_coords(in_types):
    L, I = _args(in_types)
    return (T_I, T_I, T_I) + (T_I,) * len(I) + (T_L,) * len(L)


def in_cell(inputs, in_types, a, i):
    L, I = _args(in_types)
    x = inputs[a]
    return (x[i], i, len(x) - 1 - i) + tuple(inputs[b] for b in I) + tuple(inputs[b] for b in L)


# ----------------------------------------------------------------- execution
def _ev(ast, lib, c):
    try:
        return ic.run_program(ast, lib, c)
    except RecursionError:
        return None


def _piece(piece, lib, inputs, in_types, c):
    kind, prog = piece[0], piece[-1]
    v = _ev(prog, lib, c)
    if v is None or isinstance(v, bool):
        return None
    if kind == "value":
        return v
    x = inputs[piece[1]]
    return x[v] if 0 <= v < len(x) else None


def _tree(node, lib, inputs, in_types, c):
    if node[0] == "case":
        p = _ev(node[1], lib, c)
        if p is None:
            return None
        return _tree(node[2] if p else node[3], lib, inputs, in_types, c)
    return _piece(node, lib, inputs, in_types, c)


def run(sol, lib, inputs, in_types):
    if sol[0] == "cells":
        m = _ev(sol[1], lib, len_cell(inputs, in_types))
        if m is None or isinstance(m, bool) or not 0 <= m <= ic.LEN_CAP:
            return None
        out = []
        for t in range(m):
            v = _tree(sol[2], lib, inputs, in_types, out_cell(inputs, in_types, t, m))
            if v is None:
                return None
            out.append(v)
        return tuple(out)
    if sol[0] == "select":
        x = inputs[sol[1]]
        for i in range(len(x)):
            p = _ev(sol[2], lib, in_cell(inputs, in_types, sol[1], i))
            if p:
                return x[i]
        return None
    return None


def show(sol):
    def node(n):
        if n[0] == "case":
            return "(%s ? %s : %s)" % (ic.show(n[1]), node(n[2]), node(n[3]))
        if n[0] == "value":
            return "value %s" % ic.show(n[1])
        return "copy arg%d[%s]" % (n[1], ic.show(n[2]))
    if sol[0] == "cells":
        return "<cells m=%s | %s>" % (ic.show(sol[1]), node(sol[2]))
    return "<select arg%d first | %s>" % (sol[1], ic.show(sol[2]))


def structure(sol):
    """Structure class of a constructed representation: (form, pieces, piece kinds)."""
    if sol[0] == "select":
        return "select"
    kinds = []

    def walk(n):
        if n[0] == "case":
            walk(n[2])
            walk(n[3])
        else:
            kinds.append(n[0])
    walk(sol[2])
    return "cells:%d:%s" % (len(kinds), "+".join(sorted(set(kinds))))


# ------------------------------------------------------------- construction
def _bank(lib, types, inputs, deadline, consts, want, take):
    def offer(e, t):
        take(e, t)
    return dc.FSearch(lib, types, inputs, deadline, consts, ic.uniform_costs(), want, offer).run()[0]


def _cover(pieces, preds, full, deadline):
    """A case split over predicates whose leaves cover every cell, or None.  pieces: [(mask, node)]."""
    for m, node in pieces:
        if m == full:
            return node

    def two(R):
        for pm, past in preds:
            if time.process_time() > deadline:
                return None
            a, b = pm & R, ~pm & R
            if not a or not b:
                continue
            A = next((n for m, n in pieces if not a & ~m), None)
            if A is None:
                continue
            B = next((n for m, n in pieces if not b & ~m), None)
            if B is not None:
                return ("case", past, A, B)
        return None
    got = two(full)
    if got is not None:
        return got
    firsts = []
    for pm, past in preds:
        if pm and pm != full:
            A = next((n for m, n in pieces if not pm & ~m), None)
            if A is not None:
                firsts.append((-bin(pm).count("1"), len(firsts), pm, past, A))
    for _, _, pm, past, A in sorted(firsts)[:40]:
        if time.process_time() > deadline:
            return None
        rest = two(full & ~pm)
        if rest is not None:
            return ("case", past, A, rest)
        B = next((n for m, n in pieces if not (full & ~pm) & ~m), None)
        if B is not None:
            return ("case", past, A, B)
    return None


def _length(lib, task, consts, deadline):
    tr = task["train"]
    ex = [(len_cell(i, task["in_types"]), len(o)) for i, o in tr]
    if not len_coords(task["in_types"]):
        return ("k", ex[0][1]) if len({o for _, o in ex}) == 1 else None
    s = sc.GSearch(lib, len_coords(task["in_types"]), T_I, ex, deadline, consts=consts)
    r, _ = s.run()
    return r[1] if r is not None else None


def construct_list(task, lib, consts, deadline):
    in_types, train = tuple(task["in_types"]), task["train"]
    t0 = time.process_time()
    span = deadline - t0
    m_ast = _length(lib, task, consts, t0 + 0.15 * span)
    if m_ast is None:
        return None
    L, _ = _args(in_types)
    pts, prov, ys = [], [], []
    for inputs, y in train:
        for t in range(len(y)):
            pts.append(out_cell(inputs, in_types, t, len(y)))
            ys.append(y[t])
            prov.append({a: {i for i, v in enumerate(inputs[a]) if v == y[t]} for a in L})
    if not pts:
        return None
    full = (1 << len(pts)) - 1
    pieces, seen, preds, pseen = [], set(), [], set()

    def take(e, t):
        v = e.vec
        if t == T_B:
            mk = sum(1 << k for k, b in enumerate(v) if b)
            if 0 < mk < full and mk not in pseen and len(preds) < MAX_PREDS:
                pseen.add(mk)
                preds.append((mk, e.ast()))
            return
        cands = [(sum(1 << k for k, (a, b) in enumerate(zip(v, ys)) if a == b), ("value", None))]
        for a in L:
            cands.append((sum(1 << k for k, (a_, p) in enumerate(zip(v, prov)) if a_ in p[a]), ("copy", a)))
        for mk, kind in cands:
            if mk and (kind, mk) not in seen and len(pieces) < MAX_PIECES:
                seen.add((kind, mk))
                node = ("value", e.ast()) if kind[0] == "value" else ("copy", kind[1], e.ast())
                pieces.append((mk, node))
                if mk == full:
                    raise sc.Done(("found", node), None)
    try:                                   # constants are cells' values too (the enumerator skips closed terms)
        for c in sorted(set(range(10)) | set(consts)):
            take(type("K", (), {"vec": (c,) * len(pts), "ast": lambda self, c=c: ("k", c)})(), T_I)
    except sc.Done as d:
        return ("cells", m_ast, d.sol[1])
    s = dc.FSearch(lib, out_coords(in_types), pts, t0 + 0.75 * span, consts, ic.uniform_costs(), (T_I, T_B),
                   lambda e, t: take(e, t))
    for c in range(1, s.max_level + 1):    # anytime: after every completed cost level, try to cover the cells
        try:
            for t in s.types:
                s._pool(s.top, t, c)
        except sc.Done as d:
            return ("cells", m_ast, d.sol[1])
        except ic.Budget:
            break
        if c >= 3:
            node = _cover(sorted(pieces, key=lambda p: -bin(p[0]).count("1")), preds, full,
                          min(deadline, time.process_time() + 0.1 * span))
            if node is not None:
                return ("cells", m_ast, node)
    node = _cover(sorted(pieces, key=lambda p: -bin(p[0]).count("1")), preds, full, deadline)
    return ("cells", m_ast, node) if node is not None else None


def construct_select(task, lib, consts, deadline):
    in_types, train = tuple(task["in_types"]), task["train"]
    L, _ = _args(in_types)
    for n, a in enumerate(L):
        if not all(y in i[a] for i, y in train):
            continue
        pts, groups = [], []
        for inputs, y in train:
            g = []
            for i in range(len(inputs[a])):
                g.append((len(pts), inputs[a][i] == y))
                pts.append(in_cell(inputs, in_types, a, i))
            groups.append(g)

        def accept(vec):
            for g in groups:
                first = next((ok for k, ok in g if vec[k]), None)
                if not first:
                    return False
            return True
        end = time.process_time() + (deadline - time.process_time()) / (len(L) - n)
        s = sc.GSearch(lib, in_coords(in_types), T_B, [(p, False) for p in pts], end, consts=consts, accept=accept)
        r, _ = s.run()
        if r is not None:
            return ("select", a, r[1])
    return None


def solve(task, deadline, lib=None):
    """A constructed cell representation reproducing every TRAIN example, or None."""
    lib = lib or ic.base_library()
    consts = ic.data_constants(task["train"])
    if task["out_type"] == T_L and T_L in task["in_types"]:
        sol = construct_list(task, lib, consts, deadline)
    elif task["out_type"] == T_I and T_L in task["in_types"]:
        sol = construct_select(task, lib, consts, deadline)
    else:
        return None
    if sol is not None and all(run(sol, lib, i, task["in_types"]) == o for i, o in task["train"]):
        return sol
    return None
