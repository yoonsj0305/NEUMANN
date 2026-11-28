"""EXT-0: language self-extension (stage3/DESIGN.md 13.5, decision tree 13.6).  No training, CPU only.

Engine: TF-0 (stage3/tf0.py) as is -- data (tf0.training, seed 0; fit = lengths 1-7, select = 8-10), L0 routing (a head
= one move per token class, 6 moves; path equivalence on the fit scored steps (positions at t and t-1); every single,
every pair of distinct paths, a greedy third head; pair only if >= single + 0.001), key = (x_t, per head the masked
read at t and t-1), rule table = most frequent output on the fit steps (ties: smallest output id), score = fraction of
the select scored steps right (a key not in the table is wrong).
Implementation (computes the same numbers; check (a) compares with TF-0): identical sequences are kept once with their
count as a weight (every score is a weighted fraction, identical to the per-example one); the head paths are computed by
a numba kernel with the move semantics of pf.candidates, the token classes and separators taken from the installed
pf / c1a functions (so the e0 / c0a adapters apply unchanged).

Extension grammar (13.5; the only human part):
  M  moves 6-9 added to the 6: +2, -2 (clamped to [0, t] like right / left), seek right, seek left: to the first cell
     in that direction (right: h < p <= t, left: p < h) holding x_t, inside the head's segment (same separator count
     g as the head's cell).  Not found -> the head stays and its read at that step is the empty symbol (recorded choice
     for "stops at the empty symbol").
  R  hidden register: r_t = delta(r_{t-1}, key_t) at every step (prompt included; key_t = the routing's key, the read
     at t - 1 is the empty symbol at t = 0), r_t joins the key.  delta: blue-fringe state merging with the EDSM score
     on the prefix tree of the fit key sequences (labels = the target at the scored steps; a merge is refused if it
     joins two different labels), red states <= 64 (more -> the candidate fails).  Candidates: no routing (x_t only)
     and the 20 best routings of the base search (singles, pairs, greedy triples; ties as TF-0).  A transition not
     in delta -> the register is dead (no key matches -> wrong).
  L  library channel: an adopted register of an earlier task, run on this task's sequences, gives a value per
     position; candidates add, to a routing (none or the 20 best of the base search), the value at t (the current
     cell, as x_t) and every head's masked value at t and t-1 (same masking as reads; recorded choice).  One library
     register per candidate.
  combinations (at most two per task): M+R (R on the 20 best routings of the M search), M+L, R+L (the register's key
  contains the library channel).
Search order and adoption (13.5): control = base, M, R, M+R; with library = base, the kinds adopted before (by use
count; ties M then R), L, the remaining singles (M, R), then M+R, M+L, R+L.  The first stage whose best candidate has
select score >= 0.999 is adopted; inside a stage: score, then |key components| x |rule table| (fit keys) smaller.
Judgment (one check): the adopted configuration on the out-of-distribution bins 11-20 / 21-30 / 31-40 (500 each,
tasks.eval_sets), example exact match >= 0.90 in every bin; a missing key is wrong; greedy decoding is used (it is
also compared with teacher forcing).  Rule table for the judgment: the whole training set (lengths 1-10; recorded
choice); the register / library structure is the one found on the fit set.
Discovered structures are pure data (JSON / npz): routing tables, key components, rule tables, register transitions.
Costs: CPU seconds split into search / table construction / verification.

  python stage3/ext0.py check-a --task copy|mul1     (a) TF-0 copy / N x 1 reproduced
  python stage3/ext0.py check-bc                     (b) hand parity register 1.000, (c) M unit strings
  python stage3/ext0.py stage --task T --stage base|M|R|MR [--reg ID]   (cached; L, ML, RL need --reg)
  python stage3/ext0.py control | library --order S | judge | hand | report
"""
from __future__ import annotations
import argparse
import hashlib
import heapq
import itertools
import json
import os
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT / "stage1"), str(ROOT / "stage2"), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.path.remove(str(HERE))
sys.path.insert(0, str(HERE))                    # stage3 first (stage2 also has an e0.py)

import numpy as np                                                   # noqa: E402
import numba                                                         # noqa: E402

OUT = pathlib.Path(os.environ.get("EXT0_OUT", HERE / "results" / "EXT-0"))
CACHE = OUT / "cache"
EMPTY, DEAD = -1, -2
FIT, SEL = (1, 7), (8, 10)
GAIN, ADOPT, PASS = 0.001, 0.999, 0.90
M_LIMIT = 2000                       # pairs over the best M_LIMIT paths by single score when m > M_LIMIT (recorded)
TOPR = 20
QMAX = 64
CAP_CPU = 6 * 3600
PAIR_BYTES = 1.5e9                   # memory cap for the pair codes (recorded; lowers the pair pool if needed)
OUT_OF = ("modular_arithmetic", "parity_check", "cycle_navigation", "modular_arithmetic_brackets",
          "stack_manipulation", "solve_equation", "missing_duplicate_string", "compute_sqrt", "odds_first",
          "binary_addition", "binary_multiplication", "bucket_sort")
INSIDE = ("even_pairs", "reverse_string", "duplicate_string")
MOVE_NAMES = ("stay", "right", "left", "next_sep", "start", "cont", "+2", "-2", "seek_right", "seek_left")


# ================================================================ setup, tokens
def setup(task):
    import torch
    torch.set_num_threads(1)
    import e_tasks as E
    if task in E.SUITE:
        import e0
        e0.install()
    else:
        import tf0
        tf0.setup(task)
    return TokInfo()


class TokInfo:
    """per token id: prompt-phase class, candidate separator (next_sep), segment separator (g); from the installed
    pf.token_classes / pf.candidates / c1a.separators"""

    def __init__(self):
        import torch
        import tasks as T
        import pf as PFM
        import c1a
        V = len(T.VOCAB)
        self.V, self.PAD, self.EOS = V, T.PAD, T.EOS
        self.eq, self.bar = T.TOK["="], T.TOK["|"]
        dig = torch.tensor([T.TOK[d] for d in T.DIGITS])
        x = torch.arange(V)[:, None]
        self.cls = PFM.token_classes(x, dig, T.TOK["+"], T.TOK["="], T.TOK["|"], T.TOK[T.NODES[0]],
                                     T.TOK[T.NODES[-1]] + 1)[:, 0].numpy().astype(np.int8)
        a = T.TOK[T.DIGITS[0]]
        tape = torch.stack([torch.full((V,), a), torch.arange(V)], 1)                 # [V, 2]
        issep = torch.isin(tape, torch.tensor([T.TOK["+"], T.TOK["="], T.TOK["|"]]))
        cand = PFM.candidates(tape, 1, torch.zeros(V, 1, dtype=torch.long), tape[:, 1], issep)
        self.sepc = (cand[:, 0, 3] == 1).numpy()
        self.sepg = c1a.separators(torch.arange(V)[None])[0].numpy()


