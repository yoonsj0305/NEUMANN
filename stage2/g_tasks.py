"""G-0 candidate tasks (stage2/DESIGN.md 7.5): data generators only.  Stage-1 code (stage1/tasks.py) is not changed;
this module extends its vocabulary and copies its conventions.

Vocabulary: the stage-1 vocabulary (same ids, so <pad> = 0, <eos> = 1 and the digits keep their ids) followed by the
three new infix operators of 7.5: '-' (the design's minus), '*' (the design's times), '^' (xor).  Token-kind rule of
7.4 (task-independent): digits and bits are "digit"; the infix operator between the two operands ('+', '-', '*', '^')
is the "+" kind; '=', '|', the answer phase and everything else are as in stage 1 (stage1/pf.py token_classes).

Formats (prompt -> answer, then <eos>; numbers least significant digit first, as addition):
  copy         s_0 .. s_{n-1} =  ->  s_0 .. s_{n-1}                    digits i.i.d. uniform 0-9 (a digit string)
  reverse      s_0 .. s_{n-1} =  ->  s_{n-1} .. s_0                    digits i.i.d. uniform 0-9
  xor          x_0 .. x_{n-1} ^ y_0 .. y_{n-1} =  ->  (x_i xor y_i) for i = 0..n-1   bits i.i.d. uniform, same length
  subtraction  rev(a) - rev(b) =  ->  rev(a - b)                       a >= b; the answer is the number a - b
                                                                         (no leading zeros, as addition's rev(a + b))
  mul1         rev(a) * d =  ->  rev(a * d)                            d one digit 0-9 (as a 1-digit number of
                                                                         addition, 0 included); answer as above
Reference only, not a candidate (G-0a report): subtraction_pad = subtraction with the answer padded with zeros to
len(a) digits (rev of a - b written with exactly len(a) digits).

Length conventions (7.5):
  digit tasks (copy, reverse, subtraction, mul1, subtraction_pad) as addition: training 1-10, evaluation bins
    in-distribution 1-10, out-of-distribution 11-20 / 21-30 / 31-40.  One-operand tasks (copy, reverse; mul1's a)
    draw the length uniformly in the range.  subtraction draws its two operand lengths exactly as addition
    (training: independent uniform; evaluation: the longer length uniform in the bin, the other uniform in
    1..longer), draws the two numbers, and puts the larger first (a >= b), so the longer operand is always a.
  bit task (xor) as parity: training 1-16, bins 1-16 / 17-32 / 33-48 / 49-64; n uniform in the range.
Generation seeds follow stage 1: "train:<task>:<seed>", "eval:<task>:id", "eval:<task>:<lo>-<hi>", and the
selection-only set of 7.4 "select:<task>" (1,000 in-distribution examples, stage1/c4_select.selection_set).
"""
from __future__ import annotations
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stage1"))
import tasks as T1          # noqa: E402  (stage-1 vocabulary and number helpers; unchanged)

OPS = ["-", "*", "^"]
VOCAB = T1.VOCAB + OPS
TOK = {t: i for i, t in enumerate(VOCAB)}
PAD, EOS = T1.PAD, T1.EOS
assert all(TOK[t] == T1.TOK[t] for t in T1.VOCAB)
INFIX = ["+"] + OPS                                   # the "+" kind (7.4)
DIGITS = T1.DIGITS

TASKS = ("copy", "reverse", "xor", "subtraction", "mul1")
REFERENCE = ("subtraction_pad",)
DIGIT_SPEC = {"train": (1, 10), "id": (1, 10), "ood": [(11, 20), (21, 30), (31, 40)]}      # = addition
BIT_SPEC = {"train": (1, 16), "id": (1, 16), "ood": [(17, 32), (33, 48), (49, 64)]}        # = parity
SPEC = {t: (BIT_SPEC if t == "xor" else DIGIT_SPEC) for t in TASKS + REFERENCE}

_num, _rev = T1._num, T1._rev


def copy(n, rng):
    s = [str(rng.randrange(10)) for _ in range(n)]
    return s + ["="], list(s)


def reverse(n, rng):
    s = [str(rng.randrange(10)) for _ in range(n)]
    return s + ["="], s[::-1]


def xor(n, rng):
    x = [rng.randrange(2) for _ in range(n)]
    y = [rng.randrange(2) for _ in range(n)]
    return [str(v) for v in x] + ["^"] + [str(v) for v in y] + ["="], [str(p ^ q) for p, q in zip(x, y)]


def _sub_operands(da, db, rng):
    x, y = _num(rng, da), _num(rng, db)
    return (x, y) if x >= y else (y, x)


def subtraction(da, db, rng):
    a, b = _sub_operands(da, db, rng)
    return _rev(a) + ["-"] + _rev(b) + ["="], _rev(a - b)


def subtraction_pad(da, db, rng):
    a, b = _sub_operands(da, db, rng)
    la = len(str(a))
    return _rev(a) + ["-"] + _rev(b) + ["="], list(str(a - b).zfill(la)[::-1])


def mul1(n, rng):
    a, d = _num(rng, n), rng.randrange(10)
    return _rev(a) + ["*", str(d), "="], _rev(a * d)


TWO_LENGTHS = {"subtraction": subtraction, "subtraction_pad": subtraction_pad}
ONE_LENGTH = {"copy": copy, "reverse": reverse, "xor": xor, "mul1": mul1}


def draw(task, rng, lo, hi, train_dist=False):
    """one example (prompt, answer, bin length) -- the same draw logic as stage1/tasks.draw"""
    if task in TWO_LENGTHS:
        if train_dist:
            da, db = rng.randint(lo, hi), rng.randint(lo, hi)
        else:
            m = rng.randint(lo, hi)
            o = rng.randint(1, m)
            da, db = (m, o) if rng.random() < 0.5 else (o, m)
        p, a = TWO_LENGTHS[task](da, db, rng)
        return p, a, max(da, db)
    n = rng.randint(lo, hi)
    p, a = ONE_LENGTH[task](n, rng)
    return p, a, n


def encode(prompt, answer):
    return [TOK[t] for t in prompt], [TOK[t] for t in answer] + [EOS]


def train_set(task, size, seed):
    rng = random.Random("train:%s:%d" % (task, seed))
    lo, hi = SPEC[task]["train"]
    return [encode(*draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(size)]


def eval_sets(task, n_id, n_ood):
    out = {}
    lo, hi = SPEC[task]["id"]
    rng = random.Random("eval:%s:id" % task)
    out["id_%d-%d" % (lo, hi)] = [encode(*draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n_id)]
    for lo, hi in SPEC[task]["ood"]:
        rng = random.Random("eval:%s:%d-%d" % (task, lo, hi))
        out["ood_%d-%d" % (lo, hi)] = [encode(*draw(task, rng, lo, hi)[:2]) for _ in range(n_ood)]
    return out


def selection_set(task, n=1000):
    rng = random.Random("select:%s" % task)
    lo, hi = SPEC[task]["id"]
    return [encode(*draw(task, rng, lo, hi, train_dist=True)[:2]) for _ in range(n)]
