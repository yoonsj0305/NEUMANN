"""Stage 1 / week 1: length-generalisation tasks (train on short lengths, evaluate at 2-4x the training length).

Every task is a prompt -> answer token sequence; the loss is on the answer only.  Numbers are written least
significant digit first (the standard setting of Abacus-embedding work: digits of equal significance align).

  addition        a + b, each operand 1..n digits; answer: the sum
  multiplication  a * b, each operand 1..n digits; answer: the product
  sorting         n integers 0..999, comma separated; answer: the same integers ascending
  parity          n bits; answer: their xor
  reachability    a random directed graph on n nodes (ids drawn from a fixed pool of 100 names, ~1.5 n edges) and a
                  query (s, t); answer: Y / N, balanced
"Length" is n.  Training draws n uniformly from 1..L (arithmetic: each operand 1..n digits); evaluation uses exactly
n = L, 2L, 3L, 4L (arithmetic: both operands exactly n digits).
"""
from __future__ import annotations
import random

DIGITS = [str(i) for i in range(10)]
SYMS = ["+", "*", "=", ",", ">", "|", "?", "Y", "N"]
NODES = ["v%d" % i for i in range(100)]
SPECIAL = ["<pad>", "<eos>"]
VOCAB = SPECIAL + DIGITS + SYMS + NODES
TOK = {t: i for i, t in enumerate(VOCAB)}
PAD, EOS = TOK["<pad>"], TOK["<eos>"]

# training length L per task (evaluation at 2L, 3L, 4L)
TRAIN_LEN = {"addition": 10, "multiplication": 5, "sorting": 8, "parity": 16, "reachability": 8}
TASKS = tuple(TRAIN_LEN)


def _num(rng, ndig):
    if ndig == 1:
        return rng.randrange(10)
    return rng.randrange(10 ** (ndig - 1), 10 ** ndig)


def _rev(v):
    return list(str(v)[::-1])


def example(task, n, rng, exact=False):
    """(prompt tokens, answer tokens) as strings; n = the task length.  Arithmetic operands have 1..n digits each
    (training) or exactly n digits (exact=True, evaluation)."""
    if task == "addition":
        da, db = (n, n) if exact else (rng.randint(1, n), rng.randint(1, n))
        a, b = _num(rng, da), _num(rng, db)
        return _rev(a) + ["+"] + _rev(b) + ["="], _rev(a + b)
    if task == "multiplication":
        da, db = (n, n) if exact else (rng.randint(1, n), rng.randint(1, n))
        a, b = _num(rng, da), _num(rng, db)
        return _rev(a) + ["*"] + _rev(b) + ["="], _rev(a * b)
    if task == "sorting":
        xs = [rng.randrange(1000) for _ in range(n)]
        p = []
        for i, v in enumerate(xs):
            p += _rev(v) + ([","] if i < n - 1 else [])
        a = []
        for i, v in enumerate(sorted(xs)):
            a += _rev(v) + ([","] if i < n - 1 else [])
        return p + ["="], a
    if task == "parity":
        bits = [rng.randrange(2) for _ in range(n)]
        return [str(b) for b in bits] + ["="], [str(sum(bits) % 2)]
    if task == "reachability":
        want = rng.random() < 0.5
        for _ in range(1000):
            names = rng.sample(NODES, max(n, 2))
            m = max(1, round(1.5 * n))
            edges = set()
            while len(edges) < min(m, len(names) * (len(names) - 1)):
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
        p = []
        for u, v in sorted(edges, key=lambda e: rng.random()):
            p += [u, ">", v, ","]
        return p + ["|", s, "?", t, "="], ["Y" if t in seen else "N"]
    raise KeyError(task)


def encode(prompt, answer):
    return [TOK[t] for t in prompt], [TOK[t] for t in answer] + [EOS]


def dataset(task, size, max_len, seed):
    """`size` distinct training examples, n uniform in 1..max_len"""
    rng = random.Random("train:%s:%d" % (task, seed))
    out, seen, tries = [], set(), 0
    while len(out) < size and tries < 50 * size:
        tries += 1
        n = rng.randint(1, max_len)
        p, a = example(task, n, rng)
        key = (tuple(p), tuple(a))
        if key in seen:
            continue
        seen.add(key)
        out.append(encode(p, a))
    return out


def evalset(task, n, size, seed=0):
    """evaluation examples at exactly length n (a fixed seed, independent of the training draw)"""
    rng = random.Random("eval:%s:%d:%d" % (task, n, seed))
    return [encode(*example(task, n, rng, exact=True)) for _ in range(size)]