# ================================================================ data (distinct sequences with weights)
class Data:
    def __init__(self, exs, tok, dedupe=True):
        """exs: [(prompt ids, answer ids incl. <eos>)]"""
        if dedupe:
            cnt = {}
            for p, a in exs:
                k = (tuple(p), tuple(a))
                cnt[k] = cnt.get(k, 0) + 1
            items = sorted(cnt.items())
            seqs, w = [k for k, _ in items], [c for _, c in items]
        else:
            seqs, w = [(tuple(p), tuple(a)) for p, a in exs], [1] * len(exs)
        n = len(seqs)
        self.n, self.w = n, np.array(w, dtype=np.float64)
        self.L = np.array([len(p) + len(a) for p, a in seqs], dtype=np.int64)
        Tm = int(self.L.max())
        X = np.full((n, Tm), tok.PAD, dtype=np.int64)
        for i, (p, a) in enumerate(seqs):
            X[i, :len(p) + len(a)] = p + a
        self.X, self.Tm = X, Tm
        end = (X == tok.eq) | (X == tok.bar)
        self.t0 = (X == tok.eq).argmax(1)
        assert (X == tok.eq).any(1).all()
        after = (np.cumsum(end, 1) - end) > 0
        self.CL = np.where(after, 5, tok.cls[X]).astype(np.int8)
        self.SEPC = tok.sepc[X]
        self.G = np.cumsum(tok.sepg[X], 1).astype(np.int32)
        si, st = [], []
        for i, (p, a) in enumerate(seqs):
            for t in range(len(p) - 1, len(p) + len(a) - 1):
                si.append(i)
                st.append(t)
        self.si, self.st = np.array(si, dtype=np.int64), np.array(st, dtype=np.int64)
        self.y = X[self.si, self.st + 1]
        self.sw = self.w[self.si]
        ai, at = [], []
        for i in range(n):
            for t in range(int(self.L[i]) - 1):
                ai.append(i)
                at.append(t)
        self.ai, self.at = np.array(ai, dtype=np.int64), np.array(at, dtype=np.int64)
        self.seqs = seqs
        self.memo = {}


# ================================================================ moves (numba)
@numba.njit(cache=True)
def _walk(X, L, CL, SEPC, G, col, i, pos, fail):
    h = 0
    for t in range(L[i]):
        m = col[CL[i, t]]
        xt = X[i, t]
        f = 0
        if m == 0:
            nh = h
        elif m == 1:
            nh = min(h + 1, t)
        elif m == 2:
            nh = max(h - 1, 0)
        elif m == 3:
            nh = h
            for p in range(h + 1, t + 1):
                if SEPC[i, p]:
                    nh = p
                    break
        elif m == 4:
            nh = 0
        elif m == 5:
            nh = h
            for p in range(h, t):
                if X[i, p] == xt:
                    nh = p + 1
                    break
        elif m == 6:
            nh = min(h + 2, t)
        elif m == 7:
            nh = max(h - 2, 0)
        elif m == 8:
            nh = h
            f = 1
            for p in range(h + 1, t + 1):
                if X[i, p] == xt and G[i, p] == G[i, h]:
                    nh = p
                    f = 0
                    break
        else:
            nh = h
            f = 1
            for p in range(h - 1, -1, -1):
                if X[i, p] == xt and G[i, p] == G[i, h]:
                    nh = p
                    f = 0
                    break
        h = nh
        pos[t] = h
        fail[t] = f


@numba.njit(cache=True)
def paths_kernel(X, L, CL, SEPC, G, cols, P, F):
    K = cols.shape[0]
    n = X.shape[0]
    pos = np.zeros(X.shape[1], dtype=np.int64)
    fail = np.zeros(X.shape[1], dtype=np.int64)
    for k in range(K):
        for i in range(n):
            _walk(X, L, CL, SEPC, G, cols[k], i, pos, fail)
            for t in range(L[i]):
                P[k, i, t] = pos[t]
                F[k, i, t] = fail[t]


@numba.njit(cache=True)
def sig_kernel(X, L, CL, SEPC, G, cols, off, cnt, W1, W2, out):
    """per column two hashes of (position * 2 + fail) at every scored step t and t - 1 (scored steps of sequence i:
    t = off[i] .. off[i] + cnt[i] - 1; W index runs over the scored steps in order)"""
    K = cols.shape[0]
    n = X.shape[0]
    pos = np.zeros(X.shape[1], dtype=np.int64)
    fail = np.zeros(X.shape[1], dtype=np.int64)
    for k in range(K):
        a = np.int64(0)
        b = np.int64(0)
        j = 0
        for i in range(n):
            _walk(X, L, CL, SEPC, G, cols[k], i, pos, fail)
            for t in range(off[i], off[i] + cnt[i]):
                v0 = pos[t] * 2 + fail[t]
                v1 = pos[t - 1] * 2 + fail[t - 1]
                a += W1[j, 0] * v0 + W1[j, 1] * v1
                b += W2[j, 0] * v0 + W2[j, 1] * v1
                j += 1
        out[k, 0] = a
        out[k, 1] = b


def paths(D, cols):
    cols = np.asarray(cols, dtype=np.int64).reshape(-1, 7)
    P = np.zeros((len(cols), D.n, D.Tm), dtype=np.int32)
    F = np.zeros((len(cols), D.n, D.Tm), dtype=np.int8)
    if len(cols):
        paths_kernel(D.X, D.L, D.CL, D.SEPC, D.G, cols, P, F)
    return P, F


def masked(D, P, F, tape):
    """[K, n, T] tape value at each head position if the head's segment bit is 1 and the move did not fail"""
    K = P.shape[0]
    idx = np.arange(D.n)[None, :, None]
    val = tape[idx, P]
    gp = D.G[idx, P]
    ref = gp[:, np.arange(D.n), D.t0][:, :, None]
    return np.where((gp == ref) & (F == 0), val, EMPTY).astype(np.int32)


def at_steps(M, D, which):
    """[K, n, T] -> [K, steps, 2] values at (t, t - 1) of the scored ('scored') or all ('all') steps"""
    si, st = (D.si, D.st) if which == "scored" else (D.ai, D.at)
    a = M[:, si, st]
    b = np.where(st[None] >= 1, M[:, si, np.maximum(st - 1, 0)], EMPTY)
    return np.stack([a, b], -1)


# ================================================================ scoring (weighted, TF-0 rule)
def dense(v):
    u, inv = np.unique(v, return_inverse=True)
    return inv.astype(np.int64), len(u)


class Scorer:
    def __init__(self, Fd, Sd):
        self.F, self.S = Fd, Sd
        fx, sx = Fd.X[Fd.si, Fd.st], Sd.X[Sd.si, Sd.st]
        d, self.nx = dense(np.concatenate([fx, sx]))
        self.fx, self.sx = d[:len(fx)], d[len(fx):]
        d, self.ny = dense(np.concatenate([Fd.y, Sd.y]))
        self.fy, self.sy = d[:len(Fd.y)], d[len(Fd.y):]
        self.fw, self.sw = Fd.sw, Sd.sw
        self.swt = float(Sd.sw.sum())
        self.nf = len(self.fy)

    def score(self, fk, sk, nk):
        ny = self.ny
        if nk * ny <= 20_000_000:
            cnt = np.bincount(fk * ny + self.fy, weights=self.fw, minlength=nk * ny).reshape(nk, ny)
            best = cnt.argmax(1)
            seen = cnt.max(1) > 0
            ok = (best[sk] == self.sy) & seen[sk]
        else:
            u, inv = np.unique(fk * ny + self.fy, return_inverse=True)
            c = np.bincount(inv, weights=self.fw)
            k, yv = u // ny, u % ny
            order = np.lexsort((yv, -c, k))
            k, yv = k[order], yv[order]
            first = np.ones(len(k), dtype=bool)
            first[1:] = k[1:] != k[:-1]
            tk, ty = k[first], yv[first]
            pos = np.clip(np.searchsorted(tk, sk), 0, len(tk) - 1)
            ok = (tk[pos] == sk) & (ty[pos] == self.sy)
        return float(self.sw[ok].sum() / self.swt)

    def rows_score(self, rf, rs):
        """raw key rows on fit / select steps -> (score, |table| = distinct fit keys)"""
        u, inv = np.unique(np.concatenate([rf, rs]), axis=0, return_inverse=True)
        inv = inv.reshape(-1).astype(np.int64)
        fk, sk = inv[:len(rf)], inv[len(rf):]
        return self.score(fk, sk, len(u)), int(len(np.unique(fk)))


