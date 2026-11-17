"""Stage 1 tasks (CLAUDE.md): addition, parity, associative recall (Phase A'); graph reachability (Phase A only,
excluded from Stage 1 by the 2026-11-17 decision; kept so the Phase A records stay reproducible).

Every task is a prompt -> answer token sequence; the loss is on the answer (and <eos>) only.  Numbers are written
least significant digit first (the standard Abacus setting: digits of equal significance align).

  addition      a + b; training: the two operand lengths drawn INDEPENDENTLY and uniformly from 1..10.
                Evaluation is binned by the LONGER operand's length: in-distribution 1-10 (the training
                distribution), out-of-distribution 11-20 / 21-30 / 31-40 (longer length uniform in the bin, the other
                operand's length uniform in 1..longer, which operand is longer at random).
  parity        n bits -> their xor; training n uniform in 1..16; evaluation in-distribution 1-16,
                out-of-distribution 17-32 / 33-48 / 49-64 (n uniform in the bin).
  reachability  a random directed graph on n nodes (names drawn from a fixed pool of 100, round(1.5 n) distinct
                edges, listed in random order) and a query (s, t) -> Y / N, balanced; training n uniform in 4..8;
                evaluation in-distribution 4-8, out-of-distribution 9-16 / 17-24 / 25-32.
  assoc         k1 v1 k2 v2 ... kn vn | q = -> v: n distinct keys from the 100 node names, single-digit values, the
                query uniform over the keys; training n uniform in 4..16; evaluation in-distribution 4-16,
                out-of-distribution 17-32 / 33-48 / 49-64.
The training set is N i.i.d. draws from the training distribution (fixed once per seed; duplicates are allowed, so
the distribution is exact).  Evaluation sets use their own fixed seeds.
"""
from __future__ import annotations
import random

DIGITS = [str(i) for i in range(10)]
SYMS = ["+", "=", ",", ">", "|", "?", "Y", "N"]
NODES = ["v%d" % i for i in range(100)]
SPECIAL = ["<pad>", "<eos>"]
VOCAB = SPECIAL + DIGITS + SYMS + NODES
TOK = {t: i for i, t in enumerate(VOCAB)}
PAD, EOS = TOK["<pad>"], TOK["<eos>"]

TASKS = ("addition", "parity", "reachability", "assoc", "assoc_n4")   # reachability: Phase A only; assoc_n4: check
# (training range, in-distribution bin, out-of-distribution bins)
SPEC = {
    "addition": {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 40)]},
    "parity": {"train": (1, 16), "id": (1, 16), "ood": [(17, 32), (33, 48), (49, 64)]},
    "reachability": {"train": (4, 8), "id": (4, 8), "ood": [(9, 16), (17, 24), (25, 32)]},
    "assoc": {"train": (4, 16), "id": (4, 16), "ood": [(17, 32), (33, 48), (49, 64)]},
    # Phase A'' pre-run check only: associative recall with n fixed at 4 (the out-of-distribution bins as assoc)
    "assoc_n4": {"train": (4, 4), "id": (4, 4), "ood": [(17, 32), (33, 48), (49, 64)]},
}


def _num(rng, ndig):
    return rng.randrange(10) if ndig == 1 else rng.randrange(10 ** (ndig - 1), 10 ** ndig)


def _rev(v):
    return list(str(v)[::-1])


def addition(da, db, rng):
    a, b = _num(rng, da), _num(rng, db)
    return _rev(a) + ["+"] + _rev(b) + ["="], _rev(a + b)


def parity(n, rng):
    bits = [rng.randrange(2) for _ in range(n)]
    return [str(b) for b in bits] + ["="], [str(sum(bits) % 2)]


def reachability(n, rng):
    want = rng.random() < 0.5
    for _ in range(1000):
        names = rng.sample(NODES, n)
        m = min(round(1.5 * n), n * (n - 1))
        edges = set()
        while len(edges) < m:
            u, v = rng.sample(names, 2)
            edges.add((u, v))
        s, t = rng.sample(names, 2)
        adj = {}
        for u, v in edges:
            adj.setdefault(u, []).append(v)
        seen, stack = {s}, [s]
        while stack:
            u = stack.pop()
            for v in adj.get(u, []):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        if (t in seen) == want:
            break
    el = sorted(edges)
    rng.shuffle(el)
    p = []
    for u, v in el:
        p += [u, ">", v, ","]
    return p + ["|", s, "?", t, "="], ["Y" if t in seen else "N"]


def assoc(n, rng):
    """associative recall (Phase A'): k1 v1 ... kn vn | q = -> v; n distinct keys from the 100 node names, values
    single digits, the query one of the keys (uniform)"""
    keys = rng.sample(NODES, n)
    vals = [str(rng.randrange(10)) for _ in range(n)]
    q = rng.randrange(n)
    p = []
    for k, v in zip(keys, vals):
        p += [k, v]
    return p + ["|", keys[q], "="], [vals[q]]


def draw(task, rng, lo, hi, train_dist=False):
    """one example; for addition `train_dist` = both operand lengths independent uniform in lo..hi (the training /
    in-distribution draw), otherwise the longer operand's length is uniform in lo..hi.  Returns (prompt, answer,
    length) with length = the bin coordinate (longer operand / bits / nodes)."""
    if task == "addition":
        if train_dist:
            da, db = rng.randint(lo, hi), rng.randint(lo, hi)
        else:
            m = rng.randint(lo, hi)
            o = rng.randint(1, m)
            da, db = (m, o) if rng.random() < 0.5 else (o, m)
        p, a = addition(da, db, rng)
        return p, a, max(da, db)
    n = rng.randint(lo, hi)
    p, a = {"parity": parity, "reachability": reachability, "assoc": assoc, "assoc_n4": assoc}[task](n, rng)
    return p, a, n


def encode(prompt, answer):
    return [TOK[t] for t in prompt], [TOK[t] for t in answer] + [EOS]


def train_set(task, size, seed):
    rng = random.Random("train:%s:%d" % (task, seed))
    lo, hi = SPEC[task]["train"]
    return [encode(*draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(size)]


def eval_sets(task, n_id, n_ood):
    """{bin label: [(prompt ids, answer ids)]}: the in-distribution validation bin (the training distribution) and
    the out-of-distribution bins, each from its own fixed seed"""
    out = {}
    lo, hi = SPEC[task]["id"]
    rng = random.Random("eval:%s:id" % task)
    out["id_%d-%d" % (lo, hi)] = [encode(*draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n_id)]
    for lo, hi in SPEC[task]["ood"]:
        rng = random.Random("eval:%s:%d-%d" % (task, lo, hi))
        out["ood_%d-%d" % (lo, hi)] = [encode(*draw(task, rng, lo, hi)[:2]) for _ in range(n_ood)]
    return out
