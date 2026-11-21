"""H-0 tasks with the BOS convention (stage2/DESIGN.md 9.1, 9.4, 9.6): data generators only.  stage1/tasks.py and
stage2/g_tasks.py are not changed; this module imports them.

Vocabulary: the G-0 vocabulary (stage2/g_tasks.py, 123 tokens, same ids) followed by one new token "<bos>" (id 123).
BOS is the first token of every prompt.  Token kind: "other" (it is not a digit, an infix operator, '=', '|' or a
node; stage1/pf.py token_classes gives it class 6), and it is not a PF separator.  Position 0 is the destination of the
PF "start" move (stage1/pf.py candidates), so with BOS the start move lands on BOS.

Tasks:
  the G-0 suite (copy, reverse, xor, mul1, prefix_sum) and the stage-1 tasks addition and parity: the same examples as
    without BOS (the same generation seeds and draws: g_tasks / stage1 tasks), with BOS put in front of the prompt;
  rev_xor (new held-out task, 9.6):  BOS x_0 .. x_{n-1} ^ y_0 .. y_{n-1} =  ->  (x_i xor y_i) for i = n-1 .. 0
    bits i.i.d. uniform, same length; the length convention of xor (training 1-16, bins 1-16 / 17-32 / 33-48 / 49-64);
    generation seeds "train:rev_xor:<seed>", "eval:rev_xor:id", "eval:rev_xor:<lo>-<hi>", "select:rev_xor".
"""
from __future__ import annotations
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "stage1"))
import g_tasks as G          # noqa: E402  (unchanged)
import tasks as T1           # noqa: E402  (unchanged)

BOS = "<bos>"
VOCAB = G.VOCAB + [BOS]
TOK = {t: i for i, t in enumerate(VOCAB)}
BOS_ID = TOK[BOS]
PAD, EOS = G.PAD, G.EOS
assert all(TOK[t] == G.TOK[t] for t in G.VOCAB) and BOS_ID == len(G.VOCAB)
OPS, DIGITS = G.OPS, G.DIGITS

SUITE = ("copy", "reverse", "xor", "mul1", "prefix_sum", "rev_xor")      # the H-0 task suite (9.6)
STAGE1 = ("addition", "parity")
SPEC = {t: G.SPEC[t] for t in G.SUITE}
SPEC["rev_xor"] = G.BIT_SPEC
SPEC.update({t: T1.SPEC[t] for t in STAGE1})


def rev_xor(n, rng):
    x = [rng.randrange(2) for _ in range(n)]
    y = [rng.randrange(2) for _ in range(n)]
    return [str(v) for v in x] + ["^"] + [str(v) for v in y] + ["="], [str(x[i] ^ y[i]) for i in reversed(range(n))]


def _draw_rev_xor(rng, lo, hi):
    return G.encode(*rev_xor(rng.randint(lo, hi), rng))


def _bos(exs):
    return [([BOS_ID] + list(e[0]),) + tuple(e[1:]) for e in exs]


def train_set(task, size, seed):
    if task == "rev_xor":
        rng = random.Random("train:%s:%d" % (task, seed))
        lo, hi = SPEC[task]["train"]
        return _bos([_draw_rev_xor(rng, lo, hi) for _ in range(size)])
    if task in STAGE1:
        return _bos(T1.train_set(task, size, seed))
    return _bos(G.train_set(task, size, seed))


def eval_sets(task, n_id, n_ood):
    if task == "rev_xor":
        out = {}
        lo, hi = SPEC[task]["id"]
        rng = random.Random("eval:%s:id" % task)
        out["id_%d-%d" % (lo, hi)] = _bos([_draw_rev_xor(rng, lo, hi) for _ in range(n_id)])
        for lo, hi in SPEC[task]["ood"]:
            rng = random.Random("eval:%s:%d-%d" % (task, lo, hi))
            out["ood_%d-%d" % (lo, hi)] = _bos([_draw_rev_xor(rng, lo, hi) for _ in range(n_ood)])
        return out
    src = T1.eval_sets(task, n_id, n_ood) if task in STAGE1 else G.eval_sets(task, n_id, n_ood)
    return {k: _bos(v) for k, v in src.items()}


def selection_set(task, n=1000):
    """the selection-only set "select:<task>" (stage1/c4_select.selection_set, the same seed and draw)"""
    rng = random.Random("select:%s" % task)
    lo, hi = SPEC[task]["id"]
    if task == "rev_xor":
        return _bos([_draw_rev_xor(rng, lo, hi) for _ in range(n)])
    if task in STAGE1:
        return _bos([T1.encode(*T1.draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n)])
    return _bos(G.selection_set(task, n))