def codes_pair(a, b):
    """dense codes of (t, t-1) values on two step sets with one dictionary"""
    c = np.concatenate([a, b]).astype(np.int64)
    d, n = dense((c[:, 0] + 3) * 4096 + (c[:, 1] + 3))
    dt = np.uint8 if n <= 256 else (np.uint16 if n <= 65536 else np.int32)
    return d[:len(a)].astype(dt), d[len(a):].astype(dt), n


# ================================================================ configurations -> key rows
def cfg_id(cfg):
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16]


def ncomp(cfg):
    h = len(cfg.get("routing", []))
    n = 1 + 2 * h
    if cfg.get("lib"):
        n += 1 + 2 * h
    if cfg.get("reg") is not None:
        n += 1
    return n


def rows(D, cfg, store, which="scored"):
    """raw key components [steps, C]: x_t, per head masked read (t, t-1), [library value at t, per head masked value
    (t, t-1)], [register state r_t]"""
    key = (which, json.dumps(cfg, sort_keys=True))
    if key in D.memo:
        return D.memo[key]
    si, st = (D.si, D.st) if which == "scored" else (D.ai, D.at)
    comps = [D.X[si, st][:, None]]
    rt = cfg.get("routing", [])
    if rt:
        P, F = paths(D, rt)
        M = masked(D, P, F, D.X)
        comps.append(at_steps(M, D, which).transpose(1, 0, 2).reshape(len(si), -1))
    if cfg.get("lib"):
        Lv = register_tape(D, store[cfg["lib"]], store)
        comps.append(Lv[si, st][:, None])
        if rt:
            M = masked(D, P, F, Lv)
            comps.append(at_steps(M, D, which).transpose(1, 0, 2).reshape(len(si), -1))
    if cfg.get("reg") is not None:
        R = register_tape(D, cfg["reg"], store)
        comps.append(R[si, st][:, None])
    out = np.concatenate(comps, 1).astype(np.int32)
    if len(D.memo) > 64:
        D.memo.clear()
    D.memo[key] = out
    return out


# ================================================================ registers
@numba.njit(cache=True)
def run_dfa(sym, start_idx, n_steps, trans, out):
    """sym: symbol id per step (-1 unknown) laid out per sequence; trans [Q, A] (-1 missing); out: state per step"""
    for i in range(start_idx.shape[0]):
        q = 0
        for j in range(start_idx[i], start_idx[i] + n_steps[i]):
            s = sym[j]
            if q >= 0:
                if s < 0:
                    q = DEAD
                else:
                    q = trans[q, s]
                    if q < 0:
                        q = DEAD
            out[j] = q


def map_rows(alpha, R):
    """rows R -> index in the alphabet rows (-1 if absent)"""
    if len(R) == 0:
        return np.zeros(0, dtype=np.int64)
    u, inv = np.unique(np.concatenate([alpha, R]), axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    u2a = np.full(len(u), -1, dtype=np.int64)
    u2a[inv[:len(alpha)]] = np.arange(len(alpha))
    return u2a[inv[len(alpha):]]


def register_tape(D, reg, store):
    """[n, T] register state after each position (DEAD beyond / when a transition is missing)"""
    key = ("regtape", reg["id"])
    if key in D.memo:
        return D.memo[key]
    if reg.get("hand"):
        out = HAND[reg["hand"]](D)
    else:
        allc = {"routing": reg["cfg"].get("routing", []), "lib": reg["cfg"].get("lib")}
        R = rows(D, allc, store, "all")
        sym = map_rows(np.array(reg["alphabet"], dtype=np.int32).reshape(-1, R.shape[1]), R)
        trans = np.array(reg["trans"], dtype=np.int64)
        starts = np.zeros(D.n, dtype=np.int64)
        nst = np.maximum(D.L - 1, 0)
        starts[1:] = np.cumsum(nst)[:-1]
        st = np.zeros(len(sym), dtype=np.int64)
        run_dfa(sym, starts, nst, trans, st)
        out = np.full((D.n, D.Tm), DEAD, dtype=np.int32)
        out[D.ai, D.at] = st
    D.memo[key] = out
    return out


def edsm(Fd, R, qmax=QMAX, deadline=None):
    """blue-fringe state merging (EDSM score) on the prefix tree of the key sequences of the fit set.
    R: key rows on Fd's 'all' steps.  Returns (register dict without id, info) or (None, info)."""
    alpha, sym = np.unique(R, axis=0, return_inverse=True)
    sym = sym.reshape(-1)
    # labels at the scored steps
    lab = {}
    for i, t, y in zip(Fd.si.tolist(), Fd.st.tolist(), Fd.y.tolist()):
        lab[(i, t)] = y
    # prefix tree
    child = [dict()]
    label = [None]
    conflict = 0
    j = 0
    for i in range(Fd.n):
        node = 0
        for t in range(int(Fd.L[i]) - 1):
            s = int(sym[j])
            j += 1
            nx = child[node].get(s)
            if nx is None:
                nx = len(child)
                child[node][s] = nx
                child.append(dict())
                label.append(None)
            node = nx
            y = lab.get((i, t))
            if y is not None:
                if label[node] is None:
                    label[node] = y
                elif label[node] != y:
                    conflict += 1
    N = len(child)
    info = {"pta_nodes": N, "alphabet": int(len(alpha)), "label_conflicts_in_pta": conflict}
    if conflict:
        info["failed"] = "conflicting labels in the prefix tree"
        return None, info
    # canonical numbering: BFS with children by symbol id
    order = [0]
    new = {0: 0}
    k = 0
    while k < len(order):
        v = order[k]
        k += 1
        for s in sorted(child[v]):
            c = child[v][s]
            new[c] = len(order)
            order.append(c)
    ch = [None] * N
    lb = [None] * N
    for old, nw in new.items():
        ch[nw] = sorted((s, new[c]) for s, c in child[old].items())
        lb[nw] = label[old]
    parent = list(range(N))
    trans = [dict(c) for c in ch]
    lbl = list(lb)

    def find(v):
        while parent[v] != v:
            v = parent[v]
        return v

    def fold(r, b, commit):
        log = []
        score = 0
        stack = [(r, b)]
        while stack:
            q, n = stack.pop()
            q = find(q)
            ln = lbl[n]
            if ln is not None:
                lq = lbl[q]
                if lq is None:
                    log.append((0, q, None))
                    lbl[q] = ln
                elif lq != ln:
                    undo(log)
                    return None
                else:
                    score += 1
            log.append((1, n, None))
            parent[n] = q
            tq = trans[q]
            for a, c in ch[n]:
                if a in tq:
                    stack.append((tq[a], c))
                else:
                    log.append((2, q, a))
                    tq[a] = c
        if not commit:
            undo(log)
        return score

    def undo(log):
        for kind, x, a in reversed(log):
            if kind == 0:
                lbl[x] = None
            elif kind == 1:
                parent[x] = x
            else:
                del trans[x][a]
    red = [0]
    redset = {0}
    merges = trials = 0
    while True:
        if deadline is not None and time.process_time() > deadline:
            info["failed"] = "cpu cap"
            return None, info
        blue = sorted({find(c) for r in red for c in trans[r].values()} - redset)
        if not blue:
            break
        best, promote = None, None
        for b in blue:
            if deadline is not None and time.process_time() > deadline:
                info["failed"] = "cpu cap"
                return None, info
            okb = False
            for r in red:
                trials += 1
                s = fold(r, b, False)
                if s is not None:
                    okb = True
                    if best is None or s > best[0]:
                        best = (s, b, r)
            if not okb:
                promote = b
                break
        if promote is not None:
            red.append(promote)
            redset.add(promote)
            if len(red) > qmax:
                info.update({"failed": "more than %d states" % qmax, "merges": merges, "trials": trials})
                return None, info
            continue
        fold(best[2], best[1], True)
        merges += 1
    sid = {r: q for q, r in enumerate(red)}
    T = np.full((len(red), len(alpha)), -1, dtype=np.int64)
    for r in red:
        for a, c in trans[r].items():
            T[sid[r], a] = sid[find(c)]
    info.update({"states": len(red), "merges": merges, "trials": trials,
                 "state_labels": [lbl[r] for r in red]})
    return {"alphabet": alpha.astype(int).tolist(), "trans": T.tolist(), "states": len(red)}, info


# ================================================================ hand registers (13.6-1(b), 13.7-4)
def _tape_from(D, fn):
    import tasks as T
    out = np.full((D.n, D.Tm), DEAD, dtype=np.int32)
    for i in range(D.n):
        toks = [T.VOCAB[v] for v in D.X[i, :D.L[i]]]
        st = fn(toks)
        out[i, :len(st)] = st
    return out


def _parity(toks):
    q, out = 0, []
    for tk in toks:
        if tk == "1":
            q ^= 1
        out.append(q)
    return out


HAND = {"parity": lambda D: _tape_from(D, _parity)}


# ================================================================ search stages
def load(task, tok):
    import tf0
    train = tf0.training(task, 100000)
    fit = [(p, a) for p, a, n in train if FIT[0] <= n <= FIT[1]]
    sel = [(p, a) for p, a, n in train if SEL[0] <= n <= SEL[1]]
    return train, Data(fit, tok), Data(sel, tok)


def present_classes(Fd):
    seen = set()
    for i in range(Fd.n):
        seen |= set(Fd.CL[i, :Fd.L[i] - 1].tolist())
    return sorted(int(c) for c in seen)


def columns(classes, nmoves):
    out = []
    for mv in itertools.product(range(nmoves), repeat=len(classes)):
        row = [0] * 7
        for c, m in zip(classes, mv):
            row[c] = m
        out.append(tuple(row))
    return out


def nonstay(col):
    return sum(m != 0 for m in col)


def tie(cols):
    return (sum(nonstay(c) for c in cols), tuple(sorted(tuple(c) for c in cols)))


def route_search(Fd, Sd, sc, nmoves, deadline=None):
    """TF-0 search (12.5) with nmoves moves; returns result dict incl. the 20 best routings"""
    C0 = time.process_time()
    classes = present_classes(Fd)
    cols = columns(classes, nmoves)
    off = Fd.st[np.r_[0, np.cumsum(np.bincount(Fd.si, minlength=Fd.n))[:-1]]]
    cnt = np.bincount(Fd.si, minlength=Fd.n).astype(np.int64)
    rs = np.random.default_rng(12345)
    W1 = rs.integers(1, 2 ** 31, size=(len(Fd.si), 2), dtype=np.int64)
    W2 = rs.integers(1, 2 ** 31, size=(len(Fd.si), 2), dtype=np.int64)
    carr = np.array(cols, dtype=np.int64)
    sig = np.zeros((len(cols), 2), dtype=np.int64)
    for j in range(0, len(cols), 4096):
        sig_kernel(Fd.X, Fd.L, Fd.CL, Fd.SEPC, Fd.G, carr[j:j + 4096], off.astype(np.int64), cnt, W1, W2,
                   sig[j:j + 4096])
    groups = {}
    for c, (a, b) in zip(cols, sig.tolist()):
        groups.setdefault((a, b), []).append(c)
    reps = sorted((min(v, key=lambda c: (nonstay(c), c)) for v in groups.values()), key=lambda c: (nonstay(c), c))
    m = len(reps)
    res = {"moves": nmoves, "classes": classes, "columns": len(cols), "m_distinct_paths": m,
           "path_cpu_seconds": round(time.process_time() - C0, 1)}
    codes = []
    for j in range(0, m, 64):
        ch = reps[j:j + 64]
        Pf, Ff = paths(Fd, ch)
        Ps, Fs = paths(Sd, ch)
        Mf, Ms = at_steps(masked(Fd, Pf, Ff, Fd.X), Fd, "scored"), at_steps(masked(Sd, Ps, Fs, Sd.X), Sd, "scored")
        for k in range(len(ch)):
            codes.append(codes_pair(Mf[k], Ms[k]))

    def keyset(idx):
        fk, sk, nk = sc.fx.copy(), sc.sx.copy(), sc.nx
        for i in idx:
            cf, cs, n = codes[i]
            fk, sk, nk = fk * n + cf.astype(np.int64), sk * n + cs.astype(np.int64), nk * n
        return fk, sk, nk

    def score_set(idx):
        return sc.score(*keyset(idx))
    evaluated = 0
    top = []                                  # heap of (score, -tie) best TOPR routings

    def push(s, idx):
        if len(top) >= TOPR and s < top[0][0]:
            return
        cl = [reps[i] for i in idx]
        item = (s, _neg(tie(cl)), tuple(idx))
        if len(top) < TOPR:
            heapq.heappush(top, item)
        elif item > top[0]:
            heapq.heapreplace(top, item)
    singles = []
    for i in range(m):
        s = score_set([i])
        singles.append((s, i))
        push(s, [i])
        evaluated += 1
    best1 = max(z[0] for z in singles)
    s1 = min([z for z in singles if z[0] == best1], key=lambda z: tie([reps[z[1]]]))
    res["single"] = {"score": s1[0], "column": list(reps[s1[1]])}
    pool = list(range(m))
    if m > M_LIMIT:
        pool = [i for _, i in sorted(singles, key=lambda z: (-z[0], tie([reps[z[1]]])))[:M_LIMIT]]
    nsteps = len(sc.fx) + len(sc.sx)
    cap = max(2, int(PAIR_BYTES / max(1, nsteps)))
    if len(pool) > cap:
        pool = [i for _, i in sorted(singles, key=lambda z: (-z[0], tie([reps[z[1]]])))[:cap]]
    pool.sort()
    res["pair_pool"] = len(pool)
    bestp, bp = -1.0, None
    t1 = time.process_time()
    for a_, i in enumerate(pool):
        if deadline is not None and time.process_time() > deadline:
            res["capped"] = "cpu cap during pairs"
            break
        cf, cs, n = codes[i]
        fk0, sk0, nk0 = sc.fx * n + cf.astype(np.int64), sc.sx * n + cs.astype(np.int64), sc.nx * n
        for j in pool[a_ + 1:]:
            cf2, cs2, n2 = codes[j]
            s = sc.score(fk0 * n2 + cf2.astype(np.int64), sk0 * n2 + cs2.astype(np.int64), nk0 * n2)
            evaluated += 1
            push(s, [i, j])
            if s > bestp or (s == bestp and tie([reps[i], reps[j]]) < tie([reps[k] for k in bp])):
                bestp, bp = s, (i, j)
    res["pair"] = {"score": bestp, "columns": [list(reps[i]) for i in bp] if bp else None,
                   "cpu_seconds": round(time.process_time() - t1, 1)}
    chosen, cur = (list(bp), bestp) if bp else ([s1[1]], s1[0])
    best3, b3 = -1.0, None
    if bp:
        for k in range(m):
            if k in chosen:
                continue
            s = score_set(chosen + [k])
            evaluated += 1
            push(s, chosen + [k])
            if s > best3 or (s == best3 and tie([reps[i] for i in chosen + [k]]) < tie(
                    [reps[i] for i in chosen + [b3]])):
                best3, b3 = s, k
    res["triple"] = {"score": best3, "added_column": list(reps[b3]) if b3 is not None else None,
                     "gain": best3 - cur if b3 is not None else None}
    if b3 is not None and best3 - cur >= GAIN:
        chosen, cur = chosen + [b3], best3
    if bp and bestp - s1[0] >= GAIN:
        sel_idx, sel_score = chosen, cur
    else:
        sel_idx, sel_score = [s1[1]], s1[0]
    routing = [list(reps[i]) for i in sel_idx]
    res["selected"] = {"routing": routing, "score": sel_score}
    res["top"] = [{"score": s, "routing": [list(reps[i]) for i in idx]}
                  for s, _, idx in sorted(top, reverse=True)]
    res["candidates_evaluated"] = evaluated
    return res


class _neg:
    """reverse ordering wrapper for tie tuples in the max-heap"""
    def __init__(self, v):
        self.v = v

    def __lt__(self, o):
        return self.v > o.v

    def __gt__(self, o):
        return self.v < o.v

    def __eq__(self, o):
        return self.v == o.v


# ================================================================ stage driver with cache
class Task:
    def __init__(self, task):
        self.task = task
        self.tok = setup(task)
        t = time.process_time()
        self.train, self.F, self.S = load(task, self.tok)
        self.sc = Scorer(self.F, self.S)
        self.load_seconds = round(time.process_time() - t, 1)
        self.store = {}

    def cand(self, cfg):
        """(score, |table|, occam) of a configuration (rows-based scoring)"""
        rf, rs = rows(self.F, cfg, self.store), rows(self.S, cfg, self.store)
        s, tsz = self.sc.rows_score(rf, rs)
        return s, tsz, ncomp(cfg) * tsz


def cache_path(task, stage, reg=None):
    return CACHE / task / ("%s%s.json" % (stage, ("__" + reg.replace(":", "_")) if reg else ""))


def library_store():
    """every register adopted anywhere (pure data): results/EXT-0/registers/<id>.json"""
    d = OUT / "registers"
    out = {}
    if d.exists():
        for f in sorted(d.glob("*.json")):
            r = json.loads(f.read_text())
            out[r["id"]] = r
    return out


def save_register(reg):
    d = OUT / "registers"
    d.mkdir(parents=True, exist_ok=True)
    (d / ("%s.json" % reg["id"].replace(":", "_"))).write_text(json.dumps(reg))


def run_stage(T, stage, reg_id=None, deadline=None):
    """one stage on one task; cached.  Returns the stage record."""
    f = cache_path(T.task, stage, reg_id)
    if f.exists():
        return json.loads(f.read_text())
    f.parent.mkdir(parents=True, exist_ok=True)
    C0 = time.process_time()
    rec = {"task": T.task, "stage": stage, "reg": reg_id}
    store = library_store()
    T.store.update(store)
    if stage in ("base", "M"):
        r = route_search(T.F, T.S, T.sc, 6 if stage == "base" else 10, deadline)
        cfg = {"moves": r["moves"], "routing": r["selected"]["routing"]}
        s, tsz, occ = T.cand(cfg)
        assert abs(s - r["selected"]["score"]) < 1e-9, (s, r["selected"]["score"])
        rec.update({"search": {k: v for k, v in r.items() if k != "top"}, "top": r["top"],
                    "best": {"cfg": cfg, "score": s, "table": tsz, "occam": occ},
                    "candidates_evaluated": r["candidates_evaluated"]})
    else:
        src = "M" if stage in ("MR", "ML") else "base"
        top = run_stage(T, src, None, deadline)["top"]
        mv = 10 if src == "M" else 6
        routings = [[]] + [t["routing"] for t in top]
        cands = []
        for rt in routings:
            if deadline is not None and time.process_time() > deadline:
                rec["capped"] = "cpu cap"
                break
            base = {"moves": mv, "routing": rt}
            if stage in ("L", "ML"):
                cfg = dict(base, lib=reg_id)
                s, tsz, occ = T.cand(cfg)
                cands.append({"cfg": cfg, "score": s, "table": tsz, "occam": occ})
                continue
            rcfg = dict(base, lib=reg_id) if stage == "RL" else base
            R = rows(T.F, rcfg, T.store, "all")
            t1 = time.process_time()
            dfa, info = edsm(T.F, R, deadline=deadline)
            info["edsm_cpu_seconds"] = round(time.process_time() - t1, 1)
            if dfa is None:
                cands.append({"cfg": rcfg, "score": None, "edsm": info})
                continue
            regd = dict(dfa, id="%s:%s:%s:%d" % (T.task, stage, reg_id or "-", len(cands)), task=T.task,
                        cfg=rcfg, ncomp=int(R.shape[1]))
            cfg = dict(rcfg, reg=regd)
            s, tsz, occ = T.cand(cfg)
            cands.append({"cfg": cfg, "score": s, "table": tsz, "occam": occ,
                          "edsm": {k: v for k, v in info.items() if k != "state_labels"},
                          "register_id": regd["id"]})
        ok = [c for c in cands if c["score"] is not None]
        rec["candidates"] = [{k: (v if k != "cfg" else _short(v)) for k, v in c.items()} for c in cands]
        rec["candidates_evaluated"] = len(cands)
        rec["best"] = (max(ok, key=lambda c: (c["score"], -c["occam"])) if ok else None)
    rec["cpu_seconds_search"] = round(time.process_time() - C0, 1)
    f.write_text(json.dumps(rec))
    return rec


def _short(cfg):
    c = dict(cfg)
    if isinstance(c.get("reg"), dict):
        c["reg"] = c["reg"]["id"]
    return c


def _neg_noop():
    pass


# ================================================================ checks (13.6-1)
def cmd_check_a(a):
    """(a) the base engine reproduces TF-0 copy / N x 1 (m, single / pair / triple scores, selected routing), and the
    numba paths equal tf0.batch_paths (6 moves) on sampled columns"""
    import torch
    import tf0
    T = Task(a.task)
    d = OUT / "checks"
    d.mkdir(parents=True, exist_ok=True)
    ref = json.loads((HERE / "results" / "TF-0" / a.task / "final.json").read_text())
    C0 = time.process_time()
    r = route_search(T.F, T.S, T.sc, 6)
    rng = random.Random(0)
    cols = rng.sample(columns(present_classes(T.F), 6), 12)
    x = torch.tensor(T.F.X[:300])
    pb = tf0.batch_paths(x, torch.tensor(cols)).numpy()                   # [B, K, T]
    P, _ = paths(T.F, cols)
    same = all(np.array_equal(pb[i, k, :T.F.L[i]], P[k, i, :T.F.L[i]]) for i in range(300) for k in range(len(cols)))
    out = {"task": a.task,
           "m": [r["m_distinct_paths"], ref["m_distinct_paths"]],
           "single": [r["single"]["score"], ref["single"]["score"]],
           "pair": [r["pair"]["score"], ref["pair"]["score"]],
           "triple": [r["triple"]["score"], ref["triple"]["score"]],
           "selected_routing": [r["selected"]["routing"], ref["selected"]["routing"]],
           "selected_score": [r["selected"]["score"], ref["selected"]["score"]],
           "paths_equal_tf0_batch_paths_12_columns_300_sequences": same,
           "distinct_fit_sequences": T.F.n, "distinct_select_sequences": T.S.n,
           "cpu_seconds": round(time.process_time() - C0, 1)}
    close = lambda u, v: abs(u - v) < 1e-9                                 # noqa: E731
    out["pass"] = bool(out["m"][0] == out["m"][1] and close(*out["single"]) and close(*out["pair"])
                       and close(*out["triple"]) and out["selected_routing"][0] == out["selected_routing"][1]
                       and same)
    (d / ("a_%s.json" % a.task)).write_text(json.dumps(out, indent=1))
    print(json.dumps(out), flush=True)


def ref_walk(toks, cls, sepc, g, col):
    """plain reference of the 10 moves (definitions above), for check (c)"""
    h, P, Fl = 0, [], []
    for t, xt in enumerate(toks):
        m = col[cls[t]]
        f = 0
        if m == 0:
            nh = h
        elif m == 1:
            nh = min(h + 1, t)
        elif m == 2:
            nh = max(h - 1, 0)
        elif m == 3:
            nh = next((p for p in range(h + 1, t + 1) if sepc[p]), h)
        elif m == 4:
            nh = 0
        elif m == 5:
            nh = next((p + 1 for p in range(h, t) if toks[p] == xt), h)
        elif m == 6:
            nh = min(h + 2, t)
        elif m == 7:
            nh = max(h - 2, 0)
        elif m == 8:
            q = [p for p in range(h + 1, t + 1) if toks[p] == xt and g[p] == g[h]]
            nh, f = (q[0], 0) if q else (h, 1)
        else:
            q = [p for p in range(h - 1, -1, -1) if toks[p] == xt and g[p] == g[h]]
            nh, f = (q[0], 0) if q else (h, 1)
        h = nh
        P.append(h)
        Fl.append(f)
    return P, Fl


def cmd_check_bc(a):
    import tasks as T
    d = OUT / "checks"
    d.mkdir(parents=True, exist_ok=True)
    out = {}
    # (b) hand two-state parity register in the same table / score code
    Tk = Task("parity_check")
    reg = {"id": "hand:parity", "hand": "parity"}
    s, tsz, occ = Tk.cand({"moves": 6, "routing": [], "reg": reg})
    out["b"] = {"task": "parity_check", "config": "x_t + hand parity register (2 states)", "select_score": s,
                "table": tsz, "pass": s == 1.0}
    # (b') info only: EDSM on x_t alone
    t1 = time.process_time()
    R = rows(Tk.F, {"moves": 6, "routing": []}, Tk.store, "all")
    dfa, info = edsm(Tk.F, R)
    sc_ = None
    if dfa is not None:
        regd = dict(dfa, id="dev:parity:edsm", task="parity_check", cfg={"moves": 6, "routing": []}, ncomp=1)
        sc_ = Tk.cand({"moves": 6, "routing": [], "reg": regd})[0]
    out["b_info_edsm_x_t_only"] = {"edsm": {k: v for k, v in info.items() if k != "state_labels"},
                                   "select_score": sc_, "cpu_seconds": round(time.process_time() - t1, 1)}
    # (c) the four M moves on three hand strings
    tok = Tk.tok
    strings = [("<bos> 2 0 2 1 =".split(), "0 1 2 2".split()),
               ("<bos> 1 0 + 1 1 =".split(), "0 0 1".split()),
               ("<bos> 0 1 1 0 1 0 =".split(), "1 1 1 0 0 0".split())]
    exs = [([T.TOK[x] for x in p], [T.TOK[x] for x in a_] + [T.EOS]) for p, a_ in strings]
    D = Data(exs, tok, dedupe=False)
    # columns (class: 0 digit, 1 op, 2 '=', 5 answer phase, 6 other): moves under test on the answer phase
    cols = {"+2": [0, 0, 4, 0, 0, 6, 0], "-2": [1, 0, 0, 0, 0, 7, 0], "seek_right": [1, 0, 4, 0, 0, 8, 0],
            "seek_left": [1, 0, 0, 0, 0, 9, 0]}
    expect_A = {"+2": ([0, 0, 0, 0, 0, 0, 2, 4, 6, 8, 10], [0] * 11),
                "-2": ([0, 1, 2, 3, 4, 4, 2, 0, 0, 0, 0], [0] * 11),
                "seek_right": ([0, 1, 2, 3, 4, 0, 2, 4, 4, 4, 4], [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]),
                "seek_left": ([0, 1, 2, 3, 4, 4, 2, 2, 1, 1, 1], [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1])}
    res = {}
    allok = True
    for name, col in cols.items():
        P, F = paths(D, [col])
        per = []
        for i in range(D.n):
            Li = int(D.L[i])
            toks = D.X[i, :Li].tolist()
            rp, rf = ref_walk(toks, D.CL[i, :Li].tolist(), D.SEPC[i, :Li].tolist(), D.G[i, :Li].tolist(), col)
            kp, kf = P[0, i, :Li].tolist(), F[0, i, :Li].tolist()
            ok = (kp, kf) == (rp, rf)
            if i == 0:
                ok = ok and (kp, kf) == expect_A[name]
            per.append({"string": " ".join(strings[i][0] + strings[i][1] + ["<eos>"]), "positions": kp,
                        "fail": kf, "equals_reference": (kp, kf) == (rp, rf),
                        "equals_hand_expectation": ((kp, kf) == expect_A[name]) if i == 0 else None})
            allok = allok and ok
        res[name] = {"column": col, "strings": per}
    out["c"] = {"moves": res, "pass": allok}
    out["pass"] = bool(out["b"]["pass"] and allok)
    (d / "bc.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"b": out["b"], "b_info": out["b_info_edsm_x_t_only"], "c_pass": allok}), flush=True)


# ================================================================ stage CLI (one task per process)
def cmd_stage(a):
    T = Task(a.task)
    budget = float(a.deadline) if a.deadline else None
    deadline = (time.process_time() + budget) if budget else None
    r = run_stage(T, a.stage, a.reg, deadline)
    b = r.get("best")
    print(json.dumps({"task": a.task, "stage": a.stage, "reg": a.reg,
                      "best_score": b["score"] if b else None, "cpu": r["cpu_seconds_search"],
                      "candidates": r["candidates_evaluated"], "capped": r.get("capped")}), flush=True)


def stage_rec(task, stage, reg=None, budget=None):
    """cached stage record, computed in a subprocess if missing"""
    f = cache_path(task, stage, reg)
    if not f.exists():
        tot = total_cpu()
        if tot > TOTAL_CAP:
            raise SystemExit("STOP (13.6-6): total CPU %.0f s > %d s" % (tot, TOTAL_CAP))
        import subprocess
        cmd = [sys.executable, str(HERE / "ext0.py"), "stage", "--task", task, "--stage", stage]
        if reg:
            cmd += ["--reg", reg]
        if budget:
            cmd += ["--deadline", str(budget)]
        logf = OUT / "logs" / ("%s.log" % task)
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a") as fh:
            rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
        if rc != 0 or not f.exists():
            raise RuntimeError("stage failed: %s %s %s rc=%s" % (task, stage, reg, rc))
    return json.loads(f.read_text())


TOTAL_CAP = 72 * 3600


def total_cpu():
    t = 0.0
    for f in CACHE.glob("*/*.json"):
        t += json.loads(f.read_text()).get("cpu_seconds_search", 0.0)
    for f in (OUT / "judge").glob("*.json"):
        r = json.loads(f.read_text())
        t += r.get("cpu_table", 0.0) + r.get("cpu_verify", 0.0)
    return t


KINDS = {"base": (), "M": ("M",), "R": ("R",), "MR": ("M", "R"), "L": ("L",), "ML": ("M", "L"), "RL": ("R", "L")}


def stage_best(task, stage, regs, budget=None):
    """(best candidate over the stage's registers (L stages) or the stage, cost dict, sub-records)"""
    if stage in ("L", "ML", "RL"):
        recs = [stage_rec(task, stage, r, budget) for r in regs]
    else:
        recs = [stage_rec(task, stage, None, budget)]
    best = None
    for r in recs:
        b = r.get("best")
        if b and b["score"] is not None and (best is None or (b["score"], -b["occam"]) > (best["score"], -best["occam"])):
            best = dict(b, stage=stage, reg=r.get("reg"))
    cost = {"cpu": sum(r["cpu_seconds_search"] for r in recs), "candidates": sum(r["candidates_evaluated"] for r in recs),
            "capped": any(r.get("capped") or (r.get("search") or {}).get("capped") for r in recs)}
    return best, cost


def walk_stages(task, stages, regs, budget_total=None):
    """try stages in order until one reaches ADOPT; returns record"""
    spent = 0.0
    tried = []
    best_any = None
    adopted = None
    for st in stages:
        if st in ("L", "ML", "RL") and not regs:
            continue
        left = None if budget_total is None else max(60.0, budget_total - spent)
        if budget_total is not None and spent >= budget_total:
            tried.append({"stage": st, "skipped": "cpu cap %d s" % budget_total})
            break
        b, cost = stage_best(task, st, regs, left)
        spent += cost["cpu"]
        tried.append({"stage": st, "best_score": b["score"] if b else None, **cost})
        if b and (best_any is None or b["score"] > best_any["score"]):
            best_any = b
        if b and b["score"] >= ADOPT:
            adopted = b
            break
    return {"task": task, "tried": tried, "adopted": adopted, "best_any": best_any,
            "cost_cpu": round(spent, 1), "cost_candidates": sum(t.get("candidates", 0) for t in tried)}


def cmd_control(a):
    import e_tasks as E
    d = OUT / "control"
    d.mkdir(parents=True, exist_ok=True)
    write_meta()
    for task in (a.tasks.split(",") if a.tasks else E.SUITE):
        f = d / ("%s.json" % task)
        if f.exists():
            continue
        r = walk_stages(task, ["base", "M", "R", "MR"], [], CAP_CPU)
        r["capped"] = r["cost_cpu"] >= CAP_CPU
        f.write_text(json.dumps(r, indent=1))
        print(task, "adopted", (r["adopted"] or {}).get("stage"), (r["adopted"] or {}).get("score"),
              "best", (r["best_any"] or {}).get("score"), "cpu", r["cost_cpu"], flush=True)


def order_of(seed):
    import e_tasks as E
    o = list(E.SUITE)
    random.Random("EXT-0:order:%d" % seed).shuffle(o)
    return o


def cmd_library(a):
    d = OUT / "library"
    d.mkdir(parents=True, exist_ok=True)
    f = d / ("order%d.json" % a.order)
    if f.exists():
        return
    regs, counts, out = [], {"M": 0, "R": 0, "L": 0}, []
    for task in order_of(a.order):
        used = sorted([k for k in ("M", "R") if counts[k] > 0], key=lambda k: (-counts[k], k != "M"))
        stages = ["base"] + used + ["L"] + [k for k in ("M", "R") if k not in used] + ["MR", "ML", "RL"]
        lib_before = list(regs)
        counts_before = dict(counts)
        r = walk_stages(task, stages, regs, CAP_CPU)
        ad = r["adopted"]
        kinds = KINDS[ad["stage"]] if ad else ()
        r["library_before"] = lib_before
        r["kind_counts_before"] = counts_before
        r["transfer"] = bool(ad and ("L" in kinds or any(counts_before.get(k, 0) > 0 for k in kinds)))
        for k in kinds:
            counts[k] += 1
        if ad and isinstance(ad["cfg"].get("reg"), dict):
            save_register(ad["cfg"]["reg"])
            if ad["cfg"]["reg"]["id"] not in regs:
                regs.append(ad["cfg"]["reg"]["id"])
        out.append(r)
        print("order", a.order, task, "adopted", ad["stage"] if ad else None, ad["score"] if ad else None,
              "cpu", r["cost_cpu"], "lib", len(regs), flush=True)
    f.write_text(json.dumps({"order": order_of(a.order), "tasks": out}, indent=1))


def write_meta():
    import h0a
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "env.json").write_text(json.dumps(h0a.env(["stage3/ext0.py", "stage3/tf0.py", "stage3/e_tasks.py"]),
                                             indent=1) if not (OUT / "env.json").exists() else (OUT / "env.json").read_text())
    if not (OUT / "config.json").exists():
        (OUT / "config.json").write_text(json.dumps({
            "design": "stage3/DESIGN.md 13.5, 13.6", "tasks": OUT_OF + INSIDE, "out_of_expressivity": OUT_OF,
            "inside_expressivity": INSIDE, "data": "tf0.training(task, 100000) = tasks.train_set(task, 100000, 0)",
            "fit_lengths": FIT, "select_lengths": SEL, "moves": MOVE_NAMES, "adopt": ADOPT, "pass": PASS,
            "m_limit_pairs": M_LIMIT, "pair_bytes_cap": PAIR_BYTES, "top_routings_for_R_L": TOPR, "qmax": QMAX,
            "cpu_cap_per_task_control": CAP_CPU, "control_stages": ["base", "M", "R", "MR"],
            "library_stages": "base, used kinds by count (M before R on ties), L, remaining singles (M, R), MR, ML, RL",
            "orders": "random.Random('EXT-0:order:<seed>').shuffle(e_tasks.SUITE), seeds 0-4",
            "ood": "tasks.eval_sets(task, 10, 500) bins 11-20 / 21-30 / 31-40"}, indent=1))


# ================================================================ judgment (one check)
def build_table(D, cfg, store):
    R = rows(D, cfg, store)
    u, inv = np.unique(R, axis=0, return_inverse=True)
    inv = inv.reshape(-1).astype(np.int64)
    yv, yd = np.unique(D.y, return_inverse=True)
    ny = len(yv)
    uu, ii = np.unique(inv * ny + yd, return_inverse=True)
    c = np.bincount(ii.reshape(-1), weights=D.sw)
    k, yy = uu // ny, uu % ny
    order = np.lexsort((yy, -c, k))
    k, yy = k[order], yy[order]
    first = np.ones(len(k), dtype=bool)
    first[1:] = k[1:] != k[:-1]
    out = np.full(len(u), -1, dtype=np.int64)
    out[k[first]] = yv[yy[first]]
    return u, out


def lookup(keys, outs, R):
    idx = map_rows(keys, R)
    return np.where(idx >= 0, outs[np.maximum(idx, 0)], -1)


def judge(T, cfg, store):
    import tasks as T_
    C0 = time.process_time()
    Dtr = Data([(p, a) for p, a, _ in T.train], T.tok)
    keys, outs = build_table(Dtr, cfg, store)
    t_table = time.process_time() - C0
    C1 = time.process_time()
    ev = T_.eval_sets(T.task, 10, 500)
    res = {}
    for lab, exs in ev.items():
        if not lab.startswith("ood"):
            continue
        D = Data([(list(p), list(a)) for p, a in exs], T.tok, dedupe=False)
        R = rows(D, cfg, store)
        pred = lookup(keys, outs, R)
        miss = pred < 0
        bad = (pred != D.y)
        ex_ok = np.bincount(D.si, weights=bad.astype(float), minlength=D.n) == 0
        g_ok = greedy(T, cfg, store, keys, outs, exs)
        res[lab] = {"examples": D.n, "accuracy_teacher_forced": float(ex_ok.mean()),
                    "accuracy_greedy": float(np.mean(g_ok)), "greedy_equals_teacher_forced": bool(
                        (np.array(g_ok) == ex_ok).all()), "missing_key_step_rate": float(miss.mean()),
                    "wrong_step_rate": float(bad.mean())}
    t_ver = time.process_time() - C1
    solved = all(v["accuracy_greedy"] >= PASS for v in res.values())
    return {"bins": res, "solved": solved, "table_size": int(len(keys)), "cpu_table": round(t_table, 1),
            "cpu_verify": round(t_ver, 1)}


def greedy(T, cfg, store, keys, outs, exs):
    cur = [list(p) for p, _ in exs]
    gold = [list(a) for _, a in exs]
    done = [False] * len(exs)
    ok = [False] * len(exs)
    out = [[] for _ in exs]
    for _ in range(max(len(g) for g in gold) + 3):
        act = [i for i in range(len(exs)) if not done[i]]
        if not act:
            break
        D = Data([(cur[i], [T.tok.EOS]) for i in act], T.tok, dedupe=False)
        R = rows(D, cfg, store)
        pred = lookup(keys, outs, R)
        for j, i in enumerate(act):
            v = int(pred[j])
            if v < 0:
                done[i] = True
                continue
            cur[i].append(v)
            out[i].append(v)
            if v == T.tok.EOS or len(out[i]) > len(gold[i]) + 2:
                done[i] = True
                ok[i] = out[i] == gold[i]
    return ok


def cmd_judge_task(a):
    T = Task(a.task)
    d = OUT / "judge"
    d.mkdir(parents=True, exist_ok=True)
    cfgs = json.loads(a.cfgs)
    store = library_store()
    T.store.update(store)
    for c in cfgs:
        cid = cfg_id(c)
        f = d / ("%s__%s.json" % (a.task, cid))
        if f.exists():
            continue
        r = judge(T, c, T.store)
        r.update({"task": a.task, "cfg_id": cid, "cfg": _short(c)})
        f.write_text(json.dumps(r, indent=1))
        print(a.task, cid, r["solved"], {k: v["accuracy_greedy"] for k, v in r["bins"].items()}, flush=True)


def adopted_cfgs():
    """{task: [cfg]} adopted in control and in every library order"""
    out = {}
    for f in sorted((OUT / "control").glob("*.json")):
        r = json.loads(f.read_text())
        if r["adopted"]:
            out.setdefault(r["task"], []).append(r["adopted"]["cfg"])
    for f in sorted((OUT / "library").glob("order*.json")):
        for r in json.loads(f.read_text())["tasks"]:
            if r["adopted"]:
                out.setdefault(r["task"], []).append(r["adopted"]["cfg"])
    uniq = {}
    for t, cs in out.items():
        seen = {}
        for c in cs:
            seen[cfg_id(c)] = c
        uniq[t] = list(seen.values())
    return uniq


def cmd_judge(a):
    import subprocess
    for task, cs in adopted_cfgs().items():
        for c in cs:
            if isinstance(c.get("reg"), dict):
                save_register(c["reg"])
        todo = [c for c in cs if not (OUT / "judge" / ("%s__%s.json" % (task, cfg_id(c)))).exists()]
        if not todo:
            continue
        tmp = OUT / "logs" / ("judge_%s.json" % task)
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(todo))
        with open(OUT / "logs" / ("%s.log" % task), "a") as fh:
            subprocess.check_call([sys.executable, str(HERE / "ext0.py"), "judge-task", "--task", task,
                                   "--cfgs-file", str(tmp)], stdout=fh, stderr=subprocess.STDOUT)


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("check-a")
    q.add_argument("--task", choices=("copy", "mul1"), required=True)
    sp.add_parser("check-bc")
    q = sp.add_parser("stage")
    q.add_argument("--task", required=True)
    q.add_argument("--stage", choices=tuple(KINDS), required=True)
    q.add_argument("--reg")
    q.add_argument("--deadline")
    q = sp.add_parser("control")
    q.add_argument("--tasks")
    q = sp.add_parser("library")
    q.add_argument("--order", type=int, required=True)
    sp.add_parser("judge")
    q = sp.add_parser("judge-task")
    q.add_argument("--task", required=True)
    q.add_argument("--cfgs-file", required=True)
    a = p.parse_args()
    if a.cmd == "judge-task":
        a.cfgs = pathlib.Path(a.cfgs_file).read_text()
    {"check-a": cmd_check_a, "check-bc": cmd_check_bc, "stage": cmd_stage, "control": cmd_control,
     "library": cmd_library, "judge": cmd_judge, "judge-task": cmd_judge_task}[a.cmd](a)


if __name__ == "__main__":
    main()
